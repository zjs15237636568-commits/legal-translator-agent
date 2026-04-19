# 涉外法务翻译与合规风控工具

一个**本地运行**（前后端均本地启动）、支持 **OpenAI / Claude / DeepSeek** 的 AI 协议翻译与风险审查工具。

![stack](https://img.shields.io/badge/backend-FastAPI-009688) ![stack](https://img.shields.io/badge/frontend-Vue3-42b883) ![stack](https://img.shields.io/badge/model-OpenAI%20%7C%20Claude%20%7C%20DeepSeek-blue) ![license](https://img.shields.io/badge/license-MIT-green)

> ⚠️ 本工具面向**本地单机使用**场景。翻译与风险扫描会调用公网大模型 API，敏感合同请自行评估数据出境合规性。

## 功能特性

- **沉浸式双栏工作台**：原文 / 译文 段落级同步滚动，流式呈现
- **多供应商 LLM 路由**：OpenAI / Claude / DeepSeek 运行时切换
- **术语库**：专有名词强制翻译，前端可视化管理
- **风险审查**：LLM 自动识别 🔴 法律风险 / 🟡 业务提示
- **Q&A with Citations**：问答带 `[Clause X.X]` 引用，点击跳转原文
- **版本比对**：语义对齐 + AI 业务影响总结
- **断点续翻**：失败段可单独重试
- **中英对照 Word 导出**（含风险批注）

## 目录结构

```
.
├── backend/         # Python FastAPI 后端
├── frontend/        # Vue 3 + Vite 前端
├── docs/            # 技术方案与任务拆解
└── start.sh         # 一键启动脚本（macOS/Linux）
```

## 快速开始

### 先决条件

- Python 3.10+
- Node.js 18+
- npm / yarn / pnpm

### Clone 项目

```bash
git clone https://github.com/<your-name>/legal-translator-agent.git
cd legal-translator-agent
```

### 一键启动（macOS/Linux）

```bash
chmod +x start.sh backend/run.sh
./start.sh
```

脚本会并行启动：
- 后端 `http://127.0.0.1:8765`
- 前端 `http://127.0.0.1:5173`

### 手动启动

**后端：**
```bash
cd backend
./run.sh
# 等价：
# python -m venv .venv && source .venv/bin/activate
# pip install -r requirements.txt
# uvicorn app.main:app --reload --port 8765
```

**前端：**
```bash
cd frontend
npm install
npm run dev
```

打开 `http://127.0.0.1:5173` 。

### 首次配置

1. 打开设置页面（`/settings`）
2. 选择要使用的模型供应商（OpenAI / Claude / DeepSeek）
3. 填写对应的 `API Key`、`Model`、（可选 `Base URL`）
4. 保存

> API Key 以 AES-GCM 加密存储于 `backend/data/config.enc`，主密钥在 `backend/data/.master.key`。

## 使用流程

1. **历史页** → 上传 `.docx` / `.pdf`（≤20MB）
2. 自动进入 **工作台**，开始流式翻译
3. 翻译完成后，点击 **风险扫描** 生成风险卡
4. 右下角 **Chat** 提问，回答带条款引用
5. **导出 Word** 得到中英对照 + 风险批注
6. 在 **术语库** 维护专有名词
7. 在 **版本比对** 选两个项目进行差异分析

## 关键决策

| 项 | 决策 |
|---|---|
| 模型 | 公网 OpenAI/Claude/DeepSeek，可切换 |
| 文件存储 | **不落盘**，内存处理 |
| 历史/术语 | SQLite / `glossary.json` |
| 分段策略 | Clause/Section → 段落 → Token，含 overlap |
| 段落对齐 | 段落级 `data-anchor-id` 锚点 |
| 风险引擎 | MVP 纯 LLM，无规则库 |
| 术语匹配 | 全词匹配，大小写不敏感，仅限专有名词 |
| 并发 | 段落并发 = 3 |
| 单文件上限 | 20MB |
| 鉴权 | 本地单用户，无鉴权 |

## Windows 用户

`start.sh` 为 Bash 脚本，Windows 请分别启动：

```powershell
# 终端 1 - 后端
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8765

# 终端 2 - 前端
cd frontend
npm install
npm run dev
```

## 文档

- [技术方案](docs/01-技术方案.md)
- [任务拆解](docs/02-任务拆解.md)
- [贡献指南](CONTRIBUTING.md)

## 贡献

欢迎 PR！请先阅读 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 免责声明

- 本工具生成的翻译与风险提示**仅供参考**，不构成法律意见
- 正式商业合同请由具备资质的执业律师审核后使用
- 使用本工具上传文件至大模型 API 所产生的数据合规责任由使用者自行承担

## 许可证

[MIT](LICENSE) © 2026 Legal Translator Agent Contributors
