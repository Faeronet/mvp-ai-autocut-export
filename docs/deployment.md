# Deployment (Ubuntu 22.04 + Docker + NVIDIA)

1. Install Docker Engine and Compose plugin.
2. Install NVIDIA Container Toolkit and configure the Docker runtime.
3. Copy `.env.example` to `.env` and tune GPU profile env vars.
4. Run `make docker-up` from the repository root (uses `deploy/docker-compose.yml`).

For machines without a GPU, remove `gpus: all` blocks via an override file or run `MOCK_PIPELINE=true`.

## External / LAN access (UI from another machine)

Compose publishes **web** on `0.0.0.0:80`, **api** on `0.0.0.0:8080`, **mcp** on `0.0.0.0:8090`. Open the UI at `http://<server-ip>/` from any host on the routed network.

- **Firewall** (example UFW): `sudo ufw allow 80/tcp` (and `8080`/`8090` if you need direct API/MCP from outside).
- **CORS / MCP defaults** in compose use `*` so browsers and MCP clients can talk to the API when the site is opened by IP or hostname. For production on the public Internet, set explicit `CORS_ALLOWED_ORIGINS` and `MCP_ALLOWED_HOSTS` and put TLS + auth in front (reverse proxy).
- **Dev** (`npm run dev`): Vite listens on all interfaces (`host: true`), e.g. `http://<server-ip>:5173`.
