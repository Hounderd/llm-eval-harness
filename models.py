from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from enum import Enum

class ModelProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GROQ = "groq"
    GEMINI = "gemini"

class Score(BaseModel):
    rubric_name: str
    score: float = Field(..., description="Score usually between 0.0 and 1.0 or 1-5")
    reasoning: Optional[str] = None

class TestCase(BaseModel):
    prompt: str
    target_model: str
    provider: ModelProvider
    expected_constraints: Optional[Dict[str, Any]] = None

class PromptSuite(BaseModel):
    name: str
    description: Optional[str] = None
    test_cases: List[TestCase]

class EvaluationResult(BaseModel):
    test_case: TestCase
    response: str
    scores: List[Score]
    error: Optional[str] = None
