from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Dict

import requests


class APIClient:
    def __init__(self, base_url: str, timeout_seconds: int = 30) -> None:
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.timeout = timeout_seconds

    def health(self) -> Dict[str, Any]:
        r = self.session.get(f"{self.base_url}/api/v1/health", timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    def upload_archive(self, archive_path: Path, profile: str) -> str:
        with archive_path.open("rb") as fh:
            files = {"file": (archive_path.name, fh, "application/octet-stream")}
            data = {"profile": profile}
            r = self.session.post(
                f"{self.base_url}/api/v1/jobs/upload",
                files=files,
                data=data,
                timeout=self.timeout,
            )
        r.raise_for_status()
        payload = r.json().get("data") or r.json()
        return payload["job_id"]

    def get_job(self, job_id: str) -> Dict[str, Any]:
        r = self.session.get(f"{self.base_url}/api/v1/jobs/{job_id}", timeout=self.timeout)
        r.raise_for_status()
        return r.json().get("data") or r.json()

    def get_report(self, job_id: str) -> Dict[str, Any]:
        r = self.session.get(f"{self.base_url}/api/v1/jobs/{job_id}/report", timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    def download_result(self, job_id: str, out_path: Path) -> Path:
        r = self.session.get(
            f"{self.base_url}/api/v1/jobs/{job_id}/download", timeout=max(120, self.timeout), stream=True
        )
        r.raise_for_status()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open("wb") as fh:
            for chunk in r.iter_content(chunk_size=1 << 20):
                if chunk:
                    fh.write(chunk)
        return out_path

    def wait_for_job(self, job_id: str, poll_seconds: float, timeout_seconds: int) -> Dict[str, Any]:
        t0 = time.time()
        while True:
            data = self.get_job(job_id)
            status = str(data.get("status", "")).lower()
            if status in {"completed", "partial_success", "failed", "cancelled"}:
                return data
            if time.time() - t0 > timeout_seconds:
                raise TimeoutError(f"job {job_id} did not finish in {timeout_seconds}s")
            time.sleep(poll_seconds)
