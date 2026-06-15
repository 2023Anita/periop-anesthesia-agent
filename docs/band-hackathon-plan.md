# Band of Agents Hackathon Plan

## Submission Positioning

Project title:

```text
Periop Band: Multi-Agent Perioperative Safety Coordination
```

Short description:

```text
A doctor-in-the-loop multi-agent system where perioperative clinical agents coordinate through a Band-ready collaboration layer to structure pre-op data, review ECG/labs, track intra-op events, and draft post-op surveillance plans with safety guardrails.
```

Recommended track:

```text
Track 3: Regulated & High-Stakes Workflows
```

## Why This Fits

The hackathon asks for practical enterprise workflows where multiple agents coordinate, share context, and hand off tasks. Perioperative anesthesia assessment is a high-stakes workflow with natural cross-role collaboration:

- intake and source-document organization;
- ECG and lab risk review;
- safety boundary review;
- intraoperative event handoff;
- postoperative surveillance planning;
- clinician confirmation.

The app keeps the clinician as the final reviewer and blocks surgery clearance, individualized dosing, emergency commands, medication decisions, and patient-facing advice.

## Band Collaboration Layer

The project defines four Band-facing agent roles:

| Agent | Band mention | Responsibility |
| --- | --- | --- |
| Periop Intake Agent | `@Periop Intake Agent` | Summarize source documents, case context, and missing information. |
| ECG Lab Risk Agent | `@ECG Lab Risk Agent` | Review ECG and lab findings for anesthesia-relevant risk clues. |
| Periop Safety Reviewer | `@Periop Safety Reviewer` | Audit output for surgery clearance, dosing, emergency commands, and patient advice. |
| Postop Surveillance Agent | `@Postop Surveillance Agent` | Convert pre-op risks and intra-op events into a postoperative surveillance draft. |

The local backend exposes:

```text
POST /api/cases/{case_id}/band-collaboration
GET /api/cases/{case_id}/band-collaboration/export.md
```

Without Band credentials, this endpoint returns a local collaboration trace for demo and testing. With these environment variables configured, the backend sends handoff messages to the configured Band chat room:

```bash
BAND_API_BASE=https://app.band.ai/api/v1
BAND_AGENT_API_KEY=...
BAND_CHAT_ID=...
```

The repository includes `band-agent-config.example.yaml` as the required external-agent registration checklist. Copy it to `agent_config.yaml`, fill the four Band agent UUIDs and API keys, and keep the real file out of Git.

Live verification:

```bash
./scripts/check-band-live.sh
```

The script checks that four external-agent entries exist, verifies required environment variables, creates a synthetic case, and sends the Band collaboration trace to the configured chat room.

## Demo Story

Use the elderly orthopedic critical-care sample:

1. Open the local workbench.
2. Create or load an elderly hip-fracture case.
3. Add pre-op note, ECG, labs, and imaging/cardiac context.
4. Generate the pre-op assessment draft.
5. Show ECG and lab findings, high-risk flags, missing information, and safety notice.
6. Add an intraoperative event such as hypotension with rapid atrial fibrillation.
7. Generate the postoperative surveillance draft.
8. Open the Band collaboration trace panel.
9. Export the Band transcript Markdown as submission evidence.
10. Explain the agent handoffs:
   - clinician workbench to intake;
   - intake to ECG/lab;
   - ECG/lab to safety reviewer;
   - safety reviewer to postop surveillance.
11. Save clinician confirmation to show human-in-the-loop closure.

## Three-Minute Video Script

0:00-0:25 Problem:

```text
Perioperative teams handle messy documents, ECGs, labs, and intra-op events under time pressure. The risk is not just missing data, but unsafe automation. This project keeps AI inside a clinician-reviewed workflow.
```

0:25-1:10 System:

```text
The app ingests pre-op notes, ECG text, labs, and imaging summaries. A deterministic workflow creates a safe baseline draft, while optional OpenAI Agents SDK refinement keeps the same structured schema.
```

1:10-2:10 Band collaboration:

```text
The Band-ready layer turns the workflow into explicit multi-agent collaboration. Intake, ECG/lab, safety, and postoperative surveillance agents share context and hand off work through a trace designed for Band chat-room coordination.
```

2:10-2:45 Safety and business value:

```text
The app blocks surgery clearance, drug doses, emergency commands, medication decisions, and patient-facing advice. The value is faster preparation, clearer handoff, and safer review for regulated clinical operations.
```

2:45-3:00 Close:

```text
Periop Band shows what enterprise multi-agent collaboration can look like in high-stakes care: role-specific agents, visible handoffs, auditable state, and clinician control.
```

## Submission Checklist

- Public GitHub repository.
- MIT-compatible license.
- Hosted demo URL.
- Cover image.
- Video presentation.
- Slide presentation.
- README section explaining Band's role.
- Exported Band collaboration transcript Markdown.
- Demo case with no real patient data.
- Local verification passing:

```bash
./scripts/verify-local.sh
```

## Remaining Before Final Submission

- Register the four external agents in Band.
- Create a Band chat room for the demo.
- Add the registered agents as participants.
- Copy `band-agent-config.example.yaml` to `agent_config.yaml` and fill the four agent credentials locally.
- Set `BAND_AGENT_API_KEY` and `BAND_CHAT_ID` locally or in the demo environment.
- Run the Band collaboration trace against the real room.
- Record the video with the Band room visible enough to prove collaboration.
