package middleware

import (
	"net/http"
	"strings"
)

func CORS(allowed []string) func(http.Handler) http.Handler {
	allowAny := false
	for _, o := range allowed {
		if o == "*" {
			allowAny = true
			break
		}
	}
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			origin := r.Header.Get("Origin")
			ok := false
			if allowAny {
				ok = true
			} else {
				for _, o := range allowed {
					if strings.EqualFold(o, origin) {
						ok = true
						break
					}
				}
			}
			if ok {
				if allowAny {
					if origin != "" {
						// Echo origin so browsers accept credentialed flows from any UI host (LAN/public IP).
						w.Header().Set("Access-Control-Allow-Origin", origin)
						w.Header().Set("Vary", "Origin")
					} else {
						w.Header().Set("Access-Control-Allow-Origin", "*")
					}
				} else if origin != "" {
					w.Header().Set("Access-Control-Allow-Origin", origin)
					w.Header().Set("Vary", "Origin")
				}
			}
			w.Header().Set("Access-Control-Allow-Methods", "GET,POST,PUT,DELETE,OPTIONS")
			w.Header().Set("Access-Control-Allow-Headers", "Content-Type, Authorization, Mcp-Protocol-Version, Mcp-Session-Id, X-Request-ID")
			if r.Method == http.MethodOptions {
				w.WriteHeader(http.StatusNoContent)
				return
			}
			next.ServeHTTP(w, r)
		})
	}
}
