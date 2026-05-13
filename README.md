# 麻醉围术期 Agent 本地原型

本项目是第一阶段原型：本地 Web 医生工作台 + FastAPI 后端 + OpenAI Agents SDK 工作流骨架。

## 当前能力

- 创建本地病例 session
- 上传/输入术前资料
- 抽取 PDF、Word、TXT 文本
- 图片资料预留 OCR 接口，若本机安装 Tesseract 则自动尝试 OCR
- 心电图报告/OCR 文本级结构化识别
- 生成麻醉术前评估草案
- 医生编辑并确认报告
- 本地 SQLite 保存病例、资料和报告

## 安全边界

这是麻醉医生辅助工具原型，不是自动诊断或治疗系统。所有输出都必须由麻醉医生复核确认。

第一阶段不提供：

- 自动决定是否可以手术
- 麻醉药物剂量
- 抢救处置指令
- 直接面向患者的诊疗建议
- 12 导联心电图波形级自动诊断

## 启动后端

```bash
cd "backend"
python3 -m venv ".venv"
source ".venv/bin/activate"
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8010
```

可选：配置真实 OpenAI Agents SDK 调用。

```bash
export OPENAI_API_KEY="sk-..."
```

没有 API key 时，系统会使用本地确定性 workflow，便于先验证闭环。

## 启动前端

```bash
cd "frontend"
npm install
npm run dev
```

前端默认请求 `http://127.0.0.1:8010`。

## 本地测试

```bash
cd "backend"
pytest
```

