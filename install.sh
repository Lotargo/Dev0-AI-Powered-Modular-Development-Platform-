#!/bin/bash
# install.sh - Setup Dev0 Environment

set -e

# Defaults
MODE="docker"

# Parse arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --docker) MODE="docker" ;;
        --local) MODE="local" ;;
        *) echo "Unknown parameter passed: $1"; exit 1 ;;
    esac
    shift
done

echo "--- Dev0 Installer (Mode: $MODE) ---"

# 1. Environment Configuration
if [ ! -f ".env" ]; then
    echo "Creating default .env file..."
    cat <<EOF > .env
# --- Infrastructure ---
# Note: In Docker mode, these are overridden by docker-compose.yml
QDRANT_URL=http://localhost:6333
REDIS_URL=redis://localhost:6379

# --- Keys ---
# Place your keys in separate .env.<provider> files (e.g., .env.google)
EOF
else
    echo ".env file exists. Skipping creation."
fi

# 2. Security Configuration (Nginx Basic Auth)
if [ ! -f ".htpasswd" ]; then
    echo "--- Security Setup ---"
    if command -v docker &> /dev/null; then
        echo "Creating .htpasswd for Nginx (Basic Auth)."
        read -p "Enter username [admin]: " AUTH_USER
        AUTH_USER=${AUTH_USER:-admin}

        echo -n "Enter password: "
        read -s AUTH_PASS
        echo ""

        if [ -z "$AUTH_PASS" ]; then
            echo "Password empty. Defaulting to 'admin'."
            AUTH_PASS="admin"
        fi

        echo "Generating hash using httpd:alpine..."
        docker run --rm --entrypoint htpasswd httpd:alpine -Bbn "$AUTH_USER" "$AUTH_PASS" > .htpasswd
        echo ".htpasswd generated."
    else
        echo "Warning: Docker not found. Skipping .htpasswd generation."
        echo "If you run in Docker mode later, you must generate .htpasswd manually."
    fi
else
    echo "Security: .htpasswd exists. Skipping."
fi

# 3. Installation Logic
if [ "$MODE" == "docker" ]; then
    if ! command -v docker &> /dev/null; then
        echo "Error: Docker is not installed."
        exit 1
    fi
    echo "Building Docker images..."
    # Build both infra (pull) and app
    docker compose -f docker-compose.infra.yml -f docker-compose.app.yml build
    echo "Docker build complete."

elif [ "$MODE" == "local" ]; then
    if ! command -v poetry &> /dev/null; then
        echo "Poetry not found. Please install Poetry."
        exit 1
    fi
    echo "Installing Python dependencies..."
    poetry install

    echo "Installing Playwright browsers (for dev/research)..."
    poetry run playwright install chromium

    echo "Local installation complete."
fi

echo "Setup finished. Run './start.sh' to launch."
