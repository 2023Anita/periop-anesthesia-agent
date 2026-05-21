# periop-anesthesia-agent

**语言：** [English](../README.md) | 中文 | [日本語](README.ja.md) | [한국어](README.ko.md) | [Français](README.fr.md) | [Deutsch](README.de.md)

一个由医生复核优先的临床 AI Agent 工程模板，使用 FastAPI、React、SQLite 和 OpenAI Agents SDK 构建。

![Demo](assets/demo.gif)

## 项目定位

本项目是围术期麻醉评估的本地原型：把合成术前资料、心电图文本和化验线索整理成结构化草案，由医生编辑、确认并导出。

它是临床 AI 开发模板，不是生产级医疗器械。

## 视觉概览

| 临床 AI 模板 | 安全边界 | 人机协作流程 |
| --- | --- | --- |
| ![Clinical AI Agent Template](assets/generated/clinical-ai-agent-template.png) | ![Safety Boundary](assets/generated/safety-boundary.png) | ![Human-in-the-loop Workflow](assets/generated/human-in-the-loop-workflow.png) |

## 快速启动

启动后端：

```bash
cd "backend"
python3 -m venv ".venv"
source ".venv/bin/activate"
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8010
```

启动前端：

```bash
cd "frontend"
npm install
npm run dev
```

打开 `http://127.0.0.1:5173`，点击 **Load sample case** 生成合成示例报告。

## 安全边界

本项目只生成医生复核用草案，不提供：

- 是否可以手术的结论
- 麻醉药物或治疗药物剂量
- 抢救处置指令
- 围术期停药、换药、桥接决策
- 面向患者的个体化诊疗建议

所有输出都必须由医生结合原始资料和患者实际情况复核确认。

## 测试

```bash
cd "backend"
".venv/bin/python" -m pytest
```

```bash
cd "frontend"
npm run build
```

## 路线图

- PDF 导出
- 英文合成病例样例
- 结构化安全评测集
- Agents SDK tracing 视图
- Docker Compose 一键启动
