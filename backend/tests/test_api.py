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
