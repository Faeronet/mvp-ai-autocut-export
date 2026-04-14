package steps

import (
	"encoding/json"
	"path/filepath"
	"strings"

	"github.com/google/uuid"

	"github.com/drawdigit/mvp/internal/clients/layout"
	"github.com/drawdigit/mvp/internal/clients/ocr"
	"github.com/drawdigit/mvp/internal/clients/vector"
	domainjob "github.com/drawdigit/mvp/internal/domain/job"
	"github.com/drawdigit/mvp/internal/pipeline/contracts"
	"github.com/drawdigit/mvp/internal/pipeline/progress"
	"github.com/drawdigit/mvp/internal/storage"
)

type AssembleStep struct {
	Emit *progress.Emitter
}

func (s *AssembleStep) Run(
	pc *contracts.PipelineContext,
	pageID uuid.UUID,
	sourceName string,
	prePath string,
	layout *layout.DetectResponse,
	pageUnderstanding *ocr.PageUnderstandingResponse,
	geom *vector.ExtractResponse,
	ocrRes *ocr.RunResponse,
	tableRes *ocr.TableResponse,
	pre *vector.PreprocessResponse,
) ([]byte, error) {
	_ = s.Emit.Step(pc.Ctx, pc.JobID, domainjob.StatusAssembling, "assembling", 78)
	inter := contracts.IntermediateJSON{
		Meta: contracts.Meta{
			JobID:      pc.JobID.String(),
			PageID:     pageID.String(),
			SourceFile: sourceName,
			Profile:    string(pc.Profile),
		},
		ImageMeta:         map[string]float64{},
		ProcessingProfile: string(pc.Profile),
		PageUnderstanding: contracts.PageUnderstanding{
			SheetType:        "mixed",
			Regions:          []contracts.Zone{},
			OrientationHints: map[string]int{},
			ModelVersion:     "",
			Confidence:       0.0,
		},
		Zones:       make([]contracts.Zone, 0, len(layout.Zones)),
		TextRegions: []contracts.TextRegion{},
		Geometry: contracts.GeometryBlock{
			Lines:     make([]contracts.LineSeg, 0, len(geom.Lines)),
			Circles:   make([]contracts.Circle, 0, len(geom.Circles)),
			Polylines: [][]float64{},
			Arcs:      []contracts.Arc{},
			Tables:    []contracts.TableGeom{},
			Arrows:    []contracts.Arrow{},
		},
		Texts:                []contracts.TextSpan{},
		Dims:                 []contracts.DimensionText{},
		Tables:               []contracts.TableBlock{},
		Warnings:             []string{},
		ModuleConfidences:    map[string]float64{},
		LowConfidenceRegions: []contracts.ReviewItem{},
		ReviewHints:          []contracts.ReviewHint{},
		DebugArtifacts:       map[string]string{},
		ReviewRequiredItems:  []contracts.ReviewItem{},
	}
	for k, v := range pre.ImageMeta {
		inter.ImageMeta[k] = v
	}
	for k, v := range pre.DebugArtifacts {
		inter.DebugArtifacts[k] = v
	}
	inter.Warnings = append(inter.Warnings, pre.Warnings...)
	inter.ModuleConfidences["preprocess"] = pre.PreprocessConfidence
	if pageUnderstanding != nil {
		inter.PageUnderstanding.SheetType = pageUnderstanding.SheetType
		inter.PageUnderstanding.ModelVersion = pageUnderstanding.ModelVersion
		inter.PageUnderstanding.Confidence = pageUnderstanding.Confidence
		inter.PageUnderstanding.OrientationHints = pageUnderstanding.OrientationHints
		for _, r := range pageUnderstanding.Regions {
			inter.PageUnderstanding.Regions = append(inter.PageUnderstanding.Regions, contracts.Zone{
				Label: r.Label, BBox: r.BBox, Confidence: r.Confidence,
			})
		}
		for _, h := range pageUnderstanding.ReviewHints {
			rh := contracts.ReviewHint{
				Kind: h.Kind, Reason: h.Reason, BBox: h.BBox, Confidence: h.Confidence,
			}
			inter.ReviewHints = append(inter.ReviewHints, rh)
			inter.LowConfidenceRegions = append(inter.LowConfidenceRegions, contracts.ReviewItem{
				Kind: h.Kind, Reason: h.Reason, BBox: h.BBox,
			})
		}
		if len(pageUnderstanding.Warnings) > 0 {
			inter.Warnings = append(inter.Warnings, pageUnderstanding.Warnings...)
		}
		inter.ModuleConfidences["page_understanding"] = pageUnderstanding.Confidence
	}

	if len(layout.Warnings) > 0 {
		inter.Warnings = append(inter.Warnings, layout.Warnings...)
	}
	if layout.Mode == "last_resort" {
		inter.Warnings = append(inter.Warnings, "layout_last_resort_used")
		inter.ModuleConfidences["layout"] = 0.3
	} else {
		inter.ModuleConfidences["layout"] = 0.7
	}
	for k, v := range layout.DebugArtifacts {
		inter.DebugArtifacts["layout_"+k] = v
	}
	for _, z := range layout.Zones {
		inter.Zones = append(inter.Zones, contracts.Zone{
			Label: z.Label, BBox: z.BBox, Confidence: z.Confidence,
		})
	}
	for _, ln := range geom.Lines {
		inter.Geometry.Lines = append(inter.Geometry.Lines, contracts.LineSeg{
			X1: ln.X1, Y1: ln.Y1, X2: ln.X2, Y2: ln.Y2,
			Layer: ln.Layer, Confidence: ln.Confidence,
		})
	}
	inter.ModuleConfidences["geometry"] = 0.5
	if len(inter.Geometry.Lines) > 30 {
		inter.ModuleConfidences["geometry"] = 0.75
	}
	for _, c := range geom.Circles {
		inter.Geometry.Circles = append(inter.Geometry.Circles, contracts.Circle{
			Cx: c.Cx, Cy: c.Cy, R: c.R, Layer: c.Layer,
		})
	}
	for _, it := range ocrRes.Items {
		inter.Texts = append(inter.Texts, contracts.TextSpan{
			Text: it.Text, RawText: it.RawText, NormalizedText: it.NormalizedText,
			BBox: it.BBox, Quad: it.Quad, Angle: it.Angle, OrientationDeg: it.OrientationDeg, Confidence: it.Confidence,
			SemanticRole: it.SemanticRole, ReviewRequired: it.ReviewRequired,
		})
		inter.TextRegions = append(inter.TextRegions, contracts.TextRegion{
			BBox: it.BBox, Quad: it.Quad, Angle: it.Angle, Orientation: it.OrientationDeg, SemanticRole: it.SemanticRole,
		})
		if it.SemanticRole == "dimension_text" {
			inter.Dims = append(inter.Dims, contracts.DimensionText{
				Text:              it.RawText,
				NormalizedText:    it.NormalizedText,
				BBox:              it.BBox,
				LinkedGeometryIDs: []string{},
				LinkedSymbolIDs:   []string{},
				Confidence:        it.Confidence,
				ReviewRequired:    it.ReviewRequired,
			})
		}
		if it.ReviewRequired {
			inter.ReviewRequiredItems = append(inter.ReviewRequiredItems, contracts.ReviewItem{
				Kind:   "ocr",
				Reason: "low_ocr_confidence_or_uncertain_normalization",
				BBox:   it.BBox,
			})
			inter.LowConfidenceRegions = append(inter.LowConfidenceRegions, contracts.ReviewItem{
				Kind: "ocr", Reason: "low_ocr_confidence_or_uncertain_normalization", BBox: it.BBox,
			})
		}
	}
	if len(inter.Texts) > 0 {
		inter.ModuleConfidences["ocr"] = 0.7
	} else {
		inter.ModuleConfidences["ocr"] = 0.3
	}
	if tableRes != nil {
		tb := contracts.TableBlock{
			Cells:      []contracts.TableCell{},
			BBox:       [4]float64{0, 0, 0, 0},
			Confidence: 0.35,
			Warnings:   tableRes.Warnings,
		}
		for i, c := range tableRes.Cells {
			txt := strings.TrimSpace(toString(c["text"]))
			bb := bboxFromAny(c["bbox"])
			if bb == [4]float64{0, 0, 0, 0} {
				bb = bboxFromAny(c["roi_bbox_xyxy"])
			}
			tb.Cells = append(tb.Cells, contracts.TableCell{
				Row:        i,
				Col:        0,
				Text:       txt,
				Confidence: 0.45,
				BBox:       bb,
			})
		}
		if len(tb.Cells) > 0 {
			tb.Confidence = 0.65
			inter.Tables = append(inter.Tables, tb)
		}
		if len(tableRes.Warnings) > 0 {
			inter.Warnings = append(inter.Warnings, tableRes.Warnings...)
		}
		if tableRes.Partial {
			inter.ModuleConfidences["tables"] = 0.4
		} else if len(inter.Tables) > 0 {
			inter.ModuleConfidences["tables"] = 0.7
		} else {
			inter.ModuleConfidences["tables"] = 0.3
		}
	}
	if v, ok := inter.ImageMeta["width_px"]; ok {
		inter.Meta.WidthPx = int(v)
	}
	if v, ok := inter.ImageMeta["height_px"]; ok {
		inter.Meta.HeightPx = int(v)
	}
	inter.DebugArtifacts["preprocessed_image"] = prePath
	inter.Confidence = averageConfidence(inter.ModuleConfidences)
	b, err := json.MarshalIndent(inter, "", "  ")
	if err != nil {
		return nil, err
	}
	return b, nil
}

func averageConfidence(m map[string]float64) float64 {
	if len(m) == 0 {
		return 0
	}
	var s float64
	for _, v := range m {
		s += v
	}
	return s / float64(len(m))
}

func toString(v any) string {
	if v == nil {
		return ""
	}
	s, ok := v.(string)
	if ok {
		return s
	}
	return ""
}

func bboxFromAny(v any) [4]float64 {
	arr, ok := v.([]any)
	if !ok || len(arr) < 4 {
		return [4]float64{0, 0, 0, 0}
	}
	return [4]float64{toFloat(arr[0]), toFloat(arr[1]), toFloat(arr[2]), toFloat(arr[3])}
}

func toFloat(v any) float64 {
	switch t := v.(type) {
	case float64:
		return t
	case float32:
		return float64(t)
	case int:
		return float64(t)
	default:
		return 0
	}
}

func WriteIntermediate(layout storage.Layout, jobID, pageID uuid.UUID, data []byte) (string, error) {
	p := filepath.Join(layout.WorkDir(jobID, pageID), "intermediate.json")
	if err := storage.WriteFile(p, data); err != nil {
		return "", err
	}
	return p, nil
}
