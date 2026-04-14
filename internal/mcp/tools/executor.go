package tools

import (
	"context"
	"encoding/json"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"time"

	"github.com/google/uuid"
	"github.com/redis/go-redis/v9"

	"github.com/drawdigit/mvp/internal/config"
	"github.com/drawdigit/mvp/internal/queue"
	"github.com/drawdigit/mvp/internal/services/jobs"
)

type Executor struct {
	Jobs *jobs.Service
	RDB  *redis.Client
	Cfg  config.Config
}

type CallParams struct {
	Name      string          `json:"name"`
	Arguments json.RawMessage `json:"arguments,omitempty"`
}

func (e *Executor) Call(ctx context.Context, name string, args json.RawMessage) (any, error) {
	switch name {
	case "submit_archive":
		var p struct {
			LocalPath         string `json:"local_path"`
			ProcessingProfile string `json:"processing_profile"`
		}
		_ = json.Unmarshal(args, &p)
		f, err := os.Open(p.LocalPath)
		if err != nil {
			return nil, err
		}
		defer f.Close()
		base := filepath.Base(p.LocalPath)
		j, err := e.Jobs.CreateFromUpload(ctx, base, f, p.ProcessingProfile)
		if err != nil {
			return nil, err
		}
		return map[string]any{"job_id": j.ID.String(), "accepted": true}, nil
	case "get_job_status":
		var p struct{ JobID string `json:"job_id"` }
		_ = json.Unmarshal(args, &p)
		id, _ := uuid.Parse(p.JobID)
		j, err := e.Jobs.Get(ctx, id)
		if err != nil {
			return nil, err
		}
		return map[string]any{
			"status": j.Status, "current_step": j.CurrentStep, "progress_percent": j.ProgressPercent,
			"warnings_count": j.WarningsCount, "errors_count": j.FailedPages,
		}, nil
	case "list_job_outputs":
		var p struct{ JobID string `json:"job_id"` }
		_ = json.Unmarshal(args, &p)
		id, _ := uuid.Parse(p.JobID)
		j, err := e.Jobs.Get(ctx, id)
		if err != nil {
			return nil, err
		}
		return map[string]any{"files": []string{j.ResultArchivePath}, "summary": j.Status}, nil
	case "download_result_info":
		var p struct{ JobID string `json:"job_id"` }
		_ = json.Unmarshal(args, &p)
		id, _ := uuid.Parse(p.JobID)
		j, err := e.Jobs.Get(ctx, id)
		if err != nil {
			return nil, err
		}
		st, _ := os.Stat(j.ResultArchivePath)
		sz := int64(0)
		if st != nil {
			sz = st.Size()
		}
		return map[string]any{"archive_path": j.ResultArchivePath, "file_count": 1, "size": sz}, nil
	case "get_job_report":
		var p struct{ JobID string `json:"job_id"` }
		_ = json.Unmarshal(args, &p)
		id, _ := uuid.Parse(p.JobID)
		r, err := e.Jobs.BuildReport(ctx, id)
		if err != nil {
			return nil, err
		}
		return r, nil
	case "cancel_job":
		var p struct{ JobID string `json:"job_id"` }
		_ = json.Unmarshal(args, &p)
		id, _ := uuid.Parse(p.JobID)
		if err := e.Jobs.Cancel(ctx, id); err != nil {
			return nil, err
		}
		return map[string]any{"cancelled": true}, nil
	case "retry_job":
		var p struct {
			JobID   string `json:"job_id"`
			Profile string `json:"profile"`
		}
		_ = json.Unmarshal(args, &p)
		id, _ := uuid.Parse(p.JobID)
		j, err := e.Jobs.Retry(ctx, id, p.Profile)
		if err != nil {
			return nil, err
		}
		return map[string]any{"new_job_id": j.ID.String()}, nil
	case "health_check":
		depth, _ := e.RDB.LLen(ctx, "jobs:queue").Result()
		return map[string]any{
			"status":            "ok",
			"gpu_layout":        e.Cfg.LayoutUseGPU,
			"gpu_ocr":           e.Cfg.OCRUseGPU,
			"queue_depth":       depth,
			"model_cache_dir":   e.Cfg.ModelCacheDir,
			"ml_service_health": fetchMLHealth(ctx, e.Cfg),
		}, nil
	default:
		return nil, nil
	}
}

func NewQueueDepthGetter(q *queue.Client) func(context.Context) (int64, error) {
	return func(ctx context.Context) (int64, error) {
		return q.RDB().LLen(ctx, "jobs:queue").Result()
	}
}

func fetchMLHealth(ctx context.Context, cfg config.Config) map[string]any {
	client := &http.Client{Timeout: 8 * time.Second}
	out := make(map[string]any)
	for name, base := range map[string]string{
		"layout": cfg.LayoutServiceURL,
		"ocr":    cfg.OCRServiceURL,
		"vector": cfg.VectorServiceURL,
		"export": cfg.ExportServiceURL,
	} {
		req, err := http.NewRequestWithContext(ctx, http.MethodGet, base+"/health", nil)
		if err != nil {
			out[name] = map[string]any{"error": err.Error()}
			continue
		}
		resp, err := client.Do(req)
		if err != nil {
			out[name] = map[string]any{"error": err.Error()}
			continue
		}
		b, _ := io.ReadAll(resp.Body)
		resp.Body.Close()
		var parsed any
		_ = json.Unmarshal(b, &parsed)
		out[name] = map[string]any{"http_status": resp.StatusCode, "body": parsed}
	}
	return out
}
