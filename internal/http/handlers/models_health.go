package handlers

import (
	"context"
	"encoding/json"
	"io"
	"net/http"
	"time"

	appcfg "github.com/drawdigit/mvp/internal/config"
	"github.com/drawdigit/mvp/pkg/response"
)

type ModelsHealth struct {
	Cfg    appcfg.Config
	Client *http.Client
}

func NewModelsHealth(cfg appcfg.Config) *ModelsHealth {
	return &ModelsHealth{
		Cfg: cfg,
		Client: &http.Client{
			Timeout: 10 * time.Second,
		},
	}
}

func (h *ModelsHealth) Get(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()
	out := map[string]any{
		"model_cache_dir": h.Cfg.ModelCacheDir,
		"services":        h.fetchServices(ctx),
	}
	response.OK(w, out)
}

func (h *ModelsHealth) fetchServices(ctx context.Context) map[string]any {
	services := map[string]string{
		"layout":  h.Cfg.LayoutServiceURL + "/health",
		"ocr":     h.Cfg.OCRServiceURL + "/health",
		"vector":  h.Cfg.VectorServiceURL + "/health",
		"export":  h.Cfg.ExportServiceURL + "/health",
	}
	res := make(map[string]any)
	for name, u := range services {
		req, err := http.NewRequestWithContext(ctx, http.MethodGet, u, nil)
		if err != nil {
			res[name] = map[string]any{"error": err.Error()}
			continue
		}
		resp, err := h.Client.Do(req)
		if err != nil {
			res[name] = map[string]any{"error": err.Error()}
			continue
		}
		body, _ := io.ReadAll(resp.Body)
		resp.Body.Close()
		var parsed any
		_ = json.Unmarshal(body, &parsed)
		res[name] = map[string]any{"http_status": resp.StatusCode, "body": parsed}
	}
	return res
}
