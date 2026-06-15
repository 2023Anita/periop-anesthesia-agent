from __future__ import annotations

import re

from app.schemas.periop import PreopAssessmentReport
from app.schemas.periop import SafetyCheckResponse


SAFE_RESPONSE = (
    "该请求需要麻醉医生结合现场病情、原始资料和医院流程判断。"
    "本系统只能提供资料整理、风险线索、缺失信息和医生复核用草案。"
)


BLOCKED_PATTERNS = {
    "surgery_clearance": ["能不能手术", "可不可以手术", "是否可以手术", "准不准手术", "能做手术吗", "手术禁忌"],
    "drug_dose": ["给多少", "剂量", "多少mg", "多少毫克", "用几支", "麻醉药量", "怎么给药"],
    "emergency_treatment": ["怎么抢救", "抢救流程", "立即处理", "休克怎么办", "心跳骤停", "插管怎么做"],
    "medication_decision": ["停药", "换药", "加药", "抗凝桥接", "是否停用", "要不要停"],
    "patient_direct_advice": ["我是患者", "我该怎么办", "我能不能", "我需不需要", "我要不要"],
}

OUTPUT_BLOCKED_PATTERNS = {
    "surgery_clearance": ["可以手术", "不可以手术", "不能手术", "建议取消手术", "建议延期手术", "手术许可", "cleared for surgery"],
    "drug_dose": ["丙泊酚", "依托咪酯", "咪达唑仑", "芬太尼", "罗库溴铵", "舒芬太尼"],
    "emergency_treatment": ["立即抢救", "立即插管", "立即电除颤", "立刻给药"],
    "medication_decision": ["应停用", "应换用", "应加用", "桥接抗凝方案"],
}


def check_medical_safety(text: str) -> SafetyCheckResponse:
    normalized = text.strip().lower()
    for category, terms in BLOCKED_PATTERNS.items():
        matched = [term for term in terms if term.lower() in normalized]
        if matched:
            return SafetyCheckResponse(
                allowed=False,
                category=category,
                reason=_reason_for(category),
                safe_response=SAFE_RESPONSE,
                matched_terms=matched,
            )
    return SafetyCheckResponse(
        allowed=True,
        category="allowed_support",
        reason="该输入未触发自动决策、药物剂量、抢救处置或患者直接诊疗建议边界。",
        safe_response="可以继续作为医生复核用资料整理或风险提示任务处理。",
        matched_terms=[],
    )


def check_report_output_safety(report: PreopAssessmentReport) -> SafetyCheckResponse:
    return check_output_text_safety(report.model_dump_json())


def check_output_text_safety(text: str) -> SafetyCheckResponse:
    for category, terms in OUTPUT_BLOCKED_PATTERNS.items():
        matched = [term for term in terms if term.lower() in text.lower()]
        if matched:
            if category == "drug_dose" and not _contains_dose_like_instruction(text):
                continue
            return SafetyCheckResponse(
                allowed=False,
                category=f"output_{category}",
                reason=_reason_for(category),
                safe_response=SAFE_RESPONSE,
                matched_terms=matched,
            )
    return SafetyCheckResponse(
        allowed=True,
        category="output_allowed_support",
        reason="输出未触发明确手术许可、药物剂量、抢救处置或停换药决策边界。",
        safe_response="可以作为医生复核用草案继续展示。",
        matched_terms=[],
    )


def _reason_for(category: str) -> str:
    reasons = {
        "surgery_clearance": "系统不能自动决定能否手术或替代术前麻醉评估结论。",
        "drug_dose": "系统不能提供麻醉药物、抢救药物或治疗药物的个体化剂量。",
        "emergency_treatment": "抢救和侵入性处置必须由具备资质的临床人员现场判断。",
        "medication_decision": "围术期停药、换药、桥接等决策必须由医生结合指南和病情确认。",
        "patient_direct_advice": "本系统定位为医生端辅助工具，不面向患者提供个体化诊疗建议。",
    }
    return reasons.get(category, "该请求超出医生辅助资料整理边界。")


def _contains_dose_like_instruction(text: str) -> bool:
    dose_patterns = [
        r"\d+(\.\d+)?\s*mg",
        r"\d+(\.\d+)?\s*毫克",
        r"\d+(\.\d+)?\s*mg/kg",
        r"\d+(\.\d+)?\s*(mcg|μg|ug)/kg",
        r"\d+(\.\d+)?\s*(mcg|μg|ug)",
        r"\d+(\.\d+)?\s*(ml|毫升|单位|u)\b",
        r"(滴速|泵速)\s*\d+",
        r"给\s*\d+",
        r"用\s*\d+",
    ]
    return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in dose_patterns)
