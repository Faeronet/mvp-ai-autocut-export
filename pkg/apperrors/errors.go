package apperrors

import (
	"errors"
	"fmt"
	"net/http"
)

type Kind string

const (
	KindValidation   Kind = "validation"
	KindNotFound     Kind = "not_found"
	KindConflict     Kind = "conflict"
	KindInternal     Kind = "internal"
	KindUnsupported  Kind = "unsupported"
	KindEmptyInput   Kind = "empty_input"
	KindCorrupted    Kind = "corrupted"
	KindPipeline     Kind = "pipeline"
)

type AppError struct {
	Kind       Kind
	Code       string
	Message    string
	Detail     string
	HTTPStatus int
	Err        error
}

func (e *AppError) Error() string {
	if e.Err != nil {
		return fmt.Sprintf("%s: %v", e.Message, e.Err)
	}
	return e.Message
}

func (e *AppError) Unwrap() error { return e.Err }

func New(kind Kind, code, msg string) *AppError {
	return &AppError{Kind: kind, Code: code, Message: msg, HTTPStatus: statusForKind(kind)}
}

func Wrap(kind Kind, code, msg string, err error) *AppError {
	return &AppError{Kind: kind, Code: code, Message: msg, Err: err, HTTPStatus: statusForKind(kind)}
}

func statusForKind(k Kind) int {
	switch k {
	case KindValidation, KindEmptyInput, KindUnsupported, KindCorrupted:
		return http.StatusBadRequest
	case KindNotFound:
		return http.StatusNotFound
	case KindConflict:
		return http.StatusConflict
	default:
		return http.StatusInternalServerError
	}
}

func IsAppError(err error) (*AppError, bool) {
	var ae *AppError
	if errors.As(err, &ae) {
		return ae, true
	}
	return nil, false
}
