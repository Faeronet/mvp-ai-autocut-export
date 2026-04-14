package integration

import (
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/drawdigit/mvp/pkg/telemetry"
)

func TestMetricsEndpoint(t *testing.T) {
	srv := httptest.NewServer(telemetry.Handler())
	defer srv.Close()
	res, err := http.Get(srv.URL)
	if err != nil {
		t.Fatal(err)
	}
	defer res.Body.Close()
	if res.StatusCode != http.StatusOK {
		t.Fatalf("status %d", res.StatusCode)
	}
}
