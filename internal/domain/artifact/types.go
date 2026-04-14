package artifact

type Kind string

const (
	KindDXF     Kind = "dxf"
	KindPNG     Kind = "png"
	KindJSON    Kind = "json"
	KindLog     Kind = "log"
	KindReport  Kind = "report"
	KindOverlay Kind = "overlay"
)

type Reference struct {
	Path string `json:"path"`
	Kind Kind   `json:"kind"`
}
