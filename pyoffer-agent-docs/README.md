# PyOffer Agent 文档中心

PyOffer Agent 是一个面向 **Python 后端 / AI Agent 应用开发应届生** 的简历优化与模拟面试 Web 应用。

第一版目标是先跑通核心闭环：

1. 用户创建求职项目
2. 上传简历
3. 粘贴岗位 JD
4. AI 分析简历与岗位匹配度
5. 生成 Python 后端 / Agent 方向面试题
6. 进行文本模拟面试
7. 输出结构化面试报告

## 文档目录

- [01-PRD.md](./01-PRD.md): 产品需求文档
- [02-architecture.md](./02-architecture.md): 技术架构设计
- [03-database.md](./03-database.md): 数据库表设计
- [04-api.md](./04-api.md): REST API 接口文档
- [05-agent-design.md](./05-agent-design.md): AI Agent 与 Prompt 设计
- [06-roadmap.md](./06-roadmap.md): 开发路线图与任务拆分
- [07-celery-worker.md](./07-celery-worker.md): Celery 异步任务设计
- [openapi.yaml](./openapi.yaml): OpenAPI 3.1 草案

## 推荐 MVP 技术栈

### 前端

- Next.js
- TypeScript
- Tailwind CSS
- shadcn/ui
- TanStack Query

### 后端

- Python 3.12+
- FastAPI
- SQLAlchemy 2.x
- Alembic
- Pydantic v2
- PostgreSQL
- pgvector
- Redis
- Celery

### AI 与文档处理

- OpenAI-compatible API
- LangGraph 或轻量自研 Agent Orchestrator
- PyMuPDF
- python-docx
- pgvector 向量检索

### 部署

- Docker Compose
- Nginx
- 云服务器 / Railway / Render / Fly.io

## 第一版不要做的功能

- 实时语音面试
- 支付
- 企业端
- 移动 App
- 复杂知识库管理
- 多模型调度平台

这些功能可以在文本面试闭环跑通后再加。
