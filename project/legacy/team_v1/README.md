# Legacy TEAM Mode (v1)

**Archived Date:** 21.11.2025

This directory contains the components of the original multi-agent "TEAM" mode (`run_orchestrator.py`).
This architecture was experimental and has been superseded by the "Research-Driven Team" architecture.

**Reason for Archival:**
The original TEAM mode (`Orchestrator` -> `Decomposer` -> `Engineer` -> `Tester`) was found to be less effective than the new "Research Mode" pipeline (`Researcher` -> `ContextCoder`). The new architecture splits responsibility between:
1.  **Research Team:** Creates modules and handles dependencies (Developer).
2.  **Classic Team:** Assembles recipes from modules (Constructor).

**Archived Components:**
*   `run_orchestrator_legacy.py` (Entry point)
*   `orchestrator.py`
*   `decomposer.py`
*   `engineer.py`
*   `reviewer.py`
*   `tester.py`
*   `validator.py`
*   `deterministic_verifier.py`
