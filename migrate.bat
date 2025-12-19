@echo off
echo --- Qdrant Migration ---
docker exec dev0-app poetry run python scripts/migrate_knowledge.py
pause
