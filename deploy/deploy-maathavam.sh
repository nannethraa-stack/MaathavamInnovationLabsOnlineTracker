#!/bin/bash

set -euo pipefail



REPO="/home/ubuntu/MaathavamInnovationLabsOnlineTracker"

APP="/opt/maathavam"

SERVICE="maathavam.service"

DB="$APP/project_dashboard.db"

STAMP="$(date +%Y%m%d_%H%M%S)"

BACKUP="$APP/deploy_backup_$STAMP"



echo "=========================================="

echo " Maathavam Innovation Labs Deployment"

echo "=========================================="



cd "$REPO"



echo "[1/10] Getting latest code from GitHub..."

sudo -u ubuntu git fetch origin

sudo -u ubuntu git checkout main
sudo -u ubuntu git pull --ff-only origin main
if [ -n "$(sudo -u ubuntu git status --porcelain)" ]; then echo "ERROR: Deployment checkout has uncommitted changes. Aborting."; sudo -u ubuntu git status --short; exit 1; fi




COMMIT="$(sudo -u ubuntu git rev-parse --short HEAD)"

echo "Deploying commit: $COMMIT"



echo "[2/10] Creating backup..."

sudo mkdir -p "$BACKUP"



if [ -f "$DB" ]; then

    sudo cp "$DB" "$BACKUP/project_dashboard.db"

fi



if [ -d "$APP/uploads" ]; then

    sudo tar -czf "$BACKUP/uploads.tar.gz" -C "$APP" uploads

fi



echo "[3/10] Deploying application code..."

sudo rsync -a \
    --exclude='.git/' \
    --exclude='.venv/' \
    --exclude='project_dashboard.db' \
    --exclude='project_dashboard.db.*' \
    --exclude='uploads/' \
    --exclude='deploy_backup_*/' \
    --exclude='__pycache__/' \
    "$REPO/" "$APP/"



echo "[4/10] Checking Python syntax..."

sudo "$APP/.venv/bin/python" -m py_compile "$APP/app.py"



echo "[5/10] Installing dependencies..."

sudo "$APP/.venv/bin/pip" install -r "$APP/requirements.txt" --quiet



echo "[6/10] Running database migrations..."
cd "$APP"
sudo "$APP/.venv/bin/python" -c "from app import init_db; init_db()"

echo "[7/10] Restarting application..."

sudo systemctl restart "$SERVICE"



echo "[8/10] Checking service..."

if ! sudo systemctl is-active --quiet "$SERVICE"; then

    echo "ERROR: $SERVICE failed to start."

    sudo systemctl status "$SERVICE" --no-pager

    exit 1

fi



echo "[9/10] Checking application..."

STATUS="000"



for i in {1..15}; do

    STATUS="$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:5000/login || true)"



    if [ "$STATUS" = "200" ]; then

        break

    fi



    sleep 1

done



if [ "$STATUS" != "200" ]; then

    echo "ERROR: Application health check failed."

    echo "HTTP status: $STATUS"

    sudo systemctl status "$SERVICE" --no-pager

    exit 1

fi



echo "[10/10] Deployment completed successfully."

echo

echo "Commit:       $COMMIT"

echo "Login status: HTTP $STATUS"

echo "Backup:       $BACKUP"

echo

echo "=========================================="

echo " LIVE DEPLOYMENT SUCCESSFUL"

echo "=========================================="

