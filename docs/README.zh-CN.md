# 麻醉围术期 Agent 本地原型

这是一个面向临床 AI 开发者的本地工程模板：用 FastAPI、React、SQLite 和 OpenAI Agents SDK 搭建一个“医生复核优先”的围术期麻醉评估 Agent。

它不是临床可直接使用的医疗器械，也不替代麻醉医生、心电图医生或其他临床医生判断。

## 当前能力

- 创建本地病例 session
- 上传或手动输入术前资料
- 抽取 PDF、Word、TXT 文本
- 图片资料预留 OCR 接口，本机安装 Tesseract 时会自动尝试 OCR
- 对心电图报告/OCR 文本做结构化识别
- 识别关键化验线索
- 生成麻醉术前评估草案
- 医生编辑备注并保存确认状态
- Markdown 导出报告
- 本地 SQLite 保存病例、资料和报告
- 无 `OPENAI_API_KEY` 时使用本地确定性 workflow
- 有 `OPENAI_API_KEY` 时可调用 OpenAI Agents SDK 做结构化复核

## 安全边界

本项目只生成麻醉医生复核用草案，不提供：

- 自动决定是否可以手术
- 麻醉药物或抢救药物剂量
- 抢救处置指令
- 围术期停药、换药、桥接等最终决策
- 面向患者的个体化诊疗建议
- 12 导联心电图波形级自动诊断

所有输出都必须由麻醉医生结合原始资料和患者实际情况复核确认。

## 本地启动

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

打开 `http://127.0.0.1:5173`，点击 **Load sample case**，即可加载合成示例病例并生成评估草案。

## 测试

```bash
cd "backend"
".venv/bin/python" -m pytest
```

前端构建：

```bash
cd "frontend"
npm run build
```

## 适合贡献的方向

- 更好的临床 AI 安全交互设计
- 更多合成病例样例
- 安全边界测试
- README、教程和架构图优化
- 小而清晰的前端体验改进

请保持医学声明保守：这个项目是本地原型和工程模板，不是生产级医疗系统。
