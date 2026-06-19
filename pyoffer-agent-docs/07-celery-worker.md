# 07. Celery 异步任务设计

Celery 用来处理耗时任务，尤其是文件解析、LLM 调用、报告生成和后期 RAG 向量化。

MVP 不需要把所有接口都异步化。建议规则是：

- 预计 1-3 秒内完成：可以同步返回
- 超过 3 秒或响应不稳定：走 Celery
- 需要批量处理或可能重试：走 Celery
- 涉及大文件、向量化、长报告：必须走 Celery

## 1. Celery 在系统中的位置

```text
FastAPI API
  |
  | create task
  v
Redis / RabbitMQ Broker
  |
  v
Celery Worker
  |
  |-- 调用数据库
  |-- 调用文件存储
  |-- 调用 LLM
  |-- 写回任务结果
  v
PostgreSQL
```

## 2. Broker 选择

MVP 推荐：

```text
Redis as broker
Redis as result backend
```

生产环境如果任务量变大，可以切到：

```text
RabbitMQ as broker
PostgreSQL / Redis as result backend
```

## 3. 推荐环境变量

```env
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2
CELERY_TASK_TIME_LIMIT=300
CELERY_TASK_SOFT_TIME_LIMIT=240
```

## 4. 任务类型

### 4.1 简历解析任务

任务名：

```text
resume.parse
```

输入：

```json
{
  "resume_id": "uuid"
}
```

处理：

1. 读取 resume 文件
2. 根据 file_type 解析文本
3. 写入 resumes.raw_text
4. 更新 status 为 parsed

失败：

- 更新 status 为 failed
- 记录错误信息

### 4.2 简历分析任务

任务名：

```text
resume.analyze
```

输入：

```json
{
  "resume_id": "uuid",
  "target_direction": "agent_engineer"
}
```

处理：

1. 读取 resumes.raw_text
2. 调用 ResumeAgent
3. 校验 JSON 输出
4. 写入 resumes.analysis_json
5. 更新 status 为 analyzed

### 4.3 JD 分析任务

任务名：

```text
jd.analyze
```

输入：

```json
{
  "job_description_id": "uuid"
}
```

处理：

1. 读取 JD raw_text
2. 调用 JDAnalyzerAgent
3. 写入 analysis_json

### 4.4 匹配报告任务

任务名：

```text
match_report.generate
```

输入：

```json
{
  "project_id": "uuid",
  "resume_id": "uuid",
  "job_description_id": "uuid"
}
```

处理：

1. 读取简历分析
2. 读取 JD 分析
3. 调用 MatchAgent
4. 创建 match_reports 记录

### 4.5 面试题生成任务

任务名：

```text
questions.generate
```

输入：

```json
{
  "project_id": "uuid",
  "mode": "rag_project_deep_dive",
  "difficulty": "intern",
  "count": 10,
  "focus": ["RAG", "FastAPI"]
}
```

处理：

1. 读取项目上下文
2. 调用 QuestionGeneratorAgent
3. 批量写入 questions

### 4.6 面试报告任务

任务名：

```text
interview_report.generate
```

输入：

```json
{
  "session_id": "uuid"
}
```

处理：

1. 读取完整面试消息
2. 调用 EvaluatorAgent
3. 创建 interview_reports 记录
4. 更新 interview_sessions.status 为 completed

### 4.7 项目文档索引任务

Phase 3 使用。

任务名：

```text
document.index
```

输入：

```json
{
  "document_id": "uuid"
}
```

处理：

1. 解析文档文本
2. chunk 切分
3. 调用 Embedding API
4. 写入 document_chunks

### 4.8 个人知识库文档索引任务

任务名：

```text
knowledge_document.index
```

输入：

```json
{
  "document_id": "uuid",
  "extract_questions": true
}
```

处理：

1. 校验 knowledge_document 存在。
2. 如果文档来自上传文件，解析 PDF / DOCX / TXT / Markdown。
3. 清洗文本并写入 knowledge_documents.raw_text。
4. 按标题、段落和 Q/A 边界切分 chunk。
5. 调用 Embedding API 批量生成向量。
6. 写入 knowledge_chunks。
7. 可选抽取 question_bank_items。
8. 更新 knowledge_documents.status 为 indexed。
9. 更新 async_tasks.result_json，返回 chunk_count 和 question_count。

失败：

- 更新 knowledge_documents.status 为 failed。
- 写入 parse_error 或 async_tasks.error_message。
- 只对 Embedding API 超时、限流、5xx 做有限重试。

### 4.9 题库批量导入任务

任务名：

```text
question_bank.import
```

输入：

```json
{
  "collection_id": "uuid",
  "format": "qa_markdown",
  "content": "Q: ...\nA: ..."
}
```

处理：

1. 解析 Markdown / 纯文本 Q/A。
2. 生成 question_bank_items。
3. 拼接题目、答案摘要和标签生成 embedding_text。
4. 调用 Embedding API。
5. 写入 question_bank_item_embeddings。

## 5. 任务状态设计

建议新增任务表，避免只依赖 Celery result backend。

```sql
create table async_tasks (
  id uuid primary key,
  user_id uuid not null references users(id),
  project_id uuid references projects(id),
  celery_task_id varchar(255) unique not null,
  task_type varchar(100) not null,
  status varchar(50) not null default 'pending',
  progress integer not null default 0,
  result_json jsonb,
  error_message text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index idx_async_tasks_user_id on async_tasks(user_id);
create index idx_async_tasks_project_id on async_tasks(project_id);
```

推荐 status：

```text
pending
running
success
failed
cancelled
```

## 6. 任务状态接口

创建异步任务的接口返回 task_id。

示例：

```http
POST /api/v1/resumes/{resume_id}/analyze
```

响应：

```json
{
  "task_id": "uuid",
  "status": "pending"
}
```

查询任务：

```http
GET /api/v1/tasks/{task_id}
```

响应：

```json
{
  "id": "uuid",
  "task_type": "resume.analyze",
  "status": "success",
  "progress": 100,
  "result": {
    "resume_id": "uuid"
  },
  "error_message": null
}
```

## 7. Celery 目录建议

```text
backend/
  app/
    workers/
      celery_app.py
      tasks/
        resume_tasks.py
        jd_tasks.py
        match_tasks.py
        question_tasks.py
        interview_tasks.py
        document_tasks.py
```

## 8. Worker 启动命令

开发环境：

```bash
celery -A app.workers.celery_app worker --loglevel=info --pool=solo
```

Windows 本地开发可以用 `--pool=solo`，Linux 部署时使用默认 prefork。

生产环境：

```bash
celery -A app.workers.celery_app worker --loglevel=info --concurrency=4
```

## 9. Docker Compose 服务

```yaml
worker:
  build: ./backend
  command: celery -A app.workers.celery_app worker --loglevel=info
  env_file:
    - ./backend/.env
  depends_on:
    - postgres
    - redis
```

## 10. FastAPI 与 Celery 的边界

FastAPI 负责：

- 参数校验
- 鉴权
- 创建任务记录
- 提交 Celery 任务
- 查询任务状态

Celery Worker 负责：

- 读取数据库
- 执行耗时逻辑
- 调用 LLM
- 更新业务表
- 更新任务状态

不要在 Celery 任务里复用 FastAPI 的 request/session 对象。Worker 应该自己创建数据库 session。

## 11. 重试策略

推荐只对外部服务错误重试：

- LLM 超时
- Embedding 超时
- 对象存储临时失败

不建议重试：

- 参数错误
- JSON schema 校验失败
- 文件格式不支持

示例策略：

```text
max_retries: 2
retry_backoff: true
retry_jitter: true
```

## 12. MVP 建议

第一版最值得异步化的任务：

1. resume.parse
2. resume.analyze
3. jd.analyze
4. match_report.generate
5. interview_report.generate

文本面试中的单轮追问可以先同步，因为用户本来就在等待下一题。等后面做实时语音或并发变高，再考虑 WebSocket + 后台任务。
