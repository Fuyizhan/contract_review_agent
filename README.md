# 📄 合同智审：基于 LangGraph 的多 Agent 合同审查系统

面向企业法务与业务人员，提供从合同上传、条款提取、风险与合规双轨审查，到修改建议与 PDF 报告下载的全链路智能审查服务。

## 💡 核心痛点与解决方案

传统合同审查依赖人工，耗时长且容易遗漏霸王条款；而单纯使用大模型审查长文本，存在**上下文长度限制**、**输出格式不稳定（幻觉）**以及**网络异常导致系统崩溃**等痛点。

本项目通过 **LangGraph 多 Agent 编排**架构，结合**规则引擎降级**与**结构化输出校验**，实现了一个高可用、可容错的智能审查工作流。

## 项目架构
```text
contract-review-agent/
├── src/                          # 后端核心代码
│   ├── agents/                   # 多 Agent 业务逻辑层
│   │   ├── schemas.py            # 大模型结构化输出定义 (Pydantic)
│   │   ├── llm_utils.py          # 大模型调用与重试封装 (tenacity)
│   │   ├── chunking.py           # 长文本滑动窗口分块器
│   │   ├── clause_extraction.py  # Agent 1: 条款提取
│   │   ├── risk_identification.py# Agent 2: 风险识别
│   │   ├── compliance_check.py   # Agent 3: 合规检查
│   │   └── suggestion.py         # Agent 4: 修改建议
│   ├── pipeline/                 # LangGraph 编排层
│   │   └── graph.py              # 状态图定义 (含 State 与 Reducer)
│   ├── rules/                    # 规则引擎 (降级兜底机制)
│   │   └── engine.py             # 正则切分与关键词匹配兜底逻辑
│   ├── api/                      # Web 接口层 (FastAPI)
│   │   ├── routers/              # 路由控制器 (auth, review)
│   │   ├── schemas/              # HTTP 请求/响应模型
│   │   ├── auth/                 # JWT 鉴权与密码哈希
│   │   └── main.py               # 应用入口、CORS 与生命周期
│   ├── services/                 # 服务层
│   │   ├── report_service.py     # PDF 报告生成服务
│   │   └── document_parser.py    # PDF/DOCX 文档解析服务
│   ├── db/                       # 数据库基础设施
│   │   ├── models.py             # SQLAlchemy ORM 模型
│   │   ├── session.py            # 异步引擎与依赖注入
│   │   └── crud.py               # 数据访问对象 (DAO)
│   └── config.py                 # 全局配置 (Pydantic Settings)
├── frontend/                     # 前端 React 项目
│   ├── src/
│   │   ├── api/                  # Axios 封装与拦截器
│   │   └── App.jsx               # 主页面 (登录、上传、进度、报告)
│   ├── Dockerfile                # 前端多阶段构建 (Node -> Nginx)
│   └── nginx.conf                # Nginx 反向代理配置
├── .env.example                  # 环境变量模板
├── .dockerignore                 # Docker 构建忽略规则
├── Dockerfile                    # 后端镜像构建文件
├── docker-compose.yml            # 容器编排配置 (DB + 后端 + 前端)
├── requirements.txt              # Python 依赖清单
└── README.md
```

## 🏗️ 系统架构

系统采用前后端分离架构，后端基于 FastAPI 提供异步服务，核心流水线基于 LangGraph 构建有向图。

```text
[前端 React + Vite] 
       ↓ (HTTP/JWT)
[FastAPI 路由层] 
       ↓ (异步后台任务)
[LangGraph 流水线编排]
       ├── 1. 条款提取 Agent (支持超长文本自动分块)
       ├── 2. 风险识别 Agent (并行)
       ├── 3. 合规检查 Agent (并行)
       └── 4. 修改建议 Agent (按优先级排序输出)
       ↓
[规则引擎兜底 (断网/超时自动降级)]
       ↓
[PostgreSQL / SQLite 持久化] 
       ↓ (数据组装)
[PDF 报告生成 (WeasyPrint)] 
```
## 🛠️技术栈

后端：Python 3.11, FastAPI, SQLAlchemy (Async), Pydantic

AI 编排：LangChain, LangGraph, DeepSeek API

数据库：PostgreSQL (生产) / SQLite (本地)

前端：React 18, Vite, Tailwind CSS, Axios

安全与认证：JWT, Bcrypt

文档处理：PyPDF2, python-docx

部署：Docker, Docker Compose, Nginx

## ✨ 核心工程亮点
多 Agent 并行编排与状态汇聚：利用 LangGraph 构建状态图（StateGraph），将风险与合规检查节点并行执行（Parallel Branches），显著缩短审查耗时。通过自定义 Reducer 解决并行节点的状态（Progress）覆盖冲突。

长文本智能分块（Chunking）：针对大模型上下文限制，实现了基于标点和重叠窗口的滑动分块算法（Sliding Window），保证超长合同（如 50 页以上）也能被完整提取和审查。

高可用架构（容错与降级）：

重试机制：引入 tenacity 库，针对大模型 API 实现了指数退避重试。

规则引擎兜底：一旦大模型服务宕机或超时，系统自动降级为基于正则表达式和关键词的本地规则引擎，确保审查任务不中断，并在最终报告中提示“降级警告”。

结构化输出与幻觉抑制：基于 Pydantic 定义强类型 Schema，配合 DeepSeek 的 json_mode 与 Prompt 约束，确保大模型输出 100% 可解析的 JSON 结构，避免下游系统崩溃。

异步后台任务与全链路进度追踪：利用 FastAPI 的 BackgroundTasks 和独立数据库 Session，实现后台流水线的实时进度落库，前端通过轮询实现丝滑的进度条展示。

## 🚀 快速开始
方式一：Docker 一键启动（推荐）
确保本地安装了 Docker 和 Docker Compose。

1.克隆项目并进入目录：

```text
git clone https://github.com/your-username/contract-review-system.git
cd contract-review-system
```
2.配置环境变量（填入你的 DeepSeek API Key）：

```text
cp .env.example .env
# 编辑 .env 文件，填入 LLM_API_KEY
```
3.一键启动所有服务（数据库、后端、前端）：

```text
docker compose up -d --build
```
4.访问系统：

前端页面：http://localhost

后端接口文档：http://localhost:8000/docs (默认账号: admin / 密码: admin123)

## 方式二：本地开发启动
后端：

```text
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
# 确保本地有 PostgreSQL 或修改 .env 为 SQLite
uvicorn src.api.main:app --reload
```
前端：

```text
cd frontend
npm install
npm run dev
```
