package layout

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

type DetectRequest struct {
	ImagePath string `json:"image_path"`
	Profile   string `json:"profile"`
}

type ZoneDTO struct {
	Label      string     `json:"label"`
	BBox       [4]float64 `json:"bbox_xyxy"`
	Confidence float64    `json:"confidence"`
}

type DetectResponse struct {
	Zones          []ZoneDTO         `json:"zones"`
	Overlay        string            `json:"overlay_path"`
	Warnings       []string          `json:"warnings"`
	Mode           string            `json:"mode"`
	DebugArtifacts map[string]string `json:"debug_artifacts"`
}

func (c *Client) Detect(ctx context.Context, req DetectRequest) (*DetectResponse, error) {
	var out DetectResponse
	err := c.hc.PostJSON(ctx, c.base+"/v1/layout/detect", req, &out)
	if err != nil {
		return nil, err
	}
	return &out, nil
}
