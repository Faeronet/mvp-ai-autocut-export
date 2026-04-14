package prompts

func List() []map[string]any {
	return []map[string]any{
		{
			"name":        "digitize_drawings_archive",
			"description": "Standard workflow for digitizing drawing archives",
			"arguments": []map[string]any{
				{"name": "archive_path", "required": true},
				{"name": "profile", "required": false},
			},
		},
		{
			"name":        "inspect_low_confidence_regions",
			"description": "Analyze suspicious OCR/layout regions",
			"arguments": []map[string]any{
				{"name": "job_id", "required": true},
				{"name": "page_id", "required": true},
			},
		},
		{
			"name":        "export_job_summary",
			"description": "Structured summary for a job",
			"arguments": []map[string]any{
				{"name": "job_id", "required": true},
			},
		},
	}
}

func Get(name string) (string, bool) {
	switch name {
	case "digitize_drawings_archive":
		return "Use submit_archive with local_path and processing_profile, then poll get_job_status.", true
	case "inspect_low_confidence_regions":
		return "Open resource job://{job_id}/report and review failed_pages.", true
	case "export_job_summary":
		return "Call get_job_report for structured JSON.", true
	default:
		return "", false
	}
}
