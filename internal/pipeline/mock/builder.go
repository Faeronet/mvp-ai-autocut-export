package mock

import (
	"encoding/json"

	"github.com/google/uuid"

	"github.com/drawdigit/mvp/internal/pipeline/contracts"
)

func Intermediate(jobID, pageID uuid.UUID, sourceName string, profile contracts.ProcessingProfile) ([]byte, error) {
	inter := contracts.IntermediateJSON{
		Meta: contracts.Meta{
			JobID: jobID.String(), PageID: pageID.String(), SourceFile: sourceName, Profile: string(profile),
			WidthPx: 1024, HeightPx: 768,
		},
		Zones: []contracts.Zone{
			{Label: "drawing_area", BBox: [4]float64{10, 10, 1000, 700}, Confidence: 0.9},
			{Label: "title_block", BBox: [4]float64{700, 650, 1000, 750}, Confidence: 0.8},
		},
		Geometry: contracts.GeometryBlock{
			Lines: []contracts.LineSeg{
				{X1: 50, Y1: 50, X2: 900, Y2: 50, Layer: "GEOMETRY", Confidence: 0.85},
			},
			Circles: []contracts.Circle{{Cx: 400, Cy: 400, R: 80, Layer: "GEOMETRY"}},
		},
		Texts: []contracts.TextSpan{
			{Text: "MOCK TITLE", RawText: "MOCK TITLE", NormalizedText: "MOCK TITLE", BBox: [4]float64{720, 660, 980, 740}, Confidence: 0.9, SemanticRole: "title_block"},
		},
		Warnings:   []string{"mock pipeline enabled"},
		Confidence: 0.5,
	}
	return json.MarshalIndent(inter, "", "  ")
}
