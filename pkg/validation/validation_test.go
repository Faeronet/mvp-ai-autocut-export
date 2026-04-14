package validation

import "testing"

func TestNonEmpty(t *testing.T) {
	if err := NonEmpty("f", "x"); err != nil {
		t.Fatal(err)
	}
	if err := NonEmpty("f", "  "); err == nil {
		t.Fatal("expected error")
	}
}
