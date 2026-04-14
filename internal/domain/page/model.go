package page

import (
	"time"

	"github.com/google/uuid"
)

type Status string

const (
	StatusPending   Status = "pending"
	StatusRunning   Status = "running"
	StatusCompleted Status = "completed"
	StatusFailed    Status = "failed"
)

type PageArtifact struct {
	ID               uuid.UUID
	JobID            uuid.UUID
	SourceImageName  string
	SourceImagePath  string
	PreprocessedPath string
	OverlayPath      string
	PreviewPath      string
	DXFPath          string
	JSONPath         string
	Status           Status
	ConfidenceScore  float64
	WarningsJSON     []byte
	ErrorsJSON       []byte
	CreatedAt        time.Time
	UpdatedAt        time.Time
}
