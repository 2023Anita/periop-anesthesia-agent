from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import PlainTextResponse

from app.agents.band_collaboration import (
    build_band_collaboration_trace,
    is_band_configured,
    render_band_transcript_markdown,
)
from app.agents.safety import BLOCKED_PATTERNS, check_medical_safety
from app.agents.workflow import run_preop_assessment
from app.core import store
from app.schemas.periop import (
    CaseCreate,
    CaseSummary,
    BandCollaborationResponse,
    ClinicianReviewUpdate,
    DemoCaseResponse,
    DocumentModality,
    DocumentRecord,
    IntraopEventCreate,
    IntraopEventRecord,
    PostopPlanResponse,
    PreopAssessmentReport,
    SafetyCheckRequest,
    SafetyCheckResponse,
    SystemStatusResponse,
    TextDocumentCreate,
)
from app.tools.document_extractors import extract_document_text
from app.tools.report_export import render_report_markdown


router = APIRouter()
PROJECT_ROOT = Path(__file__).resolve().parents[3]
SAMPLE_CASE_PATH = PROJECT_ROOT / "data" / "samples" / "sample-preop-ecg.txt"
EVAL_CASES_PATH = PROJECT_ROOT / "backend" / "app" / "evals" / "cases.jsonl"


def _count_eval_cases() -> int:
    if not EVAL_CASES_PATH.exists():
        return 0
    return sum(1 for line in EVAL_CASES_PATH.read_text(encoding="utf-8").splitlines() if line.strip())


@router.get("/system/status", response_model=SystemStatusResponse)
def get_system_status() -> SystemStatusResponse:
    return SystemStatusResponse(
        deterministic_workflow_available=True,
        agents_sdk_refinement_configured=bool(os.getenv("OPENAI_API_KEY")),
        band_collaboration_configured=is_band_configured(),
        eval_case_count=_count_eval_cases(),
        safety_boundary_categories=sorted(BLOCKED_PATTERNS),
    )


@router.get("/cases", response_model=list[CaseSummary])
def list_cases() -> list[CaseSummary]:
    return store.list_cases()


@router.post("/cases", response_model=CaseSummary)
def create_case(payload: CaseCreate) -> CaseSummary:
    return store.create_case(payload.title)


@router.get("/cases/{case_id}", response_model=CaseSummary)
def get_case(case_id: str) -> CaseSummary:
    try:
        return store.get_case(case_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/cases/{case_id}/documents", response_model=list[DocumentRecord])
def list_documents(case_id: str) -> list[DocumentRecord]:
    try:
        return store.list_documents(case_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/cases/{case_id}/documents", response_model=DocumentRecord)
async def upload_document(
    case_id: str,
    modality: DocumentModality = Form(default=DocumentModality.other),
    file: UploadFile = File(...),
) -> DocumentRecord:
    try:
        content = await file.read()
        extracted = extract_document_text(file.filename or "uploaded-file", content)
        return store.add_document(
            case_id=case_id,
            filename=file.filename or "uploaded-file",
            modality=modality,
            extracted_text=extracted.text,
            extraction_notes=extracted.notes,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/cases/{case_id}/documents/text", response_model=DocumentRecord)
def add_text_document(case_id: str, payload: TextDocumentCreate) -> DocumentRecord:
    try:
        return store.add_document(
            case_id=case_id,
            filename=payload.filename,
            modality=payload.modality,
            extracted_text=payload.text,
            extraction_notes=["医生手动输入文本。"],
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/cases/{case_id}/analyze/preop", response_model=PreopAssessmentReport)
async def analyze_preop(case_id: str) -> PreopAssessmentReport:
    try:
        documents = store.list_documents(case_id)
        if not documents:
            raise HTTPException(status_code=400, detail="请先上传或输入术前资料。")
        report = await run_preop_assessment(case_id, documents)
        return store.save_report(report)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/demo/sample-case", response_model=DemoCaseResponse)
async def create_sample_case() -> DemoCaseResponse:
    if not SAMPLE_CASE_PATH.exists():
        raise HTTPException(status_code=500, detail="Sample case file is missing.")

    sample_text = SAMPLE_CASE_PATH.read_text(encoding="utf-8").strip()
    case = store.create_case("Sample perioperative assessment case")
    document = store.add_document(
        case_id=case.id,
        filename=SAMPLE_CASE_PATH.name,
        modality=DocumentModality.ecg,
        extracted_text=sample_text,
        extraction_notes=["Loaded from the synthetic public demo sample."],
    )
    report = await run_preop_assessment(case.id, [document])
    saved_report = store.save_report(report)
    return DemoCaseResponse(case=store.get_case(case.id), documents=[document], report=saved_report)


@router.get("/cases/{case_id}/report", response_model=PreopAssessmentReport)
def get_report(case_id: str) -> PreopAssessmentReport:
    try:
        return store.get_report(case_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/cases/{case_id}/report/export.md", response_class=PlainTextResponse)
def export_report_markdown(case_id: str) -> PlainTextResponse:
    try:
        report = store.get_report(case_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    filename = f"periop-assessment-{case_id}.md"
    return PlainTextResponse(
        render_report_markdown(report),
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.patch("/cases/{case_id}/report/clinician-review", response_model=PreopAssessmentReport)
def update_review(case_id: str, payload: ClinicianReviewUpdate) -> PreopAssessmentReport:
    try:
        return store.update_clinician_review(case_id, payload)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/cases/{case_id}/intraop-events", response_model=list[IntraopEventRecord])
def list_intraop_events(case_id: str) -> list[IntraopEventRecord]:
    try:
        return store.list_intraop_events(case_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/cases/{case_id}/intraop-events", response_model=IntraopEventRecord)
def add_intraop_event(case_id: str, payload: IntraopEventCreate) -> IntraopEventRecord:
    try:
        return store.add_intraop_event(case_id, payload)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/cases/{case_id}/postop-plan", response_model=PostopPlanResponse)
def build_postop_plan(case_id: str) -> PostopPlanResponse:
    try:
        report = store.get_report(case_id)
        events = store.list_intraop_events(case_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _build_postop_plan(case_id, report, events)


@router.post("/cases/{case_id}/band-collaboration", response_model=BandCollaborationResponse)
async def create_band_collaboration_trace(case_id: str, send_to_band: bool = False) -> BandCollaborationResponse:
    try:
        documents = store.list_documents(case_id)
        report = store.get_report(case_id)
        events = store.list_intraop_events(case_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    try:
        return await build_band_collaboration_trace(
            case_id=case_id,
            documents=documents,
            report=report,
            events=events,
            send_to_band=send_to_band,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Band collaboration failed: {exc}") from exc


@router.get("/cases/{case_id}/band-collaboration/export.md", response_class=PlainTextResponse)
async def export_band_collaboration_markdown(case_id: str) -> PlainTextResponse:
    try:
        documents = store.list_documents(case_id)
        report = store.get_report(case_id)
        events = store.list_intraop_events(case_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    trace = await build_band_collaboration_trace(
        case_id=case_id,
        documents=documents,
        report=report,
        events=events,
        send_to_band=False,
    )
    filename = f"band-collaboration-{case_id}.md"
    return PlainTextResponse(
        render_band_transcript_markdown(trace),
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/safety/check", response_model=SafetyCheckResponse)
def safety_check(payload: SafetyCheckRequest) -> SafetyCheckResponse:
    return check_medical_safety(payload.text)


def _build_postop_plan(
    case_id: str,
    report: PreopAssessmentReport,
    events: list[IntraopEventRecord],
) -> PostopPlanResponse:
    surveillance_focus = [
        "PACU 内持续复核生命体征、疼痛、恶心呕吐、出血和意识状态。",
        *report.perioperative_monitoring_focus,
    ]
    suggested_checks = list(report.suggested_additional_checks)
    escalation_triggers = [
        "持续低氧、低血压、胸痛、意识改变、活动性出血或新发神经系统异常时，需立即由临床团队评估。",
    ]

    for flag in report.risk_flags:
        if flag.severity in {"high", "critical"}:
            surveillance_focus.append(f"围绕高风险线索复核：{flag.name}。")

    for event in events:
        if event.event_type.value in {"hypotension", "hypertension", "arrhythmia"}:
            suggested_checks.append("术中血流动力学或心律事件后，由医生判断是否复查心电图、电解质、血红蛋白或心肌损伤标志物。")
        if event.event_type.value == "hypoxemia":
            suggested_checks.append("术中低氧事件后，关注呼吸频率、SpO2、气道状态，必要时由医生判断是否需血气或胸部影像。")
        if event.event_type.value == "bleeding":
            suggested_checks.append("术中出血事件后，关注出血量、血红蛋白、凝血和容量状态。")
        if event.severity in {"high", "critical"}:
            escalation_triggers.append(f"术中记录了 {event.severity} 级事件：{event.description}，术后交接需明确复核。")

    return PostopPlanResponse(
        case_id=case_id,
        generated_at=datetime.now(timezone.utc),
        surveillance_focus=_dedupe(surveillance_focus),
        suggested_checks=_dedupe(suggested_checks),
        escalation_triggers=_dedupe(escalation_triggers),
        safety_notice=(
            "本术后计划为医生端交接和复核清单，不能替代术后医嘱、处方、抢救流程或病区处置决定。"
        ),
    )


def _dedupe(items: list[str]) -> list[str]:
    seen = set()
    result = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            result.append(item)
    return result
