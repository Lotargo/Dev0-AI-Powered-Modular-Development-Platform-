#!/bin/bash
# scripts/migrate.sh

echo "--- Qdrant Migration ---"
# We execute inside the container to ensure dependencies and env vars are correct.
docker exec dev0-app poetry run python scripts/migrate_knowledge.py
