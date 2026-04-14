package jobs

import (
	"context"
	"encoding/json"
	"os"

	"github.com/google/uuid"
)

type Report struct {
	JobID          string            `json:"job_id"`
	Pages          []PageReport      `json:"pages"`
	Confidence     map[string]float64 `json:"confidence_summary"`
	Warnings       []string          `json:"warnings"`
	FailedPages    []string          `json:"failed_pages"`
}

type PageReport struct {
	PageID     string  `json:"page_id"`
	Source     string  `json:"source"`
	Status     string  `json:"status"`
	Confidence float64 `json:"confidence"`
}

func (s *Service) BuildReport(ctx context.Context, jobID uuid.UUID) (*Report, error) {
	pages, err := s.Pages.ListByJob(ctx, jobID)
	if err != nil {
		return nil, err
	}
	r := &Report{JobID: jobID.String(), Confidence: map[string]float64{}, Warnings: []string{}, FailedPages: []string{}}
	for _, p := range pages {
		pr := PageReport{
			PageID: p.ID.String(), Source: p.SourceImageName, Status: string(p.Status), Confidence: p.ConfidenceScore,
		}
		r.Pages = append(r.Pages, pr)
		r.Confidence[p.ID.String()] = p.ConfidenceScore
		if p.Status == "failed" {
			r.FailedPages = append(r.FailedPages, p.ID.String())
		}
	}
	return r, nil
}

func (s *Service) ReadIntermediateJSON(ctx context.Context, jobID, pageID uuid.UUID) ([]byte, error) {
	pages, err := s.Pages.ListByJob(ctx, jobID)
	if err != nil {
		return nil, err
	}
	for _, p := range pages {
		if p.ID == pageID && p.JSONPath != "" {
			return os.ReadFile(p.JSONPath)
		}
	}
	return nil, os.ErrNotExist
}

func ReportJSON(r *Report) ([]byte, error) {
	return json.MarshalIndent(r, "", "  ")
}
