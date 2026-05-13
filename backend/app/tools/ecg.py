from __future__ import annotations

import re

from app.schemas.periop import ECGFinding


def analyze_ecg_text(source: str, text: str) -> ECGFinding | None:
    normalized = text.strip()
    if not normalized:
        return None

    lower = normalized.lower()
    if not _looks_like_ecg(lower):
        return None

    finding = ECGFinding(
        source=source,
        heart_rate=_extract_value(normalized, [r"心率[:：]?\s*(\d+\s*次/分)", r"HR[:：]?\s*(\d+)"]),
        rhythm=_extract_rhythm(normalized),
        pr_interval=_extract_value(normalized, [r"PR[:：]?\s*([0-9.]+\s*ms)", r"PR间期[:：]?\s*([0-9.]+\s*ms)"]),
        qrs_duration=_extract_value(normalized, [r"QRS[:：]?\s*([0-9.]+\s*ms)", r"QRS时限[:：]?\s*([0-9.]+\s*ms)"]),
        qtc=_extract_value(normalized, [r"QTc[:：]?\s*([0-9.]+\s*ms)", r"QTc间期[:：]?\s*([0-9.]+\s*ms)"]),
    )

    finding.st_t_changes = _collect_terms(
        normalized,
        ["ST-T改变", "ST段压低", "ST段抬高", "T波倒置", "T波低平", "缺血"],
    )
    finding.conduction_findings = _collect_terms(
        normalized,
        ["房室传导阻滞", "右束支传导阻滞", "左束支传导阻滞", "一度房室传导阻滞", "二度房室传导阻滞", "三度房室传导阻滞"],
    )
    finding.arrhythmia_findings = _collect_terms(
        normalized,
        ["房颤", "心房颤动", "房扑", "室性早搏", "房性早搏", "室上速", "心动过缓", "心动过速"],
    )
    finding.anesthesia_risk_notes = _ecg_risk_notes(finding, normalized)
    finding.missing_info = _missing_ecg_info(finding)
    return finding


def _looks_like_ecg(text: str) -> bool:
    keywords = ["心电图", "ecg", "ekg", "窦性", "st-t", "qtc", "qrs", "房颤", "传导阻滞"]
    return any(keyword in text for keyword in keywords)


def _extract_value(text: str, patterns: list[str]) -> str | None:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None


def _extract_rhythm(text: str) -> str | None:
    for term in ["窦性心律", "心房颤动", "房颤", "心房扑动", "房扑", "起搏心律"]:
        if term in text:
            return term
    return None


def _collect_terms(text: str, terms: list[str]) -> list[str]:
    return [term for term in terms if term in text]


def _ecg_risk_notes(finding: ECGFinding, text: str) -> list[str]:
    notes: list[str] = []
    if finding.qtc:
        numbers = re.findall(r"\d+", finding.qtc)
        if numbers and int(numbers[0]) >= 480:
            notes.append("QTc 延长：麻醉相关用药和电解质异常需医生重点复核。")
    if finding.arrhythmia_findings:
        notes.append("存在心律失常线索：需结合症状、既往病史、用药和血流动力学稳定性评估。")
    if finding.conduction_findings:
        notes.append("存在传导阻滞线索：术中监测和备用处置策略需麻醉医生确认。")
    if finding.st_t_changes or "缺血" in text:
        notes.append("存在 ST-T/缺血相关线索：需结合症状、肌钙蛋白、心超或心内科意见。")
    if not notes:
        notes.append("未从心电图文本中发现明确高危关键词，但仍需医生结合原始图和病史复核。")
    return notes


def _missing_ecg_info(finding: ECGFinding) -> list[str]:
    missing = []
    if not finding.heart_rate:
        missing.append("未抽取到心率。")
    if not finding.rhythm:
        missing.append("未抽取到明确节律。")
    if not finding.qtc:
        missing.append("未抽取到 QTc。")
    return missing

