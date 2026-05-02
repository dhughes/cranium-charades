#!/bin/bash
set -e

echo "🚀 Deploying Cranium Charades..."

# Pull latest changes
echo "📥 Pulling latest changes..."
git pull

# Activate virtual environment and update dependencies
echo "📦 Updating dependencies..."
source venv/bin/activate
pip install -r requirements.txt

echo "🔧 Updating Caddy configuration..."
sudo /mnt/data/infrastructure/deploy.sh caddy

# Restart service
echo "📋 Updating systemd unit..."
sudo /mnt/data/infrastructure/deploy.sh service cranium-charades
echo "🔄 Restarting service..."
sudo systemctl restart cranium-charades

# Show status
echo "✅ Deployment complete!"
echo "📊 Service status:"
systemctl status cranium-charades
