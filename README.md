# Cranium Charades 🧠

Real-time multiplayer word-guessing game for remote teams playing over Zoom or voice calls. Players take turns being the "guesser" while teammates give hints. Race against a 60-second timer to guess as many words as possible!

**See [REQUIREMENTS.md](REQUIREMENTS.md) for complete game mechanics and technical details.**

## Local Development

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run locally
python app.py
```

Visit http://127.0.0.1:8004

## Production Deployment

### First Time Setup on Server

```bash
# On the server
cd ~/apps
git clone <repo-url> cranium-charades
cd cranium-charades

# Create virtual environment and install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Install and start systemd service
sudo ln -s /home/dhughes/apps/cranium-charades/cranium-charades.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable cranium-charades
sudo systemctl start cranium-charades

# Deploy Caddy config
cd ~/infrastructure
sudo ./deploy.sh
```

### Subsequent Deployments

```bash
# From your local machine
./deploy.sh

# Or manually on server
ssh dhughes@ssh.doughughes.net
cd ~/apps/cranium-charades
git pull
sudo systemctl restart cranium-charades
```

## Configuration

- **Port**: 8004
- **Path**: `/cranium-charades`
- **Access**: Private (requires login)
- **URL**: https://doughughes.net/cranium-charades

## Files

- `app.py` - Flask application
- `app.json` - Display metadata for index page
- `caddy.conf` - Caddy routing configuration
- `cranium-charades.service` - Systemd service file
- `requirements.txt` - Python dependencies
