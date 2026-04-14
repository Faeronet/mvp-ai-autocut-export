package handlers

import (
	"encoding/json"
	"fmt"
	"net/http"
	"time"

	"github.com/go-chi/chi/v5"
	"github.com/google/uuid"

	jobrepo "github.com/drawdigit/mvp/internal/repositories/job"
)

type SSE struct {
	Jobs *jobrepo.Repository
}

func (s *SSE) JobEvents(w http.ResponseWriter, r *http.Request) {
	id, err := uuid.Parse(chi.URLParam(r, "id"))
	if err != nil {
		http.Error(w, "bad id", http.StatusBadRequest)
		return
	}
	w.Header().Set("Content-Type", "text/event-stream")
	w.Header().Set("Cache-Control", "no-cache")
	w.Header().Set("Connection", "keep-alive")
	fl, ok := w.(http.Flusher)
	if !ok {
		http.Error(w, "streaming unsupported", http.StatusInternalServerError)
		return
	}
	t := time.NewTicker(2 * time.Second)
	defer t.Stop()
	for {
		select {
		case <-r.Context().Done():
			return
		case <-t.C:
			j, err := s.Jobs.Get(r.Context(), id)
			if err != nil || j == nil {
				fmt.Fprintf(w, "event: error\ndata: {\"error\":\"not found\"}\n\n")
				fl.Flush()
				return
			}
			b, _ := json.Marshal(map[string]any{
				"status": j.Status, "progress": j.ProgressPercent, "step": j.CurrentStep,
			})
			fmt.Fprintf(w, "event: progress\ndata: %s\n\n", string(b))
			fl.Flush()
		}
	}
}
