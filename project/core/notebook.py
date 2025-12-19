"""
Defines the Pydantic models for the project's state, known as the "Dynamic Notebook".

This notebook acts as a centralized, evolving source of truth for the multi-agent team.
It is read and updated by the Orchestrator, ensuring that every agent has access to the
full context of the project's goals, current status, generated artifacts, and known issues.
"""
import json
from pydantic import BaseModel, Field
from typing import List, Dict, Literal, Optional

# --- Type definitions for controlled vocabularies ---
T_AgentStatus = Literal["pending", "working", "completed", "failed", "idle"]
T_ProjectPhase = Literal["planning", "decomposition", "design", "implementation", "testing", "review", "finalizing", "done"]
T_AgentName = Literal["planner", "decomposer", "architect", "engineer", "tester", "reviewer"]


# --- Agent-specific data models ---

class AgentState(BaseModel):
    """Base model for an agent's state within the notebook."""
    task: Optional[str] = None
    output: Optional[str] = None
    status: T_AgentStatus = "idle"
    retries: int = 0

class ModuleSpec(BaseModel):
    """Defines the contract for a module to be implemented."""
    name: str
    interface: Dict[str, str] = Field(description="Defines the input and output signatures, e.g., {'input': 'raw_data: DataFrame', 'output': 'cleaned_data: DataFrame'}")
    description: str
    properties: List[str] = Field(default_factory=list, description="Architectural properties to be applied via decorators, e.g., ['atomic', 'sandbox']")

class DecomposerState(AgentState):
    """State for the Decomposer agent."""
    module_specs: List[ModuleSpec] = Field(default_factory=list)

class ArchitectState(AgentState):
    """State for the Architect agent."""
    design_schema: Optional[str] = Field(None, description="A graph or text representation of module dependencies.")
    integration_plan: Optional[str] = None

class EngineerState(AgentState):
    """State for the Engineer agent."""
    implemented_modules: List[str] = Field(default_factory=list)

class TestResult(BaseModel):
    """Represents the outcome of a single test run for a module."""
    module_name: str
    status: Literal["passed", "failed"]
    details: str

class TesterState(AgentState):
    """State for the Tester agent."""
    test_results: List[TestResult] = Field(default_factory=list)


# --- Main Notebook Model ---

class ProjectNotebook(BaseModel):
    """
    The central, evolving state of the project, managed by the Orchestrator.
    """
    project_goal: str
    current_phase: T_ProjectPhase = "planning"
    active_agent: T_AgentName = "planner"

    # Agent States
    planner: AgentState = Field(default_factory=AgentState)
    decomposer: DecomposerState = Field(default_factory=DecomposerState)
    architect: ArchitectState = Field(default_factory=ArchitectState)
    engineer: EngineerState = Field(default_factory=EngineerState)
    tester: TesterState = Field(default_factory=TesterState)
    reviewer: AgentState = Field(default_factory=AgentState)

    # General Project Sections
    known_issues: List[str] = Field(default_factory=list)
    resolved_issues: List[str] = Field(default_factory=list)
    available_modules: List[str] = Field(default_factory=list, description="Modules available for reuse.")

    def save(self, path: str = "notebook.json"):
        """Saves the current state of the notebook to a JSON file."""
        with open(path, "w", encoding="utf-8") as f:
            # Using model_dump instead of dict for compatibility with newer Pydantic versions
            json.dump(self.model_dump(), f, indent=2, ensure_ascii=False)

    @classmethod
    def load(cls, path: str = "notebook.json") -> "ProjectNotebook":
        """Loads the notebook state from a JSON file."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return cls(**data)
        except FileNotFoundError:
            # This allows creating a new notebook if one doesn't exist
            return None
        except json.JSONDecodeError:
            raise ValueError(f"Error decoding JSON from {path}")
