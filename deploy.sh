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

# Restart service
echo "🔄 Restarting service..."
sudo systemctl restart cranium-charades

# Show status
echo "✅ Deployment complete!"
systemctl status cranium-charades --no-pager
