from __future__ import annotations

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


def _reason_for(category: str) -> str:
    reasons = {
        "surgery_clearance": "系统不能自动决定能否手术或替代术前麻醉评估结论。",
        "drug_dose": "系统不能提供麻醉药物、抢救药物或治疗药物的个体化剂量。",
        "emergency_treatment": "抢救和侵入性处置必须由具备资质的临床人员现场判断。",
        "medication_decision": "围术期停药、换药、桥接等决策必须由医生结合指南和病情确认。",
        "patient_direct_advice": "本系统定位为医生端辅助工具，不面向患者提供个体化诊疗建议。",
    }
    return reasons.get(category, "该请求超出医生辅助资料整理边界。")
