# 02. 技术架构设计

## 1. 总体架构

```text
Browser
  |
  | HTTPS / REST API
  v
Next.js Frontend
  |
  | REST API
  v
FastAPI Backend
  |
  |-- Auth Service
  |-- Project Service
  |-- Resume Service
  |-- JD Service
  |-- Match Service
  |-- Question Service
  |-- Question Bank Service
  |-- Knowledge Base Service
  |-- Interview Service
  |-- Report Service
  |
  v
AI Orchestrator
  |
  |-- ResumeAgent
  |-- JDAnalyzerAgent
  |-- MatchAgent
  |-- QuestionGeneratorAgent
  |-- KnowledgeRetriever
  |-- InterviewerAgent
  |-- EvaluatorAgent
  |
  v
PostgreSQL + pgvector
Redis
Object Storage
LLM Provider
```

耗时任务通过 Celery Worker 执行，避免 API 请求长时间阻塞：

```text
FastAPI Backend
  |
  | enqueue task
  v
Redis / RabbitMQ Broker
  |
  v
Celery Worker
  |
  |-- Resume Parse Task
  |-- Knowledge Document Parse Task
  |-- Knowledge Chunk Task
  |-- Embedding Index Task
  |-- Resume Analyze Task
  |-- JD Analyze Task
  |-- Match Report Task
  |-- Question Generate Task
  |-- Interview Report Task
  |-- Document Index Task
  |
  v
PostgreSQL / Object Storage / LLM Provider
```

## 2. 推荐技术栈

### 前端

- Next.js App Router
- TypeScript
- Tailwind CSS
- shadcn/ui
- TanStack Query
- React Hook Form
- Zod

### 后端

- Python 3.12+
- FastAPI
- Pydantic v2
- SQLAlchemy 2.x
- Alembic
- Uvicorn
- python-jose / PyJWT
- passlib / bcrypt
- Celery

### 数据层

- PostgreSQL
- pgvector
- Redis
- Redis Broker / RabbitMQ Broker
- MinIO 或 S3-compatible Object Storage

### AI 层

- OpenAI-compatible Chat Completions API
- Embeddings API
- LangGraph 或轻量 Orchestrator
- Prompt 模板文件化管理

### 文档解析

- PyMuPDF: PDF 文本提取
- python-docx: DOCX 文本提取
- 后期可接入 unstructured

## 3. 后端分层

```text
api/
  路由层，只处理 HTTP 入参、鉴权和响应

schemas/
  Pydantic 请求和响应模型

models/
  SQLAlchemy ORM 模型

repositories/
  数据访问层

services/
  业务逻辑层

agents/
  AI Agent 编排层

prompts/
  Prompt 模板

core/
  配置、安全、数据库、日志、异常处理

workers/
  异步任务
```

## 4. 推荐后端目录

```text
backend/
  app/
    main.py
    api/
      deps.py
      v1/
        auth.py
        projects.py
        resumes.py
        job_descriptions.py
        match_reports.py
        questions.py
        interviews.py
    core/
      config.py
      security.py
      database.py
      exceptions.py
      logging.py
    models/
      user.py
      project.py
      resume.py
      job_description.py
      match_report.py
      question.py
      interview.py
    schemas/
      auth.py
      project.py
      resume.py
      job_description.py
      match_report.py
      question.py
      interview.py
    repositories/
      base.py
      project_repository.py
      resume_repository.py
    services/
      auth_service.py
      project_service.py
      resume_service.py
      jd_service.py
      match_service.py
      question_service.py
      question_bank_service.py
      knowledge_base_service.py
      interview_service.py
      report_service.py
    agents/
      base.py
      resume_agent.py
      jd_analyzer_agent.py
      match_agent.py
      question_generator_agent.py
      knowledge_retriever.py
      interviewer_agent.py
      evaluator_agent.py
    prompts/
      resume_analysis.md
      jd_analysis.md
      match_analysis.md
      question_generation.md
      knowledge_question_generation.md
      interviewer.md
      evaluator.md
    utils/
      document_parser.py
      json_utils.py
    workers/
      celery_app.py
      tasks/
        resume_tasks.py
        jd_tasks.py
        match_tasks.py
        question_tasks.py
        interview_tasks.py
        document_tasks.py
  alembic/
  tests/
  pyproject.toml
```

## 5. 前端目录建议

```text
frontend/
  app/
    login/
    register/
    projects/
      page.tsx
      [projectId]/
        page.tsx
        analysis/
          page.tsx
        interview/
          page.tsx
        reports/
          [reportId]/
            page.tsx
  components/
    layout/
    project/
    resume/
    interview/
    report/
    ui/
  lib/
    api.ts
    auth.ts
    query-client.ts
  hooks/
  types/
```

## 6. 关键业务流

### 6.1 简历分析流

```text
用户上传简历
  ↓
后端保存文件
  ↓
提取简历文本
  ↓
写入 resumes.raw_text
  ↓
调用 ResumeAgent
  ↓
写入 resumes.analysis_json
  ↓
返回分析结果
```

### 6.2 匹配分析流

```text
用户提交 JD
  ↓
调用 JDAnalyzerAgent
  ↓
保存 JD 分析结果
  ↓
读取简历分析 + JD 分析
  ↓
调用 MatchAgent
  ↓
生成 match_reports
```

### 6.3 模拟面试流

```text
创建 interview_session
  ↓
读取项目上下文：简历、JD、匹配报告
  ↓
InterviewerAgent 生成第一题
  ↓
用户提交回答
  ↓
InterviewerAgent 根据回答生成反馈和追问
  ↓
循环多轮
  ↓
用户结束面试
  ↓
EvaluatorAgent 生成报告
```

### 6.4 个人题库与知识库流

```text
用户上传八股文 / 面经 / 面试题 / 项目复习资料
  ↓
后端保存原始文件或文本
  ↓
Celery 解析文档并提取 raw_text
  ↓
按标题、段落、问答格式切分 chunk
  ↓
调用 Embedding API 生成向量
  ↓
写入 knowledge_chunks.embedding
  ↓
可选：抽取结构化题目写入 question_bank_items
  ↓
QuestionGeneratorAgent 按简历、JD、匹配报告和知识库检索结果生成题目
```

知识库用于检索增强，不替代结构化题库。推荐同时保留两层数据：

- `question_bank_items`：结构化面试题，适合列表、复习、收藏、错题本。
- `knowledge_chunks`：向量化知识片段，适合语义检索、RAG 出题和生成参考答案。

### 6.5 知识库增强出题流

```text
用户选择方向、难度、题量
  ↓
后端读取项目上下文：简历、JD、匹配报告
  ↓
构造检索 query：岗位要求 + 缺失能力 + 训练模式
  ↓
pgvector 检索相关知识片段和题库条目
  ↓
QuestionGeneratorAgent 结合检索结果生成面试题
  ↓
保存 questions，并记录来源 knowledge_chunk_ids / question_bank_item_ids
```

## 7. 同步与异步边界

### 同步处理

- 登录注册
- 项目 CRUD
- JD 保存
- 获取报告
- 提交面试回答

### 可异步处理

- 简历解析
- 简历 AI 分析
- JD AI 分析
- 匹配报告生成
- 面试题批量生成
- 知识库文档解析
- 知识 chunk 切分
- embedding 生成和索引
- 八股文抽题入库
- 大文档解析
- 向量化
- 复杂报告生成

建议从项目结构上预留 Celery。MVP 中，文本面试单轮追问可以同步返回；简历解析、AI 分析、匹配报告和最终报告优先走 Celery，并通过任务状态接口查询结果。

## 8. 安全设计

- 密码使用 bcrypt 哈希
- 使用 JWT access token
- 所有项目资源必须校验 user_id
- 文件上传限制大小和类型
- LLM Prompt 中避免泄露其他用户数据
- 日志中不打印完整简历、JD 和 token

## 9. 环境变量

```env
APP_ENV=local
APP_SECRET_KEY=replace_me
DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/pyoffer
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2
OBJECT_STORAGE_ENDPOINT=http://localhost:9000
OBJECT_STORAGE_ACCESS_KEY=minio
OBJECT_STORAGE_SECRET_KEY=minio123
LLM_BASE_URL=https://api.example.com/v1
LLM_API_KEY=replace_me
LLM_MODEL=gpt-4.1-mini
EMBEDDING_MODEL=text-embedding-3-small
```
