package validation

import (
	"strings"

	"github.com/drawdigit/mvp/pkg/apperrors"
)

func NonEmpty(field, s string) error {
	if strings.TrimSpace(s) == "" {
		return apperrors.New(apperrors.KindValidation, "empty_field", field+" is required")
	}
	return nil
}
