package steps

import (
	"github.com/drawdigit/mvp/internal/clients/ocr"
	domainjob "github.com/drawdigit/mvp/internal/domain/job"
	"github.com/drawdigit/mvp/internal/pipeline/contracts"
	"github.com/drawdigit/mvp/internal/pipeline/progress"
)

type PageUnderstandingStep struct {
	Client *ocr.Client
	Emit   *progress.Emitter
}

func (s *PageUnderstandingStep) Run(pc *contracts.PipelineContext, imagePath string) (*ocr.PageUnderstandingResponse, error) {
	_ = s.Emit.Step(pc.Ctx, pc.JobID, domainjob.StatusLayout, "page-understanding", 28)
	return s.Client.PageUnderstand(pc.Ctx, ocr.PageUnderstandingRequest{
		ImagePath: imagePath,
		Profile:   string(pc.Profile),
	})
}
