from __future__ import annotations

import os
from datetime import datetime, timezone

from app.schemas.periop import DocumentModality, DocumentRecord, PreopAssessmentReport, RiskFlag
from app.tools.ecg import analyze_ecg_text
from app.tools.lab_checks import build_lab_risk_flags, extract_lab_findings
from app.tools.risk_scores import (
    asa_suggestion,
    build_patient_context,
    build_risk_flags,
    extract_source_findings,
    ponv_summary,
    rcri_summary,
    stop_bang_summary,
)


SAFETY_NOTICE = (
    "本报告为麻醉医生术前评估辅助草案，不是自动诊断、治疗、用药、麻醉方案或能否手术的最终决定。"
    "所有内容必须由麻醉医生结合原始资料和患者实际情况复核确认。"
)


async def run_preop_assessment(case_id: str, documents: list[DocumentRecord]) -> PreopAssessmentReport:
    base_report = _build_deterministic_report(case_id, documents)
    if os.getenv("OPENAI_API_KEY"):
        return await _try_agents_sdk_refinement(base_report)
    return base_report


def _build_deterministic_report(case_id: str, documents: list[DocumentRecord]) -> PreopAssessmentReport:
    doc_pairs = [(doc.filename, doc.extracted_text) for doc in documents]
    all_text = "\n\n".join(text for _, text in doc_pairs)
    context = build_patient_context(all_text)
    findings = extract_source_findings(doc_pairs)
    lab_findings = extract_lab_findings(doc_pairs)

    ecg_findings = []
    for doc in documents:
        if doc.modality == DocumentModality.ecg or "心电图" in doc.extracted_text or "ECG" in doc.extracted_text.upper():
            finding = analyze_ecg_text(doc.filename, doc.extracted_text)
            if finding:
                ecg_findings.append(finding)

    risk_flags = build_risk_flags(context, all_text)
    risk_flags.extend(build_lab_risk_flags(lab_findings))
    for finding in ecg_findings:
        for note in finding.anesthesia_risk_notes:
            severity = "high" if any(term in note for term in ["QTc", "ST-T", "缺血", "传导阻滞"]) else "medium"
            risk_flags.append(
                RiskFlag(
                    name="心电图相关麻醉风险",
                    severity=severity,
                    rationale=note,
                    evidence=[finding.source],
                )
            )

    missing = _missing_information(context, all_text, bool(ecg_findings))
    return PreopAssessmentReport(
        case_id=case_id,
        generated_at=datetime.now(timezone.utc),
        patient_context=context,
        source_findings=findings,
        ecg_findings=ecg_findings,
        lab_findings=lab_findings,
        risk_flags=risk_flags,
        asa_suggestion=asa_suggestion(context),
        rcri_summary=rcri_summary(context),
        stop_bang_summary=stop_bang_summary(all_text),
        ponv_summary=ponv_summary(all_text),
        missing_information=missing,
        suggested_follow_up_questions=[
            "请确认拟行手术名称、手术级别、急诊/择期属性。",
            "请补充活动耐量、胸痛/气促/晕厥等心肺症状。",
            "请确认抗凝/抗血小板药物最近一次服用时间。",
            "请确认既往麻醉异常、困难气道、PONV 和药物过敏史。",
        ],
        suggested_additional_checks=[
            "资料不完整时补充血常规、凝血、肝肾功能、电解质和心电图。",
            "存在心血管高危线索时，由医生判断是否需要心超、肌钙蛋白或心内科会诊。",
            "存在 OSA 或困难气道线索时，补充气道评估和术后呼吸监测计划。",
        ],
        perioperative_monitoring_focus=[
            "术中血压、心率、氧合、通气和出血量动态监测。",
            "高危患者关注心肌缺血、心律失常、低氧、低血压和术后谵妄。",
            "术后根据术前风险和术中事件决定 PACU/病房监测重点。",
        ],
        safety_notice=SAFETY_NOTICE,
    )


async def _try_agents_sdk_refinement(report: PreopAssessmentReport) -> PreopAssessmentReport:
    try:
        from app.agents.sdk_workflow import refine_report_with_agents_sdk

        return await refine_report_with_agents_sdk(report)
    except Exception:
        return report


def _missing_information(context, all_text: str, has_ecg: bool) -> list[str]:
    missing = []
    if not context.age:
        missing.append("年龄未结构化抽取，需医生确认。")
    if not context.planned_surgery:
        missing.append("拟行手术名称和手术级别未结构化抽取。")
    if "血常规" not in all_text and "Hb" not in all_text and "血红蛋白" not in all_text:
        missing.append("未见明确血常规/血红蛋白资料。")
    if "凝血" not in all_text and "PT" not in all_text and "APTT" not in all_text:
        missing.append("未见明确凝血功能资料。")
    if "肌酐" not in all_text and "Cr" not in all_text:
        missing.append("未见明确肾功能/肌酐资料。")
    if not has_ecg:
        missing.append("未见可结构化识别的心电图资料。")
    return missing
