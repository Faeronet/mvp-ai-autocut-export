package transport

import (
	"net"
	"net/http"
	"strings"
)

func ValidateOrigin(r *http.Request, allowedHosts []string) bool {
	origin := r.Header.Get("Origin")
	if origin == "" {
		return true
	}
	for _, h := range allowedHosts {
		if h == "*" {
			return true
		}
	}
	host := r.Host
	if h, _, err := net.SplitHostPort(host); err == nil {
		host = h
	}
	for _, h := range allowedHosts {
		if strings.EqualFold(h, host) || h == "*" {
			return true
		}
	}
	o := strings.TrimPrefix(strings.ToLower(origin), "http://")
	o = strings.TrimPrefix(o, "https://")
	for _, h := range allowedHosts {
		if strings.HasPrefix(o, strings.ToLower(h)) {
			return true
		}
	}
	return false
}
