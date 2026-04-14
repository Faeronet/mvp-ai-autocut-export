# Architecture

The system is a monorepo with a Go control plane (API, worker, MCP) and Python ML/CV microservices. PostgreSQL stores job metadata, Redis backs the FIFO queue and GPU lock, and `/data` holds archives and artifacts.

The worker executes a modular pipeline: unpack → validate → preprocess (vector) → layout → geometry (vector) → ROI OCR → assemble JSON → export (DXF+PNG) → zip package.

MCP exposes JSON-RPC over HTTP at `/mcp` with optional stdio debugging (`--stdio`).
