package integration

import (
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"github.com/drawdigit/mvp/internal/clients/httpclient"
	"github.com/drawdigit/mvp/internal/clients/ocr"
)

func TestTableClientContract(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/v1/table/structure" {
			t.Fatalf("unexpected path %s", r.URL.Path)
		}
		_ = json.NewEncoder(w).Encode(map[string]any{
			"cells":    []map[string]any{{"text": "A1"}},
			"html":     "",
			"warnings": []string{},
			"partial":  false,
		})
	}))
	defer srv.Close()

	c := ocr.New(srv.URL, httpclient.New(2*time.Second))
	res, err := c.TableStructure(context.Background(), ocr.TableRequest{ImagePath: "/tmp/x.png", Profile: "balanced"})
	if err != nil {
		t.Fatal(err)
	}
	if len(res.Cells) == 0 {
		t.Fatal("expected at least one cell")
	}
}
