#!/bin/bash
# Install Envy as a systemd service

set -e

echo "Installing Envy as a systemd service..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "This script must be run as root (use sudo)"
    exit 1
fi

# Get current user (the one who called sudo)
REAL_USER=${SUDO_USER:-$USER}

# Base directory
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Copy service file
echo "Copying service file..."
sed "s/%i/$REAL_USER/g" "$BASE_DIR/scripts/envy.service" | \
    sed "s|/opt/envy|$BASE_DIR|g" > /etc/systemd/system/envy.service

# Reload systemd
echo "Reloading systemd..."
systemctl daemon-reload

# Enable service
echo "Enabling service..."
systemctl enable envy.service

echo ""
echo "Envy service installed successfully!"
echo ""
echo "To start: sudo systemctl start envy"
echo "To stop:  sudo systemctl stop envy"
echo "To view logs: journalctl -u envy -f"
echo ""
