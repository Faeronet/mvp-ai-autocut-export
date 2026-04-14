package handlers

import (
	"context"
	"net/http"
	"time"

	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/redis/go-redis/v9"

	"github.com/drawdigit/mvp/internal/config"
	"github.com/drawdigit/mvp/pkg/response"
)

type Health struct {
	Pool *pgxpool.Pool
	RDB  *redis.Client
	Cfg  config.Config
}

func (h *Health) Live(w http.ResponseWriter, r *http.Request) {
	response.OK(w, map[string]any{"status": "ok"})
}

func (h *Health) Ready(w http.ResponseWriter, r *http.Request) {
	ctx, cancel := context.WithTimeout(r.Context(), 2*time.Second)
	defer cancel()
	out := map[string]any{"postgres": "unknown", "redis": "unknown"}
	if err := h.Pool.Ping(ctx); err != nil {
		out["postgres"] = err.Error()
	} else {
		out["postgres"] = "ok"
	}
	if err := h.RDB.Ping(ctx).Err(); err != nil {
		out["redis"] = err.Error()
	} else {
		out["redis"] = "ok"
	}
	response.OK(w, out)
}

func (h *Health) ConfigProfiles(w http.ResponseWriter, r *http.Request) {
	response.OK(w, map[string]any{
		"profiles": []map[string]any{
			{"name": "balanced", "description": "Default trade-off"},
			{"name": "quality", "description": "Higher fidelity, more VRAM/time"},
			{"name": "low_vram", "description": "Aggressive resize, sequential"},
		},
		"gpu_profile": h.Cfg.ProfileGPU,
	})
}
