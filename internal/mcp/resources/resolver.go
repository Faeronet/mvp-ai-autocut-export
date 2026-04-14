package resources

import (
	"context"
	"encoding/json"
	"os"
	"strings"

	"github.com/google/uuid"

	"github.com/drawdigit/mvp/internal/services/jobs"
)

type Resolver struct {
	Jobs *jobs.Service
}

type ReadResult struct {
	URI     string `json:"uri"`
	Mime    string `json:"mimeType"`
	Content string `json:"text"`
}

func (r *Resolver) Read(ctx context.Context, uri string) (*ReadResult, error) {
	switch {
	case strings.HasPrefix(uri, "job://"):
		parts := strings.Split(strings.TrimPrefix(uri, "job://"), "/")
		if len(parts) < 2 {
			return nil, os.ErrNotExist
		}
		jobID, err := uuid.Parse(parts[0])
		if err != nil {
			return nil, err
		}
		if len(parts) >= 2 && parts[1] == "manifest" {
			j, err := r.Jobs.Get(ctx, jobID)
			if err != nil {
				return nil, err
			}
			b, _ := json.MarshalIndent(map[string]any{"result_archive": j.ResultArchivePath}, "", "  ")
			return &ReadResult{URI: uri, Mime: "application/json", Content: string(b)}, nil
		}
		if len(parts) >= 2 && parts[1] == "report" {
			rep, err := r.Jobs.BuildReport(ctx, jobID)
			if err != nil {
				return nil, err
			}
			b, err := json.MarshalIndent(rep, "", "  ")
			if err != nil {
				return nil, err
			}
			return &ReadResult{URI: uri, Mime: "application/json", Content: string(b)}, nil
		}
		if len(parts) >= 4 && parts[1] == "page" && parts[3] == "intermediate" {
			pageID, _ := uuid.Parse(parts[2])
			b, err := r.Jobs.ReadIntermediateJSON(ctx, jobID, pageID)
			if err != nil {
				return nil, err
			}
			return &ReadResult{URI: uri, Mime: "application/json", Content: string(b)}, nil
		}
		if len(parts) >= 4 && parts[1] == "page" && parts[3] == "preview" {
			return &ReadResult{URI: uri, Mime: "text/plain", Content: "binary preview path not inlined in MVP"}, nil
		}
	case uri == "system://profiles":
		return &ReadResult{URI: uri, Mime: "application/json", Content: `{"profiles":["balanced","quality","low_vram"]}`}, nil
	case uri == "system://health":
		return &ReadResult{URI: uri, Mime: "application/json", Content: `{"status":"ok"}`}, nil
	}
	return nil, os.ErrNotExist
}

func List() []map[string]any {
	return []map[string]any{
		{"uri": "system://profiles", "name": "profiles"},
		{"uri": "system://health", "name": "health"},
	}
}
