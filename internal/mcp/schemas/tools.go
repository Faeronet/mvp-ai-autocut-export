package schemas

type ToolDef struct {
	Name        string         `json:"name"`
	Description string         `json:"description"`
	InputSchema map[string]any `json:"inputSchema"`
}

func ToolList() []ToolDef {
	return []ToolDef{
		{Name: "submit_archive", Description: "Submit processing job", InputSchema: map[string]any{
			"type": "object",
			"properties": map[string]any{
				"local_path":         map[string]any{"type": "string"},
				"processing_profile": map[string]any{"type": "string"},
			},
		}},
		{Name: "get_job_status", Description: "Get job status", InputSchema: map[string]any{
			"type": "object", "properties": map[string]any{"job_id": map[string]any{"type": "string"}},
		}},
		{Name: "list_job_outputs", Description: "List outputs", InputSchema: map[string]any{
			"type": "object", "properties": map[string]any{"job_id": map[string]any{"type": "string"}},
		}},
		{Name: "download_result_info", Description: "Download info", InputSchema: map[string]any{
			"type": "object", "properties": map[string]any{"job_id": map[string]any{"type": "string"}},
		}},
		{Name: "get_job_report", Description: "Report", InputSchema: map[string]any{
			"type": "object", "properties": map[string]any{"job_id": map[string]any{"type": "string"}},
		}},
		{Name: "cancel_job", Description: "Cancel", InputSchema: map[string]any{
			"type": "object", "properties": map[string]any{"job_id": map[string]any{"type": "string"}},
		}},
		{Name: "retry_job", Description: "Retry", InputSchema: map[string]any{
			"type": "object", "properties": map[string]any{
				"job_id": map[string]any{"type": "string"},
				"profile": map[string]any{"type": "string"},
			},
		}},
		{Name: "health_check", Description: "Health", InputSchema: map[string]any{"type": "object"}},
	}
}
