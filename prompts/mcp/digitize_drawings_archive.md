# digitize_drawings_archive

Use MCP tool `submit_archive` with `local_path` pointing to a ZIP of scans and `processing_profile` (`balanced`, `quality`, or `low_vram`). Poll `get_job_status` until terminal state, then fetch `download_result_info` and resources `job://{id}/manifest`.
