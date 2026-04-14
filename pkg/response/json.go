package response

import (
	"encoding/json"
	"net/http"

	"github.com/drawdigit/mvp/pkg/apperrors"
)

type Envelope struct {
	Success bool            `json:"success"`
	Data    any             `json:"data,omitempty"`
	Error   *ErrorBody      `json:"error,omitempty"`
	Meta    map[string]any  `json:"meta,omitempty"`
}

type ErrorBody struct {
	Code    string `json:"code"`
	Message string `json:"message"`
	Detail  string `json:"detail,omitempty"`
	Kind    string `json:"kind,omitempty"`
}

func JSON(w http.ResponseWriter, status int, v any) {
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(v)
}

func OK(w http.ResponseWriter, data any) {
	JSON(w, http.StatusOK, Envelope{Success: true, Data: data})
}

func Error(w http.ResponseWriter, err error) {
	ae, ok := apperrors.IsAppError(err)
	if !ok {
		JSON(w, http.StatusInternalServerError, Envelope{
			Success: false,
			Error:   &ErrorBody{Code: "internal_error", Message: "internal error"},
		})
		return
	}
	st := ae.HTTPStatus
	if st == 0 {
		st = http.StatusInternalServerError
	}
	JSON(w, st, Envelope{
		Success: false,
		Error: &ErrorBody{
			Code:    ae.Code,
			Message: ae.Message,
			Detail:  ae.Detail,
			Kind:    string(ae.Kind),
		},
	})
}
