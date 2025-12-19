# Developer Guide

## 1. Environment Setup

### Prerequisites
- Python 3.12+
- Docker & Docker Compose
- Poetry (Dependency Manager)

### Installation
1.  **Clone the repository.**
2.  **Run the installer:**
    ```bash
    ./install.sh
    ```
    This script checks dependencies, builds Docker images, and generates necessary credentials.

3.  **Configure Secrets:**
    Create `.env.<provider>` files in the root (e.g., `.env.google`, `.env.tavily`) with your API keys.

## 2. Running the Project

### Docker (Recommended)
Start the full stack:
```bash
./start.sh
```
This launches:
*   **App Server:** `http://localhost:8000`
*   **Admin UI:** `http://localhost/admin/`
*   **Infrastructure:** Redis, Qdrant.

### Local Development
To run components individually for debugging:
```bash
# Start Infrastructure
docker-compose -f docker-compose.infra.yml up -d

# Run the Orchestrator
poetry run python run_orchestrator.py
```

## 3. Testing

Run the test suite:
```bash
poetry run pytest
```

## 4. Project Structure
*   `project/core`: Core framework (Orchestrator, Event Bus, Memory).
*   `project/modules`: Atomic tools (File system, etc.).
*   `project/recipes`: Composite agents and workflows.
*   `docs/`: Documentation.
*   `scripts/`: Utility scripts.
