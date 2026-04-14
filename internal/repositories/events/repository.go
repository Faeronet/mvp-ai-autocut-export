package events

import (
	"context"

	"github.com/google/uuid"
	"github.com/jackc/pgx/v5/pgxpool"
)

type Repository struct {
	pool *pgxpool.Pool
}

func NewRepository(pool *pgxpool.Pool) *Repository {
	return &Repository{pool: pool}
}

func (r *Repository) Append(ctx context.Context, jobID uuid.UUID, step, message, level string) error {
	_, err := r.pool.Exec(ctx, `
		INSERT INTO job_events (job_id, step, message, level) VALUES ($1,$2,$3,$4)
	`, jobID, step, message, level)
	return err
}

func (r *Repository) Recent(ctx context.Context, jobID uuid.UUID, limit int) ([]EventRow, error) {
	if limit <= 0 || limit > 1000 {
		limit = 200
	}
	rows, err := r.pool.Query(ctx, `
		SELECT step, message, level, created_at FROM job_events WHERE job_id=$1 ORDER BY created_at DESC LIMIT $2
	`, jobID, limit)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var out []EventRow
	for rows.Next() {
		var e EventRow
		if err := rows.Scan(&e.Step, &e.Message, &e.Level, &e.CreatedAt); err != nil {
			return nil, err
		}
		out = append(out, e)
	}
	return out, rows.Err()
}

type EventRow struct {
	Step      string
	Message   string
	Level     string
	CreatedAt interface{}
}
