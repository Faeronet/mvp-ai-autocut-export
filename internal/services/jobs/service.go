package jobs

import (
	"context"
	"io"
	"os"
	"path/filepath"

	"github.com/google/uuid"

	"github.com/drawdigit/mvp/internal/config"
	"github.com/drawdigit/mvp/internal/queue"
	"github.com/drawdigit/mvp/internal/storage"
	domainjob "github.com/drawdigit/mvp/internal/domain/job"
	jobrepo "github.com/drawdigit/mvp/internal/repositories/job"
	eventrepo "github.com/drawdigit/mvp/internal/repositories/events"
	pagerepo "github.com/drawdigit/mvp/internal/repositories/page"
	"github.com/drawdigit/mvp/pkg/apperrors"
)

type Service struct {
	Cfg    config.Config
	Jobs   *jobrepo.Repository
	Pages  *pagerepo.Repository
	Events *eventrepo.Repository
	Layout storage.Layout
	Queue  *queue.Client
}

func (s *Service) CreateFromUpload(ctx context.Context, filename string, r io.Reader, profile string) (*domainjob.Job, error) {
	if profile == "" {
		profile = "balanced"
	}
	id := uuid.New()
	job := &domainjob.Job{
		ID:               id,
		Status:           domainjob.StatusQueued,
		InputArchiveName: filename,
		InputArchivePath: filepath.Join(s.Layout.JobDir(id), "input", filename),
		Profile:          profile,
	}
	if err := storage.EnsureDir(filepath.Dir(job.InputArchivePath)); err != nil {
		return nil, err
	}
	f, err := os.Create(job.InputArchivePath)
	if err != nil {
		return nil, err
	}
	defer f.Close()
	if _, err := io.Copy(f, r); err != nil {
		return nil, err
	}
	if err := s.Jobs.Create(ctx, job); err != nil {
		return nil, err
	}
	_ = s.Events.Append(ctx, id, "upload", "archive stored", "info")
	if err := s.Queue.Enqueue(ctx, id); err != nil {
		return nil, err
	}
	return job, nil
}

func (s *Service) Get(ctx context.Context, id uuid.UUID) (*domainjob.Job, error) {
	j, err := s.Jobs.Get(ctx, id)
	if err != nil {
		return nil, err
	}
	if j == nil {
		return nil, apperrors.New(apperrors.KindNotFound, "job_not_found", "job not found")
	}
	return j, nil
}

func (s *Service) List(ctx context.Context, limit int) ([]domainjob.Job, error) {
	return s.Jobs.List(ctx, limit)
}

func (s *Service) Cancel(ctx context.Context, id uuid.UUID) error {
	j, err := s.Jobs.Get(ctx, id)
	if err != nil {
		return apperrors.New(apperrors.KindNotFound, "job_not_found", "job not found")
	}
	if domainjob.IsTerminal(j.Status) {
		return apperrors.New(apperrors.KindConflict, "job_terminal", "job already finished")
	}
	return s.Jobs.UpdateStatusOnly(ctx, id, domainjob.StatusCancelled)
}

func (s *Service) Retry(ctx context.Context, id uuid.UUID, profile string) (*domainjob.Job, error) {
	old, err := s.Jobs.Get(ctx, id)
	if err != nil {
		return nil, apperrors.New(apperrors.KindNotFound, "job_not_found", "job not found")
	}
	newID := uuid.New()
	p := old.Profile
	if profile != "" {
		p = profile
	}
	j := &domainjob.Job{
		ID:               newID,
		Status:           domainjob.StatusQueued,
		InputArchiveName: old.InputArchiveName,
		InputArchivePath: filepath.Join(s.Layout.JobDir(newID), "input", old.InputArchiveName),
		Profile:          p,
	}
	if err := storage.EnsureDir(filepath.Dir(j.InputArchivePath)); err != nil {
		return nil, err
	}
	if err := storage.CopyFile(j.InputArchivePath, old.InputArchivePath); err != nil {
		return nil, apperrors.Wrap(apperrors.KindInternal, "retry_copy_failed", "could not copy input archive", err)
	}
	if err := s.Jobs.Create(ctx, j); err != nil {
		return nil, err
	}
	_ = s.Events.Append(ctx, newID, "retry", "retried from "+id.String(), "info")
	if err := s.Queue.Enqueue(ctx, newID); err != nil {
		return nil, err
	}
	return j, nil
}
