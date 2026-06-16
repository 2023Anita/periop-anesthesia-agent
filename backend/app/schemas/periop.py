from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class DocumentModality(str, Enum):
    clinical_note = "clinical_note"
    lab = "lab"
    ecg = "ecg"
    imaging = "imaging"
    medication = "medication"
    airway = "airway"
    other = "other"


class ReviewStatus(str, Enum):
    draft = "draft"
    clinician_confirmed = "clinician_confirmed"


class IntraopEventType(str, Enum):
    hypotension = "hypotension"
    hypertension = "hypertension"
    hypoxemia = "hypoxemia"
    arrhythmia = "arrhythmia"
    bleeding = "bleeding"
    airway = "airway"
    medication = "medication"
    other = "other"


class CaseSummary(BaseModel):
    id: str
    title: str
    status: str = "draft"
    created_at: datetime
    updated_at: datetime


class CaseCreate(BaseModel):
    title: str = Field(default="新术前评估病例", min_length=1, max_length=120)


class DocumentRecord(BaseModel):
    id: str
    case_id: str
    filename: str
    modality: DocumentModality
    extracted_text: str
    extraction_notes: list[str] = Field(default_factory=list)
    created_at: datetime


class TextDocumentCreate(BaseModel):
    filename: str = "manual-input.txt"
    modality: DocumentModality = DocumentModality.clinical_note
    text: str = Field(min_length=1)


class PatientContext(BaseModel):
    age: str | None = None
    sex: str | None = None
    height_weight_bmi: str | None = None
    planned_surgery: str | None = None
    urgency: str | None = None
    history: list[str] = Field(default_factory=list)
    medications: list[str] = Field(default_factory=list)
    allergies: list[str] = Field(default_factory=list)
    anesthesia_history: list[str] = Field(default_factory=list)


class DocumentFinding(BaseModel):
    source: str
    fact: str
    confidence: Literal["low", "medium", "high"] = "medium"


class RiskFlag(BaseModel):
    name: str
    severity: Literal["low", "medium", "high", "critical"]
    rationale: str
    evidence: list[str] = Field(default_factory=list)
    clinician_review_required: bool = True


class ECGFinding(BaseModel):
    source: str
    analyzer_name: str = "rule_based_text_ecg_adapter"
    adapter_version: str = "0.1.0"
    confidence: Literal["low", "medium", "high"] = "medium"
    heart_rate: str | None = None
    rhythm: str | None = None
    pr_interval: str | None = None
    qrs_duration: str | None = None
    qtc: str | None = None
    st_t_changes: list[str] = Field(default_factory=list)
    conduction_findings: list[str] = Field(default_factory=list)
    arrhythmia_findings: list[str] = Field(default_factory=list)
    anesthesia_risk_notes: list[str] = Field(default_factory=list)
    missing_info: list[str] = Field(default_factory=list)
    clinician_review_required: bool = True


class LabFinding(BaseModel):
    name: str
    value: str
    unit: str | None = None
    interpretation: Literal["low", "normal", "high", "critical", "unknown"] = "unknown"
    anesthesia_relevance: str
    source: str


class PreopAssessmentReport(BaseModel):
    case_id: str
    generated_at: datetime
    patient_context: PatientContext
    source_findings: list[DocumentFinding] = Field(default_factory=list)
    ecg_findings: list[ECGFinding] = Field(default_factory=list)
    lab_findings: list[LabFinding] = Field(default_factory=list)
    risk_flags: list[RiskFlag] = Field(default_factory=list)
    asa_suggestion: str
    rcri_summary: str
    stop_bang_summary: str
    ponv_summary: str
    missing_information: list[str]
    suggested_follow_up_questions: list[str]
    suggested_additional_checks: list[str]
    perioperative_monitoring_focus: list[str]
    safety_notice: str
    review_status: ReviewStatus = ReviewStatus.draft
    clinician_notes: str = ""
    postop_surveillance_plan: list[str] = Field(default_factory=list)


class IntraopEventCreate(BaseModel):
    event_type: IntraopEventType = IntraopEventType.other
    severity: Literal["low", "medium", "high", "critical"] = "medium"
    description: str = Field(min_length=1, max_length=1000)
    observed_at: datetime | None = None
    clinician_action_summary: str = Field(default="", max_length=1000)


class IntraopEventRecord(BaseModel):
    id: str
    case_id: str
    event_type: IntraopEventType
    severity: Literal["low", "medium", "high", "critical"]
    description: str
    observed_at: datetime
    clinician_action_summary: str = ""
    created_at: datetime


class PostopPlanResponse(BaseModel):
    case_id: str
    generated_at: datetime
    surveillance_focus: list[str] = Field(default_factory=list)
    suggested_checks: list[str] = Field(default_factory=list)
    escalation_triggers: list[str] = Field(default_factory=list)
    safety_notice: str


class BandAgentRole(BaseModel):
    name: str
    responsibility: str
    band_mention: str


class BandCollaborationStep(BaseModel):
    order: int
    from_agent: str
    to_agent: str
    handoff: str
    shared_context: list[str] = Field(default_factory=list)
    expected_output: str
    sender_key: str = ""
    receiver_key: str = ""
    room_event_type: str = "handoff"
    directed_message: str = ""
    status: Literal["planned", "sent_to_band", "local_trace"] = "planned"


class BandMessageReceipt(BaseModel):
    step_order: int
    adapter_mode: Literal["local", "live"]
    sender_agent: str
    receiver_agent: str
    endpoint: str
    message_id: str
    delivered: bool
    detail: str = ""


class BandCollaborationResponse(BaseModel):
    case_id: str
    generated_at: datetime
    band_configured: bool
    room_id: str | None = None
    adapter_mode: Literal["local", "live"] = "local"
    minimum_agent_requirement_met: bool
    agent_roles: list[BandAgentRole]
    collaboration_steps: list[BandCollaborationStep]
    message_receipts: list[BandMessageReceipt] = Field(default_factory=list)
    audit_notes: list[str] = Field(default_factory=list)


class ClinicianReviewUpdate(BaseModel):
    clinician_notes: str = ""
    review_status: ReviewStatus = ReviewStatus.clinician_confirmed


class SafetyCheckRequest(BaseModel):
    text: str = Field(min_length=1)


class SafetyCheckResponse(BaseModel):
    allowed: bool
    category: str
    reason: str
    safe_response: str
    matched_terms: list[str] = Field(default_factory=list)


class SystemStatusResponse(BaseModel):
    deterministic_workflow_available: bool
    agents_sdk_refinement_configured: bool
    band_collaboration_configured: bool = False
    eval_case_count: int
    safety_boundary_categories: list[str] = Field(default_factory=list)


class DemoCaseResponse(BaseModel):
    case: CaseSummary
    documents: list[DocumentRecord]
    report: PreopAssessmentReport
