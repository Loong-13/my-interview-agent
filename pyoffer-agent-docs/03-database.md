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

项目面试题表。这里保存针对某个求职项目生成或选中的训练题。

```sql
create table questions (
  id uuid primary key,
  project_id uuid not null references projects(id),
  question_bank_item_id uuid,
  type varchar(80) not null,
  difficulty varchar(50) not null default 'intern',
  question text not null,
  reference_answer text,
  evaluation_points jsonb not null default '[]',
  source_chunk_ids jsonb not null default '[]',
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
question_bank_review
```

推荐 source：

```text
ai_generated
question_bank
knowledge_base
mixed
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

## 11. 个人题库与知识库

个人题库与知识库用于支持用户上传八股文、面经、项目复习资料和历史面试题，并通过向量检索增强出题、模拟面试和复习建议。

需要启用 pgvector：

```sql
create extension if not exists vector;
```

### knowledge_collections

知识库集合。用户可以按方向或用途创建多个集合，例如“Python 八股文”“FastAPI 面试题”“RAG 项目复习”。

```sql
create table knowledge_collections (
  id uuid primary key,
  user_id uuid not null references users(id),
  name varchar(200) not null,
  description text,
  visibility varchar(50) not null default 'private',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index idx_knowledge_collections_user_id on knowledge_collections(user_id);
```

推荐 visibility：

```text
private
shared
public
```

### knowledge_documents

上传的原始资料。可以是 PDF / DOCX / TXT / Markdown，也可以是用户直接粘贴的文本。

```sql
create table knowledge_documents (
  id uuid primary key,
  user_id uuid not null references users(id),
  collection_id uuid references knowledge_collections(id),
  title varchar(255) not null,
  file_name varchar(255),
  file_url varchar(500),
  file_type varchar(50),
  content_type varchar(50) not null default 'interview_notes',
  raw_text text,
  metadata jsonb not null default '{}',
  status varchar(50) not null default 'uploaded',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index idx_knowledge_documents_user_id on knowledge_documents(user_id);
create index idx_knowledge_documents_collection_id on knowledge_documents(collection_id);
create index idx_knowledge_documents_content_type on knowledge_documents(content_type);
```

推荐 content_type：

```text
interview_notes
question_bank
experience_post
project_doc
course_note
other
```

推荐 status：

```text
uploaded
parsed
chunked
indexed
failed
```

### knowledge_chunks

知识片段表。用于 pgvector 语义检索。

```sql
create table knowledge_chunks (
  id uuid primary key,
  user_id uuid not null references users(id),
  collection_id uuid references knowledge_collections(id),
  document_id uuid not null references knowledge_documents(id),
  chunk_index integer not null,
  title varchar(255),
  content text not null,
  token_count integer,
  embedding vector(1536),
  metadata jsonb not null default '{}',
  created_at timestamptz not null default now()
);

create index idx_knowledge_chunks_user_id on knowledge_chunks(user_id);
create index idx_knowledge_chunks_collection_id on knowledge_chunks(collection_id);
create index idx_knowledge_chunks_document_id on knowledge_chunks(document_id);
create index idx_knowledge_chunks_embedding
  on knowledge_chunks
  using ivfflat (embedding vector_cosine_ops)
  with (lists = 100);
```

如果使用 `text-embedding-3-small`，向量维度是 1536。如果后续切换模型，需要同步调整 embedding 维度或增加 `embedding_model` 字段区分。

### question_bank_items

结构化题库表。用于保存用户上传或系统抽取的八股题、项目题、开放题和参考答案。

```sql
create table question_bank_items (
  id uuid primary key,
  user_id uuid not null references users(id),
  collection_id uuid references knowledge_collections(id),
  document_id uuid references knowledge_documents(id),
  source_chunk_id uuid references knowledge_chunks(id),
  type varchar(80) not null,
  difficulty varchar(50) not null default 'intern',
  question text not null,
  reference_answer text,
  evaluation_points jsonb not null default '[]',
  tags jsonb not null default '[]',
  source varchar(50) not null default 'manual',
  quality_score integer,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index idx_question_bank_items_user_id on question_bank_items(user_id);
create index idx_question_bank_items_collection_id on question_bank_items(collection_id);
create index idx_question_bank_items_type on question_bank_items(type);
create index idx_question_bank_items_difficulty on question_bank_items(difficulty);
```

推荐 source：

```text
manual
document_extract
ai_generated
imported
```

### question_bank_item_embeddings

题目本身也可以向量化，便于按 JD、简历短板或用户回答语义检索相关题目。

```sql
create table question_bank_item_embeddings (
  id uuid primary key,
  question_bank_item_id uuid not null references question_bank_items(id),
  embedding_text text not null,
  embedding vector(1536),
  embedding_model varchar(100) not null,
  created_at timestamptz not null default now()
);

create index idx_question_bank_item_embeddings_item_id
  on question_bank_item_embeddings(question_bank_item_id);

create index idx_question_bank_item_embeddings_vector
  on question_bank_item_embeddings
  using ivfflat (embedding vector_cosine_ops)
  with (lists = 100);
```

推荐 `embedding_text` 拼接：

```text
题目 + 参考答案摘要 + 标签 + 题型 + 难度
```

## 12. 项目资料 RAG 扩展表

项目资料 RAG 表主要面向某个求职项目，例如上传项目文档、论文、代码说明，让模拟面试可以围绕具体项目追问。

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
