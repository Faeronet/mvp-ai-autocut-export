package job

type Status string

const (
	StatusQueued         Status = "queued"
	StatusUnpacking      Status = "unpacking"
	StatusPreprocessing  Status = "preprocessing"
	StatusLayout         Status = "layout"
	StatusGeometry       Status = "geometry"
	StatusOCR            Status = "ocr"
	StatusAssembling     Status = "assembling"
	StatusExporting      Status = "exporting"
	StatusPackaging      Status = "packaging"
	StatusCompleted      Status = "completed"
	StatusFailed         Status = "failed"
	StatusPartialSuccess Status = "partial_success"
	StatusCancelled      Status = "cancelled"
)

func IsTerminal(s Status) bool {
	switch s {
	case StatusCompleted, StatusFailed, StatusPartialSuccess, StatusCancelled:
		return true
	default:
		return false
	}
}
