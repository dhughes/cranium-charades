# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Cranium Charades is a real-time multiplayer word-guessing game for remote teams. Players join games via shareable links and take turns being the "guesser" while teammates give hints over Zoom or voice calls. The guesser races against a 60-second timer to guess as many words as possible based on their teammates' hints. No screen sharing required - each player views the game in their own browser. Currently in early development with a landing page scaffold.

See REQUIREMENTS.md for complete game mechanics and implementation details.

## Development Commands

### Local Development
```bash
# Setup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run locally
python app.py
# Access at http://127.0.0.1:8004
```

### Deployment
```bash
# Deploy to production (from local machine)
./deploy-to-prod.sh

# Manual deployment on server
ssh dhughes@ssh.doughughes.net
cd ~/apps/cranium-charades
git pull
sudo systemctl restart cranium-charades
```

## Architecture

**Simple Flask Application**
- Single-file Flask app (`app.py`) with embedded HTML templates
- Runs on port 8004 (both locally and in production)
- Public URL: https://www.doughughes.net/cranium-charades
- Caddy reverse proxy handles routing via `/cranium-charades` path prefix

**Deployment Infrastructure**
- Systemd service manages the Flask process with auto-restart
- Caddy configuration in `caddy.conf` strips path prefix before proxying
- `deploy.sh` runs on server: git pull → pip install → update Caddy → restart service
- `deploy-to-prod.sh` runs locally: git push → SSH to server → run deploy.sh

**Key Configuration**
- `app.json`: Metadata for app (name, icon 🧠, description)
- `cranium-charades.service`: Systemd service definition
- `caddy.conf`: Reverse proxy routing configuration

## Important Notes

- The app is intentionally minimal - single Python file with no separate frontend assets yet
- When modifying deployment scripts, remember SSH commands need `cd` to set working directory: `ssh user@host 'cd ~/path && script.sh'`
- Infrastructure deployment (`~/infrastructure/deploy.sh caddy`) is managed externally
