from __future__ import annotations

from agents import Agent, GuardrailFunctionOutput, Runner, RunConfig, RunContextWrapper, TResponseInputItem, input_guardrail, trace

from app.agents.safety import check_medical_safety
from app.schemas.periop import PreopAssessmentReport, SafetyCheckResponse


@input_guardrail
async def medical_safety_guardrail(
    ctx: RunContextWrapper[None],
    agent: Agent,
    input: str | list[TResponseInputItem],
) -> GuardrailFunctionOutput:
    text = input if isinstance(input, str) else str(input)
    safety = check_medical_safety(text)
    return GuardrailFunctionOutput(output_info=safety, tripwire_triggered=not safety.allowed)


def build_preop_orchestrator() -> Agent:
    intake_agent = Agent(
        name="Intake Agent",
        instructions="只负责复核病例摘要、资料来源和缺失信息；不得给诊疗决策。",
    )
    ecg_agent = Agent(
        name="ECG Agent",
        instructions="只负责复核心电图文本级发现及其麻醉相关风险；不得替代心电图医生诊断。",
    )
    lab_agent = Agent(
        name="Lab Risk Agent",
        instructions="只负责复核关键化验异常与麻醉相关风险；不得给治疗剂量或处置命令。",
    )
    preop_risk_agent = Agent(
        name="Preop Risk Agent",
        instructions="只负责术前麻醉风险草案、追问问题和补充检查建议；最终必须由麻醉医生确认。",
    )

    return Agent(
        name="Perioperative Anesthesia Orchestrator",
        instructions=(
            "你是麻醉医生端辅助系统的主控 Agent。你会收到一个已经由确定性工具生成的结构化草案。"
            "你的任务是调用专家 Agent 复核表达、补齐缺失项和保持结构清晰。"
            "禁止输出药物剂量、自动决定能否手术、抢救处置指令或患者直接诊疗建议。"
            "必须保留 safety_notice，并保持输出为 PreopAssessmentReport 结构。"
        ),
        input_guardrails=[medical_safety_guardrail],
        tools=[
            intake_agent.as_tool(
                tool_name="intake_review",
                tool_description="复核病例摘要、资料来源和缺失信息。",
            ),
            ecg_agent.as_tool(
                tool_name="ecg_review",
                tool_description="复核心电图文本级发现及麻醉相关风险。",
            ),
            lab_agent.as_tool(
                tool_name="lab_risk_review",
                tool_description="复核关键化验异常及麻醉相关风险。",
            ),
            preop_risk_agent.as_tool(
                tool_name="preop_risk_review",
                tool_description="复核术前麻醉风险草案、追问问题和补充检查建议。",
            ),
        ],
        output_type=PreopAssessmentReport,
    )


async def refine_report_with_agents_sdk(report: PreopAssessmentReport) -> PreopAssessmentReport:
    orchestrator = build_preop_orchestrator()
    with trace("periop_anesthesia_preop_assessment"):
        result = await Runner.run(
            orchestrator,
            "请复核这份麻醉术前评估草案，保持医生辅助边界，输出同一结构：\n"
            + report.model_dump_json(),
            run_config=RunConfig(workflow_name="periop_anesthesia_preop_assessment"),
        )
    return result.final_output
