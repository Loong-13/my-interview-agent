# 03. 数据库表设计

数据库建议使用 PostgreSQL。MVP 阶段可以先不用强枚举类型，使用 varchar 存储状态和方向，方便快速迭代。

## 1. users

用户表。

```sql
create table users (
  id uuid primary key,
  email varchar(255) unique not null,
  password_hash varchar(255) not null,
  nickname varchar(100),
  avatar_url varchar(500),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
```

## 2. projects

求职项目表。一个用户可以有多个项目。

```sql
create table projects (
  id uuid primary key,
  user_id uuid not null references users(id),
  name varchar(200) not null,
  target_company varchar(200),
  target_role varchar(200) not null,
  direction varchar(50) not null,
  experience_level varchar(50) not null default 'intern',
  status varchar(50) not null default 'active',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index idx_projects_user_id on projects(user_id);
```

推荐 direction：

```text
python_backend
agent_engineer
llm_application
```

推荐 experience_level：

```text
intern
new_grad
```

## 3. resumes

简历表。

```sql
create table resumes (
  id uuid primary key,
  project_id uuid not null references projects(id),
  file_name varchar(255),
  file_url varchar(500),
  file_type varchar(50),
  raw_text text,
  parsed_json jsonb,
  analysis_json jsonb,
  status varchar(50) not null default 'uploaded',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index idx_resumes_project_id on resumes(project_id);
```

推荐 status：

```text
uploaded
parsed
analyzed
failed
```

analysis_json 示例：

```json
{
  "detected_direction": "agent_engineer",
  "skills": ["Python", "FastAPI", "RAG", "PostgreSQL"],
  "projects": [
    {
      "name": "AI 文档问答系统",
      "tech_stack": ["FastAPI", "pgvector", "LLM"],
      "deep_dive_points": ["文档切分", "向量检索", "答案评估"]
    }
  ],
  "weaknesses": ["缺少 RAG 评估指标", "数据库设计描述不足"],
  "suggestions": ["补充召回率评估方法", "说明接口鉴权和部署方式"]
}
```

## 4. job_descriptions

岗位 JD 表。

```sql
create table job_descriptions (
  id uuid primary key,
  project_id uuid not null references projects(id),
  company varchar(200),
  position varchar(200),
  raw_text text not null,
  analysis_json jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index idx_job_descriptions_project_id on job_descriptions(project_id);
```

analysis_json 示例：

```json
{
  "direction": "agent_engineer",
  "required_skills": ["Python", "RAG", "Prompt Engineering"],
  "bonus_skills": ["LangGraph", "FastAPI", "PostgreSQL"],
  "interview_topics": ["RAG 流程", "Agent 工具调用", "项目深挖"]
}
```

## 5. match_reports

简历与 JD 匹配报告。

```sql
create table match_reports (
  id uuid primary key,
  project_id uuid not null references projects(id),
  resume_id uuid not null references resumes(id),
  job_description_id uuid not null references job_descriptions(id),
  match_score integer not null,
  matched_skills jsonb not null default '[]',
  missing_skills jsonb not null default '[]',
  interview_focus jsonb not null default '[]',
  suggestions jsonb not null default '[]',
  raw_report jsonb,
  created_at timestamptz not null default now()
);

create index idx_match_reports_project_id on match_reports(project_id);
```

## 6. questions

面试题表。

```sql
create table questions (
  id uuid primary key,
  project_id uuid not null references projects(id),
  type varchar(80) not null,
  difficulty varchar(50) not null default 'intern',
  question text not null,
  reference_answer text,
  evaluation_points jsonb not null default '[]',
  source varchar(50) not null default 'ai_generated',
  created_at timestamptz not null default now()
);

create index idx_questions_project_id on questions(project_id);
create index idx_questions_type on questions(type);
```

推荐 type：

```text
python_basic
python_backend_project
fastapi_backend
agent_basic
rag_project_deep_dive
```

## 7. interview_sessions

面试会话表。

```sql
create table interview_sessions (
  id uuid primary key,
  project_id uuid not null references projects(id),
  mode varchar(80) not null,
  difficulty varchar(50) not null default 'intern',
  status varchar(50) not null default 'created',
  started_at timestamptz,
  ended_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index idx_interview_sessions_project_id on interview_sessions(project_id);
```

推荐 status：

```text
created
running
completed
cancelled
```

## 8. interview_messages

面试消息表。

```sql
create table interview_messages (
  id uuid primary key,
  session_id uuid not null references interview_sessions(id),
  role varchar(50) not null,
  content text not null,
  question_id uuid references questions(id),
  feedback_json jsonb,
  created_at timestamptz not null default now()
);

create index idx_interview_messages_session_id on interview_messages(session_id);
```

推荐 role：

```text
system
interviewer
candidate
evaluator
```

## 9. interview_reports

面试报告表。

```sql
create table interview_reports (
  id uuid primary key,
  session_id uuid not null references interview_sessions(id),
  overall_score integer not null,
  scores jsonb not null default '{}',
  strengths jsonb not null default '[]',
  weaknesses jsonb not null default '[]',
  suggestions jsonb not null default '[]',
  recommended_topics jsonb not null default '[]',
  improved_answers jsonb not null default '[]',
  raw_report jsonb,
  created_at timestamptz not null default now()
);

create unique index idx_interview_reports_session_id on interview_reports(session_id);
```

scores 示例：

```json
{
  "python_foundation": 78,
  "backend_engineering": 72,
  "database_understanding": 68,
  "agent_understanding": 75,
  "project_depth": 70,
  "communication": 80
}
```

## 10. async_tasks

异步任务状态表。用于记录 Celery 任务状态，不只依赖 Redis result backend。

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
create index idx_async_tasks_celery_task_id on async_tasks(celery_task_id);
```

推荐 status：

```text
pending
running
success
failed
cancelled
```

## 11. 后期 RAG 扩展表

MVP 后可以增加资料上传与向量检索。

### documents

```sql
create table documents (
  id uuid primary key,
  project_id uuid not null references projects(id),
  file_name varchar(255),
  file_url varchar(500),
  file_type varchar(50),
  raw_text text,
  status varchar(50) not null default 'uploaded',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
```

### document_chunks

需要启用 pgvector：

```sql
create extension if not exists vector;
```

```sql
create table document_chunks (
  id uuid primary key,
  document_id uuid not null references documents(id),
  project_id uuid not null references projects(id),
  chunk_index integer not null,
  content text not null,
  embedding vector(1536),
  metadata jsonb not null default '{}',
  created_at timestamptz not null default now()
);

create index idx_document_chunks_project_id on document_chunks(project_id);
```
