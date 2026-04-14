package steps

import (
	"encoding/json"

	"github.com/google/uuid"

	"github.com/drawdigit/mvp/internal/clients/export"
	"github.com/drawdigit/mvp/internal/pipeline/contracts"
	"github.com/drawdigit/mvp/internal/pipeline/progress"
	"github.com/drawdigit/mvp/internal/storage"
	domainjob "github.com/drawdigit/mvp/internal/domain/job"
)

type ExportStep struct {
	Client *export.Client
	Emit   *progress.Emitter
}

func (s *ExportStep) Run(
	pc *contracts.PipelineContext,
	pageID uuid.UUID,
	interJSON []byte,
	layout storage.Layout,
) (dxfPath, pngPath string, err error) {
	_ = s.Emit.Step(pc.Ctx, pc.JobID, domainjob.StatusExporting, "exporting", 88)
	var inter contracts.IntermediateJSON
	if err := json.Unmarshal(interJSON, &inter); err != nil {
		return "", "", err
	}
	_ = pageID
	wd := layout.WorkDir(pc.JobID, pageID)
	dxfPath = storage.Join(wd, "out.dxf")
	pngPath = storage.Join(wd, "preview.png")
	res, err := s.Client.Render(pc.Ctx, export.RenderRequest{
		Intermediate: inter,
		OutputDXF:    dxfPath,
		OutputPNG:    pngPath,
		Profile:      string(pc.Profile),
	})
	if err != nil {
		return "", "", err
	}
	return res.DXFPath, res.PNGPath, nil
}
