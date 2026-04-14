package steps

import (
	"github.com/drawdigit/mvp/internal/clients/httpclient"
	"github.com/drawdigit/mvp/internal/clients/vector"
	"github.com/drawdigit/mvp/internal/config"
	"github.com/drawdigit/mvp/internal/pipeline/contracts"
	"github.com/drawdigit/mvp/internal/pipeline/progress"
	domainjob "github.com/drawdigit/mvp/internal/domain/job"
)

type PreprocessStep struct {
	BaseURL string
	HC      *httpclient.Client
	Emit    *progress.Emitter
	Cfg     config.Config
}

func (s *PreprocessStep) Run(pc *contracts.PipelineContext, imagePath, outDir string) (*vector.PreprocessResponse, error) {
	_ = s.Emit.Step(pc.Ctx, pc.JobID, domainjob.StatusPreprocessing, "preprocessing", 15)
	req := vector.PreprocessRequest{
		ImagePath: imagePath,
		OutputDir: outDir,
		Profile:   string(pc.Profile),
		SaveDebug: pc.Profile == contracts.ProfileQuality,
	}
	return vector.Preprocess(pc.Ctx, s.BaseURL, s.HC, req)
}
