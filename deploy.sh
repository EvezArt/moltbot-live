#!/bin/bash
# MoltBot Live — One-Command VPS Deployment
# Usage: curl -sSL https://raw.githubusercontent.com/EvezArt/moltbot-live/main/deploy.sh | bash
set -e

echo "═══════════════════════════════════════════"
echo "  🦞 MoltBot Live — VPS Deployment"
echo "═══════════════════════════════════════════"
echo ""

# Check requirements
command -v docker >/dev/null 2>&1 || {
    echo "Installing Docker..."
    curl -fsSL https://get.docker.com | sh
    sudo systemctl enable docker
    sudo systemctl start docker
}

command -v docker-compose >/dev/null 2>&1 || command -v "docker compose" >/dev/null 2>&1 || {
    echo "Installing Docker Compose..."
    sudo apt-get update && sudo apt-get install -y docker-compose-plugin
}

# Clone or update repo
INSTALL_DIR="$HOME/moltbot-live"
if [ -d "$INSTALL_DIR" ]; then
    echo "Updating existing installation..."
    cd "$INSTALL_DIR"
    git pull
else
    echo "Cloning MoltBot Live..."
    git clone https://github.com/EvezArt/moltbot-live.git "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi

# Configure
if [ ! -f .env ]; then
    cp .env.example .env
    echo ""
    echo "⚠️  Configure your .env file:"
    echo "   nano $INSTALL_DIR/.env"
    echo ""
    echo "Required:"
    echo "  YOUTUBE_STREAM_KEY=your-stream-key"
    echo "  MOLTBOOK_API_KEY=your-api-key"
    echo ""
    read -p "Edit .env now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        ${EDITOR:-nano} .env
    fi
fi

# Build and run
echo ""
echo "Building container..."
docker compose build

echo ""
echo "Starting MoltBot Live..."
docker compose up -d

echo ""
echo "═══════════════════════════════════════════"
echo "  🔴 MoltBot Live is STREAMING"
echo "═══════════════════════════════════════════"
echo ""
echo "Commands:"
echo "  docker compose logs -f    # View logs"
echo "  docker compose restart    # Restart stream"
echo "  docker compose down       # Stop stream"
echo ""
echo "Dashboard: Running inside container"
echo "Stream:    Pushing to YouTube Live"
echo ""
