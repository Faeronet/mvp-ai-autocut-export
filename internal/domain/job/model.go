package job

import (
	"time"

	"github.com/google/uuid"
)

type Job struct {
	ID                uuid.UUID
	CreatedAt         time.Time
	UpdatedAt         time.Time
	Status            Status
	InputArchiveName  string
	InputArchivePath  string
	ResultArchivePath string
	TotalPages        int
	CompletedPages    int
	FailedPages       int
	ProgressPercent   int
	CurrentStep       string
	ErrorMessage      string
	WarningsCount     int
	Profile           string
	TimingsJSON       []byte
}
