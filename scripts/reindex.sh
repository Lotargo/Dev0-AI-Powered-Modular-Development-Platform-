#!/bin/bash
# scripts/reindex.sh

set -e

echo "--- Reindexing Knowledge Base ---"
if ! docker ps | grep -q dev0-app; then
    echo "Error: Dev0 app container is not running."
    echo "Please run './start.sh' first."
    exit 1
fi

docker exec dev0-app poetry run python scripts/index_codebase.py
echo "Reindexing complete."
