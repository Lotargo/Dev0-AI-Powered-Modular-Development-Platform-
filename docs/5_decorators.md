# Decorators Guide (Meta-Framework)

**Dev0** utilizes a "Meta-Language" based on Python decorators. This allows AI agents to focus on "Pure Code" (business logic), while reliability, observability, and safety are injected declaratively by the system.

## 1. Philosophy
LLMs often struggle with writing complex error handling boilerplate (`try-except` blocks) and logging logic correctly. Instead of burdening the agent with this, we instruct them to write a clean function and tag it with `@safe_call`.

The **Stitcher** component automatically detects these tags in the agent's output and "stitches" the actual decorators and imports into the final code.

## 2. Available Decorators

### 2.1. `@atomic`
*   **Import:** `from project.core.framework.atomic import atomic`
*   **Purpose:** Marks a function as an "Atomic Module".
*   **Effect:**
    *   The function is indexed by the `ModuleRegistry`.
    *   It is embedded into the **Knowledge Base** (Qdrant).
    *   It becomes discoverable for the Architect to use in future recipes.

### 2.2. `@safe_call`
*   **Import:** `from project.core.framework.safe_call import safe_call`
*   **Purpose:** Error handling (Result Object Pattern).
*   **Effect:**
    *   Catches any exception within the function.
    *   Returns a `SafeCallResult(value=..., error=...)` object.
    *   **Note:** Supports both synchronous and asynchronous (`async def`) functions.

### 2.3. `@retry`
*   **Import:** `from project.core.framework.retry import retry`
*   **Purpose:** Resilience (Retry logic).
*   **Parameters:**
    *   `attempts` (int): Number of attempts (default: 3).
    *   `delay` (float): Delay between attempts in seconds.
*   **Example:** `@retry(attempts=5, delay=2.0)`

### 2.4. `@observable`
*   **Import:** `from project.core.framework.observability import observable`
*   **Purpose:** Observability ("Glass Box").
*   **Parameters:**
    *   `source_name` (str, optional): Name of the event source (e.g., "Architect"). If omitted, function name is used.
*   **Effect:**
    *   Automatically generates `Trace ID` and `Span ID`.
    *   Publishes `EXECUTION_START`, `EXECUTION_COMPLETE`, and `EXECUTION_ERROR` events to Redis.
    *   Enables real-time visualization in the Admin UI.

## 3. Usage Example (Agent Workflow)

The Agent generates a JSON specification:

```json
{
  "pure_code": "import httpx\n\nasync def execute(url: str):\n    async with httpx.AsyncClient() as client:\n        return await client.get(url)",
  "decorators": ["@safe_call", "@retry(attempts=3)", "@observable(source_name='WebFetcher')"]
}
```

The **Stitcher** transforms this into a valid Python file:

```python
from project.core.framework.safe_call import safe_call
from project.core.framework.retry import retry
from project.core.framework.observability import observable
import httpx

@safe_call
@retry(attempts=3)
@observable(source_name='WebFetcher')
async def execute(url: str):
    async with httpx.AsyncClient() as client:
        return await client.get(url)
```
