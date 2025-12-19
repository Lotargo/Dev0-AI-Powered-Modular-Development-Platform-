#!/bin/bash
# start.sh - Start Dev0

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

echo "--- Starting Dev0 (Mode: $MODE) ---"

if [ "$MODE" == "docker" ]; then
    echo "Launching full stack in Docker..."
    # We include both infra and app configs
    docker compose -f docker-compose.infra.yml -f docker-compose.app.yml up --remove-orphans

elif [ "$MODE" == "local" ]; then
    echo "Ensuring infrastructure is up..."
    # Only start infrastructure
    docker compose -f docker-compose.infra.yml up -d

    echo "Infrastructure started. Starting Local Server..."
    poetry run uvicorn project.main:app --host 0.0.0.0 --port 8000 --reload
fi
