package vector

import (
	"context"

	"github.com/drawdigit/mvp/internal/clients/httpclient"
)

type PreprocessRequest struct {
	ImagePath string `json:"image_path"`
	OutputDir string `json:"output_dir"`
	Profile   string `json:"profile"`
	SaveDebug bool   `json:"save_debug"`
}

type PreprocessResponse struct {
	PreprocessedPath     string             `json:"preprocessed_path"`
	BinaryPath           string             `json:"binary_path"`
	SoftPath             string             `json:"soft_path"`
	DebugArtifacts       map[string]string  `json:"debug_artifacts"`
	ImageMeta            map[string]float64 `json:"image_meta"`
	Warnings             []string           `json:"warnings"`
	PreprocessConfidence float64            `json:"preprocess_confidence"`
}

func Preprocess(ctx context.Context, base string, hc *httpclient.Client, req PreprocessRequest) (*PreprocessResponse, error) {
	var out PreprocessResponse
	err := hc.PostJSON(ctx, base+"/v1/vector/preprocess", req, &out)
	if err != nil {
		return nil, err
	}
	return &out, nil
}
