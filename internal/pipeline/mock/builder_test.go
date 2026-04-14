package mock

import (
	"testing"

	"github.com/google/uuid"

	"github.com/drawdigit/mvp/internal/pipeline/contracts"
)

func TestIntermediate(t *testing.T) {
	jid := uuid.New()
	pid := uuid.New()
	b, err := Intermediate(jid, pid, "a.png", contracts.ProfileBalanced)
	if err != nil {
		t.Fatal(err)
	}
	if len(b) < 50 {
		t.Fatal("too short")
	}
}
