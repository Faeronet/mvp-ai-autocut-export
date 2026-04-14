package progress

import (
	"context"

	"github.com/google/uuid"

	eventrepo "github.com/drawdigit/mvp/internal/repositories/events"
	jobrepo "github.com/drawdigit/mvp/internal/repositories/job"
	domainjob "github.com/drawdigit/mvp/internal/domain/job"
)

type Emitter struct {
	Jobs   *jobrepo.Repository
	Events *eventrepo.Repository
}

func (e *Emitter) Step(ctx context.Context, jobID uuid.UUID, status domainjob.Status, step string, pct int) error {
	if err := e.Jobs.UpdateStatus(ctx, jobID, status, step, pct); err != nil {
		return err
	}
	return e.Events.Append(ctx, jobID, step, step, "info")
}

func (e *Emitter) Log(ctx context.Context, jobID uuid.UUID, step, msg, level string) error {
	return e.Events.Append(ctx, jobID, step, msg, level)
}
