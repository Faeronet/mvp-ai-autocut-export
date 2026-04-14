package steps

import (
	"path/filepath"

	"github.com/drawdigit/mvp/internal/pipeline/contracts"
	"github.com/drawdigit/mvp/internal/pipeline/progress"
	"github.com/drawdigit/mvp/internal/storage"
	"github.com/drawdigit/mvp/internal/tools/archive"
	domainjob "github.com/drawdigit/mvp/internal/domain/job"
)

type UnpackStep struct {
	Layout  storage.Layout
	Emit    *progress.Emitter
}

func (s *UnpackStep) Run(pc *contracts.PipelineContext, archivePath string) (extractDir string, err error) {
	_ = s.Emit.Step(pc.Ctx, pc.JobID, domainjob.StatusUnpacking, "unpacking", 5)
	extractDir = s.Layout.ExtractDir(pc.JobID)
	if err := archive.Extract(pc.Ctx, archivePath, extractDir); err != nil {
		return "", err
	}
	_ = s.Emit.Log(pc.Ctx, pc.JobID, "unpack", "extracted to "+filepath.Base(extractDir), "info")
	return extractDir, nil
}
