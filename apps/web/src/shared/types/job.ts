export type JobStatus = string;

export interface Job {
  id: string;
  created_at: string;
  updated_at: string;
  status: JobStatus;
  input_archive_name: string;
  result_archive_path?: string;
  total_pages: number;
  completed_pages: number;
  failed_pages: number;
  progress_percent: number;
  current_step: string;
  error_message?: string;
  warnings_count: number;
  profile: string;
}
