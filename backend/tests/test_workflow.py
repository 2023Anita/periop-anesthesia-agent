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
        extracted_text="心电图：窦性心律，心率 58 次/分，QTc 492 ms，ST-T改变。",
        extraction_notes=[],
        created_at=datetime.now(timezone.utc),
    )

    report = asyncio.run(run_preop_assessment("case-1", [doc]))

    assert report.ecg_findings
    assert any(flag.name == "心电图相关麻醉风险" for flag in report.risk_flags)
    assert "医生" in report.safety_notice

