# Remote Deployment Setup

This document describes how to deploy Trafficinator on your remote machine with automatic updates using GitHub Container Registry and Watchtower.

## Prerequisites

- Docker and Docker Compose installed on your remote machine
- Portainer (optional, for easier management)
- Your `config/urls.txt` file uploaded to the remote machine

## Setup Steps

### 1. Clone or Upload Files

Upload these files to your remote machine:
- `docker-compose.prod.yml`
- `config/` directory with your URLs file

### 2. Configure Environment Variables

Edit the environment variables in `docker-compose.prod.yml`:

```yaml
environment:
  MATOMO_URL: "https://your-matomo-instance.com/matomo.php"
  MATOMO_SITE_ID: "1"
  TARGET_VISITS_PER_DAY: "20000"
  # ... other settings
```

### 3. Deploy with Watchtower

Run the production compose file:

```bash
docker-compose -f docker-compose.prod.yml up -d
```

This will:
- Pull the latest image from GitHub Container Registry
- Start the Trafficinator container
- Start Watchtower to monitor for updates every 30 seconds

### 4. Verify Deployment

Check container status:
```bash
docker-compose -f docker-compose.prod.yml ps
docker-compose -f docker-compose.prod.yml logs -f matomo_loadgen
```

## Automatic Updates

Watchtower is configured to:
- Check for updates every 30 seconds
- Only monitor the `matomo-loadgen` container
- Automatically pull new images and restart the container
- Clean up old images after updates

## Manual Operations

### Update Configuration
```bash
# Edit docker-compose.prod.yml
docker-compose -f docker-compose.prod.yml up -d
```

### Stop/Start
```bash
# Stop
docker-compose -f docker-compose.prod.yml down

# Start
docker-compose -f docker-compose.prod.yml up -d
```

### View Logs
```bash
docker-compose -f docker-compose.prod.yml logs -f
```

## Network Configuration

If using Nginx Proxy Manager or Cloudflare Tunnel:

1. Uncomment the networks section in `docker-compose.prod.yml`
2. Remove port mappings if not needed
3. Attach to your external proxy network

## GitHub Actions Workflow

The included workflow (`.github/workflows/docker-build.yml`) will:
- Build images on pushes to `main` and `develop` branches
- Push to GitHub Container Registry as `ghcr.io/puttrix/trafficinator:latest`
- Tag images with branch names and commit SHAs

## Security Notes

- GitHub Container Registry images are pulled using public access
- No authentication required for public repositories
- Watchtower runs with Docker socket access (standard for container management)