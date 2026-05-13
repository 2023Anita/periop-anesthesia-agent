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
            "text": "患者高血压。心电图：窦性心律，心率 70 次/分，QTc: 460 ms。",
        },
    )
    assert doc_resp.status_code == 200

    analyze_resp = client.post(f"/api/cases/{case_id}/analyze/preop")
    assert analyze_resp.status_code == 200
    report = analyze_resp.json()
    assert report["case_id"] == case_id
    assert report["ecg_findings"]

