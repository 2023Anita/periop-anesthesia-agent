# periop-anesthesia-agent

**语言：** [English](../README.md) | 中文 | [日本語](README.ja.md) | [한국어](README.ko.md) | [Français](README.fr.md) | [Deutsch](README.de.md)

一个由医生复核优先的临床 AI Agent 工程模板，使用 FastAPI、React、SQLite 和 OpenAI Agents SDK 构建。

![Demo](assets/demo.gif)

## 项目定位

**一句话：这是一个“医生复核优先”的本地临床 AI Agent 模板，用围术期麻醉评估作为真实场景，演示如何把零散医疗资料整理成可审阅、可追踪、可导出的结构化草案。**

它不是想做一个替代医生的“自动诊断系统”，而是回答一个更工程化的问题：

> 如果我们要把 AI 放进真实临床工作流，怎样才能让它先做资料整理、风险线索提取和缺失信息提示，同时把最终判断牢牢留给医生？

### 它解决的具体问题

围术期麻醉评估通常不是一个单一问答任务，而是一组碎片化资料的整合工作：

| 临床资料 | 原始状态 | 本项目做什么 |
| --- | --- | --- |
| 术前病历 | 病史、用药、过敏史散落在文本里 | 抽取患者背景、既往史、用药线索 |
| 心电图报告 | 结论文字与关键参数混在一起 | 结构化识别心率、节律、QTc、ST-T 等线索 |
| 化验片段 | Hb、肌酐、电解质等指标分散出现 | 提取关键化验并提示麻醉相关风险 |
| 医生复核 | 需要把 AI 输出改成可信草案 | 提供备注、确认和 Markdown 导出入口 |

### 工作流

```text
合成术前资料
  -> 本地确定性抽取
  -> ECG / 化验 / 风险线索工具
  -> 可选 OpenAI Agents SDK 复核
  -> 医生审阅、编辑、确认、导出
```

这个顺序很重要：项目先保证**本地可运行、规则可测试、安全边界可验证**，再把大模型放在“复核和表达优化”层，而不是让模型直接做临床决策。

### 它适合谁

- 想学习 OpenAI Agents SDK 如何落到真实业务场景的开发者
- 想做医疗/临床 AI 原型，但又担心安全边界失控的人
- 想参考 FastAPI + React + SQLite 本地 AI 工作台结构的人
- 想把“human-in-the-loop”从口号变成界面和测试的人

### 它不是什么

- 不是生产级医疗器械
- 不是自动诊断系统
- 不是麻醉方案生成器
- 不是能否手术的自动裁决工具
- 不包含真实患者数据

### 为什么这个项目值得看

很多 AI medical demo 只展示“模型会回答”，但真实临床工具更难的是这些部分：

- 如何处理不完整、混乱、来源不同的资料
- 如何让没有 API key 的用户也能跑通 demo
- 如何把医生确认做成产品流程，而不是 README 里一句免责声明
- 如何把安全边界写成代码测试和 UI 行为
- 如何把本地原型包装成可 fork、可改造、可教学的工程模板

所以，这个仓库的核心价值不是“AI 给出一个医学答案”，而是展示一个更稳妥的临床 AI 工程骨架：**AI 做资料整理和草案生成，医生保留判断权，所有输出都可复核。**

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
