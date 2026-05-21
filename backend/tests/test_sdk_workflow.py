from app.agents.sdk_workflow import build_preop_orchestrator


def test_build_preop_orchestrator_contains_specialist_tools():
    agent = build_preop_orchestrator()
    tool_names = {tool.name for tool in agent.tools}

    assert agent.name == "Perioperative Anesthesia Orchestrator"
    assert {"intake_review", "ecg_review", "lab_risk_review", "preop_risk_review"}.issubset(tool_names)
