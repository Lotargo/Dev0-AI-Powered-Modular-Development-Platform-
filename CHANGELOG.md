# Changelog

## [Codemane RDA_7] - 2025-11-24

### Added
- **Code RAG (Intelligence from Code):** Implemented `codebase` and `documentation` collections in Qdrant. Agents (`ContextCoder`, `Researcher`) now scan existing code/docs to prevent duplication and maintain style consistency.
- **Verification-Driven Development (VDD):** Introduced a QA layer where `SecondaryVerifier` generates and executes functional tests against the running MVP server.
- **MCP Integration:** Full support for Model Context Protocol (MCP) with Stdio and SSE transports.
- **Observability ("Glass Box"):** Implemented `RedisEventBus` and `@observable` decorator for real-time tracing of agent execution and state.
- **Expert Intervention:** Added a fallback mechanism where "Expert" models (Gemini 2.5/3.0) take over after 4 failed attempts by weaker models.

### Changed
- **Orchestrator Logic:** Restored the unified `run_orchestrator.py` as a "Smart Switch" between `CLASSIC` (Assembler) and `RESEARCH` (ContextCoder) modes.
- **Dependency Management:**
  - Implemented smart parsing of `Requirements:` docstrings.
  - Added a mapping dictionary to fix common agent hallucinations (e.g., `PIL` -> `Pillow`).
  - `RESEARCH` mode now forces `poetry install` to ensure environment consistency.
- **Model Configuration:** Updated `config.py` to prioritize Gemini 2.5 Pro and remove deprecated models.
- **System Architecture:** Adopted a "Glass Box" philosophy with full event publication to Redis.

### Fixed
- **Qdrant Locking:** Resolved `BlockingIOError` in subprocesses by managing Qdrant connections properly (closing before spawning).
- **Google Client:** Fixed `ValueError` in `function_call` handling for Gemini models.
- **Dependency Hell:** Addressed issues where compiled projects failed due to missing libraries.

### Removed
- **Legacy Decorator Strategy:** Moved away from requiring LLMs to write complex decorators manually; replaced with "Direct Code Generation" + `Stitcher` injection.
