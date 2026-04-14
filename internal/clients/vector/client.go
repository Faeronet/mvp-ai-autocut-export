package vector

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

type ExtractRequest struct {
	ImagePath string `json:"image_path"`
	Profile   string `json:"profile"`
}

type LineDTO struct {
	X1         float64 `json:"x1"`
	Y1         float64 `json:"y1"`
	X2         float64 `json:"x2"`
	Y2         float64 `json:"y2"`
	Layer      string  `json:"layer"`
	Confidence float64 `json:"confidence"`
}

type CircleDTO struct {
	Cx    float64 `json:"cx"`
	Cy    float64 `json:"cy"`
	R     float64 `json:"r"`
	Layer string  `json:"layer"`
}

type ExtractResponse struct {
	Lines   []LineDTO   `json:"lines"`
	Circles []CircleDTO `json:"circles"`
	Tables  []any       `json:"tables"`
}

func (c *Client) Extract(ctx context.Context, req ExtractRequest) (*ExtractResponse, error) {
	var out ExtractResponse
	err := c.hc.PostJSON(ctx, c.base+"/v1/vector/extract", req, &out)
	if err != nil {
		return nil, err
	}
	return &out, nil
}
