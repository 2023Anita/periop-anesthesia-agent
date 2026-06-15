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
        heart_rate=_extract_value(normalized, [r"心率[:：]?\s*(\d+\s*次/分)", r"HR[:：]?\s*(\d+\s*bpm|\d+)", r"heart rate[:：]?\s*(\d+\s*bpm|\d+)"]),
        rhythm=_extract_rhythm(normalized),
        pr_interval=_extract_value(normalized, [r"PR[:：]?\s*([0-9.]+\s*ms)", r"PR间期[:：]?\s*([0-9.]+\s*ms)"]),
        qrs_duration=_extract_value(normalized, [r"QRS[:：]?\s*([0-9.]+\s*ms)", r"QRS时限[:：]?\s*([0-9.]+\s*ms)"]),
        qtc=_extract_value(normalized, [r"QTc[:：]?\s*([0-9.]+\s*ms)", r"QTc间期[:：]?\s*([0-9.]+\s*ms)"]),
    )

    finding.st_t_changes = _collect_terms(
        normalized,
        ["ST-T改变", "ST段压低", "ST段抬高", "T波倒置", "T波低平", "异常Q波", "缺血", "ST-T changes", "ST depression", "ST elevation", "T-wave inversion", "ischemia"],
    )
    finding.conduction_findings = _collect_terms(
        normalized,
        [
            "房室传导阻滞",
            "右束支传导阻滞",
            "左束支传导阻滞",
            "一度房室传导阻滞",
            "二度房室传导阻滞",
            "三度房室传导阻滞",
            "完全性右束支传导阻滞",
            "完全性左束支传导阻滞",
            "right bundle branch block",
            "left bundle branch block",
            "AV block",
        ],
    )
    finding.arrhythmia_findings = _collect_terms(
        normalized,
        ["房颤", "心房颤动", "房扑", "室性早搏", "频发室早", "房性早搏", "室上速", "心动过缓", "心动过速", "起搏心律", "atrial fibrillation", "atrial flutter", "PVC", "bradycardia", "tachycardia", "paced rhythm"],
    )
    finding.anesthesia_risk_notes = _ecg_risk_notes(finding, normalized)
    finding.missing_info = _missing_ecg_info(finding)
    return finding


def _looks_like_ecg(text: str) -> bool:
    keywords = ["心电图", "ecg", "ekg", "窦性", "sinus", "st-t", "qtc", "qrs", "房颤", "atrial fibrillation", "传导阻滞", "bundle branch block", "室性早搏", "心动过缓", "bradycardia"]
    return any(keyword in text for keyword in keywords)


def _extract_value(text: str, patterns: list[str]) -> str | None:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None


def _extract_rhythm(text: str) -> str | None:
    for term in ["窦性心律", "心房颤动", "房颤", "心房扑动", "房扑", "起搏心律", "sinus rhythm", "atrial fibrillation", "atrial flutter", "paced rhythm"]:
        if term.lower() in text.lower():
            return term
    return None


def _collect_terms(text: str, terms: list[str]) -> list[str]:
    return [term for term in terms if term in text]


def _ecg_risk_notes(finding: ECGFinding, text: str) -> list[str]:
    notes: list[str] = []
    hr_value = _numeric_prefix(finding.heart_rate)
    if hr_value is not None and hr_value < 50:
        notes.append("明显心动过缓线索：需结合症状、传导阻滞和术中备用处置策略复核。")
    if hr_value is not None and hr_value > 120:
        notes.append("明显心动过速线索：需结合容量状态、感染、疼痛、心律失常和心功能评估。")
    if finding.qtc:
        qtc_value = _numeric_prefix(finding.qtc)
        if qtc_value is not None and qtc_value >= 500:
            notes.append("QTc 明显延长：需医生重点复核电解质、既往晕厥史和可能延长 QT 的围术期用药。")
        elif qtc_value is not None and qtc_value >= 480:
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


def _numeric_prefix(value: str | None) -> int | None:
    if not value:
        return None
    numbers = re.findall(r"\d+", value)
    return int(numbers[0]) if numbers else None
