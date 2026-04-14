package middleware

import (
	"context"
	"net/http"

	"github.com/google/uuid"

	"github.com/drawdigit/mvp/pkg/logger"
)

func RequestID(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		rid := r.Header.Get("X-Request-ID")
		if rid == "" {
			rid = uuid.New().String()
		}
		w.Header().Set("X-Request-ID", rid)
		ctx := logger.WithRequestID(r.Context(), rid)
		next.ServeHTTP(w, r.WithContext(ctx))
	})
}

func RequestIDFromRequest(r *http.Request) string {
	return logger.RequestIDFromContext(r.Context())
}

func WithRequestID(ctx context.Context, id string) context.Context {
	return logger.WithRequestID(ctx, id)
}
