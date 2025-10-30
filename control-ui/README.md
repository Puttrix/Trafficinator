# Trafficinator Control UI

Web-based control interface for the Trafficinator load generator.

## Features

- 🚀 FastAPI-based REST API
- 🐳 Docker SDK integration for container control
- 🔒 API key authentication
- 📊 Real-time status monitoring
- 📝 Container log viewing
- ⚙️ Configuration management

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Trafficinator project cloned

### Running with Docker Compose

1. **Copy the example environment file:**
   ```bash
   cp .env.webui.example .env
   ```

2. **Edit `.env` and configure your settings:**
   ```bash
   # Update MATOMO_URL, MATOMO_SITE_ID, etc.
   # IMPORTANT: Change CONTROL_UI_API_KEY for security
   nano .env
   ```

3. **Start both services:**
   ```bash
   docker-compose -f docker-compose.webui.yml up --build
   ```

4. **Access the API:**
   - API: http://localhost:8000
   - Docs: http://localhost:8000/docs
   - Health: http://localhost:8000/health

### Development Setup

For local development without Docker:

1. **Install dependencies:**
   ```bash
   cd control-ui
   python -m venv venv
   source venv/bin/activate  # or `venv\Scripts\activate` on Windows
   pip install -r requirements.txt
   ```

2. **Run the development server:**
   ```bash
   python app.py
   ```

3. **Access at:** http://localhost:8000

## API Endpoints

### Health Check
```bash
GET /health
```

### Root
```bash
GET /
```

Response:
```json
{
  "name": "Trafficinator Control UI API",
  "version": "1.0.0",
  "status": "running",
  "docs": "/docs",
  "health": "/health"
}
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `CONTROL_UI_PORT` | Port for the API server | `8000` |
| `CONTROL_UI_API_KEY` | API key for authentication | `change-me-in-production` |
| `CORS_ORIGINS` | Allowed CORS origins (comma-separated) | `*` |

### Security

**⚠️ Important:** Always change the default `CONTROL_UI_API_KEY` in production!

```bash
# Generate a secure API key
openssl rand -hex 32
```

Update your `.env` file:
```
CONTROL_UI_API_KEY=your-secure-random-key-here
```

## Docker Socket Access

The Control UI requires access to the Docker socket to manage containers:

```yaml
volumes:
  - /var/run/docker.sock:/var/run/docker.sock
```

**Security Note:** This grants the container significant privileges. Only run the Control UI in trusted environments.

## Troubleshooting

### Connection Issues

If the UI can't connect to Docker:

1. **Check Docker socket permissions:**
   ```bash
   ls -l /var/run/docker.sock
   ```

2. **Ensure Docker is running:**
   ```bash
   docker ps
   ```

3. **Check container logs:**
   ```bash
   docker-compose -f docker-compose.webui.yml logs control-ui
   ```

### Container Not Found

If the `matomo-loadgen` container isn't found:

1. **Verify the container exists:**
   ```bash
   docker ps -a | grep matomo-loadgen
   ```

2. **Ensure correct container name:**
   - Default name: `matomo-loadgen`
   - Configured in `docker_client.py`

## Architecture

```
┌─────────────────────┐
│   Control UI API    │
│   (FastAPI, :8000)  │
└──────────┬──────────┘
           │
      ┌────▼─────┐
      │  Docker  │
      │   SDK    │
      └────┬─────┘
           │
    ┌──────▼──────────┐
    │ matomo-loadgen  │
    │   container     │
    └─────────────────┘
```

## Development

### Project Structure

```
control-ui/
├── app.py              # FastAPI application
├── docker_client.py    # Docker SDK wrapper
├── requirements.txt    # Python dependencies
├── Dockerfile          # Container definition
└── README.md          # This file
```

### Adding Features

1. **New endpoints:** Add to `app.py`
2. **Docker operations:** Extend `docker_client.py`
3. **Dependencies:** Update `requirements.txt`

### Testing

```bash
# Run with auto-reload for development
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

## Next Steps

- [ ] P-016: Implement core REST API endpoints
- [ ] P-017: Add configuration validation
- [ ] P-018: Configuration persistence (SQLite)
- [ ] P-019: Authentication and security layer
- [ ] P-020: Frontend implementation

## License

MIT License - See project root for details
