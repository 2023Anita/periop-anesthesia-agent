# periop-anesthesia-agent

**Langue :** [English](../README.md) | [中文](README.zh-CN.md) | [日本語](README.ja.md) | [한국어](README.ko.md) | Français | [Deutsch](README.de.md)

Un modèle d’agent IA clinique revu par un médecin, construit avec FastAPI, React, SQLite et l’OpenAI Agents SDK.

![Demo](assets/demo.gif)

## Présentation

Ce dépôt est un prototype local pour l’évaluation anesthésique périopératoire. Il transforme des notes préopératoires synthétiques, du texte ECG et des indices biologiques en brouillon structuré que le clinicien peut relire, modifier, confirmer et exporter.

Il s’agit d’un modèle d’ingénierie pour l’IA clinique, pas d’un dispositif médical de production.

## Vue visuelle

| Modèle d’IA clinique | Limite de sécurité | Workflow avec revue humaine |
| --- | --- | --- |
| ![Clinical AI Agent Template](assets/generated/clinical-ai-agent-template.png) | ![Safety Boundary](assets/generated/safety-boundary.png) | ![Human-in-the-loop Workflow](assets/generated/human-in-the-loop-workflow.png) |

## Démarrage rapide

Backend :

```bash
cd "backend"
python3 -m venv ".venv"
source ".venv/bin/activate"
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8010
```

Frontend :

```bash
cd "frontend"
npm install
npm run dev
```

Ouvrez `http://127.0.0.1:5173`, puis cliquez sur **Load sample case**.

## Limites de sécurité

Ce prototype génère uniquement un brouillon à relire par un clinicien. Il ne fournit pas :

- de décision d’aptitude opératoire ;
- de dose d’anesthésique ou de médicament ;
- d’instructions d’urgence ;
- de décision finale d’arrêt, changement ou relais de traitement ;
- de conseil médical individualisé destiné au patient.

## Tests

```bash
cd "backend"
".venv/bin/python" -m pytest
```

```bash
cd "frontend"
npm run build
```

## Feuille de route

- Export PDF
- Cas synthétiques en anglais
- Évaluations de sécurité structurées
- Vue de tracing Agents SDK
- Démarrage Docker Compose
