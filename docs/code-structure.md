# Code structure (non-monolithic layout)

- `cmd/*`: thin entrypoints only.
- `internal/http`: transport layer split into `handlers`, `routes`, `middleware`, `dto`.
- `internal/services`: business logic (jobs orchestration).
- `internal/repositories`: SQL access.
- `internal/clients`: outbound HTTP to Python services.
- `internal/pipeline`: orchestration plus `steps/` for each pipeline phase.
- `internal/mcp`: MCP protocol, tools, resources, prompts, transport.
- `pkg/*`: shared libraries (logger, errors, response, validation, telemetry).
- `services/*-service`: Python FastAPI apps split by `api/`, `services/`, `inference/`, `preprocessing/`, `postprocessing/`, `exporters/`.
- `apps/web`: React feature folders (`features/*`) and `shared/*`.

This separation keeps HTTP handlers free of SQL and keeps ML preprocessing out of route files.
