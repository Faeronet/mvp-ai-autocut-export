package contracts

import (
	"context"

	"github.com/google/uuid"

	"github.com/drawdigit/mvp/internal/config"
)

// PipelineContext carries per-job state through steps.
type PipelineContext struct {
	Ctx    context.Context
	JobID  uuid.UUID
	Config config.Config
	Profile ProcessingProfile
	Mock   bool
}

// ProcessingProfile maps user-facing profile to service parameters.
type ProcessingProfile string

const (
	ProfileBalanced ProcessingProfile = "balanced"
	ProfileQuality  ProcessingProfile = "quality"
	ProfileLowVRAM  ProcessingProfile = "low_vram"
)

func ParseProfile(s string) ProcessingProfile {
	switch s {
	case string(ProfileQuality):
		return ProfileQuality
	case string(ProfileLowVRAM):
		return ProfileLowVRAM
	default:
		return ProfileBalanced
	}
}
