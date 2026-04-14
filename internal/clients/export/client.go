package export

import (
	"context"

	"github.com/drawdigit/mvp/internal/clients/httpclient"
	"github.com/drawdigit/mvp/internal/pipeline/contracts"
)

type Client struct {
	base string
	hc   *httpclient.Client
}

func New(base string, hc *httpclient.Client) *Client {
	return &Client{base: base, hc: hc}
}

type RenderRequest struct {
	Intermediate contracts.IntermediateJSON `json:"intermediate"`
	OutputDXF    string                     `json:"output_dxf"`
	OutputPNG    string                     `json:"output_png"`
	Profile      string                     `json:"profile"`
}

type RenderResponse struct {
	DXFPath           string `json:"dxf_path"`
	PNGPath           string `json:"png_path"`
	DiagnosticPNGPath string `json:"diagnostic_png_path"`
}

func (c *Client) Render(ctx context.Context, req RenderRequest) (*RenderResponse, error) {
	var out RenderResponse
	err := c.hc.PostJSON(ctx, c.base+"/v1/export/render", req, &out)
	if err != nil {
		return nil, err
	}
	return &out, nil
}
