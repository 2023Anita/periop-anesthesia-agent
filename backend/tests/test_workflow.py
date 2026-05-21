from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from app.agents.workflow import run_preop_assessment
from app.schemas.periop import DocumentModality, DocumentRecord


def test_preop_workflow_extracts_ecg_risk_without_openai_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    doc = DocumentRecord(
        id="doc-1",
        case_id="case-1",
        filename="ecg.txt",
        modality=DocumentModality.ecg,
        extracted_text="患者男，68岁，拟行择期胆囊切除术。心电图：窦性心律，心率 58 次/分，QTc 492 ms，ST-T改变。Hb 82 g/L，肌酐 130 umol/L。",
        extraction_notes=[],
        created_at=datetime.now(timezone.utc),
    )

    report = asyncio.run(run_preop_assessment("case-1", [doc]))

    assert report.ecg_findings
    assert report.patient_context.age == "68"
    assert report.patient_context.sex == "男"
    assert report.patient_context.planned_surgery == "择期胆囊切除术"
    assert report.lab_findings
    assert any(flag.name == "心电图相关麻醉风险" for flag in report.risk_flags)
    assert any(flag.name.startswith("关键化验异常") for flag in report.risk_flags)
    assert "医生" in report.safety_notice


def test_preop_workflow_does_not_extract_negated_allergy(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    doc = DocumentRecord(
        id="doc-1",
        case_id="case-1",
        filename="clinical-note.txt",
        modality=DocumentModality.clinical_note,
        extracted_text="患者男，68岁，拟行择期胆囊切除术。否认青霉素过敏。心电图：窦性心律，心率 68 次/分。",
        extraction_notes=[],
        created_at=datetime.now(timezone.utc),
    )

    report = asyncio.run(run_preop_assessment("case-1", [doc]))

    assert report.patient_context.allergies == []
    assert not any("过敏/相关线索" in finding.fact for finding in report.source_findings)
