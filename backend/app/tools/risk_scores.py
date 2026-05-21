from __future__ import annotations

import re

from app.schemas.periop import DocumentFinding, PatientContext, RiskFlag


HISTORY_TERMS = {
    "高血压": ["高血压", "hypertension"],
    "糖尿病": ["糖尿病", "diabetes", "dm"],
    "冠心病": ["冠心病", "心肌梗死", "心绞痛", "cad", "mi"],
    "心衰": ["心衰", "心功能不全", "heart failure"],
    "COPD/哮喘": ["copd", "慢阻肺", "哮喘"],
    "肾功能异常": ["肾功能不全", "肌酐升高", "ckd", "尿毒症"],
    "脑卒中": ["脑卒中", "脑梗", "脑出血", "stroke"],
    "睡眠呼吸暂停风险": ["睡眠呼吸暂停", "OSA", "打鼾", "鼾症"],
}

MEDICATION_TERMS = [
    "阿司匹林",
    "氯吡格雷",
    "替格瑞洛",
    "华法林",
    "利伐沙班",
    "阿哌沙班",
    "达比加群",
    "低分子肝素",
    "胰岛素",
    "二甲双胍",
    "GLP-1",
    "司美格鲁肽",
    "激素",
    "β受体阻滞剂",
    "ACEI",
    "ARB",
]
ALLERGY_TERMS = ["过敏", "青霉素", "头孢", "碘", "乳胶"]


def build_patient_context(all_text: str) -> PatientContext:
    context = PatientContext()
    context.age = _extract_first(all_text, [r"(\d{1,3})\s*岁", r"年龄[:：]?\s*(\d{1,3})"])
    context.sex = _extract_sex(all_text)
    context.planned_surgery = _extract_first(
        all_text,
        [
            r"拟行[:：]?\s*([^。\n；;]{2,40}?(?:术|手术))",
            r"拟行手术[:：]?\s*([^。\n；;]{2,40})",
            r"手术名称[:：]?\s*([^。\n；;]{2,40})",
        ],
    )
    context.height_weight_bmi = _extract_body_size(all_text)
    for name, terms in HISTORY_TERMS.items():
        if any(term.lower() in all_text.lower() for term in terms):
            context.history.append(name)
    for term in MEDICATION_TERMS:
        if term.lower() in all_text.lower():
            context.medications.append(term)
    for term in ALLERGY_TERMS:
        if _contains_unnegated_term(all_text, term):
            context.allergies.append(term)
    if "急诊" in all_text:
        context.urgency = "急诊"
    elif "择期" in all_text:
        context.urgency = "择期"
    for term in ["全麻异常", "困难插管", "困难气道", "恶性高热", "PONV", "术后恶心呕吐"]:
        if term.lower() in all_text.lower():
            context.anesthesia_history.append(term)
    return context


def extract_source_findings(documents: list[tuple[str, str]]) -> list[DocumentFinding]:
    findings: list[DocumentFinding] = []
    for source, text in documents:
        for name, terms in HISTORY_TERMS.items():
            if any(term.lower() in text.lower() for term in terms):
                findings.append(DocumentFinding(source=source, fact=f"发现既往史线索：{name}", confidence="medium"))
        for medication in MEDICATION_TERMS:
            if medication.lower() in text.lower():
                findings.append(DocumentFinding(source=source, fact=f"发现用药线索：{medication}", confidence="medium"))
        for allergy in ALLERGY_TERMS:
            if _contains_unnegated_term(text, allergy):
                findings.append(DocumentFinding(source=source, fact=f"发现过敏/相关线索：{allergy}", confidence="medium"))
    return findings


def build_risk_flags(context: PatientContext, all_text: str) -> list[RiskFlag]:
    flags: list[RiskFlag] = []
    if any(item in context.history for item in ["冠心病", "心衰", "脑卒中"]):
        flags.append(
            RiskFlag(
                name="心血管围术期风险",
                severity="high",
                rationale="病史中存在冠心病、心衰或脑卒中线索，需要麻醉医生复核心血管风险。",
                evidence=context.history,
            )
        )
    if "肾功能异常" in context.history:
        flags.append(
            RiskFlag(
                name="肾功能相关风险",
                severity="medium",
                rationale="存在肾功能异常线索，需关注用药、液体管理和术后肾功能复查。",
                evidence=context.history,
            )
        )
    if any(med in context.medications for med in ["阿司匹林", "氯吡格雷", "华法林", "利伐沙班", "达比加群"]):
        flags.append(
            RiskFlag(
                name="抗栓/出血风险",
                severity="high",
                rationale="资料中出现抗血小板或抗凝药物，围术期停药和桥接策略必须由医生确认。",
                evidence=context.medications,
            )
        )
    if any(med in context.medications for med in ["GLP-1", "司美格鲁肽"]):
        flags.append(
            RiskFlag(
                name="胃排空延迟/误吸风险",
                severity="medium",
                rationale="资料中出现 GLP-1 类药物线索，术前禁食、胃排空和误吸风险需医生确认。",
                evidence=context.medications,
            )
        )
    if any(word in all_text for word in ["困难气道", "张口受限", "颈椎活动受限", "Mallampati III", "Mallampati IV"]):
        flags.append(
            RiskFlag(
                name="困难气道风险",
                severity="high",
                rationale="资料中存在困难气道相关线索，需麻醉医生复核气道评估。",
                evidence=["困难气道相关关键词"],
            )
        )
    if not flags:
        flags.append(
            RiskFlag(
                name="未发现明确高危关键词",
                severity="low",
                rationale="当前资料未提示明确高危关键词，但资料可能不完整，仍需医生复核。",
                evidence=[],
            )
        )
    return flags


def asa_suggestion(context: PatientContext) -> str:
    if any(item in context.history for item in ["冠心病", "心衰", "COPD/哮喘", "肾功能异常", "脑卒中"]):
        return "ASA 分级草案：可能为 II-III 级，需麻醉医生结合功能状态和原始资料确认。"
    if context.history:
        return "ASA 分级草案：可能为 II 级，需医生确认疾病控制情况。"
    return "ASA 分级草案：资料不足或未见明显系统疾病线索，需医生补全病史后确认。"


def rcri_summary(context: PatientContext) -> str:
    risk_items = [item for item in context.history if item in {"冠心病", "心衰", "脑卒中", "糖尿病", "肾功能异常"}]
    return f"RCRI 草案：发现 {len(risk_items)} 类相关线索（{', '.join(risk_items) or '暂无'}），需结合手术类型和肌酐等数据确认。"


def stop_bang_summary(all_text: str) -> str:
    terms = ["打鼾", "睡眠呼吸暂停", "OSA", "BMI", "颈围", "白天嗜睡"]
    hits = [term for term in terms if term.lower() in all_text.lower()]
    return f"STOP-Bang 草案：发现 {len(hits)} 项相关线索（{', '.join(hits) or '暂无'}），缺少身高体重、颈围或睡眠症状时不能完成评分。"


def ponv_summary(all_text: str) -> str:
    terms = ["女性", "不吸烟", "晕动病", "PONV", "术后恶心", "阿片"]
    hits = [term for term in terms if term.lower() in all_text.lower()]
    return f"PONV 风险草案：发现 {len(hits)} 项相关线索（{', '.join(hits) or '暂无'}），需补充吸烟史、既往 PONV 和术后镇痛计划。"


def _extract_first(text: str, patterns: list[str]) -> str | None:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None


def _contains_unnegated_term(text: str, term: str) -> bool:
    for match in re.finditer(re.escape(term), text, flags=re.IGNORECASE):
        prefix = text[max(0, match.start() - 8) : match.start()]
        if not any(negation in prefix for negation in ["否认", "无", "未见", "没有", "无明确"]):
            return True
    return False


def _extract_sex(text: str) -> str | None:
    if re.search(r"(患者)?\s*男|男性|性别[:：]?\s*男", text):
        return "男"
    if re.search(r"(患者)?\s*女|女性|性别[:：]?\s*女", text):
        return "女"
    return None


def _extract_body_size(text: str) -> str | None:
    height = _extract_first(text, [r"身高[:：]?\s*(\d{2,3}\s*cm)", r"(\d{2,3}\s*cm)"])
    weight = _extract_first(text, [r"体重[:：]?\s*(\d{2,3}\s*kg)", r"(\d{2,3}\s*kg)"])
    bmi = _extract_first(text, [r"BMI[:：]?\s*([0-9.]+)"])
    parts = [part for part in [height, weight, f"BMI {bmi}" if bmi else None] if part]
    return " / ".join(parts) if parts else None
