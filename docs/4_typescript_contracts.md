# TypeScript Contract Generation

This document explains the automatic generation of TypeScript interfaces from Python Pydantic models in **Dev0**.

## Purpose

To ensure type safety and synchronization between the Python backend (FastAPI) and the frontend (TypeScript/React), Dev0 automates the creation of shared data models. This prevents "drift" where the backend API changes but the frontend types remain outdated.

## Mechanism

We use `pydantic-to-typescript` to convert Pydantic models into TypeScript interfaces.

### Workflow:

1.  **Analyze Models:** The tool inspects Python modules for classes inheriting from `pydantic.BaseModel`.
2.  **Type Mapping:** Python types are mapped to TypeScript:
    -   `str` -> `string`
    -   `int`, `float` -> `number`
    -   `Optional[T]` -> `T | null`
    -   `List[T]` -> `T[]`
3.  **Output:** A `.ts` file is generated, ready for import by the frontend.

### Example Command

```bash
pydantic-to-typescript --module project/modules --output frontend/src/types/generated.ts
```

## Benefits

1.  **Type Safety:** Compilation errors occur immediately if the backend changes an API contract, preventing runtime bugs.
2.  **Efficiency:** Developers don't need to manually write TypeScript interfaces.
3.  **Single Source of Truth:** The Pydantic model is the definitive definition of the data structure.
