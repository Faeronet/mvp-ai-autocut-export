package steps

import (
	"github.com/drawdigit/mvp/internal/clients/layout"
	"github.com/drawdigit/mvp/internal/pipeline/contracts"
	"github.com/drawdigit/mvp/internal/pipeline/progress"
	domainjob "github.com/drawdigit/mvp/internal/domain/job"
)

type LayoutStep struct {
	Client *layout.Client
	Emit   *progress.Emitter
}

func (s *LayoutStep) Run(pc *contracts.PipelineContext, imagePath string) (*layout.DetectResponse, error) {
	_ = s.Emit.Step(pc.Ctx, pc.JobID, domainjob.StatusLayout, "layout", 35)
	return s.Client.Detect(pc.Ctx, layout.DetectRequest{
		ImagePath: imagePath,
		Profile:   string(pc.Profile),
	})
}
