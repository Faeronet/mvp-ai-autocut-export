package telemetry

import (
	"net/http"
	"strconv"
	"sync/atomic"
)

var requests atomic.Uint64

func IncRequest() {
	requests.Add(1)
}

func Handler() http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "text/plain")
		_, _ = w.Write([]byte("requests_total " + strconv.FormatUint(requests.Load(), 10) + "\n"))
	}
}
