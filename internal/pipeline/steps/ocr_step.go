package steps

import (
	"github.com/drawdigit/mvp/internal/clients/ocr"
	"github.com/drawdigit/mvp/internal/pipeline/contracts"
	"github.com/drawdigit/mvp/internal/pipeline/progress"
	domainjob "github.com/drawdigit/mvp/internal/domain/job"
)

type OCRStep struct {
	Client *ocr.Client
	Emit   *progress.Emitter
}

func (s *OCRStep) Run(pc *contracts.PipelineContext, softPath string, zones []ocr.ROI) (*ocr.RunResponse, error) {
	_ = s.Emit.Step(pc.Ctx, pc.JobID, domainjob.StatusOCR, "ocr", 65)
	return s.Client.Run(pc.Ctx, ocr.RunRequest{
		ImagePath: softPath,
		ROIs:      zones,
		Profile:   string(pc.Profile),
	})
}
