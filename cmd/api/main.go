package main

import (
	"context"
	"log/slog"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/drawdigit/mvp/internal/config"
	"github.com/drawdigit/mvp/internal/db"
	dbpool "github.com/drawdigit/mvp/internal/repositories/db"
	"github.com/drawdigit/mvp/internal/http/routes"
	jobrepo "github.com/drawdigit/mvp/internal/repositories/job"
	pagerepo "github.com/drawdigit/mvp/internal/repositories/page"
	eventrepo "github.com/drawdigit/mvp/internal/repositories/events"
	"github.com/drawdigit/mvp/internal/queue"
	"github.com/drawdigit/mvp/internal/services/jobs"
	"github.com/drawdigit/mvp/internal/storage"
	"github.com/drawdigit/mvp/pkg/logger"
	"github.com/drawdigit/mvp/pkg/telemetry"
)

func main() {
	cfg := config.Load()
	log := logger.New(cfg.LogLevel)
	slog.SetDefault(log)

	ctx := context.Background()
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

	rdb := queue.New(cfg.RedisAddr, "").RDB()
	defer rdb.Close()

	jobsRepo := jobrepo.NewRepository(pool)
	pagesRepo := pagerepo.NewRepository(pool)
	eventsRepo := eventrepo.NewRepository(pool)
	qc := queue.New(cfg.RedisAddr, "")
	layout := storage.NewLayout(cfg.DataDir)

	jobSvc := &jobs.Service{
		Cfg: cfg, Jobs: jobsRepo, Pages: pagesRepo, Events: eventsRepo,
		Layout: layout, Queue: qc,
	}

	apiHandler := routes.NewAPIRouter(cfg, pool, rdb, jobSvc)
	mux := http.NewServeMux()
	mux.Handle("/metrics", telemetry.Handler())
	mux.Handle("/", countRequests(apiHandler))

	srv := &http.Server{Addr: cfg.HTTPAddr, Handler: mux, ReadHeaderTimeout: 10 * time.Second}
	go func() {
		slog.Info("api listening", "addr", cfg.HTTPAddr)
		if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			slog.Error("listen", "err", err)
			os.Exit(1)
		}
	}()

	ch := make(chan os.Signal, 1)
	signal.Notify(ch, syscall.SIGINT, syscall.SIGTERM)
	<-ch
	shCtx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	_ = srv.Shutdown(shCtx)
}

func countRequests(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		telemetry.IncRequest()
		next.ServeHTTP(w, r)
	})
}
