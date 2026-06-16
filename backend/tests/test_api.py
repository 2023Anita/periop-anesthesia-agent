from fastapi.testclient import TestClient

from app.main import app


def test_create_case_text_document_and_analyze(tmp_path, monkeypatch):
    monkeypatch.setenv("PERIOP_DB_PATH", str(tmp_path / "test.sqlite"))
    from app.core.store import init_db

    init_db()
    client = TestClient(app)

    case_resp = client.post("/api/cases", json={"title": "测试术前病例"})
    assert case_resp.status_code == 200
    case_id = case_resp.json()["id"]

    doc_resp = client.post(
        f"/api/cases/{case_id}/documents/text",
        json={
            "filename": "manual.txt",
            "modality": "ecg",
            "text": "患者女，72岁，拟行髋关节置换术，高血压。心电图：窦性心律，心率 70 次/分，QTc: 460 ms。Hb 86 g/L。",
        },
    )
    assert doc_resp.status_code == 200

    analyze_resp = client.post(f"/api/cases/{case_id}/analyze/preop")
    assert analyze_resp.status_code == 200
    report = analyze_resp.json()
    assert report["case_id"] == case_id
    assert report["patient_context"]["age"] == "72"
    assert report["patient_context"]["sex"] == "女"
    assert report["ecg_findings"]
    assert report["lab_findings"]


def test_safety_check_api_blocks_clearance_request(tmp_path, monkeypatch):
    monkeypatch.setenv("PERIOP_DB_PATH", str(tmp_path / "test.sqlite"))
    from app.core.store import init_db

    init_db()
    client = TestClient(app)

    resp = client.post("/api/safety/check", json={"text": "这个患者能不能手术？"})

    assert resp.status_code == 200
    data = resp.json()
    assert data["allowed"] is False
    assert data["category"] == "surgery_clearance"


def test_system_status_reports_runtime_controls(tmp_path, monkeypatch):
    monkeypatch.setenv("PERIOP_DB_PATH", str(tmp_path / "test.sqlite"))
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("BAND_AGENT_API_KEY", raising=False)
    monkeypatch.delenv("BAND_CHAT_ID", raising=False)
    from app.core.store import init_db

    init_db()
    client = TestClient(app)

    resp = client.get("/api/system/status")

    assert resp.status_code == 200
    data = resp.json()
    assert data["deterministic_workflow_available"] is True
    assert data["agents_sdk_refinement_configured"] is False
    assert data["band_collaboration_configured"] is False
    assert data["eval_case_count"] >= 1
    assert "drug_dose" in data["safety_boundary_categories"]


def test_sample_case_endpoint_creates_closed_loop_demo(tmp_path, monkeypatch):
    monkeypatch.setenv("PERIOP_DB_PATH", str(tmp_path / "test.sqlite"))
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    from app.core.store import init_db

    init_db()
    client = TestClient(app)

    resp = client.post("/api/demo/sample-case")

    assert resp.status_code == 200
    data = resp.json()
    assert data["case"]["title"] == "Sample perioperative assessment case"
    assert data["documents"][0]["filename"] == "sample-preop-ecg.txt"
    assert data["report"]["case_id"] == data["case"]["id"]
    assert data["report"]["ecg_findings"]
    assert data["report"]["lab_findings"]
    assert data["report"]["risk_flags"]
    assert "医生" in data["report"]["safety_notice"]


def test_export_report_markdown_contains_clinical_sections(tmp_path, monkeypatch):
    monkeypatch.setenv("PERIOP_DB_PATH", str(tmp_path / "test.sqlite"))
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    from app.core.store import init_db

    init_db()
    client = TestClient(app)
    sample_resp = client.post("/api/demo/sample-case")
    case_id = sample_resp.json()["case"]["id"]

    resp = client.get(f"/api/cases/{case_id}/report/export.md")

    assert resp.status_code == 200
    assert "text/markdown" in resp.headers["content-type"]
    assert "# Perioperative Anesthesia Assessment Draft" in resp.text
    assert "## Safety Notice" in resp.text
    assert "## ECG Findings" in resp.text
    assert "## Lab Findings" in resp.text
    assert "## Postoperative Surveillance Draft" in resp.text


def test_intraop_event_and_postop_plan_api(tmp_path, monkeypatch):
    monkeypatch.setenv("PERIOP_DB_PATH", str(tmp_path / "test.sqlite"))
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    from app.core.store import init_db

    init_db()
    client = TestClient(app)
    sample_resp = client.post("/api/demo/sample-case")
    case_id = sample_resp.json()["case"]["id"]

    event_resp = client.post(
        f"/api/cases/{case_id}/intraop-events",
        json={
            "event_type": "hypoxemia",
            "severity": "high",
            "description": "PACU 前术中曾出现一过性低氧，需要交接复核。",
            "clinician_action_summary": "已由麻醉医生现场处理并完成交接。",
        },
    )
    assert event_resp.status_code == 200
    event = event_resp.json()
    assert event["event_type"] == "hypoxemia"
    assert event["case_id"] == case_id

    list_resp = client.get(f"/api/cases/{case_id}/intraop-events")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1

    plan_resp = client.get(f"/api/cases/{case_id}/postop-plan")
    assert plan_resp.status_code == 200
    plan = plan_resp.json()
    assert plan["case_id"] == case_id
    assert plan["surveillance_focus"]
    assert any("血气" in item or "胸部影像" in item for item in plan["suggested_checks"])
    assert "不能替代术后医嘱" in plan["safety_notice"]


def test_band_collaboration_trace_meets_minimum_agent_requirement(tmp_path, monkeypatch):
    monkeypatch.setenv("PERIOP_DB_PATH", str(tmp_path / "test.sqlite"))
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("BAND_AGENT_API_KEY", raising=False)
    monkeypatch.delenv("BAND_CHAT_ID", raising=False)
    from app.core.store import init_db

    init_db()
    client = TestClient(app)
    sample_resp = client.post("/api/demo/sample-case")
    case_id = sample_resp.json()["case"]["id"]
    client.post(
        f"/api/cases/{case_id}/intraop-events",
        json={
            "event_type": "arrhythmia",
            "severity": "high",
            "description": "术中出现快速房颤，需要交接复核。",
        },
    )

    resp = client.post(f"/api/cases/{case_id}/band-collaboration")

    assert resp.status_code == 200
    data = resp.json()
    assert data["band_configured"] is False
    assert data["minimum_agent_requirement_met"] is True
    assert len(data["agent_roles"]) >= 3
    assert len(data["collaboration_steps"]) >= 3
    assert data["adapter_mode"] == "local"
    assert len(data["message_receipts"]) == len(data["collaboration_steps"])
    assert all(step["status"] == "local_trace" for step in data["collaboration_steps"])
    assert all(step["directed_message"].startswith(step["to_agent"]) for step in data["collaboration_steps"])
    assert all(receipt["delivered"] is True for receipt in data["message_receipts"])
    assert any("@Periop Safety Reviewer" in step["to_agent"] for step in data["collaboration_steps"])


def test_band_collaboration_markdown_export_contains_agent_handoffs(tmp_path, monkeypatch):
    monkeypatch.setenv("PERIOP_DB_PATH", str(tmp_path / "test.sqlite"))
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("BAND_AGENT_API_KEY", raising=False)
    monkeypatch.delenv("BAND_CHAT_ID", raising=False)
    from app.core.store import init_db

    init_db()
    client = TestClient(app)
    sample_resp = client.post("/api/demo/sample-case")
    case_id = sample_resp.json()["case"]["id"]

    resp = client.get(f"/api/cases/{case_id}/band-collaboration/export.md")

    assert resp.status_code == 200
    assert "text/markdown" in resp.headers["content-type"]
    assert "# Band Collaboration Trace" in resp.text
    assert "@Periop Intake Agent" in resp.text
    assert "@ECG Lab Risk Agent" in resp.text
    assert "@Periop Safety Reviewer" in resp.text
    assert "@Postop Surveillance Agent" in resp.text
    assert "Minimum 3-agent requirement met: `True`" in resp.text
    assert "## Message Receipts" in resp.text
    assert "Adapter mode: `local`" in resp.text
