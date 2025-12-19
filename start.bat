@echo off
echo --- Starting Dev0 (Docker Mode) ---
docker compose -f docker-compose.infra.yml -f docker-compose.app.yml up --remove-orphans
pause
