from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class EvidenceItem(BaseModel):
    source: Optional[str]
    evidence_type: Optional[str]
    evidence_strength: Optional[str]
    summary: Optional[str]
    details: Optional[str]
    created_at: datetime = Field(default_factory=datetime.utcnow)


class DecisionEntry(BaseModel):
    decision: str
    rationale: Optional[str]
    supporting_evidence: Optional[str]
    decision_date: datetime = Field(default_factory=datetime.utcnow)
    changed_by: Optional[str]
    notes: Optional[str]


class TargetRecord(BaseModel):
    name: str
    target_type: str
    disease_context: Optional[str]
    modality: Optional[str]
    therapeutic_rationale: Optional[str]
    scientific_concerns: Optional[str]
    current_status: Optional[str]
    evidence: List[EvidenceItem] = []
    decision_history: List[DecisionEntry] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
