from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

# --- Tool & Function Calling Models ---

class Function(BaseModel):
    name: str
    description: str
    parameters: Dict[str, Any]

class Tool(BaseModel):
    type: str = "function"
    function: Function

class FunctionCall(BaseModel):
    name: str
    arguments: str # JSON string of arguments

class ToolCall(BaseModel):
    id: str
    type: str = "function"
    function: FunctionCall

# --- Core Chat Completion Models ---

class ChatCompletionMessage(BaseModel):
    role: str
    content: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None

class ChatCompletionChoice(BaseModel):
    index: int
    message: ChatCompletionMessage
    finish_reason: Optional[str] = None

class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[ChatCompletionChoice]
    usage: Optional[Dict[str, Any]] = None

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[Dict[str, Any]]
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = None
    stream: Optional[bool] = False
    tools: Optional[List[Tool]] = None
    tool_choice: Optional[str] = "auto"
