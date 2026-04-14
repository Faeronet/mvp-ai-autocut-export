package steps

import (
	"archive/zip"
	"encoding/json"
	"io"
	"os"
	"path/filepath"

	"github.com/google/uuid"

	"github.com/drawdigit/mvp/internal/pipeline/contracts"
	"github.com/drawdigit/mvp/internal/pipeline/progress"
	"github.com/drawdigit/mvp/internal/storage"
	domainjob "github.com/drawdigit/mvp/internal/domain/job"
)

type PackageStep struct {
	Emit *progress.Emitter
}

type Manifest struct {
	JobID   string              `json:"job_id"`
	Pages   []ManifestPage      `json:"pages"`
	Profile string              `json:"profile"`
}

type ManifestPage struct {
	PageID string `json:"page_id"`
	DXF    string `json:"dxf"`
	PNG    string `json:"png"`
	JSON   string `json:"json"`
}

func (s *PackageStep) Run(pc *contracts.PipelineContext, layout storage.Layout, pageIDs []uuid.UUID) (string, error) {
	_ = s.Emit.Step(pc.Ctx, pc.JobID, domainjob.StatusPackaging, "packaging", 95)
	outZip := layout.ResultZip(pc.JobID)
	if err := storage.EnsureDir(filepath.Dir(outZip)); err != nil {
		return "", err
	}
	zf, err := os.Create(outZip)
	if err != nil {
		return "", err
	}
	defer zf.Close()
	zw := zip.NewWriter(zf)
	defer zw.Close()

	manifest := Manifest{JobID: pc.JobID.String(), Profile: string(pc.Profile)}
	for _, pid := range pageIDs {
		wd := layout.WorkDir(pc.JobID, pid)
		entries := []struct{ src, name string }{
			{filepath.Join(wd, "out.dxf"), filepath.Join("dxf", pid.String()+".dxf")},
			{filepath.Join(wd, "preview.png"), filepath.Join("preview", pid.String()+".png")},
			{filepath.Join(wd, "intermediate.json"), filepath.Join("json", pid.String()+".json")},
		}
		mp := ManifestPage{PageID: pid.String()}
		for _, e := range entries {
			if err := addFile(zw, e.src, e.name); err != nil {
				continue
			}
			switch filepath.Dir(e.name) {
			case "dxf":
				mp.DXF = e.name
			case "preview":
				mp.PNG = e.name
			case "json":
				mp.JSON = e.name
			}
		}
		manifest.Pages = append(manifest.Pages, mp)
	}
	mb, _ := json.MarshalIndent(manifest, "", "  ")
	mw, err := zw.Create("manifest.json")
	if err != nil {
		return "", err
	}
	if _, err := mw.Write(mb); err != nil {
		return "", err
	}
	report := map[string]any{
		"job_id": pc.JobID.String(),
		"status": "packaged",
	}
	rb, _ := json.MarshalIndent(report, "", "  ")
	rw, err := zw.Create(filepath.Join("json", "report.json"))
	if err != nil {
		return "", err
	}
	if _, err := rw.Write(rb); err != nil {
		return "", err
	}
	return outZip, nil
}

func addFile(zw *zip.Writer, diskPath, zipPath string) error {
	fi, err := os.Open(diskPath)
	if err != nil {
		return err
	}
	defer fi.Close()
	w, err := zw.Create(zipPath)
	if err != nil {
		return err
	}
	_, err = io.Copy(w, fi)
	return err
}
