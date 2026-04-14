package handlers

import (
	"encoding/json"
	"io"
	"net/http"
	"os"
	"strconv"

	"github.com/go-chi/chi/v5"
	"github.com/google/uuid"

	"github.com/drawdigit/mvp/internal/http/dto"
	"github.com/drawdigit/mvp/internal/services/jobs"
	"github.com/drawdigit/mvp/pkg/response"
)

type Jobs struct {
	Svc *jobs.Service
}

func (h *Jobs) Upload(w http.ResponseWriter, r *http.Request) {
	_ = r.ParseMultipartForm(256 << 20)
	file, hdr, err := r.FormFile("file")
	if err != nil {
		response.Error(w, err)
		return
	}
	defer file.Close()
	profile := r.FormValue("profile")
	j, err := h.Svc.CreateFromUpload(r.Context(), hdr.Filename, file, profile)
	if err != nil {
		response.Error(w, err)
		return
	}
	response.OK(w, map[string]any{"job_id": j.ID, "status": j.Status})
}

func (h *Jobs) Get(w http.ResponseWriter, r *http.Request) {
	id, err := uuid.Parse(chi.URLParam(r, "id"))
	if err != nil {
		http.Error(w, "bad id", http.StatusBadRequest)
		return
	}
	j, err := h.Svc.Get(r.Context(), id)
	if err != nil {
		response.Error(w, err)
		return
	}
	response.OK(w, dto.JobFromDomain(j))
}

func (h *Jobs) List(w http.ResponseWriter, r *http.Request) {
	limit, _ := strconv.Atoi(r.URL.Query().Get("limit"))
	list, err := h.Svc.List(r.Context(), limit)
	if err != nil {
		response.Error(w, err)
		return
	}
	out := make([]dto.JobResponse, 0, len(list))
	for i := range list {
		out = append(out, dto.JobFromDomain(&list[i]))
	}
	response.OK(w, map[string]any{"jobs": out})
}

func (h *Jobs) Report(w http.ResponseWriter, r *http.Request) {
	id, err := uuid.Parse(chi.URLParam(r, "id"))
	if err != nil {
		http.Error(w, "bad id", http.StatusBadRequest)
		return
	}
	rep, err := h.Svc.BuildReport(r.Context(), id)
	if err != nil {
		response.Error(w, err)
		return
	}
	b, err := jobs.ReportJSON(rep)
	if err != nil {
		response.Error(w, err)
		return
	}
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	_, _ = w.Write(b)
}

func (h *Jobs) Download(w http.ResponseWriter, r *http.Request) {
	id, err := uuid.Parse(chi.URLParam(r, "id"))
	if err != nil {
		http.Error(w, "bad id", http.StatusBadRequest)
		return
	}
	j, err := h.Svc.Get(r.Context(), id)
	if err != nil {
		response.Error(w, err)
		return
	}
	if j.ResultArchivePath == "" {
		http.Error(w, "not ready", http.StatusConflict)
		return
	}
	f, err := os.Open(j.ResultArchivePath)
	if err != nil {
		http.Error(w, "missing file", http.StatusNotFound)
		return
	}
	defer f.Close()
	w.Header().Set("Content-Type", "application/zip")
	w.Header().Set("Content-Disposition", "attachment; filename=results_"+id.String()+".zip")
	_, _ = io.Copy(w, f)
}

func (h *Jobs) Cancel(w http.ResponseWriter, r *http.Request) {
	id, err := uuid.Parse(chi.URLParam(r, "id"))
	if err != nil {
		http.Error(w, "bad id", http.StatusBadRequest)
		return
	}
	if err := h.Svc.Cancel(r.Context(), id); err != nil {
		response.Error(w, err)
		return
	}
	response.OK(w, map[string]any{"cancelled": true})
}

func (h *Jobs) Retry(w http.ResponseWriter, r *http.Request) {
	id, err := uuid.Parse(chi.URLParam(r, "id"))
	if err != nil {
		http.Error(w, "bad id", http.StatusBadRequest)
		return
	}
	var body struct {
		Profile string `json:"profile"`
	}
	_ = json.NewDecoder(r.Body).Decode(&body)
	j, err := h.Svc.Retry(r.Context(), id, body.Profile)
	if err != nil {
		response.Error(w, err)
		return
	}
	response.OK(w, map[string]any{"job_id": j.ID})
}
