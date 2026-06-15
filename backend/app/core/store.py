from __future__ import annotations

import json
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.schemas.periop import (
    CaseSummary,
    ClinicianReviewUpdate,
    DocumentModality,
    DocumentRecord,
    IntraopEventCreate,
    IntraopEventRecord,
    IntraopEventType,
    PreopAssessmentReport,
)


ROOT_DIR = Path(__file__).resolve().parents[3]
DEFAULT_DB_PATH = ROOT_DIR / "data" / "periop_agent.sqlite"


def _db_path() -> Path:
    return Path(os.getenv("PERIOP_DB_PATH", str(DEFAULT_DB_PATH)))


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _connect() -> sqlite3.Connection:
    db_path = _db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS cases (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                case_id TEXT NOT NULL,
                filename TEXT NOT NULL,
                modality TEXT NOT NULL,
                extracted_text TEXT NOT NULL,
                extraction_notes TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(case_id) REFERENCES cases(id)
            );

            CREATE TABLE IF NOT EXISTS reports (
                case_id TEXT PRIMARY KEY,
                report_json TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(case_id) REFERENCES cases(id)
            );

            CREATE TABLE IF NOT EXISTS intraop_events (
                id TEXT PRIMARY KEY,
                case_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                description TEXT NOT NULL,
                observed_at TEXT NOT NULL,
                clinician_action_summary TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(case_id) REFERENCES cases(id)
            );
            """
        )


def create_case(title: str) -> CaseSummary:
    case_id = str(uuid.uuid4())
    now = _now()
    with _connect() as conn:
        conn.execute(
            "INSERT INTO cases (id, title, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
            (case_id, title, "draft", now, now),
        )
    return get_case(case_id)


def list_cases() -> list[CaseSummary]:
    with _connect() as conn:
        rows = conn.execute("SELECT * FROM cases ORDER BY updated_at DESC").fetchall()
    return [_case_from_row(row) for row in rows]


def get_case(case_id: str) -> CaseSummary:
    with _connect() as conn:
        row = conn.execute("SELECT * FROM cases WHERE id = ?", (case_id,)).fetchone()
    if row is None:
        raise KeyError(f"Case not found: {case_id}")
    return _case_from_row(row)


def add_document(
    case_id: str,
    filename: str,
    modality: DocumentModality,
    extracted_text: str,
    extraction_notes: list[str],
) -> DocumentRecord:
    get_case(case_id)
    doc_id = str(uuid.uuid4())
    now = _now()
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO documents
            (id, case_id, filename, modality, extracted_text, extraction_notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                doc_id,
                case_id,
                filename,
                modality.value,
                extracted_text,
                json.dumps(extraction_notes, ensure_ascii=False),
                now,
            ),
        )
        conn.execute("UPDATE cases SET updated_at = ? WHERE id = ?", (now, case_id))
    return get_document(doc_id)


def get_document(doc_id: str) -> DocumentRecord:
    with _connect() as conn:
        row = conn.execute("SELECT * FROM documents WHERE id = ?", (doc_id,)).fetchone()
    if row is None:
        raise KeyError(f"Document not found: {doc_id}")
    return _document_from_row(row)


def list_documents(case_id: str) -> list[DocumentRecord]:
    get_case(case_id)
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM documents WHERE case_id = ? ORDER BY created_at ASC",
            (case_id,),
        ).fetchall()
    return [_document_from_row(row) for row in rows]


def save_report(report: PreopAssessmentReport) -> PreopAssessmentReport:
    now = _now()
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO reports (case_id, report_json, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(case_id) DO UPDATE SET
                report_json = excluded.report_json,
                updated_at = excluded.updated_at
            """,
            (report.case_id, report.model_dump_json(), now),
        )
        conn.execute("UPDATE cases SET status = ?, updated_at = ? WHERE id = ?", ("assessed", now, report.case_id))
    return report


def get_report(case_id: str) -> PreopAssessmentReport:
    with _connect() as conn:
        row = conn.execute("SELECT report_json FROM reports WHERE case_id = ?", (case_id,)).fetchone()
    if row is None:
        raise KeyError(f"Report not found: {case_id}")
    return PreopAssessmentReport.model_validate_json(row["report_json"])


def update_clinician_review(case_id: str, update: ClinicianReviewUpdate) -> PreopAssessmentReport:
    report = get_report(case_id)
    report.clinician_notes = update.clinician_notes
    report.review_status = update.review_status
    now = _now()
    with _connect() as conn:
        conn.execute(
            """
            UPDATE reports SET report_json = ?, updated_at = ? WHERE case_id = ?
            """,
            (report.model_dump_json(), now, case_id),
        )
        conn.execute(
            "UPDATE cases SET status = ?, updated_at = ? WHERE id = ?",
            (update.review_status.value, now, case_id),
        )
    return report


def add_intraop_event(case_id: str, payload: IntraopEventCreate) -> IntraopEventRecord:
    get_case(case_id)
    event_id = str(uuid.uuid4())
    now = _now()
    observed_at = (payload.observed_at or datetime.now(timezone.utc)).isoformat()
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO intraop_events
            (id, case_id, event_type, severity, description, observed_at, clinician_action_summary, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event_id,
                case_id,
                payload.event_type.value,
                payload.severity,
                payload.description,
                observed_at,
                payload.clinician_action_summary,
                now,
            ),
        )
        conn.execute("UPDATE cases SET status = ?, updated_at = ? WHERE id = ?", ("intraop_event_logged", now, case_id))
    return get_intraop_event(event_id)


def get_intraop_event(event_id: str) -> IntraopEventRecord:
    with _connect() as conn:
        row = conn.execute("SELECT * FROM intraop_events WHERE id = ?", (event_id,)).fetchone()
    if row is None:
        raise KeyError(f"Intraop event not found: {event_id}")
    return _intraop_event_from_row(row)


def list_intraop_events(case_id: str) -> list[IntraopEventRecord]:
    get_case(case_id)
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM intraop_events WHERE case_id = ? ORDER BY observed_at ASC, created_at ASC",
            (case_id,),
        ).fetchall()
    return [_intraop_event_from_row(row) for row in rows]


def _case_from_row(row: sqlite3.Row) -> CaseSummary:
    return CaseSummary(
        id=row["id"],
        title=row["title"],
        status=row["status"],
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


def _document_from_row(row: sqlite3.Row) -> DocumentRecord:
    notes: Any = json.loads(row["extraction_notes"])
    return DocumentRecord(
        id=row["id"],
        case_id=row["case_id"],
        filename=row["filename"],
        modality=DocumentModality(row["modality"]),
        extracted_text=row["extracted_text"],
        extraction_notes=notes if isinstance(notes, list) else [],
        created_at=datetime.fromisoformat(row["created_at"]),
    )


def _intraop_event_from_row(row: sqlite3.Row) -> IntraopEventRecord:
    return IntraopEventRecord(
        id=row["id"],
        case_id=row["case_id"],
        event_type=IntraopEventType(row["event_type"]),
        severity=row["severity"],
        description=row["description"],
        observed_at=datetime.fromisoformat(row["observed_at"]),
        clinician_action_summary=row["clinician_action_summary"],
        created_at=datetime.fromisoformat(row["created_at"]),
    )
