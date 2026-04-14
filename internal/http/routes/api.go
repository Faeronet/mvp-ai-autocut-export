package routes

import (
	"net/http"

	"github.com/go-chi/chi/v5"
	"github.com/go-chi/chi/v5/middleware"
	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/redis/go-redis/v9"

	appcfg "github.com/drawdigit/mvp/internal/config"
	httph "github.com/drawdigit/mvp/internal/http/handlers"
	mw "github.com/drawdigit/mvp/internal/http/middleware"
	jobrepo "github.com/drawdigit/mvp/internal/repositories/job"
	"github.com/drawdigit/mvp/internal/services/jobs"
)

func NewAPIRouter(cfg appcfg.Config, pool *pgxpool.Pool, rdb *redis.Client, jobSvc *jobs.Service) http.Handler {
	r := chi.NewRouter()
	r.Use(middleware.Recoverer)
	r.Use(mw.RequestID)
	r.Use(mw.CORS(cfg.AllowedOrigins))

	h := &httph.Jobs{Svc: jobSvc}
	hr := &httph.Health{Pool: pool, RDB: rdb, Cfg: cfg}
	mh := httph.NewModelsHealth(cfg)
	sse := &httph.SSE{Jobs: jobrepo.NewRepository(pool)}

	r.Route("/api/v1", func(r chi.Router) {
		r.Get("/health", hr.Ready)
		r.Get("/health/models", mh.Get)
		r.Get("/config/profiles", hr.ConfigProfiles)
		r.Route("/jobs", func(r chi.Router) {
			r.Post("/upload", h.Upload)
			r.Get("/", h.List)
			r.Get("/{id}", h.Get)
			r.Get("/{id}/report", h.Report)
			r.Get("/{id}/download", h.Download)
			r.Get("/{id}/events", sse.JobEvents)
			r.Post("/{id}/cancel", h.Cancel)
			r.Post("/{id}/retry", h.Retry)
		})
	})
	r.Get("/healthz", hr.Live)
	return r
}
