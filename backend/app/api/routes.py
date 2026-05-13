from __future__ import annotations

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.agents.workflow import run_preop_assessment
from app.core import store
from app.schemas.periop import (
    CaseCreate,
    CaseSummary,
    ClinicianReviewUpdate,
    DocumentModality,
    DocumentRecord,
    PreopAssessmentReport,
    TextDocumentCreate,
)
from app.tools.document_extractors import extract_document_text


router = APIRouter()


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


@router.get("/cases/{case_id}/report", response_model=PreopAssessmentReport)
def get_report(case_id: str) -> PreopAssessmentReport:
    try:
        return store.get_report(case_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.patch("/cases/{case_id}/report/clinician-review", response_model=PreopAssessmentReport)
def update_review(case_id: str, payload: ClinicianReviewUpdate) -> PreopAssessmentReport:
    try:
        return store.update_clinician_review(case_id, payload)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

