package ocr

import (
	"context"

	"github.com/drawdigit/mvp/internal/clients/httpclient"
)

type Client struct {
	base string
	hc   *httpclient.Client
}

func New(base string, hc *httpclient.Client) *Client {
	return &Client{base: base, hc: hc}
}

type ROI struct {
	BBox     [4]float64 `json:"bbox_xyxy"`
	Semantic string     `json:"semantic_role"`
}

type RunRequest struct {
	ImagePath string `json:"image_path"`
	ROIs      []ROI  `json:"rois"`
	Profile   string `json:"profile"`
}

type OCRItem struct {
	RawText        string     `json:"raw_text"`
	NormalizedText string     `json:"normalized_text"`
	Text           string     `json:"text"`
	BBox           [4]float64 `json:"bbox_xyxy"`
	Quad           []float64  `json:"quad_xy"`
	Angle          float64    `json:"angle_deg"`
	OrientationDeg int        `json:"orientation_deg"`
	Confidence     float64    `json:"confidence"`
	SemanticRole   string     `json:"semantic_role"`
	ReviewRequired bool       `json:"review_required"`
}

type RunResponse struct {
	Items []OCRItem `json:"items"`
}

type TableRequest struct {
	ImagePath string `json:"image_path"`
	Profile   string `json:"profile"`
	ROIs      []ROI  `json:"rois"`
}

type TableResponse struct {
	Cells    []map[string]any `json:"cells"`
	HTML     string           `json:"html"`
	Warnings []string         `json:"warnings"`
	Partial  bool             `json:"partial"`
}

type PageUnderstandingRequest struct {
	ImagePath string `json:"image_path"`
	Profile   string `json:"profile"`
}

type LayoutRegion struct {
	Label      string     `json:"label"`
	BBox       [4]float64 `json:"bbox_xyxy"`
	Confidence float64    `json:"confidence"`
	Source     string     `json:"source"`
}

type ReviewHint struct {
	Kind       string     `json:"kind"`
	Reason     string     `json:"reason"`
	BBox       [4]float64 `json:"bbox_xyxy"`
	Confidence float64    `json:"confidence"`
}

type PageUnderstandingResponse struct {
	SheetType        string         `json:"sheet_type"`
	Regions          []LayoutRegion `json:"regions"`
	OrientationHints map[string]int `json:"orientation_hints"`
	ReviewHints      []ReviewHint   `json:"review_hints"`
	Warnings         []string       `json:"warnings"`
	ModelVersion     string         `json:"model_version"`
	Confidence       float64        `json:"confidence"`
}

func (c *Client) Run(ctx context.Context, req RunRequest) (*RunResponse, error) {
	var out RunResponse
	err := c.hc.PostJSON(ctx, c.base+"/v1/ocr/run", req, &out)
	if err != nil {
		return nil, err
	}
	return &out, nil
}

func (c *Client) TableStructure(ctx context.Context, req TableRequest) (*TableResponse, error) {
	var out TableResponse
	err := c.hc.PostJSON(ctx, c.base+"/v1/table/structure", req, &out)
	if err != nil {
		return nil, err
	}
	return &out, nil
}

func (c *Client) PageUnderstand(ctx context.Context, req PageUnderstandingRequest) (*PageUnderstandingResponse, error) {
	var out PageUnderstandingResponse
	err := c.hc.PostJSON(ctx, c.base+"/v1/page/understand", req, &out)
	if err != nil {
		return nil, err
	}
	return &out, nil
}
