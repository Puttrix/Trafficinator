# Trafficinator Web UI - Security Best Practices

Comprehensive security guidelines for deploying and operating the Trafficinator Web Control Interface.

---

## Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [Network Security](#network-security)
- [HTTPS/TLS](#httpstls)
- [Rate Limiting](#rate-limiting)
- [CORS Configuration](#cors-configuration)
- [Deployment Security](#deployment-security)
- [Monitoring & Logging](#monitoring--logging)
- [Security Checklist](#security-checklist)

---

## Overview

The Trafficinator Web UI includes multiple security layers to protect your deployment:

- **API Key Authentication** - Simple, effective access control
- **Rate Limiting** - Protection against abuse and DoS
- **Security Headers** - Browser-level protections
- **CORS Controls** - Origin-based access restrictions
- **Docker Isolation** - Container-level separation

**Security Model:** Defense in depth with multiple independent layers.

---

## Authentication

### API Key Management

**Default Key (DEV ONLY):**
```yaml
CONTROL_UI_API_KEY: "change-me-in-production"
```

⚠️ **Never use the default key in production!**

### Generate Secure Keys

**Method 1: OpenSSL**
```bash
openssl rand -base64 32
# Example output: vR7mK9pL2nQ4wX8yT6hN1bS5aF3jG0cM9vR7mK9pL2n=
```

**Method 2: Python**
```python
import secrets
print(secrets.token_urlsafe(32))
# Example output: xK9mL2nP5qR8tV1wY4zA7bC0dF3gH6jM9pN2qS5uX8y
```

**Method 3: pwgen**
```bash
pwgen -s 48 1
# Example output: T7mK9pL2nQ5wX8yV1bN4aS7cF0gH3jM6pR9tU2xY5zB8dE1gH4k
```

### Key Requirements

- **Minimum length:** 32 characters
- **Character set:** Letters, numbers, symbols
- **Randomness:** Cryptographically secure generation
- **Rotation:** Change keys periodically (quarterly recommended)

### Storage Best Practices

**1. Environment Variables (Recommended)**
```yaml
# docker-compose.webui.yml
services:
  control-ui:
    environment:
      CONTROL_UI_API_KEY: "${CONTROL_UI_API_KEY}"
```

```bash
# .env (add to .gitignore!)
CONTROL_UI_API_KEY=your-secure-key-here
```

**2. Docker Secrets (Advanced)**
```yaml
services:
  control-ui:
    secrets:
      - control_ui_api_key
    environment:
      CONTROL_UI_API_KEY_FILE: /run/secrets/control_ui_api_key

secrets:
  control_ui_api_key:
    external: true
```

```bash
# Create secret
echo "your-secure-key" | docker secret create control_ui_api_key -
```

**3. Kubernetes Secrets**
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: trafficinator-api-key
type: Opaque
stringData:
  api-key: your-secure-key-here
```

### Authentication Flow

```
1. Client sends request with X-API-Key header
2. Server extracts key from header
3. Constant-time comparison with stored key
4. Grant/deny access based on match
```

**Constant-time comparison prevents timing attacks.**

### Disable Authentication (DEV ONLY)

```yaml
environment:
  CONTROL_UI_API_KEY: ""  # Empty = auth disabled
```

⚠️ **Only use in isolated development environments!**

---

## Network Security

### Port Binding

**Development (all interfaces):**
```yaml
ports:
  - "8000:8000"
```

**Production (localhost only):**
```yaml
ports:
  - "127.0.0.1:8000:8000"
```

**With Reverse Proxy:**
```yaml
# No external ports needed
expose:
  - "8000"
networks:
  - internal
```

### Docker Networks

**Isolated Network:**
```yaml
networks:
  trafficinator:
    driver: bridge
    internal: false  # Set to true to disable internet access

services:
  control-ui:
    networks:
      - trafficinator
  
  matomo-loadgen:
    networks:
      - trafficinator
```

**Multiple Networks:**
```yaml
networks:
  frontend:
    # External access via reverse proxy
  backend:
    internal: true  # Internal only

services:
  control-ui:
    networks:
      - frontend  # Accessible from proxy
      - backend   # Can reach matomo-loadgen
  
  matomo-loadgen:
    networks:
      - backend   # Not directly accessible
```

### Firewall Rules

**iptables Example:**
```bash
# Allow only from specific IPs
sudo iptables -A INPUT -p tcp --dport 8000 -s 192.168.1.0/24 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 8000 -j DROP
```

**UFW Example:**
```bash
# Allow from specific subnet
sudo ufw allow from 192.168.1.0/24 to any port 8000
sudo ufw deny 8000
```

---

## HTTPS/TLS

### Why HTTPS is Essential

1. **Encrypt API keys in transit**
2. **Prevent man-in-the-middle attacks**
3. **Enable security headers (HSTS)**
4. **Meet compliance requirements**

### Reverse Proxy Setup

**Option 1: Nginx**

```nginx
server {
    listen 443 ssl http2;
    server_name trafficinator.example.com;
    
    ssl_certificate /etc/ssl/certs/trafficinator.crt;
    ssl_certificate_key /etc/ssl/private/trafficinator.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**Option 2: Caddy (Auto HTTPS)**

```caddyfile
trafficinator.example.com {
    reverse_proxy 127.0.0.1:8000
}
```

**Option 3: Traefik**

```yaml
services:
  traefik:
    image: traefik:v2.10
    command:
      - "--providers.docker=true"
      - "--entrypoints.websecure.address=:443"
      - "--certificatesresolvers.le.acme.email=admin@example.com"
      - "--certificatesresolvers.le.acme.storage=/letsencrypt/acme.json"
      - "--certificatesresolvers.le.acme.httpchallenge.entrypoint=web"
    ports:
      - "443:443"
    volumes:
      - "/var/run/docker.sock:/var/run/docker.sock:ro"
      - "./letsencrypt:/letsencrypt"
  
  control-ui:
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.control-ui.rule=Host(`trafficinator.example.com`)"
      - "traefik.http.routers.control-ui.entrypoints=websecure"
      - "traefik.http.routers.control-ui.tls.certresolver=le"
```

### Certificate Options

1. **Let's Encrypt** - Free automated certificates
2. **Self-signed** - Internal networks only
3. **Commercial CA** - Purchased certificates
4. **Corporate CA** - Enterprise PKI

### Self-Signed Certificate (Internal Use)

```bash
# Generate certificate
openssl req -x509 -newkey rsa:4096 -nodes \
  -keyout trafficinator.key \
  -out trafficinator.crt \
  -days 365 \
  -subj "/CN=trafficinator.local"

# Use in nginx
ssl_certificate /etc/ssl/certs/trafficinator.crt;
ssl_certificate_key /etc/ssl/private/trafficinator.key;
```

---

## Rate Limiting

### Current Limits

| Endpoint | Limit | Window | Purpose |
|----------|-------|--------|---------|
| /api/status | 60/min | 1 min | Normal monitoring |
| /api/logs | 30/min | 1 min | Log retrieval |
| /api/start | 10/min | 1 min | Control operations |
| /api/stop | 10/min | 1 min | Control operations |
| /api/restart | 10/min | 1 min | Control operations |
| /api/validate | 30/min | 1 min | Config validation |
| /api/test-connection | 20/min | 1 min | Connection testing |

### Customize Rate Limits

Edit `/control-ui/app.py`:

```python
@app.get("/api/status")
@limiter.limit("100/minute")  # Increase to 100/min
async def get_status(...):
    ...

@app.post("/api/start")
@limiter.limit("5/minute")  # Decrease to 5/min
async def start_container(...):
    ...
```

### IP-Based Limiting

Rate limits are per-IP address. Behind a reverse proxy, ensure proper IP forwarding:

```python
# app.py
from slowapi.util import get_remote_address

# With reverse proxy (use X-Forwarded-For)
def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host

limiter = Limiter(key_func=get_client_ip)
```

### Response Headers

Rate limit info included in responses:

```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1698585600
Retry-After: 60
```

### Handling 429 Errors

**Client-side backoff:**

```javascript
async function apiCall() {
    const response = await fetch('/api/status');
    
    if (response.status === 429) {
        const retryAfter = response.headers.get('Retry-After');
        await sleep(retryAfter * 1000);
        return apiCall(); // Retry
    }
    
    return response.json();
}
```

---

## CORS Configuration

### Default (Development)

```yaml
environment:
  CORS_ORIGINS: "*"  # Allow all origins
```

⚠️ **Not recommended for production!**

### Production Configuration

**Single Origin:**
```yaml
environment:
  CORS_ORIGINS: "https://dashboard.example.com"
```

**Multiple Origins:**
```yaml
environment:
  CORS_ORIGINS: "https://dashboard.example.com,https://admin.example.com"
```

### CORS Headers

Automatically configured:

```
Access-Control-Allow-Origin: https://dashboard.example.com
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
Access-Control-Allow-Headers: *
Access-Control-Allow-Credentials: true
Access-Control-Max-Age: 3600
```

### Same-Origin (Most Secure)

Serve UI and API from same origin:

```
https://trafficinator.example.com/ui   # UI
https://trafficinator.example.com/api  # API
```

No CORS needed - all requests are same-origin.

---

## Deployment Security

### Production Checklist

- [ ] Strong API key (32+ characters)
- [ ] API key in environment variable or secret
- [ ] HTTPS enabled via reverse proxy
- [ ] CORS restricted to known origins
- [ ] Port binding to localhost or internal network
- [ ] Docker networks configured
- [ ] Rate limits reviewed and adjusted
- [ ] Security headers verified
- [ ] Logs monitoring enabled
- [ ] Regular security updates scheduled

### Environment Hardening

**1. Run as Non-Root User**

```dockerfile
# Dockerfile
FROM python:3.11-slim

RUN adduser --disabled-password --gecos '' appuser
USER appuser

WORKDIR /app
COPY --chown=appuser:appuser . .
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

**2. Read-Only Filesystem**

```yaml
services:
  control-ui:
    read_only: true
    tmpfs:
      - /tmp
      - /app/tmp
```

**3. Resource Limits**

```yaml
services:
  control-ui:
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 512M
        reservations:
          cpus: '0.5'
          memory: 256M
```

**4. Drop Capabilities**

```yaml
services:
  control-ui:
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE  # Only if binding to ports < 1024
```

### Security Updates

**Regular Updates:**

```bash
# Update base image
docker-compose pull

# Rebuild with latest packages
docker-compose build --no-cache

# Restart services
docker-compose up -d
```

**Automated Updates (Watchtower):**

```yaml
services:
  watchtower:
    image: containrrr/watchtower
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    command: --interval 86400 --cleanup
```

---

## Monitoring & Logging

### Application Logs

**View Logs:**
```bash
docker logs -f trafficinator-control-ui
```

**Log Levels:**
- INFO - Normal operations
- WARNING - Potential issues
- ERROR - Failed operations
- DEBUG - Detailed debugging (dev only)

### Security Events to Monitor

1. **Failed Authentication**
   ```
   WARNING: Invalid API key attempt from 192.168.1.100
   ```

2. **Rate Limit Exceeded**
   ```
   INFO: Rate limit exceeded for 192.168.1.100 on /api/status
   ```

3. **Container Control Operations**
   ```
   INFO: Container started by user with API key ***
   INFO: Container stopped by user with API key ***
   ```

4. **Configuration Changes**
   ```
   INFO: Configuration validated and applied
   WARNING: High concurrency (20) configured
   ```

### Centralized Logging

**Syslog Driver:**
```yaml
services:
  control-ui:
    logging:
      driver: syslog
      options:
        syslog-address: "tcp://192.168.1.50:514"
        tag: "trafficinator-ui"
```

**JSON File Driver:**
```yaml
services:
  control-ui:
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"
```

### Health Monitoring

**Endpoint:**
```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "docker": "connected",
  "container_found": true,
  "authenticated": true
}
```

**Docker Health Check:**
```yaml
services:
  control-ui:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

---

## Security Checklist

### Development Environment

- [ ] Use default API key or disable auth
- [ ] Allow CORS from localhost
- [ ] Bind to all interfaces (0.0.0.0)
- [ ] Enable verbose logging
- [ ] Use HTTP (no TLS needed)

### Staging Environment

- [ ] Generate unique API key
- [ ] Store key in environment variable
- [ ] Configure specific CORS origins
- [ ] Enable HTTPS with self-signed cert
- [ ] Test rate limiting
- [ ] Review security headers
- [ ] Verify authentication

### Production Environment

- [ ] Strong, unique API key (32+ chars)
- [ ] Key stored in secrets manager
- [ ] HTTPS with valid certificate
- [ ] CORS restricted to known origins
- [ ] Port bound to localhost or internal network
- [ ] Docker network isolation enabled
- [ ] Rate limits reviewed and appropriate
- [ ] All security headers enabled
- [ ] Logging to centralized system
- [ ] Health checks configured
- [ ] Resource limits set
- [ ] Run as non-root user
- [ ] Read-only filesystem where possible
- [ ] Regular security updates scheduled
- [ ] Access logs monitored
- [ ] Backup and recovery tested

### Periodic Reviews

**Monthly:**
- Review access logs for anomalies
- Check for security updates
- Verify API key rotation schedule

**Quarterly:**
- Rotate API keys
- Security audit of configuration
- Update dependencies
- Review and adjust rate limits

**Annually:**
- Comprehensive security assessment
- Penetration testing
- Review and update security policies
- Certificate renewal (if not automated)

---

## Additional Resources

- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)
- [Docker Security Best Practices](https://docs.docker.com/engine/security/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [Let's Encrypt](https://letsencrypt.org/)

---

## Reporting Security Issues

If you discover a security vulnerability, please:

1. **Do NOT** open a public GitHub issue
2. Email security concerns to: [security@example.com]
3. Include detailed description and steps to reproduce
4. Allow reasonable time for fix before public disclosure

---

**Last Updated:** October 29, 2025
**Version:** 1.0.0
