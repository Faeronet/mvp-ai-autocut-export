package pipeline

import (
	"encoding/json"
	"path/filepath"
	"time"

	"github.com/google/uuid"

	"github.com/drawdigit/mvp/internal/clients/export"
	"github.com/drawdigit/mvp/internal/clients/httpclient"
	"github.com/drawdigit/mvp/internal/clients/layout"
	"github.com/drawdigit/mvp/internal/clients/ocr"
	"github.com/drawdigit/mvp/internal/clients/vector"
	"github.com/drawdigit/mvp/internal/config"
	domainjob "github.com/drawdigit/mvp/internal/domain/job"
	domainpage "github.com/drawdigit/mvp/internal/domain/page"
	"github.com/drawdigit/mvp/internal/pipeline/contracts"
	"github.com/drawdigit/mvp/internal/pipeline/mock"
	"github.com/drawdigit/mvp/internal/pipeline/progress"
	"github.com/drawdigit/mvp/internal/pipeline/steps"
	"github.com/drawdigit/mvp/internal/queue"
	jobrepo "github.com/drawdigit/mvp/internal/repositories/job"
	pagerepo "github.com/drawdigit/mvp/internal/repositories/page"
	"github.com/drawdigit/mvp/internal/storage"
)

type RunnerDeps struct {
	Config  config.Config
	Jobs    *jobrepo.Repository
	Pages   *pagerepo.Repository
	Layout  storage.Layout
	Emit    *progress.Emitter
	Queue   *queue.Client
	GPULock *queue.GPULock
}

func RunJob(deps RunnerDeps, pc *contracts.PipelineContext, archivePath string) error {
	hc := httpclient.New(deps.Config.RequestTimeout)
	layoutC := layout.New(deps.Config.LayoutServiceURL, hc)
	ocrC := ocr.New(deps.Config.OCRServiceURL, hc)
	vecC := vector.New(deps.Config.VectorServiceURL, hc)
	expC := export.New(deps.Config.ExportServiceURL, hc)

	unpack := &steps.UnpackStep{Layout: deps.Layout, Emit: deps.Emit}
	validate := &steps.ValidateStep{Emit: deps.Emit}
	pre := &steps.PreprocessStep{BaseURL: deps.Config.VectorServiceURL, HC: hc, Emit: deps.Emit, Cfg: deps.Config}
	lay := &steps.LayoutStep{Client: layoutC, Emit: deps.Emit}
	pu := &steps.PageUnderstandingStep{Client: ocrC, Emit: deps.Emit}
	geo := &steps.GeometryStep{Client: vecC, Emit: deps.Emit}
	oc := &steps.OCRStep{Client: ocrC, Emit: deps.Emit}
	tbl := &steps.TableStep{Client: ocrC, Emit: deps.Emit}
	asm := &steps.AssembleStep{Emit: deps.Emit}
	exp := &steps.ExportStep{Client: expC, Emit: deps.Emit}
	pkg := &steps.PackageStep{Emit: deps.Emit}

	extractDir, err := unpack.Run(pc, archivePath)
	if err != nil {
		return err
	}
	imagePaths, err := validate.Run(pc, extractDir)
	if err != nil {
		return err
	}
	_ = deps.Jobs.SetPages(pc.Ctx, pc.JobID, len(imagePaths), 0, 0)

	var pageIDs []uuid.UUID
	completed := 0
	failed := 0
	timings := map[string]any{}

	for _, img := range imagePaths {
		pageID := uuid.New()
		pageIDs = append(pageIDs, pageID)
		pa := &domainpage.PageArtifact{
			ID: pageID, JobID: pc.JobID,
			SourceImageName: filepath.Base(img),
			SourceImagePath: img,
			Status:          domainpage.StatusRunning,
		}
		if err := deps.Pages.Create(pc.Ctx, pa); err != nil {
			failed++
			continue
		}
		workDir := deps.Layout.WorkDir(pc.JobID, pageID)
		_ = storage.EnsureDir(workDir)

		t0 := time.Now()
		if pc.Mock {
			b, err := mock.Intermediate(pc.JobID, pageID, pa.SourceImageName, pc.Profile)
			if err != nil {
				failed++
				continue
			}
			jsonPath, err := steps.WriteIntermediate(deps.Layout, pc.JobID, pageID, b)
			if err != nil {
				failed++
				continue
			}
			dxf, png, err := exp.Run(pc, pageID, b, deps.Layout)
			if err != nil {
				failed++
				_ = deps.Pages.SetStatus(pc.Ctx, pageID, domainpage.StatusFailed, 0, []byte(`[]`), []byte(`["export failed"]`))
				continue
			}
			_ = deps.Pages.UpdatePaths(pc.Ctx, pageID, "", "", png, dxf, jsonPath)
			_ = deps.Pages.SetStatus(pc.Ctx, pageID, domainpage.StatusCompleted, 0.8, []byte(`[]`), []byte(`[]`))
			completed++
			timings[pageID.String()] = time.Since(t0).Seconds()
			continue
		}

		ctx := pc.Ctx
		_ = deps.GPULock.Acquire(ctx)
		preRes, err := pre.Run(pc, img, workDir)
		if err != nil {
			_ = deps.GPULock.Release(ctx)
			failed++
			_ = deps.Pages.SetStatus(pc.Ctx, pageID, domainpage.StatusFailed, 0, []byte(`[]`), []byte(`["preprocess failed"]`))
			continue
		}
		pageUnderstanding, puErr := pu.Run(pc, preRes.PreprocessedPath)
		if puErr != nil {
			pageUnderstanding = &ocr.PageUnderstandingResponse{
				SheetType:    "mixed",
				Warnings:     []string{"page_understanding_failed"},
				Regions:      []ocr.LayoutRegion{},
				ReviewHints:  []ocr.ReviewHint{},
				Confidence:   0.0,
				ModelVersion: "paddleocr-vl-0.9b",
			}
		}
		layRes, err := lay.Run(pc, preRes.PreprocessedPath)
		if err != nil {
			_ = deps.GPULock.Release(ctx)
			failed++
			_ = deps.Pages.SetStatus(pc.Ctx, pageID, domainpage.StatusFailed, 0, []byte(`[]`), []byte(`["layout failed"]`))
			continue
		}
		layRes.Zones = fuseLayoutWithPageUnderstanding(layRes.Zones, pageUnderstanding.Regions)
		geoRes, err := geo.Run(pc, preRes.BinaryPath)
		if err != nil {
			_ = deps.GPULock.Release(ctx)
			failed++
			_ = deps.Pages.SetStatus(pc.Ctx, pageID, domainpage.StatusFailed, 0, []byte(`[]`), []byte(`["geometry failed"]`))
			continue
		}
		rois := zonesToROIs(layRes.Zones)
		ocrRes, err := oc.Run(pc, preRes.SoftPath, rois)
		_ = deps.GPULock.Release(ctx)
		if err != nil {
			failed++
			_ = deps.Pages.SetStatus(pc.Ctx, pageID, domainpage.StatusFailed, 0, []byte(`[]`), []byte(`["ocr failed"]`))
			continue
		}
		tableRes, tblErr := tbl.Run(pc, preRes.SoftPath, tableROIsFromZones(layRes.Zones))
		if tblErr != nil {
			tableRes = &ocr.TableResponse{Warnings: []string{"table_step_failed"}, Partial: true}
		}
		inter, err := asm.Run(pc, pageID, pa.SourceImageName, preRes.PreprocessedPath, layRes, pageUnderstanding, geoRes, ocrRes, tableRes, preRes)
		if err != nil {
			failed++
			continue
		}
		jsonPath, err := steps.WriteIntermediate(deps.Layout, pc.JobID, pageID, inter)
		if err != nil {
			failed++
			continue
		}
		dxf, png, err := exp.Run(pc, pageID, inter, deps.Layout)
		if err != nil {
			failed++
			_ = deps.Pages.SetStatus(pc.Ctx, pageID, domainpage.StatusFailed, 0, []byte(`[]`), []byte(`["export failed"]`))
			continue
		}
		_ = deps.Pages.UpdatePaths(pc.Ctx, pageID, preRes.PreprocessedPath, layRes.Overlay, png, dxf, jsonPath)
		_ = deps.Pages.SetStatus(pc.Ctx, pageID, domainpage.StatusCompleted, interConfidence(inter), []byte(`[]`), []byte(`[]`))
		completed++
		timings[pageID.String()] = time.Since(t0).Seconds()
	}

	_ = deps.Jobs.SetPages(pc.Ctx, pc.JobID, len(imagePaths), completed, failed)
	_ = deps.Jobs.SetTimings(pc.Ctx, pc.JobID, timings)

	outPath, err := pkg.Run(pc, deps.Layout, pageIDs)
	if err != nil {
		return err
	}
	_ = deps.Jobs.SetResultPath(pc.Ctx, pc.JobID, outPath)
	if len(imagePaths) > 0 && failed == len(imagePaths) {
		_ = deps.Jobs.SetFailed(pc.Ctx, pc.JobID, "all pages failed")
		return nil
	}
	st := domainjob.StatusCompleted
	if failed > 0 && completed > 0 {
		st = domainjob.StatusPartialSuccess
	} else if failed > 0 {
		st = domainjob.StatusFailed
	}
	return deps.Jobs.SetCompleted(pc.Ctx, pc.JobID, st, 0)
}

func fuseLayoutWithPageUnderstanding(layoutZones []layout.ZoneDTO, vlmRegions []ocr.LayoutRegion) []layout.ZoneDTO {
	byLabel := map[string]layout.ZoneDTO{}
	for _, z := range layoutZones {
		byLabel[z.Label] = z
	}
	for _, r := range vlmRegions {
		cur, exists := byLabel[r.Label]
		if !exists || r.Confidence > cur.Confidence {
			byLabel[r.Label] = layout.ZoneDTO{
				Label:      r.Label,
				BBox:       r.BBox,
				Confidence: r.Confidence,
			}
		}
	}
	out := make([]layout.ZoneDTO, 0, len(byLabel))
	for _, z := range byLabel {
		out = append(out, z)
	}
	return out
}

func zonesToROIs(zones []layout.ZoneDTO) []ocr.ROI {
	out := make([]ocr.ROI, 0, len(zones))
	for _, z := range zones {
		role := "general_notes"
		switch z.Label {
		case "title_block":
			role = "title_block"
		case "specification_table":
			role = "table"
		case "dimension_cluster":
			role = "dimension_text"
		case "notes_block":
			role = "notes"
		}
		out = append(out, ocr.ROI{BBox: z.BBox, Semantic: role})
	}
	if len(out) == 0 {
		out = append(out, ocr.ROI{BBox: [4]float64{0, 0, 4096, 4096}, Semantic: "general_notes"})
	}
	return out
}

func tableROIsFromZones(zones []layout.ZoneDTO) []ocr.ROI {
	out := make([]ocr.ROI, 0, 2)
	for _, z := range zones {
		if z.Label == "specification_table" || z.Label == "title_block" {
			out = append(out, ocr.ROI{BBox: z.BBox, Semantic: z.Label})
		}
	}
	return out
}

func interConfidence(data []byte) float64 {
	var v map[string]any
	if err := json.Unmarshal(data, &v); err != nil {
		return 0.5
	}
	c, ok := v["confidence"].(float64)
	if !ok {
		return 0.5
	}
	return c
}
