@echo off
setlocal EnableDelayedExpansion

echo --- Dev0 Installer (Windows) ---

REM 1. Check Docker
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Docker is not installed or not in PATH.
    echo Please install Docker Desktop for Windows.
    pause
    exit /b 1
)

REM 2. Environment Configuration
if not exist .env (
    echo Creating default .env file...
    (
        echo # --- Infrastructure ---
        echo # Note: In Docker mode, these are overridden by docker-compose.yml
        echo QDRANT_URL=http://localhost:6333
        echo REDIS_URL=redis://localhost:6379
        echo.
        echo # --- Keys ---
        echo # Place your keys in separate .env.provider files
    ) > .env
) else (
    echo .env file exists. Skipping creation.
)

REM 3. Security Configuration (Nginx Basic Auth)
if not exist .htpasswd (
    echo --- Security Setup ---
    echo Creating .htpasswd for Nginx (Basic Auth).

    set "AUTH_USER=admin"
    set /p "AUTH_USER=Enter username [admin]: "

    echo Enter password (will be visible):
    set "AUTH_PASS=admin"
    set /p "AUTH_PASS="

    echo Generating hash using httpd:alpine...
    docker run --rm --entrypoint htpasswd httpd:alpine -Bbn "!AUTH_USER!" "!AUTH_PASS!" > .htpasswd
    echo .htpasswd generated.
) else (
    echo Security: .htpasswd exists. Skipping.
)

REM 4. Build
echo Building Docker images...
docker compose -f docker-compose.infra.yml -f docker-compose.app.yml build

echo Setup finished. Run 'start.bat' to launch.
pause
