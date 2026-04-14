package main

import (
	"bufio"
	"bytes"
	"context"
	"io"
	"log/slog"
	"net/http"
	"net/http/httptest"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/drawdigit/mvp/internal/config"
	"github.com/drawdigit/mvp/internal/db"
	dbpool "github.com/drawdigit/mvp/internal/repositories/db"
	jobrepo "github.com/drawdigit/mvp/internal/repositories/job"
	pagerepo "github.com/drawdigit/mvp/internal/repositories/page"
	eventrepo "github.com/drawdigit/mvp/internal/repositories/events"
	"github.com/drawdigit/mvp/internal/mcp/resources"
	"github.com/drawdigit/mvp/internal/mcp/server"
	"github.com/drawdigit/mvp/internal/mcp/session"
	"github.com/drawdigit/mvp/internal/mcp/tools"
	"github.com/drawdigit/mvp/internal/queue"
	"github.com/drawdigit/mvp/internal/services/jobs"
	"github.com/drawdigit/mvp/internal/storage"
	"github.com/drawdigit/mvp/pkg/logger"
)

func main() {
	cfg := config.Load()
	slog.SetDefault(logger.New(cfg.LogLevel))

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
	jobSvc := &jobs.Service{
		Cfg: cfg, Jobs: jobsRepo, Pages: pagesRepo, Events: eventsRepo,
		Layout: storage.NewLayout(cfg.DataDir), Queue: qc,
	}

	h := &server.Handler{
		Sessions:   session.NewStore(),
		Executor:   &tools.Executor{Jobs: jobSvc, RDB: rdb, Cfg: cfg},
		Resources:  &resources.Resolver{Jobs: jobSvc},
		AllowHosts: append(cfg.MCPAllowedHosts, "localhost", "127.0.0.1"),
	}

	if len(os.Args) > 1 && os.Args[1] == "--stdio" {
		runStdio(h)
		return
	}

	addr := getenv("MCP_HTTP_ADDR", ":8090")
	mux := http.NewServeMux()
	mux.Handle("/mcp", h)
	srv := &http.Server{Addr: addr, Handler: mux, ReadHeaderTimeout: 10 * time.Second}
	go func() {
		slog.Info("mcp http", "addr", addr, "path", "/mcp")
		if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			slog.Error("mcp listen", "err", err)
			os.Exit(1)
		}
	}()

	ch := make(chan os.Signal, 1)
	signal.Notify(ch, syscall.SIGINT, syscall.SIGTERM)
	<-ch
	shCtx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	_ = srv.Shutdown(shCtx)
}

func runStdio(h http.Handler) {
	sc := bufio.NewScanner(os.Stdin)
	for sc.Scan() {
		line := sc.Bytes()
		req := httptest.NewRequest(http.MethodPost, "/mcp", bytes.NewReader(line))
		req.Header.Set("Mcp-Protocol-Version", "2024-11-05")
		rec := httptest.NewRecorder()
		h.ServeHTTP(rec, req)
		_, _ = io.Copy(os.Stdout, rec.Body)
		_, _ = os.Stdout.WriteString("\n")
	}
}

func getenv(k, d string) string {
	if v := os.Getenv(k); v != "" {
		return v
	}
	return d
}
