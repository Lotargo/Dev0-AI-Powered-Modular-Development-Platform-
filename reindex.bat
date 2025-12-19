@echo off
echo --- Reindexing Knowledge Base (Dev0 must be running) ---
docker exec dev0-app poetry run python scripts/index_codebase.py
echo Reindexing complete.
pause
