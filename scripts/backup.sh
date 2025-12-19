#!/bin/bash
# scripts/backup.sh - Backup Redis and Qdrant

set -e

TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
BACKUP_DIR="backups/$TIMESTAMP"
mkdir -p "$BACKUP_DIR"

echo "--- Starting Backup $TIMESTAMP ---"
echo "Destination: $BACKUP_DIR"

# 1. Redis Backup
echo "1. Redis: Triggering SAVE..."
if docker ps | grep -q dev0-redis; then
    docker exec dev0-redis redis-cli save
    docker cp dev0-redis:/data/dump.rdb "$BACKUP_DIR/redis.rdb"
    echo "Redis backup saved."
else
    echo "Warning: Redis container not found. Skipping Redis backup."
fi

# 2. Qdrant Backup
echo "2. Qdrant: Snapshotting..."
# Run the python helper script
# Try poetry first, then python3
if command -v poetry &> /dev/null; then
    poetry run python scripts/backup_qdrant.py "$BACKUP_DIR"
else
    # Assuming httpx is installed in environment
    python3 scripts/backup_qdrant.py "$BACKUP_DIR"
fi

echo "--- Backup Complete ---"
