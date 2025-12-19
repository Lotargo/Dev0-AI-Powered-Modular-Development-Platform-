import uuid
from pydantic import BaseModel, Field
from typing import List, Optional

class BaseExperience(BaseModel):
    """
    Базовая модель для любого типа "опыта".
    """
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    success: bool

class PlannerExperience(BaseExperience):
    """
    Опыт Планировщика: хранит стратегическую информацию о задаче.
    """
    task: str
    plan: str
    logs: str

class EngineerExperience(BaseExperience):
    """
    Опыт Инженера: хранит удачные примеры реализации кода.
    Векторизуется по описанию задачи из плана.
    """
    task_summary: str
    code_snippet: str
    filepath: str

class TesterExperience(BaseExperience):
    """
    Опыт Тестировщика: хранит информацию о найденных багах и тестовых случаях.
    Векторизуется по коду, который тестировался.
    """
    module_code: str
    test_code: str
    errors_found: Optional[str] = None

class ReviewerExperience(BaseModel):
    """
    Опыт Ревьюера: хранит историю проверок кода.
    Не является 'опытом' в том же смысле, что и у других, поэтому не наследуется от BaseExperience.
    """
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    module_filepath: str
    code_before: str
    feedback: str
    code_after: Optional[str] = None # Если были внесены исправления
