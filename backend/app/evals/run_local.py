from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path

from app.agents.safety import check_medical_safety, check_output_text_safety
from app.agents.workflow import run_preop_assessment
from app.schemas.periop import DocumentModality, DocumentRecord


EVAL_DIR = Path(__file__).resolve().parent
CASES_PATH = EVAL_DIR / "cases.jsonl"
RESULTS_DIR = EVAL_DIR / "results"
LATEST_PATH = RESULTS_DIR / "latest.json"


async def main() -> int:
    cases = [json.loads(line) for line in CASES_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    results = []
    failures = 0
    for case in cases:
        passed, details = await run_case(case)
        failures += 0 if passed else 1
        results.append({"id": case["id"], "passed": passed, "details": details})

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    LATEST_PATH.write_text(
        json.dumps(
            {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "total": len(results),
                "passed": len(results) - failures,
                "failed": failures,
                "results": results,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"eval cases: {len(results)}, passed: {len(results) - failures}, failed: {failures}")
    print(f"results: {LATEST_PATH}")
    return 1 if failures else 0


async def run_case(case: dict) -> tuple[bool, dict]:
    if case["type"] == "safety":
        safety = check_medical_safety(case["text"])
        expect = case["expect"]
        passed = safety.allowed == expect["allowed"] and safety.category == expect["category"]
        return passed, safety.model_dump()

    if case["type"] == "output_safety":
        safety = check_output_text_safety(case["text"])
        expect = case["expect"]
        passed = safety.allowed == expect["allowed"] and safety.category == expect["category"]
        return passed, safety.model_dump()

    doc = DocumentRecord(
        id=f"{case['id']}-doc",
        case_id=case["id"],
        filename=f"{case['id']}.txt",
        modality=DocumentModality.ecg if "心电图" in case["text"] else DocumentModality.clinical_note,
        extracted_text=case["text"],
        extraction_notes=["eval fixture"],
        created_at=datetime.now(timezone.utc),
    )
    report = await run_preop_assessment(case["id"], [doc])
    expect = case["expect"]
    details = {
        "risk_flags": [flag.name for flag in report.risk_flags],
        "missing_information": report.missing_information,
        "ecg_count": len(report.ecg_findings),
        "lab_names": [lab.name for lab in report.lab_findings],
    }
    checks = []
    if "min_risk_flags" in expect:
        checks.append(len(report.risk_flags) >= expect["min_risk_flags"])
    if expect.get("ecg") is True:
        checks.append(bool(report.ecg_findings))
    if "labs" in expect:
        lab_names = {lab.name for lab in report.lab_findings}
        checks.append(set(expect["labs"]).issubset(lab_names))
    if "missing_contains" in expect:
        checks.append(any(expect["missing_contains"] in item for item in report.missing_information))
    if "max_high_ecg_risk_flags" in expect:
        high_ecg_flags = [
            flag for flag in report.risk_flags
            if flag.name == "心电图相关麻醉风险" and flag.severity in {"high", "critical"}
        ]
        checks.append(len(high_ecg_flags) <= expect["max_high_ecg_risk_flags"])
    return all(checks), details


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
