package contracts

// IntermediateJSON is the structured assembly between CV/OCR and export.
type IntermediateJSON struct {
	Meta                 Meta               `json:"meta"`
	ImageMeta            map[string]float64 `json:"image_meta"`
	ProcessingProfile    string             `json:"processing_profile"`
	PageUnderstanding    PageUnderstanding  `json:"page_understanding"`
	Zones                []Zone             `json:"zones"`
	TextRegions          []TextRegion       `json:"text_regions"`
	Geometry             GeometryBlock      `json:"geometry"`
	Texts                []TextSpan         `json:"texts"`
	Title                *TitleBlock        `json:"title_block,omitempty"`
	Dims                 []DimensionText    `json:"dimensions"`
	Tables               []TableBlock       `json:"tables"`
	Warnings             []string           `json:"warnings"`
	Confidence           float64            `json:"confidence"`
	ModuleConfidences    map[string]float64 `json:"module_confidences"`
	LowConfidenceRegions []ReviewItem       `json:"low_confidence_regions"`
	ReviewHints          []ReviewHint       `json:"review_hints"`
	DebugArtifacts       map[string]string  `json:"debug_artifacts"`
	ReviewRequiredItems  []ReviewItem       `json:"review_required_items"`
}

type Meta struct {
	JobID      string `json:"job_id"`
	PageID     string `json:"page_id"`
	SourceFile string `json:"source_file"`
	WidthPx    int    `json:"width_px"`
	HeightPx   int    `json:"height_px"`
	Profile    string `json:"profile"`
}

type Zone struct {
	Label      string     `json:"label"`
	BBox       [4]float64 `json:"bbox_xyxy"`
	Confidence float64    `json:"confidence"`
}

type PageUnderstanding struct {
	SheetType        string         `json:"sheet_type"`
	Regions          []Zone         `json:"regions"`
	OrientationHints map[string]int `json:"orientation_hints"`
	ModelVersion     string         `json:"model_version"`
	Confidence       float64        `json:"confidence"`
}

type GeometryBlock struct {
	Lines       []LineSeg   `json:"lines"`
	Polylines   [][]float64 `json:"polylines"`
	Circles     []Circle    `json:"circles"`
	Arcs        []Arc       `json:"arcs"`
	Tables      []TableGeom `json:"tables"`
	Arrows      []Arrow     `json:"arrows"`
	Centerlines []LineSeg   `json:"centerlines"`
}

type LineSeg struct {
	X1         float64 `json:"x1"`
	Y1         float64 `json:"y1"`
	X2         float64 `json:"x2"`
	Y2         float64 `json:"y2"`
	Layer      string  `json:"layer"`
	Confidence float64 `json:"confidence"`
}

type Circle struct {
	Cx    float64 `json:"cx"`
	Cy    float64 `json:"cy"`
	R     float64 `json:"r"`
	Layer string  `json:"layer"`
}

type Arc struct {
	Cx, Cy, R, Start, End float64
	Layer                 string `json:"layer"`
}

type TableGeom struct {
	Rows int        `json:"rows"`
	Cols int        `json:"cols"`
	BBox [4]float64 `json:"bbox_xyxy"`
}

type Arrow struct {
	X1, Y1, X2, Y2 float64
}

type TextSpan struct {
	Text           string     `json:"text"`
	RawText        string     `json:"raw_text"`
	NormalizedText string     `json:"normalized_text"`
	BBox           [4]float64 `json:"bbox_xyxy"`
	Quad           []float64  `json:"quad_xy"`
	Angle          float64    `json:"angle_deg"`
	OrientationDeg int        `json:"orientation_deg"`
	Confidence     float64    `json:"confidence"`
	SemanticRole   string     `json:"semantic_role"`
	ReviewRequired bool       `json:"review_required"`
}

type TextRegion struct {
	BBox         [4]float64 `json:"bbox_xyxy"`
	Quad         []float64  `json:"quad_xy"`
	Angle        float64    `json:"angle_deg"`
	Orientation  int        `json:"orientation_deg"`
	SemanticRole string     `json:"semantic_role"`
}

type TitleBlock struct {
	RawLines []string `json:"raw_lines"`
}

type DimensionText struct {
	Text              string     `json:"text"`
	NormalizedText    string     `json:"normalized_text"`
	BBox              [4]float64 `json:"bbox_xyxy"`
	LinkedGeometryIDs []string   `json:"linked_geometry_ids"`
	LinkedSymbolIDs   []string   `json:"linked_symbol_ids"`
	Confidence        float64    `json:"confidence"`
	ReviewRequired    bool       `json:"review_required"`
}

type TableBlock struct {
	Cells      []TableCell `json:"cells"`
	BBox       [4]float64  `json:"bbox_xyxy"`
	Confidence float64     `json:"confidence"`
	Warnings   []string    `json:"warnings"`
}

type TableCell struct {
	Row        int        `json:"row"`
	Col        int        `json:"col"`
	Text       string     `json:"text"`
	Confidence float64    `json:"confidence"`
	BBox       [4]float64 `json:"bbox_xyxy"`
}

type ReviewItem struct {
	Kind   string     `json:"kind"`
	Reason string     `json:"reason"`
	BBox   [4]float64 `json:"bbox_xyxy"`
}

type ReviewHint struct {
	Kind       string     `json:"kind"`
	Reason     string     `json:"reason"`
	BBox       [4]float64 `json:"bbox_xyxy"`
	Confidence float64    `json:"confidence"`
}
