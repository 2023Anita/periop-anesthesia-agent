from app.agents.safety import check_medical_safety


def test_safety_blocks_drug_dose():
    result = check_medical_safety("麻醉诱导药应该给多少剂量？")

    assert result.allowed is False
    assert result.category == "drug_dose"
    assert "医生" in result.safe_response


def test_safety_allows_risk_summary():
    result = check_medical_safety("请整理术前资料的风险线索和缺失信息。")

    assert result.allowed is True
    assert result.category == "allowed_support"
