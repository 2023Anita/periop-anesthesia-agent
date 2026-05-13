from app.tools.ecg import analyze_ecg_text


def test_analyze_ecg_text_detects_qtc_and_arrhythmia():
    finding = analyze_ecg_text("ecg-report", "心电图：心房颤动，HR: 96，QTc: 486 ms，右束支传导阻滞。")

    assert finding is not None
    assert finding.qtc == "486 ms"
    assert "心房颤动" in finding.rhythm
    assert finding.arrhythmia_findings
    assert finding.conduction_findings
    assert finding.anesthesia_risk_notes

