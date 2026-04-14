package storage

import (
	"path/filepath"

	"github.com/google/uuid"
)

type Layout struct {
	Root string
}

func NewLayout(root string) Layout {
	return Layout{Root: root}
}

func (l Layout) JobDir(jobID uuid.UUID) string {
	return filepath.Join(l.Root, "jobs", jobID.String())
}

func (l Layout) InputArchive(jobID uuid.UUID) string {
	return filepath.Join(l.JobDir(jobID), "input", "archive.bin")
}

func (l Layout) ExtractDir(jobID uuid.UUID) string {
	return filepath.Join(l.JobDir(jobID), "extract")
}

func (l Layout) WorkDir(jobID uuid.UUID, pageID uuid.UUID) string {
	return filepath.Join(l.JobDir(jobID), "pages", pageID.String())
}

func (l Layout) OutputDir(jobID uuid.UUID) string {
	return filepath.Join(l.JobDir(jobID), "output")
}

func (l Layout) ResultZip(jobID uuid.UUID) string {
	return filepath.Join(l.OutputDir(jobID), "results_"+jobID.String()+".zip")
}
