package dto

import (
	"time"

	"github.com/google/uuid"

	domainjob "github.com/drawdigit/mvp/internal/domain/job"
)

type JobResponse struct {
	ID                uuid.UUID     `json:"id"`
	CreatedAt         time.Time     `json:"created_at"`
	UpdatedAt         time.Time     `json:"updated_at"`
	Status            string        `json:"status"`
	InputArchiveName  string        `json:"input_archive_name"`
	ResultArchivePath string        `json:"result_archive_path,omitempty"`
	TotalPages        int           `json:"total_pages"`
	CompletedPages    int           `json:"completed_pages"`
	FailedPages       int           `json:"failed_pages"`
	ProgressPercent   int           `json:"progress_percent"`
	CurrentStep       string        `json:"current_step"`
	ErrorMessage      string        `json:"error_message,omitempty"`
	WarningsCount     int           `json:"warnings_count"`
	Profile           string        `json:"profile"`
}

func JobFromDomain(j *domainjob.Job) JobResponse {
	return JobResponse{
		ID:                j.ID,
		CreatedAt:         j.CreatedAt,
		UpdatedAt:         j.UpdatedAt,
		Status:            string(j.Status),
		InputArchiveName:  j.InputArchiveName,
		ResultArchivePath: j.ResultArchivePath,
		TotalPages:        j.TotalPages,
		CompletedPages:    j.CompletedPages,
		FailedPages:       j.FailedPages,
		ProgressPercent:   j.ProgressPercent,
		CurrentStep:       j.CurrentStep,
		ErrorMessage:      j.ErrorMessage,
		WarningsCount:     j.WarningsCount,
		Profile:           j.Profile,
	}
}

type ProfileInfo struct {
	Name        string            `json:"name"`
	Description string            `json:"description"`
	Params      map[string]string `json:"params"`
}
