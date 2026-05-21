# periop-anesthesia-agent

**言語:** [English](../README.md) | [中文](README.zh-CN.md) | 日本語 | [한국어](README.ko.md) | [Français](README.fr.md) | [Deutsch](README.de.md)

FastAPI、React、SQLite、OpenAI Agents SDKで構築された、医師レビュー前提の臨床AIエージェントテンプレートです。

![Demo](assets/demo.gif)

## 概要

このリポジトリは、周術期麻酔評価のローカルプロトタイプです。合成された術前記録、心電図テキスト、検査データを構造化されたドラフトに変換し、医師が確認、編集、エクスポートできます。

これは臨床AI開発者向けのテンプレートであり、本番医療機器ではありません。

## ビジュアル概要

| 臨床AIテンプレート | 安全境界 | ヒューマン・イン・ザ・ループ |
| --- | --- | --- |
| ![Clinical AI Agent Template](assets/generated/clinical-ai-agent-template.png) | ![Safety Boundary](assets/generated/safety-boundary.png) | ![Human-in-the-loop Workflow](assets/generated/human-in-the-loop-workflow.png) |

## クイックスタート

バックエンド：

```bash
cd "backend"
python3 -m venv ".venv"
source ".venv/bin/activate"
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8010
```

フロントエンド：

```bash
cd "frontend"
npm install
npm run dev
```

`http://127.0.0.1:5173` を開き、**Load sample case** をクリックします。

## 安全境界

このプロトタイプは医師レビュー用のドラフトのみを生成します。以下は行いません。

- 手術可否の判断
- 麻酔薬または治療薬の投与量提示
- 救急処置指示
- 薬剤中止・変更・ブリッジングの最終判断
- 患者向けの個別医療助言

## テスト

```bash
cd "backend"
".venv/bin/python" -m pytest
```

```bash
cd "frontend"
npm run build
```

## ロードマップ

- PDFエクスポート
- 英語の合成症例
- 安全評価ケース
- Agents SDK tracingビュー
- Docker Composeによる起動
