from __future__ import annotations

import re

from app.schemas.periop import LabFinding, RiskFlag


LAB_PATTERNS = {
    "Hb": {
        "patterns": [r"\bHb[:：]?\s*([0-9.]+)\s*(g/L)?", r"血红蛋白[:：]?\s*([0-9.]+)\s*(g/L)?"],
        "unit": "g/L",
        "low": 90,
        "high": None,
        "relevance": "贫血会影响氧输送和围术期输血/监测策略。",
    },
    "PLT": {
        "patterns": [r"\bPLT[:：]?\s*([0-9.]+)\s*(?:10\^9/L|×10\^9/L)?", r"血小板[:：]?\s*([0-9.]+)"],
        "unit": "10^9/L",
        "low": 80,
        "high": None,
        "relevance": "血小板异常会影响出血风险和椎管内麻醉安全性评估。",
    },
    "Cr": {
        "patterns": [r"\bCr[:：]?\s*([0-9.]+)\s*(umol/L|μmol/L)?", r"肌酐[:：]?\s*([0-9.]+)\s*(umol/L|μmol/L)?", r"creatinine[:：]?\s*([0-9.]+)\s*(umol/L|μmol/L)?"],
        "unit": "umol/L",
        "low": None,
        "high": 110,
        "relevance": "肾功能异常会影响用药、液体管理和术后肾功能复查。",
    },
    "K": {
        "patterns": [r"\bK\+?[:：]?\s*([0-9.]+)\s*(mmol/L)?", r"血钾[:：]?\s*([0-9.]+)\s*(mmol/L)?"],
        "unit": "mmol/L",
        "low": 3.2,
        "high": 5.5,
        "relevance": "血钾异常与心律失常和围术期安全密切相关。",
    },
    "Glu": {
        "patterns": [r"\bGlu[:：]?\s*([0-9.]+)\s*(mmol/L)?", r"血糖[:：]?\s*([0-9.]+)\s*(mmol/L)?"],
        "unit": "mmol/L",
        "low": 3.0,
        "high": 10.0,
        "relevance": "血糖异常需要围术期监测和降糖方案复核。",
    },
    "INR": {
        "patterns": [r"\bINR[:：]?\s*([0-9.]+)"],
        "unit": None,
        "low": None,
        "high": 1.5,
        "relevance": "凝血异常会影响出血风险、麻醉方式和手术时机评估。",
    },
}


def extract_lab_findings(documents: list[tuple[str, str]]) -> list[LabFinding]:
    findings: list[LabFinding] = []
    for source, text in documents:
        for name, config in LAB_PATTERNS.items():
            match = _first_match(text, config["patterns"])
            if not match:
                continue
            value = match.group(1)
            interpretation = _interpret(float(value), config["low"], config["high"])
            findings.append(
                LabFinding(
                    name=name,
                    value=value,
                    unit=config["unit"],
                    interpretation=interpretation,
                    anesthesia_relevance=config["relevance"],
                    source=source,
                )
            )
    return findings


def build_lab_risk_flags(labs: list[LabFinding]) -> list[RiskFlag]:
    flags: list[RiskFlag] = []
    for lab in labs:
        if lab.interpretation in {"low", "high", "critical"}:
            severity = "high" if lab.interpretation == "critical" else "medium"
            flags.append(
                RiskFlag(
                    name=f"关键化验异常：{lab.name}",
                    severity=severity,
                    rationale=f"{lab.name}={lab.value}{lab.unit or ''}，{lab.anesthesia_relevance}",
                    evidence=[lab.source],
                )
            )
    return flags


def _first_match(text: str, patterns: list[str]) -> re.Match[str] | None:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return match
    return None


def _interpret(value: float, low: float | None, high: float | None) -> str:
    if low is not None and value < low:
        return "critical" if value < low * 0.8 else "low"
    if high is not None and value > high:
        return "critical" if value > high * 1.5 else "high"
    return "normal"
