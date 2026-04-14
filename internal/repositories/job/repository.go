package job

import (
	"context"
	"encoding/json"
	"errors"
	"time"

	"github.com/google/uuid"
	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"

	domain "github.com/drawdigit/mvp/internal/domain/job"
)

type Repository struct {
	pool *pgxpool.Pool
}

func NewRepository(pool *pgxpool.Pool) *Repository {
	return &Repository{pool: pool}
}

func (r *Repository) Create(ctx context.Context, j *domain.Job) error {
	timings := j.TimingsJSON
	if len(timings) == 0 {
		timings = []byte(`{}`)
	}
	_, err := r.pool.Exec(ctx, `
		INSERT INTO jobs (id, status, input_archive_name, input_archive_path, profile, timings_json)
		VALUES ($1,$2,$3,$4,$5,$6)
	`, j.ID, j.Status, j.InputArchiveName, j.InputArchivePath, j.Profile, timings)
	return err
}

func (r *Repository) Get(ctx context.Context, id uuid.UUID) (*domain.Job, error) {
	row := r.pool.QueryRow(ctx, `
		SELECT id, created_at, updated_at, status, input_archive_name, input_archive_path,
		       COALESCE(result_archive_path, ''),
		       total_pages, completed_pages, failed_pages, progress_percent,
		       COALESCE(current_step, ''), COALESCE(error_message, ''),
		       warnings_count, profile, timings_json
		FROM jobs WHERE id = $1
	`, id)
	var j domain.Job
	var timings []byte
	err := row.Scan(
		&j.ID, &j.CreatedAt, &j.UpdatedAt, &j.Status, &j.InputArchiveName, &j.InputArchivePath, &j.ResultArchivePath,
		&j.TotalPages, &j.CompletedPages, &j.FailedPages, &j.ProgressPercent, &j.CurrentStep, &j.ErrorMessage,
		&j.WarningsCount, &j.Profile, &timings,
	)
	if err != nil {
		if errors.Is(err, pgx.ErrNoRows) {
			return nil, nil
		}
		return nil, err
	}
	j.TimingsJSON = timings
	return &j, nil
}

func (r *Repository) UpdateStatus(ctx context.Context, id uuid.UUID, status domain.Status, step string, progress int) error {
	_, err := r.pool.Exec(ctx, `
		UPDATE jobs SET status=$2, current_step=$3, progress_percent=$4, updated_at=now() WHERE id=$1
	`, id, status, step, progress)
	return err
}

func (r *Repository) SetResultPath(ctx context.Context, id uuid.UUID, path string) error {
	_, err := r.pool.Exec(ctx, `UPDATE jobs SET result_archive_path=$2, updated_at=now() WHERE id=$1`, id, path)
	return err
}

func (r *Repository) SetPages(ctx context.Context, id uuid.UUID, total, completed, failed int) error {
	_, err := r.pool.Exec(ctx, `
		UPDATE jobs SET total_pages=$2, completed_pages=$3, failed_pages=$4, updated_at=now() WHERE id=$1
	`, id, total, completed, failed)
	return err
}

func (r *Repository) SetFailed(ctx context.Context, id uuid.UUID, msg string) error {
	_, err := r.pool.Exec(ctx, `UPDATE jobs SET status=$2, error_message=$3, updated_at=now() WHERE id=$1`,
		id, domain.StatusFailed, msg)
	return err
}

func (r *Repository) SetCompleted(ctx context.Context, id uuid.UUID, status domain.Status, warnings int) error {
	_, err := r.pool.Exec(ctx, `
		UPDATE jobs SET status=$2, progress_percent=100, warnings_count=$3, updated_at=now() WHERE id=$1
	`, id, status, warnings)
	return err
}

func (r *Repository) SetTimings(ctx context.Context, id uuid.UUID, timings map[string]any) error {
	b, _ := json.Marshal(timings)
	_, err := r.pool.Exec(ctx, `UPDATE jobs SET timings_json=$2::jsonb, updated_at=now() WHERE id=$1`, id, b)
	return err
}

func (r *Repository) List(ctx context.Context, limit int) ([]domain.Job, error) {
	if limit <= 0 || limit > 500 {
		limit = 50
	}
	rows, err := r.pool.Query(ctx, `
		SELECT id, created_at, updated_at, status, input_archive_name, input_archive_path,
		       COALESCE(result_archive_path, ''),
		       total_pages, completed_pages, failed_pages, progress_percent,
		       COALESCE(current_step, ''), COALESCE(error_message, ''),
		       warnings_count, profile, timings_json
		FROM jobs ORDER BY created_at DESC LIMIT $1
	`, limit)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var out []domain.Job
	for rows.Next() {
		var j domain.Job
		var timings []byte
		if err := rows.Scan(
			&j.ID, &j.CreatedAt, &j.UpdatedAt, &j.Status, &j.InputArchiveName, &j.InputArchivePath, &j.ResultArchivePath,
			&j.TotalPages, &j.CompletedPages, &j.FailedPages, &j.ProgressPercent, &j.CurrentStep, &j.ErrorMessage,
			&j.WarningsCount, &j.Profile, &timings,
		); err != nil {
			return nil, err
		}
		j.TimingsJSON = timings
		out = append(out, j)
	}
	return out, rows.Err()
}

func (r *Repository) Touch(ctx context.Context, id uuid.UUID) error {
	_, err := r.pool.Exec(ctx, `UPDATE jobs SET updated_at=now() WHERE id=$1`, id)
	return err
}

func (r *Repository) UpdateStatusOnly(ctx context.Context, id uuid.UUID, status domain.Status) error {
	_, err := r.pool.Exec(ctx, `UPDATE jobs SET status=$2, updated_at=now() WHERE id=$1`, id, status)
	return err
}

func Now() time.Time { return time.Now().UTC() }
