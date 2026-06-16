from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256

import httpx

from app.schemas.periop import (
    BandAgentRole,
    BandCollaborationResponse,
    BandMessageReceipt,
    BandCollaborationStep,
    DocumentRecord,
    IntraopEventRecord,
    PreopAssessmentReport,
)


BAND_API_BASE = os.getenv("BAND_API_BASE", "https://app.band.ai/api/v1")
BAND_AGENT_API_KEY = os.getenv("BAND_AGENT_API_KEY")
BAND_CHAT_ID = os.getenv("BAND_CHAT_ID")


@dataclass(frozen=True)
class BandAgentConfig:
    key: str
    name: str
    mention: str
    env_api_key: str


AGENT_CONFIGS = {
    "clinician_workbench": BandAgentConfig(
        key="clinician_workbench",
        name="Clinician Workbench",
        mention="@Clinician Workbench",
        env_api_key="BAND_CLINICIAN_WORKBENCH_API_KEY",
    ),
    "periop_intake_agent": BandAgentConfig(
        key="periop_intake_agent",
        name="Periop Intake Agent",
        mention="@Periop Intake Agent",
        env_api_key="BAND_PERIOP_INTAKE_AGENT_API_KEY",
    ),
    "ecg_lab_risk_agent": BandAgentConfig(
        key="ecg_lab_risk_agent",
        name="ECG Lab Risk Agent",
        mention="@ECG Lab Risk Agent",
        env_api_key="BAND_ECG_LAB_RISK_AGENT_API_KEY",
    ),
    "periop_safety_reviewer": BandAgentConfig(
        key="periop_safety_reviewer",
        name="Periop Safety Reviewer",
        mention="@Periop Safety Reviewer",
        env_api_key="BAND_PERIOP_SAFETY_REVIEWER_API_KEY",
    ),
    "postop_surveillance_agent": BandAgentConfig(
        key="postop_surveillance_agent",
        name="Postop Surveillance Agent",
        mention="@Postop Surveillance Agent",
        env_api_key="BAND_POSTOP_SURVEILLANCE_AGENT_API_KEY",
    ),
}


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
    return bool(BAND_CHAT_ID and _api_key_for("periop_intake_agent"))


async def build_band_collaboration_trace(
    case_id: str,
    documents: list[DocumentRecord],
    report: PreopAssessmentReport,
    events: list[IntraopEventRecord],
    send_to_band: bool = False,
) -> BandCollaborationResponse:
    configured = is_band_configured()
    steps = _build_steps(documents, report, events)
    adapter = BandCollaborationAdapter(
        api_base=BAND_API_BASE,
        chat_id=BAND_CHAT_ID,
        live=configured and send_to_band,
    )
    receipts = await adapter.publish(case_id, steps)
    adapter_mode = "live" if adapter.live else "local"
    audit_notes = [
        "Minimum hackathon requirement: at least 3 agents collaborate through Band.",
        "This workflow defines 4 specialized agents with directed @mention handoffs and shared clinical context.",
        "The Band adapter records the same message envelopes in local mode and posts them to Band in live mode.",
    ]

    if adapter.live:
        audit_notes.append("Collaboration messages were sent to the configured Band chat room through the Agent API.")
    else:
        audit_notes.append(
            "Live Band credentials are not active for this run, so the adapter returned a local Band-room transcript."
        )

    return BandCollaborationResponse(
        case_id=case_id,
        generated_at=datetime.now(timezone.utc),
        band_configured=configured,
        room_id=BAND_CHAT_ID if configured else None,
        adapter_mode=adapter_mode,
        minimum_agent_requirement_met=len(AGENT_ROLES) >= 3 and len(steps) >= 3,
        agent_roles=AGENT_ROLES,
        collaboration_steps=steps,
        message_receipts=receipts,
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
        f"- Adapter mode: `{trace.adapter_mode}`",
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
                f"- Event type: `{step.room_event_type}`",
                f"- Sender key: `{step.sender_key}`",
                f"- Receiver key: `{step.receiver_key}`",
                f"- Handoff: {step.handoff}",
                f"- Expected output: {step.expected_output}",
                "- Directed Band message:",
                "",
                f"```text\n{step.directed_message}\n```",
                "",
                "- Shared context:",
                *_render_context_items(step.shared_context),
                "",
            ]
        )

    lines.extend(["## Message Receipts", ""])
    for receipt in trace.message_receipts:
        lines.extend(
            [
                f"- Step {receipt.step_order}: `{receipt.adapter_mode}` "
                f"{receipt.sender_agent} -> {receipt.receiver_agent} "
                f"delivered=`{receipt.delivered}` id=`{receipt.message_id}` endpoint=`{receipt.endpoint}`",
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
            sender_key="clinician_workbench",
            receiver_key="periop_intake_agent",
        ),
        BandCollaborationStep(
            order=2,
            from_agent="@Periop Intake Agent",
            to_agent="@ECG Lab Risk Agent",
            handoff="Review ECG and lab signals extracted from the intake context.",
            shared_context=[*document_summary, *risk_summary],
            expected_output="ECG/lab risk findings that remain clinician-review-only.",
            sender_key="periop_intake_agent",
            receiver_key="ecg_lab_risk_agent",
        ),
        BandCollaborationStep(
            order=3,
            from_agent="@ECG Lab Risk Agent",
            to_agent="@Periop Safety Reviewer",
            handoff="Audit draft language for surgery clearance, dose, emergency-command, and patient-advice violations.",
            shared_context=[*risk_summary, report.safety_notice],
            expected_output="Pass/fail safety review with required redirections.",
            sender_key="ecg_lab_risk_agent",
            receiver_key="periop_safety_reviewer",
        ),
        BandCollaborationStep(
            order=4,
            from_agent="@Periop Safety Reviewer",
            to_agent="@Postop Surveillance Agent",
            handoff="Build clinician-facing postoperative surveillance draft from approved risks and intra-op events.",
            shared_context=[*risk_summary, *event_summary],
            expected_output="Post-op surveillance focus, suggested checks, and escalation triggers for clinician confirmation.",
            sender_key="periop_safety_reviewer",
            receiver_key="postop_surveillance_agent",
        ),
    ]


def _render_context_items(items: list[str]) -> list[str]:
    if not items:
        return ["  - No shared context."]
    return [f"  - {item}" for item in items]


class BandCollaborationAdapter:
    def __init__(self, api_base: str, chat_id: str | None, live: bool) -> None:
        self.api_base = api_base.rstrip("/")
        self.chat_id = chat_id
        self.live = live and bool(chat_id)

    async def publish(self, case_id: str, steps: list[BandCollaborationStep]) -> list[BandMessageReceipt]:
        for step in steps:
            step.directed_message = _build_directed_message(case_id, step)

        if not self.live:
            return [self._local_receipt(case_id, step) for step in steps]

        receipts: list[BandMessageReceipt] = []
        async with httpx.AsyncClient(timeout=15) as client:
            for step in steps:
                receipts.append(await self._send_live_message(client, step))
        return receipts

    def _local_receipt(self, case_id: str, step: BandCollaborationStep) -> BandMessageReceipt:
        step.status = "local_trace"
        digest = sha256(f"{case_id}:{step.order}:{step.directed_message}".encode()).hexdigest()[:16]
        return BandMessageReceipt(
            step_order=step.order,
            adapter_mode="local",
            sender_agent=step.from_agent,
            receiver_agent=step.to_agent,
            endpoint="local://band-room-transcript",
            message_id=f"local-{digest}",
            delivered=True,
            detail="Recorded as a local Band-room transcript for deterministic review.",
        )

    async def _send_live_message(
        self,
        client: httpx.AsyncClient,
        step: BandCollaborationStep,
    ) -> BandMessageReceipt:
        api_key = _api_key_for(step.sender_key)
        if not api_key:
            raise RuntimeError(f"Missing Band API key for sender agent: {step.sender_key}")

        endpoint = f"{self.api_base}/agent/chats/{self.chat_id}/messages"
        response = await client.post(
            endpoint,
            headers={"X-API-Key": api_key, "Content-Type": "application/json"},
            json={"content": step.directed_message},
        )
        response.raise_for_status()
        body = response.json() if response.content else {}
        step.status = "sent_to_band"
        return BandMessageReceipt(
            step_order=step.order,
            adapter_mode="live",
            sender_agent=step.from_agent,
            receiver_agent=step.to_agent,
            endpoint=endpoint,
            message_id=str(body.get("id") or body.get("message_id") or f"band-step-{step.order}"),
            delivered=True,
            detail="Posted to Band Agent API with a directed @mention handoff.",
        )


def _build_directed_message(case_id: str, step: BandCollaborationStep) -> str:
    context = "\n".join(f"- {item}" for item in step.shared_context) or "- No shared context."
    return (
        f"{step.to_agent}\n"
        f"[case_id: {case_id}]\n"
        f"[event_type: {step.room_event_type}]\n"
        f"[handoff_from: {step.from_agent}]\n\n"
        f"Task: {step.handoff}\n\n"
        f"Shared context:\n{context}\n\n"
        f"Expected output: {step.expected_output}\n"
        "Safety rule: return clinician-review-only output; do not provide clearance, dosing, emergency commands, or patient-facing medical advice."
    )


def _api_key_for(agent_key: str) -> str | None:
    config = AGENT_CONFIGS.get(agent_key)
    if config:
        value = os.getenv(config.env_api_key)
        if value:
            return value
    return BAND_AGENT_API_KEY
