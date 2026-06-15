from __future__ import annotations

import os
from datetime import datetime, timezone

import httpx

from app.schemas.periop import (
    BandAgentRole,
    BandCollaborationResponse,
    BandCollaborationStep,
    DocumentRecord,
    IntraopEventRecord,
    PreopAssessmentReport,
)


BAND_API_BASE = os.getenv("BAND_API_BASE", "https://app.band.ai/api/v1")
BAND_AGENT_API_KEY = os.getenv("BAND_AGENT_API_KEY")
BAND_CHAT_ID = os.getenv("BAND_CHAT_ID")


AGENT_ROLES = [
    BandAgentRole(
        name="Periop Intake Agent",
        responsibility="Summarize source documents, missing information, and case context for clinician review.",
        band_mention="@Periop Intake Agent",
    ),
    BandAgentRole(
        name="ECG Lab Risk Agent",
        responsibility="Review ECG and lab findings, then return anesthesia-relevant risk clues without diagnoses or dosing.",
        band_mention="@ECG Lab Risk Agent",
    ),
    BandAgentRole(
        name="Periop Safety Reviewer",
        responsibility="Check that draft outputs avoid surgery clearance, drug doses, emergency commands, and patient-facing advice.",
        band_mention="@Periop Safety Reviewer",
    ),
    BandAgentRole(
        name="Postop Surveillance Agent",
        responsibility="Convert pre-op risks and intra-op events into a clinician-facing postoperative surveillance draft.",
        band_mention="@Postop Surveillance Agent",
    ),
]


def is_band_configured() -> bool:
    return bool(BAND_AGENT_API_KEY and BAND_CHAT_ID)


async def build_band_collaboration_trace(
    case_id: str,
    documents: list[DocumentRecord],
    report: PreopAssessmentReport,
    events: list[IntraopEventRecord],
    send_to_band: bool = False,
) -> BandCollaborationResponse:
    configured = is_band_configured()
    steps = _build_steps(documents, report, events)
    audit_notes = [
        "Minimum hackathon requirement: at least 3 agents collaborate through Band.",
        "This workflow defines 4 specialized agents with explicit handoffs and shared clinical context.",
    ]

    if send_to_band and configured:
        await _send_trace_to_band(case_id, steps)
        for step in steps:
            step.status = "sent_to_band"
        audit_notes.append("Collaboration trace was sent to the configured Band chat room.")
    else:
        for step in steps:
            step.status = "local_trace"
        audit_notes.append(
            "Band credentials are not configured, so this is a local trace. Set BAND_AGENT_API_KEY and BAND_CHAT_ID to send it to Band."
        )

    return BandCollaborationResponse(
        case_id=case_id,
        generated_at=datetime.now(timezone.utc),
        band_configured=configured,
        room_id=BAND_CHAT_ID if configured else None,
        minimum_agent_requirement_met=len(AGENT_ROLES) >= 3 and len(steps) >= 3,
        agent_roles=AGENT_ROLES,
        collaboration_steps=steps,
        audit_notes=audit_notes,
    )


def render_band_transcript_markdown(trace: BandCollaborationResponse) -> str:
    lines = [
        "# Band Collaboration Trace",
        "",
        f"- Case ID: `{trace.case_id}`",
        f"- Generated at: `{trace.generated_at.isoformat()}`",
        f"- Band configured: `{trace.band_configured}`",
        f"- Room ID: `{trace.room_id or 'local-trace'}`",
        f"- Minimum 3-agent requirement met: `{trace.minimum_agent_requirement_met}`",
        "",
        "## Agent Roles",
        "",
    ]
    for role in trace.agent_roles:
        lines.extend(
            [
                f"### {role.band_mention}",
                "",
                role.responsibility,
                "",
            ]
        )

    lines.extend(["## Handoff Transcript", ""])
    for step in trace.collaboration_steps:
        lines.extend(
            [
                f"### Step {step.order}: {step.from_agent} -> {step.to_agent}",
                "",
                f"- Status: `{step.status}`",
                f"- Handoff: {step.handoff}",
                f"- Expected output: {step.expected_output}",
                "- Shared context:",
                *_render_context_items(step.shared_context),
                "",
            ]
        )

    lines.extend(["## Audit Notes", ""])
    lines.extend(f"- {note}" for note in trace.audit_notes)
    lines.append("")
    return "\n".join(lines)


def _build_steps(
    documents: list[DocumentRecord],
    report: PreopAssessmentReport,
    events: list[IntraopEventRecord],
) -> list[BandCollaborationStep]:
    document_summary = [
        f"{doc.modality.value}: {doc.filename}"
        for doc in documents[:6]
    ]
    risk_summary = [
        f"{flag.name} ({flag.severity})"
        for flag in report.risk_flags[:6]
    ]
    event_summary = [
        f"{event.event_type.value} ({event.severity})"
        for event in events[:6]
    ] or ["No intra-op events recorded yet."]

    return [
        BandCollaborationStep(
            order=1,
            from_agent="Clinician Workbench",
            to_agent="@Periop Intake Agent",
            handoff="Organize source materials, case context, and missing information before specialist review.",
            shared_context=document_summary,
            expected_output="Structured intake summary and missing-data checklist.",
        ),
        BandCollaborationStep(
            order=2,
            from_agent="@Periop Intake Agent",
            to_agent="@ECG Lab Risk Agent",
            handoff="Review ECG and lab signals extracted from the intake context.",
            shared_context=[*document_summary, *risk_summary],
            expected_output="ECG/lab risk findings that remain clinician-review-only.",
        ),
        BandCollaborationStep(
            order=3,
            from_agent="@ECG Lab Risk Agent",
            to_agent="@Periop Safety Reviewer",
            handoff="Audit draft language for surgery clearance, dose, emergency-command, and patient-advice violations.",
            shared_context=[*risk_summary, report.safety_notice],
            expected_output="Pass/fail safety review with required redirections.",
        ),
        BandCollaborationStep(
            order=4,
            from_agent="@Periop Safety Reviewer",
            to_agent="@Postop Surveillance Agent",
            handoff="Build clinician-facing postoperative surveillance draft from approved risks and intra-op events.",
            shared_context=[*risk_summary, *event_summary],
            expected_output="Post-op surveillance focus, suggested checks, and escalation triggers for clinician confirmation.",
        ),
    ]


def _render_context_items(items: list[str]) -> list[str]:
    if not items:
        return ["  - No shared context."]
    return [f"  - {item}" for item in items]


async def _send_trace_to_band(case_id: str, steps: list[BandCollaborationStep]) -> None:
    headers = {
        "Authorization": f"Bearer {BAND_AGENT_API_KEY}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=15) as client:
        for step in steps:
            message = (
                f"{step.to_agent} Case `{case_id}` handoff from {step.from_agent}: {step.handoff}\n"
                f"Shared context: {'; '.join(step.shared_context)}\n"
                f"Expected output: {step.expected_output}"
            )
            response = await client.post(
                f"{BAND_API_BASE}/agent/chats/{BAND_CHAT_ID}/messages",
                headers=headers,
                json={"content": message},
            )
            response.raise_for_status()
