from app.tools.ecg import analyze_ecg_text


def test_analyze_ecg_text_detects_qtc_and_arrhythmia():
    finding = analyze_ecg_text("ecg-report", "心电图：心房颤动，HR: 96，QTc: 486 ms，右束支传导阻滞。")

    assert finding is not None
    assert finding.qtc == "486 ms"
    assert "心房颤动" in finding.rhythm
    assert finding.arrhythmia_findings
    assert finding.conduction_findings
    assert finding.anesthesia_risk_notes


def test_analyze_ecg_text_flags_marked_bradycardia_and_qtc():
    finding = analyze_ecg_text("ecg-report", "心电图：窦性心律，心率 44 次/分，QTc 512 ms，ST段压低。")

    assert finding is not None
    assert any("心动过缓" in note for note in finding.anesthesia_risk_notes)
    assert any("QTc 明显延长" in note for note in finding.anesthesia_risk_notes)
