package main

import (
	"context"
	"log/slog"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/google/uuid"

	"github.com/drawdigit/mvp/internal/clients/httpclient"
	"github.com/drawdigit/mvp/internal/config"
	"github.com/drawdigit/mvp/internal/db"
	"github.com/drawdigit/mvp/internal/pipeline"
	"github.com/drawdigit/mvp/internal/pipeline/contracts"
	"github.com/drawdigit/mvp/internal/pipeline/progress"
	"github.com/drawdigit/mvp/internal/queue"
	dbpool "github.com/drawdigit/mvp/internal/repositories/db"
	eventrepo "github.com/drawdigit/mvp/internal/repositories/events"
	jobrepo "github.com/drawdigit/mvp/internal/repositories/job"
	pagerepo "github.com/drawdigit/mvp/internal/repositories/page"
	"github.com/drawdigit/mvp/internal/storage"
	"github.com/drawdigit/mvp/pkg/logger"
)

func main() {
	cfg := config.Load()
	slog.SetDefault(logger.New(cfg.LogLevel))

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	pool, err := dbpool.NewPool(ctx, cfg.PostgresDSN)
	if err != nil {
		slog.Error("postgres", "err", err)
		os.Exit(1)
	}
	defer pool.Close()
	if err := db.RunMigrations(ctx, pool); err != nil {
		slog.Error("migrate", "err", err)
		os.Exit(1)
	}

	qc := queue.New(cfg.RedisAddr, "")
	lock := queue.NewGPULock(qc.RDB(), cfg.GPUSemaphoreKey, cfg.GPULockTTL)

	jobsRepo := jobrepo.NewRepository(pool)
	pagesRepo := pagerepo.NewRepository(pool)
	eventsRepo := eventrepo.NewRepository(pool)
	emit := &progress.Emitter{Jobs: jobsRepo, Events: eventsRepo}
	layoutSt := storage.NewLayout(cfg.DataDir)

	_ = httpclient.New(cfg.RequestTimeout)

	go func() {
		for {
			msg, err := qc.BlockingPop(ctx, 5*time.Second)
			if err != nil {
				slog.Warn("queue", "err", err)
				time.Sleep(time.Second)
				continue
			}
			if msg == nil {
				continue
			}
			go runOne(ctx, cfg, jobsRepo, pagesRepo, emit, layoutSt, lock, qc, msg.JobID)
		}
	}()

	ch := make(chan os.Signal, 1)
	signal.Notify(ch, syscall.SIGINT, syscall.SIGTERM)
	<-ch
	cancel()
}

func runOne(
	ctx context.Context,
	cfg config.Config,
	jobsRepo *jobrepo.Repository,
	pagesRepo *pagerepo.Repository,
	emit *progress.Emitter,
	layoutSt storage.Layout,
	lock *queue.GPULock,
	qc *queue.Client,
	jobID uuid.UUID,
) {
	j, err := jobsRepo.Get(ctx, jobID)
	if err != nil {
		slog.Error("job load failed", "id", jobID, "err", err)
		return
	}
	if j == nil {
		slog.Warn("job not in postgres (stale redis queue after DB reset?)", "id", jobID)
		return
	}
	pc := &contracts.PipelineContext{
		Ctx: ctx, JobID: jobID,
		Config:  cfg,
		Profile: contracts.ParseProfile(j.Profile),
		Mock:    cfg.MockPipeline,
	}
	deps := pipeline.RunnerDeps{
		Config: cfg, Jobs: jobsRepo, Pages: pagesRepo,
		Layout: layoutSt, Emit: emit, Queue: qc, GPULock: lock,
	}
	if err := pipeline.RunJob(deps, pc, j.InputArchivePath); err != nil {
		slog.Error("pipeline failed", "job", jobID, "err", err)
		_ = jobsRepo.SetFailed(ctx, jobID, err.Error())
	}
}
