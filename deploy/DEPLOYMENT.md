# Deployment Guide - Receptionist AI

This guide covers deploying Receptionist AI on a Linux server (tested on Hetzner/Ubuntu).

## Architecture Overview

```
                    ┌─────────────────────────────────────────┐
                    │              Nginx (port 80/443)        │
                    │  - Serves frontend static files         │
                    │  - Proxies /api/* to backend            │
                    │  - Serves /widget/* static files        │
                    └─────────────────┬───────────────────────┘
                                      │
                    ┌─────────────────┴───────────────────────┐
                    │         Backend (port 8001)             │
                    │  - FastAPI + Uvicorn                    │
                    │  - Systemd service                      │
                    │  - SQLite database                      │
                    └─────────────────────────────────────────┘
```

## Prerequisites

### System Packages

```bash
sudo apt update
sudo apt install -y nginx python3 python3-pip nodejs npm
```

### Install uv (Python package manager)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.local/bin/env  # or restart shell
```

### Install pnpm (for frontend)

```bash
npm install -g pnpm
```

## Deployment Steps

### 1. Clone the Repository

```bash
cd /home/$USER/projects
git clone <repository-url> receptionist_ai
cd receptionist_ai
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment and install dependencies
uv sync

# Configure environment
cp .env.example .env
nano .env  # Add your OPENAI_API_KEY
```

Verify the backend runs:

```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8001
# Ctrl+C to stop after verifying
```

### 3. Frontend Build

```bash
cd frontend/admin

# Install dependencies
pnpm install

# Set production API URL
echo "VITE_API_URL=/api" > .env.production

# Build for production
pnpm build
```

The built files will be in `frontend/admin/dist/`.

### 4. Configure Systemd Service

Copy and enable the backend service:

```bash
# Edit the service file if your paths differ
nano deploy/receptionist-ai.service

# Install the service
sudo cp deploy/receptionist-ai.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable receptionist-ai
sudo systemctl start receptionist-ai

# Check status
sudo systemctl status receptionist-ai
```

**Service file (`deploy/receptionist-ai.service`):**

```ini
[Unit]
Description=Receptionist AI Backend API
After=network.target

[Service]
Type=simple
User=<your-username>
Group=<your-username>
WorkingDirectory=/home/<your-username>/projects/receptionist_ai/backend
Environment="PATH=/home/<your-username>/projects/receptionist_ai/backend/.venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/home/<your-username>/projects/receptionist_ai/backend/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8001
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

### 5. Configure Nginx

#### Option A: Standalone Nginx (Direct Install)

```bash
# Copy nginx config
sudo cp deploy/receptionist-ai.nginx.conf /etc/nginx/sites-available/receptionist-ai
sudo ln -s /etc/nginx/sites-available/receptionist-ai /etc/nginx/sites-enabled/

# Edit and update paths/domain
sudo nano /etc/nginx/sites-available/receptionist-ai

# Test and reload
sudo nginx -t
sudo systemctl reload nginx
```

#### Option B: Docker Nginx (Shared with Other Projects)

If you have an existing Docker nginx setup (like on this Hetzner server), add to your `nginx.conf`:

```nginx
# Upstream for receptionist backend
upstream receptionist_api {
    server host.docker.internal:8001;
}

# HTTP redirect
server {
    listen 80;
    server_name receptionist-ai.yourdomain.com;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 301 https://$host$request_uri;
    }
}

# HTTPS server
server {
    listen 443 ssl http2;
    server_name receptionist-ai.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/receptionist-ai.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/receptionist-ai.yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;

    # Frontend (React SPA)
    location / {
        root /var/www/receptionist_ai;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # Backend API - strip /api prefix
    location /api/ {
        proxy_pass http://receptionist_api/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Widget static files
    location /widget {
        alias /var/www/receptionist_ai_widget;
        index index.html;
    }

    # Backend static files (chat.js)
    location /static {
        proxy_pass http://receptionist_api/static;
        proxy_set_header Host $host;
    }
}
```

Add volume mounts to your `docker-compose.yaml`:

```yaml
nginx:
  volumes:
    - /path/to/receptionist_ai/frontend/admin/dist:/var/www/receptionist_ai:ro
    - /path/to/receptionist_ai/frontend/widget:/var/www/receptionist_ai_widget:ro
  extra_hosts:
    - "host.docker.internal:host-gateway"
```

Then restart nginx:

```bash
docker compose restart nginx
```

### 6. SSL Certificate (Let's Encrypt)

#### Standalone Nginx:

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d receptionist-ai.yourdomain.com
```

#### Docker Nginx with Certbot:

```bash
docker exec -it <certbot-container> certbot certonly \
  --webroot -w /var/www/certbot \
  -d receptionist-ai.yourdomain.com
```

## Current Hetzner Server Setup

On this server (`receptionist-ai.pragnyalabs.com`):

- **Backend**: Systemd service on port 8001
- **Frontend**: Built files at `/home/sreenivasanac/projects/receptionist_ai/frontend/admin/dist`
- **Nginx**: Docker container from `/home/sreenivasanac/projects/namesmith/deploy`
- **SSL**: Let's Encrypt via certbot container

## Common Operations

### View Logs

```bash
# Backend logs
sudo journalctl -u receptionist-ai -f

# Nginx logs (Docker)
docker logs -f deploy-nginx-1
```

### Restart Services

```bash
# Restart backend
sudo systemctl restart receptionist-ai

# Restart nginx (Docker)
cd /home/sreenivasanac/projects/namesmith/deploy
docker compose restart nginx
```

### Deploy Updates

```bash
cd /home/sreenivasanac/projects/receptionist_ai

# Pull latest code
git pull

# Backend updates
cd backend
uv sync  # if dependencies changed
sudo systemctl restart receptionist-ai

# Frontend updates
cd ../frontend/admin
pnpm install  # if dependencies changed
pnpm build
cd /home/sreenivasanac/projects/namesmith/deploy
docker compose restart nginx
```

### Check Health

```bash
# Backend health
curl http://localhost:8001/health
curl https://receptionist-ai.pragnyalabs.com/api/health

# Check processes
ps aux | grep uvicorn
sudo systemctl status receptionist-ai
```

## Troubleshooting

### Backend won't start

```bash
# Check logs
sudo journalctl -u receptionist-ai -n 50

# Test manually
cd /home/sreenivasanac/projects/receptionist_ai/backend
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8001
```

### 502 Bad Gateway

- Check if backend is running: `curl http://localhost:8001/health`
- Check nginx can reach backend (Docker needs `host.docker.internal`)
- Check firewall isn't blocking port 8001

### Frontend changes not showing

```bash
# Rebuild frontend
cd frontend/admin && pnpm build

# Restart nginx to clear cache
docker compose restart nginx  # or sudo systemctl reload nginx
```

### Database issues

SQLite database is at `backend/data/receptionist.db`. To reset:

```bash
# Backup first!
cp backend/data/receptionist.db backend/data/receptionist.db.backup

# Delete to reset (will recreate on startup)
rm backend/data/receptionist.db
sudo systemctl restart receptionist-ai
```
