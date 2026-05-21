# periop-anesthesia-agent

**언어:** [English](../README.md) | [中文](README.zh-CN.md) | [日本語](README.ja.md) | 한국어 | [Français](README.fr.md) | [Deutsch](README.de.md)

FastAPI, React, SQLite, OpenAI Agents SDK로 만든 의사 검토 중심 임상 AI 에이전트 템플릿입니다.

![Demo](assets/demo.gif)

## 개요

이 저장소는 수술 전 마취 평가를 위한 로컬 프로토타입입니다. 합성된 수술 전 기록, 심전도 텍스트, 검사 단서를 구조화된 초안으로 바꾸고, 의사가 검토, 수정, 확인, 내보내기할 수 있게 합니다.

이 프로젝트는 임상 AI 개발자를 위한 템플릿이며, 실제 의료기기가 아닙니다.

## 시각적 개요

| 임상 AI 템플릿 | 안전 경계 | 사람 검토 워크플로 |
| --- | --- | --- |
| ![Clinical AI Agent Template](assets/generated/clinical-ai-agent-template.png) | ![Safety Boundary](assets/generated/safety-boundary.png) | ![Human-in-the-loop Workflow](assets/generated/human-in-the-loop-workflow.png) |

## 빠른 시작

백엔드:

```bash
cd "backend"
python3 -m venv ".venv"
source ".venv/bin/activate"
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8010
```

프론트엔드:

```bash
cd "frontend"
npm install
npm run dev
```

`http://127.0.0.1:5173` 을 열고 **Load sample case** 를 클릭하세요.

## 안전 경계

이 프로토타입은 의사 검토용 초안만 생성합니다. 다음을 수행하지 않습니다.

- 수술 가능 여부 판단
- 마취제 또는 치료제 용량 제시
- 응급 처치 지시
- 약물 중단, 변경, 브리징 최종 결정
- 환자 대상 개인화 의료 조언

## 테스트

```bash
cd "backend"
".venv/bin/python" -m pytest
```

```bash
cd "frontend"
npm run build
```

## 로드맵

- PDF 내보내기
- 영어 합성 증례
- 구조화된 안전 평가
- Agents SDK tracing 화면
- Docker Compose 실행
