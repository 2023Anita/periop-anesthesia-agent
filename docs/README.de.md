# periop-anesthesia-agent

**Sprache:** [English](../README.md) | [中文](README.zh-CN.md) | [日本語](README.ja.md) | [한국어](README.ko.md) | [Français](README.fr.md) | Deutsch

Eine klinische KI-Agent-Vorlage mit ärztlicher Prüfung, gebaut mit FastAPI, React, SQLite und dem OpenAI Agents SDK.

![Demo](assets/demo.gif)

## Überblick

Dieses Repository ist ein lokaler Prototyp für die perioperative Anästhesiebewertung. Es wandelt synthetische präoperative Notizen, EKG-Text und Laborhinweise in einen strukturierten Entwurf um, den eine Ärztin oder ein Arzt prüfen, bearbeiten, bestätigen und exportieren kann.

Es ist eine Vorlage für klinische KI-Entwicklung, kein medizinisches Produktivsystem.

## Visueller Überblick

| Klinische KI-Vorlage | Sicherheitsgrenze | Human-in-the-loop-Workflow |
| --- | --- | --- |
| ![Clinical AI Agent Template](assets/generated/clinical-ai-agent-template.png) | ![Safety Boundary](assets/generated/safety-boundary.png) | ![Human-in-the-loop Workflow](assets/generated/human-in-the-loop-workflow.png) |

## Schnellstart

Backend:

```bash
cd "backend"
python3 -m venv ".venv"
source ".venv/bin/activate"
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8010
```

Frontend:

```bash
cd "frontend"
npm install
npm run dev
```

Öffnen Sie `http://127.0.0.1:5173` und klicken Sie auf **Load sample case**.

## Sicherheitsgrenze

Dieser Prototyp erzeugt nur einen Entwurf zur ärztlichen Prüfung. Er liefert keine:

- Entscheidung zur OP-Freigabe;
- Anästhesie- oder Medikamentendosis;
- Notfallanweisung;
- endgültige Entscheidung zu Absetzen, Wechsel oder Bridging von Medikamenten;
- individualisierte medizinische Beratung für Patientinnen oder Patienten.

## Tests

```bash
cd "backend"
".venv/bin/python" -m pytest
```

```bash
cd "frontend"
npm run build
```

## Roadmap

- PDF-Export
- Englische synthetische Fälle
- Strukturierte Sicherheits-Evals
- Agents SDK Tracing-Ansicht
- Docker Compose Start
