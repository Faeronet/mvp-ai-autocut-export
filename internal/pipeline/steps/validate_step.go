package steps

import (
	"github.com/drawdigit/mvp/internal/pipeline/contracts"
	"github.com/drawdigit/mvp/internal/pipeline/progress"
	"github.com/drawdigit/mvp/internal/tools/images"
	domainjob "github.com/drawdigit/mvp/internal/domain/job"
	"github.com/drawdigit/mvp/pkg/apperrors"
)

type ValidateStep struct {
	Emit *progress.Emitter
}

func (s *ValidateStep) Run(pc *contracts.PipelineContext, extractDir string) ([]string, error) {
	_ = s.Emit.Step(pc.Ctx, pc.JobID, domainjob.StatusPreprocessing, "validate_input", 8)
	paths, err := images.ListRecursive(extractDir)
	if err != nil {
		return nil, apperrors.Wrap(apperrors.KindCorrupted, "list_images_failed", "failed to list images", err)
	}
	if len(paths) == 0 {
		return nil, apperrors.New(apperrors.KindEmptyInput, "no_images", "archive contains no supported images")
	}
	return paths, nil
}
