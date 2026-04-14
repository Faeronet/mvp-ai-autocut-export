#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List

from iteropt.analyze import collect_metrics_from_result_zip, quality_score
from iteropt.api_client import APIClient
from iteropt.archives import build_zip_from_images, discover_archives, extract_images_for_comparison
from iteropt.config import IterationConfig
from iteropt.fs_utils import ensure_iter_dirs, write_json, write_simple_yaml
from iteropt.reporting import write_summary_md


def _git_changed_files(repo_root: Path) -> List[str]:
    try:
        r = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
        )
    except Exception:
        return []
    out: List[str] = []
    for ln in r.stdout.splitlines():
        if not ln.strip():
            continue
        out.append(ln[3:])
    return out


def _flatten_metrics(per_archive: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not per_archive:
        return {"page_count": 0}
    metric_keys = [
        "page_count",
        "layout_zone_count_avg",
        "title_block_coverage_avg",
        "spec_table_coverage_avg",
        "ocr_avg_conf_avg",
        "ocr_junk_ratio_avg",
        "table_cell_count_avg",
        "table_text_fill_ratio_avg",
        "geom_line_count_avg",
        "frame_leakage_avg",
        "table_leakage_avg",
        "review_density_avg",
        "page_confidence_avg",
        "line_density_similarity_avg",
    ]
    out: Dict[str, Any] = {}
    for k in metric_keys:
        vals = [float(m.get(k, 0.0)) for m in per_archive]
        out[k] = sum(vals) / max(1, len(vals))
    out["warnings_union"] = sorted({w for m in per_archive for w in m.get("warnings_union", [])})
    out["archives"] = per_archive
    return out


def run_iteration(cfg: IterationConfig, archives: List[Path], repo_root: Path) -> Dict[str, Any]:
    ensure_iter_dirs(cfg.iter_dir)
    client = APIClient(cfg.api_base, timeout_seconds=max(30, cfg.timeout_seconds // 2))
    health = client.health()
    write_json(cfg.iter_dir / "logs" / "health.json", health)

    per_archive_metrics: List[Dict[str, Any]] = []
    per_archive_runs: List[Dict[str, Any]] = []
    for archive in archives:
        run_dir = cfg.iter_dir / "artifacts" / archive.stem
        run_dir.mkdir(parents=True, exist_ok=True)
        src_dir = run_dir / "source_extract"
        src_images = extract_images_for_comparison(archive, src_dir)
        submitted = archive
        job_id = client.upload_archive(submitted, cfg.profile)
        final_job = client.wait_for_job(job_id, cfg.poll_seconds, cfg.timeout_seconds)
        # If RAR extraction fails inside worker on a broken member, retry with locally rebuilt ZIP
        # from successfully extracted images (keeps the run alive for quality analysis).
        if (
            str(final_job.get("status", "")).lower() == "failed"
            and archive.suffix.lower() == ".rar"
            and src_images
        ):
            rebuilt_zip = build_zip_from_images(src_images, src_dir, run_dir / "rebuilt_from_rar.zip")
            if rebuilt_zip is not None:
                submitted = rebuilt_zip
                job_id = client.upload_archive(submitted, cfg.profile)
                final_job = client.wait_for_job(job_id, cfg.poll_seconds, cfg.timeout_seconds)
        report = client.get_report(job_id)
        result_archive_path = str(final_job.get("result_archive_path") or "")
        if not result_archive_path:
            metrics = {
                "archive": archive.name,
                "submitted_archive": submitted.name,
                "job_id": job_id,
                "page_count": 0,
                "warnings_union": ["job_completed_without_result_archive"],
                "job_status": final_job.get("status"),
            }
        else:
            zip_path = client.download_result(job_id, run_dir / "result.zip")
            extracted_result = run_dir / "result_unpacked"
            metrics = collect_metrics_from_result_zip(
                result_zip=zip_path,
                extracted_dir=extracted_result,
                src_images=src_images,
                side_by_side_dir=cfg.iter_dir / "side_by_side" / archive.stem,
            )
            # Keep quick-access iteration-level visual artifacts.
            for p in extracted_result.rglob("preview/*.png"):
                shutil.copy2(p, cfg.iter_dir / "previews" / f"{archive.stem}__{p.name}")
            for p in extracted_result.rglob("preview_diagnostic/*.png"):
                shutil.copy2(p, cfg.iter_dir / "diagnostics" / f"{archive.stem}__{p.name}")
        metrics["archive"] = archive.name
        metrics["submitted_archive"] = submitted.name
        metrics["job_id"] = job_id
        per_archive_metrics.append(metrics)
        per_archive_runs.append(
            {"archive": archive.name, "job_id": job_id, "status": final_job.get("status"), "report": report}
        )
        write_json(run_dir / "job.json", final_job)
        write_json(run_dir / "report.json", report)
        write_json(cfg.iter_dir / "reports" / f"{archive.stem}.json", report)
        write_json(run_dir / "metrics.json", metrics)

    agg = _flatten_metrics(per_archive_metrics)
    row: Dict[str, Any] = {
        "iteration": cfg.iteration_id,
        "profile": cfg.profile,
        **{k: agg.get(k) for k in agg.keys() if k != "archives"},
    }
    row["quality_score"] = quality_score(row)
    row["changed_files"] = _git_changed_files(repo_root)
    write_json(cfg.iter_dir / "metrics.json", row)
    write_simple_yaml(
        cfg.iter_dir / "config_used.yaml",
        {
            "profile": cfg.profile,
            "api_base": cfg.api_base,
            "poll_seconds": cfg.poll_seconds,
            "timeout_seconds": cfg.timeout_seconds,
            "iteration_id": cfg.iteration_id,
        },
    )
    write_json(cfg.iter_dir / "model_info.json", {"note": "model versions are captured through service health/model endpoints"})
    (cfg.iter_dir / "changed_files.txt").write_text("\n".join(row["changed_files"]), encoding="utf-8")
    write_summary_md(cfg.iter_dir / "summary.md", row, archives)
    return row


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Iterative full-run optimizer over test_metr archives.")
    p.add_argument("--api-base", default="http://localhost:8080")
    p.add_argument("--test-metr-dir", default="test_metr")
    p.add_argument("--experiments-dir", default="experiments")
    p.add_argument("--iterations", type=int, default=2)
    p.add_argument("--profiles", default="balanced,quality")
    p.add_argument("--poll-seconds", type=float, default=2.5)
    p.add_argument("--timeout-seconds", type=int, default=3600)
    p.add_argument("--plateau-delta", type=float, default=0.005)
    return p.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    test_metr_dir = (repo_root / args.test_metr_dir).resolve()
    experiments_dir = (repo_root / args.experiments_dir).resolve()
    experiments_dir.mkdir(parents=True, exist_ok=True)
    archives = discover_archives(test_metr_dir)
    if not archives:
        raise SystemExit(f"no archives found in {test_metr_dir}")

    profiles = [p.strip() for p in args.profiles.split(",") if p.strip()]
    leaderboard: List[Dict[str, Any]] = []
    best_score = -1.0
    stagnant = 0
    for i in range(1, args.iterations + 1):
        profile = profiles[(i - 1) % len(profiles)]
        cfg = IterationConfig(
            iteration_id=i,
            profile=profile,
            api_base=args.api_base,
            poll_seconds=args.poll_seconds,
            timeout_seconds=args.timeout_seconds,
            test_metr_dir=test_metr_dir,
            experiments_dir=experiments_dir,
        )
        row = run_iteration(cfg, archives, repo_root)
        leaderboard.append(row)
        if row["quality_score"] > best_score + args.plateau_delta:
            best_score = row["quality_score"]
            stagnant = 0
            (cfg.iter_dir / "best_flag.txt").write_text("best_so_far\n", encoding="utf-8")
        else:
            stagnant += 1
        if stagnant >= 2:
            break

    leaderboard = sorted(leaderboard, key=lambda x: x["quality_score"], reverse=True)
    write_json(experiments_dir / "leaderboard.json", {"rows": leaderboard})
    md = ["# Iteration Leaderboard", ""]
    for row in leaderboard:
        md.append(
            f"- iter {row['iteration']:03d} | profile `{row['profile']}` | score `{row['quality_score']:.4f}` | pages `{row.get('page_count', 0):.1f}`"
        )
    (experiments_dir / "leaderboard.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
