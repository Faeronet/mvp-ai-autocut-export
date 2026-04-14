package steps

import (
	"github.com/drawdigit/mvp/internal/clients/vector"
	"github.com/drawdigit/mvp/internal/pipeline/contracts"
	"github.com/drawdigit/mvp/internal/pipeline/progress"
	domainjob "github.com/drawdigit/mvp/internal/domain/job"
)

type GeometryStep struct {
	Client *vector.Client
	Emit   *progress.Emitter
}

func (s *GeometryStep) Run(pc *contracts.PipelineContext, binPath string) (*vector.ExtractResponse, error) {
	_ = s.Emit.Step(pc.Ctx, pc.JobID, domainjob.StatusGeometry, "geometry", 50)
	return s.Client.Extract(pc.Ctx, vector.ExtractRequest{
		ImagePath: binPath,
		Profile:   string(pc.Profile),
	})
}
