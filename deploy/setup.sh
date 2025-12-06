#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "=== Receptionist AI Deployment Setup ==="

# Copy systemd service for backend
echo "1. Setting up systemd service for backend..."
sudo cp "$SCRIPT_DIR/receptionist-ai.service" /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable receptionist-ai
sudo systemctl restart receptionist-ai
echo "   Backend service started on port 8001!"

# Check backend status
echo "2. Checking backend service status..."
sudo systemctl status receptionist-ai --no-pager || true

# Restart Docker nginx to pick up new config
echo "3. Restarting Docker nginx..."
cd /home/sreenivasanac/projects/namesmith/deploy
docker compose restart nginx
echo "   Nginx restarted!"

echo ""
echo "=== Setup Complete ==="
echo "Your site should be available at: http://receptionist_ai.pragnyalabs.com"
echo ""
echo "To enable HTTPS, run:"
echo "  docker exec -it deploy-certbot-1 certbot certonly --webroot -w /var/www/certbot -d receptionist_ai.pragnyalabs.com"
