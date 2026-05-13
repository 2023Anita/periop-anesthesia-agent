from app.tools.lab_checks import build_lab_risk_flags, extract_lab_findings


def test_extract_lab_findings_and_flags_abnormal_values():
    labs = extract_lab_findings([("lab.txt", "血红蛋白 78 g/L，PLT 65，肌酐 148 umol/L，K 5.8 mmol/L，INR 1.7")])
    flags = build_lab_risk_flags(labs)

    names = {lab.name for lab in labs}
    assert {"Hb", "PLT", "Cr", "K", "INR"}.issubset(names)
    assert any(lab.interpretation in {"low", "high", "critical"} for lab in labs)
    assert len(flags) >= 4
