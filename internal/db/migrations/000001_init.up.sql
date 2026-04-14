CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    status TEXT NOT NULL,
    input_archive_name TEXT NOT NULL,
    input_archive_path TEXT NOT NULL,
    result_archive_path TEXT,
    total_pages INT NOT NULL DEFAULT 0,
    completed_pages INT NOT NULL DEFAULT 0,
    failed_pages INT NOT NULL DEFAULT 0,
    progress_percent INT NOT NULL DEFAULT 0,
    current_step TEXT NOT NULL DEFAULT '',
    error_message TEXT NOT NULL DEFAULT '',
    warnings_count INT NOT NULL DEFAULT 0,
    profile TEXT NOT NULL DEFAULT 'balanced',
    timings_json JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_created ON jobs(created_at DESC);

CREATE TABLE IF NOT EXISTS page_artifacts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    source_image_name TEXT NOT NULL,
    source_image_path TEXT NOT NULL,
    preprocessed_path TEXT NOT NULL DEFAULT '',
    overlay_path TEXT NOT NULL DEFAULT '',
    preview_path TEXT NOT NULL DEFAULT '',
    dxf_path TEXT NOT NULL DEFAULT '',
    json_path TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL,
    confidence_score DOUBLE PRECISION NOT NULL DEFAULT 0,
    warnings_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    errors_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_pages_job ON page_artifacts(job_id);

CREATE TABLE IF NOT EXISTS job_events (
    id BIGSERIAL PRIMARY KEY,
    job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    step TEXT NOT NULL,
    message TEXT NOT NULL,
    level TEXT NOT NULL DEFAULT 'info',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_events_job ON job_events(job_id, created_at);
