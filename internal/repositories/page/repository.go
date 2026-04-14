package page

import (
	"context"

	"github.com/google/uuid"
	"github.com/jackc/pgx/v5/pgxpool"

	domain "github.com/drawdigit/mvp/internal/domain/page"
)

type Repository struct {
	pool *pgxpool.Pool
}

func NewRepository(pool *pgxpool.Pool) *Repository {
	return &Repository{pool: pool}
}

func (r *Repository) Create(ctx context.Context, p *domain.PageArtifact) error {
	_, err := r.pool.Exec(ctx, `
		INSERT INTO page_artifacts (id, job_id, source_image_name, source_image_path, status)
		VALUES ($1,$2,$3,$4,$5)
	`, p.ID, p.JobID, p.SourceImageName, p.SourceImagePath, p.Status)
	return err
}

func (r *Repository) ListByJob(ctx context.Context, jobID uuid.UUID) ([]domain.PageArtifact, error) {
	rows, err := r.pool.Query(ctx, `
		SELECT id, job_id, source_image_name, source_image_path, preprocessed_path, overlay_path, preview_path,
		       dxf_path, json_path, status, confidence_score, warnings_json, errors_json, created_at, updated_at
		FROM page_artifacts WHERE job_id=$1 ORDER BY source_image_name
	`, jobID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var out []domain.PageArtifact
	for rows.Next() {
		var p domain.PageArtifact
		if err := rows.Scan(
			&p.ID, &p.JobID, &p.SourceImageName, &p.SourceImagePath, &p.PreprocessedPath, &p.OverlayPath,
			&p.PreviewPath, &p.DXFPath, &p.JSONPath, &p.Status, &p.ConfidenceScore,
			&p.WarningsJSON, &p.ErrorsJSON, &p.CreatedAt, &p.UpdatedAt,
		); err != nil {
			return nil, err
		}
		out = append(out, p)
	}
	return out, rows.Err()
}

func (r *Repository) UpdatePaths(ctx context.Context, id uuid.UUID, pre, overlay, preview, dxf, jsonPath string) error {
	_, err := r.pool.Exec(ctx, `
		UPDATE page_artifacts SET preprocessed_path=$2, overlay_path=$3, preview_path=$4, dxf_path=$5, json_path=$6, updated_at=now()
		WHERE id=$1
	`, id, pre, overlay, preview, dxf, jsonPath)
	return err
}

func (r *Repository) SetStatus(ctx context.Context, id uuid.UUID, st domain.Status, conf float64, warnings, errors []byte) error {
	_, err := r.pool.Exec(ctx, `
		UPDATE page_artifacts SET status=$2, confidence_score=$3, warnings_json=$4::jsonb, errors_json=$5::jsonb, updated_at=now()
		WHERE id=$1
	`, id, st, conf, warnings, errors)
	return err
}
