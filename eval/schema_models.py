"""
eval/schema_models.py
=====================
Pydantic Schemas for Constrained Decoding and Evaluation Harness.
Ensures tool calls, extracted parameters, and calculations conform strictly to structured invariants.
"""

from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field, field_validator


class ToolCallSchema(BaseModel):
    """Schema for structured LLM tool invocations."""
    tool_name: str = Field(..., description="Target tool name to invoke (e.g., 'rag_query', 'calculate', 'python_repl')")
    parameters: Dict[str, Any] = Field(..., description="Dictionary of typed tool arguments")
    thought_rationale: str = Field(..., description="Chain-of-thought justification for selecting this tool")


class ExtractionFieldSchema(BaseModel):
    """Schema for an extracted technical parameter."""
    field_name: str
    value: Union[str, float, int, bool, None]
    unit: Optional[str] = None
    confidence: float = Field(..., ge=0.0, le=1.0)
    source_span: str


class StructuredExtractionResult(BaseModel):
    """Schema for entire document extraction payload."""
    document_type: str
    equipment_tag: str
    component_name: str
    nominal_thickness_mm: Optional[float] = None
    measured_thickness_mm: Optional[float] = None
    design_minimum_mm: Optional[float] = None
    design_pressure_barg: Optional[float] = None
    operating_temperature_c: Optional[float] = None
    fields: List[ExtractionFieldSchema] = []

    @field_validator("nominal_thickness_mm", "measured_thickness_mm", "design_minimum_mm")
    @classmethod
    def validate_positive_thickness(cls, v):
        if v is not None and v <= 0:
            raise ValueError("Thickness values must be strictly positive (> 0.0 mm)")
        return v


class PlanStepSchema(BaseModel):
    """Schema for an individual agent execution plan step."""
    step_id: int
    action: str
    rationale: str
    expected_output_type: str


class StructuredPlanSchema(BaseModel):
    """Schema for multi-step agent reasoning plans."""
    objective: str
    steps: List[PlanStepSchema]
    safety_classification: str


class GoldenTestCase(BaseModel):
    """Schema for a golden evaluation dataset case."""
    case_id: str
    category: str  # "EXTRACTION", "RETRIEVAL", "CALCULATION", "ABSTENTION", "ADVERSARIAL"
    input_text: str
    expected_output: Dict[str, Any]
    required_abstention: bool = False
    expected_failure_code: Optional[str] = None
