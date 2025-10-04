from pydantic import BaseModel
from typing import List

# Schemas para a resposta da API

class TestResultItem(BaseModel):
    question: str
    expected_answer: str
    actual_answer: str
    latency_ms: float
    is_correct: bool

class ModelTestResult(BaseModel):
    model_name: str
    results: List[TestResultItem]

class TestSummaryResponse(BaseModel):
    filename: str
    filesize_bytes: int
    test_summary: List[ModelTestResult]