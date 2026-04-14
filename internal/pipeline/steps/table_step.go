package steps

import (
	"github.com/drawdigit/mvp/internal/clients/ocr"
	domainjob "github.com/drawdigit/mvp/internal/domain/job"
	"github.com/drawdigit/mvp/internal/pipeline/contracts"
	"github.com/drawdigit/mvp/internal/pipeline/progress"
)

type TableStep struct {
	Client *ocr.Client
	Emit   *progress.Emitter
}

func (s *TableStep) Run(pc *contracts.PipelineContext, imagePath string, rois []ocr.ROI) (*ocr.TableResponse, error) {
	_ = s.Emit.Step(pc.Ctx, pc.JobID, domainjob.StatusOCR, "table-structure", 60)
	return s.Client.TableStructure(pc.Ctx, ocr.TableRequest{
		ImagePath: imagePath,
		Profile:   string(pc.Profile),
		ROIs:      rois,
	})
}
