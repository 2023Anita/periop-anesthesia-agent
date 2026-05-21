from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import PlainTextResponse

from app.agents.safety import check_medical_safety
from app.agents.workflow import run_preop_assessment
from app.core import store
from app.schemas.periop import (
    CaseCreate,
    CaseSummary,
    ClinicianReviewUpdate,
    DemoCaseResponse,
    DocumentModality,
    DocumentRecord,
    PreopAssessmentReport,
    SafetyCheckRequest,
    SafetyCheckResponse,
    TextDocumentCreate,
)
from app.tools.document_extractors import extract_document_text
from app.tools.report_export import render_report_markdown


router = APIRouter()
PROJECT_ROOT = Path(__file__).resolve().parents[3]
SAMPLE_CASE_PATH = PROJECT_ROOT / "data" / "samples" / "sample-preop-ecg.txt"


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


@router.post("/safety/check", response_model=SafetyCheckResponse)
def safety_check(payload: SafetyCheckRequest) -> SafetyCheckResponse:
    return check_medical_safety(payload.text)
