# 04. REST API 接口文档

接口统一前缀：

```http
/api/v1
```

鉴权方式：

```http
Authorization: Bearer <access_token>
```

错误响应格式：

```json
{
  "code": "VALIDATION_ERROR",
  "message": "请求参数错误",
  "details": {}
}
```

## 1. Auth

### 注册

```http
POST /api/v1/auth/register
```

请求：

```json
{
  "email": "user@example.com",
  "password": "12345678",
  "nickname": "小明"
}
```

响应：

```json
{
  "id": "uuid",
  "email": "user@example.com",
  "nickname": "小明"
}
```

### 登录

```http
POST /api/v1/auth/login
```

请求：

```json
{
  "email": "user@example.com",
  "password": "12345678"
}
```

响应：

```json
{
  "access_token": "jwt_token",
  "token_type": "bearer"
}
```

### 获取当前用户

```http
GET /api/v1/auth/me
```

响应：

```json
{
  "id": "uuid",
  "email": "user@example.com",
  "nickname": "小明"
}
```

## 2. Projects

### 创建项目

```http
POST /api/v1/projects
```

请求：

```json
{
  "name": "Python 后端实习 - 字节",
  "target_company": "字节跳动",
  "target_role": "Python Backend Intern",
  "direction": "python_backend",
  "experience_level": "intern"
}
```

响应：

```json
{
  "id": "uuid",
  "name": "Python 后端实习 - 字节",
  "target_company": "字节跳动",
  "target_role": "Python Backend Intern",
  "direction": "python_backend",
  "experience_level": "intern",
  "status": "active"
}
```

### 获取项目列表

```http
GET /api/v1/projects
```

响应：

```json
{
  "items": [
    {
      "id": "uuid",
      "name": "Python 后端实习 - 字节",
      "target_company": "字节跳动",
      "target_role": "Python Backend Intern",
      "direction": "python_backend",
      "latest_match_score": 78,
      "status": "active"
    }
  ],
  "total": 1
}
```

### 获取项目详情

```http
GET /api/v1/projects/{project_id}
```

### 更新项目

```http
PATCH /api/v1/projects/{project_id}
```

请求：

```json
{
  "name": "Python 后端实习 - 更新",
  "target_company": "某公司"
}
```

### 删除项目

```http
DELETE /api/v1/projects/{project_id}
```

建议 MVP 中做软删除或归档：

```json
{
  "status": "archived"
}
```

## 3. Resumes

### 上传简历

```http
POST /api/v1/projects/{project_id}/resumes
Content-Type: multipart/form-data
```

参数：

```text
file: resume.pdf
```

响应：

```json
{
  "resume_id": "uuid",
  "file_name": "resume.pdf",
  "status": "uploaded"
}
```

### 解析简历

```http
POST /api/v1/resumes/{resume_id}/parse
```

响应：

```json
{
  "resume_id": "uuid",
  "status": "parsed",
  "raw_text": "简历文本..."
}
```

### 分析简历

```http
POST /api/v1/resumes/{resume_id}/analyze
```

请求：

```json
{
  "target_direction": "agent_engineer"
}
```

响应：

```json
{
  "detected_direction": "agent_engineer",
  "skills": ["Python", "FastAPI", "RAG", "PostgreSQL"],
  "weaknesses": [
    "RAG 项目缺少评估指标",
    "后端项目缺少接口设计细节"
  ],
  "suggestions": [
    "补充文档切分、召回策略和效果评估",
    "补充 FastAPI 鉴权、数据库设计和部署方式"
  ],
  "project_deep_dive_points": [
    "你在 RAG 项目中如何选择 chunk size？",
    "你如何处理向量检索召回不准的问题？"
  ]
}
```

## 4. Job Descriptions

### 创建 JD

```http
POST /api/v1/projects/{project_id}/job-descriptions
```

请求：

```json
{
  "company": "某公司",
  "position": "AI Agent 实习生",
  "raw_text": "岗位要求：熟悉 Python、FastAPI、RAG、Agent..."
}
```

响应：

```json
{
  "id": "uuid",
  "company": "某公司",
  "position": "AI Agent 实习生"
}
```

### 分析 JD

```http
POST /api/v1/job-descriptions/{jd_id}/analyze
```

响应：

```json
{
  "direction": "agent_engineer",
  "required_skills": ["Python", "RAG", "Prompt Engineering", "Tool Calling"],
  "bonus_skills": ["LangGraph", "向量数据库", "FastAPI"],
  "interview_topics": ["RAG 流程", "Agent 工具调用", "项目深挖"]
}
```

## 5. Match Reports

### 生成匹配报告

```http
POST /api/v1/projects/{project_id}/match-reports
```

请求：

```json
{
  "resume_id": "uuid",
  "job_description_id": "uuid"
}
```

响应：

```json
{
  "id": "uuid",
  "match_score": 78,
  "matched_skills": ["Python", "FastAPI", "PostgreSQL"],
  "missing_skills": ["LangGraph", "RAG 评估", "Celery"],
  "interview_focus": [
    "Python 协程",
    "FastAPI 依赖注入",
    "RAG 文档切分",
    "Agent 工具失败处理"
  ],
  "suggestions": [
    "简历中补充 Agent 项目的工具调用流程",
    "补充数据库设计和接口性能优化经验"
  ]
}
```

## 6. Questions

### 生成面试题

```http
POST /api/v1/projects/{project_id}/questions/generate
```

请求：

```json
{
  "mode": "rag_project_deep_dive",
  "difficulty": "intern",
  "count": 10,
  "focus": ["RAG", "FastAPI", "PostgreSQL"]
}
```

响应：

```json
{
  "questions": [
    {
      "id": "uuid",
      "type": "rag_project_deep_dive",
      "difficulty": "intern",
      "question": "你在 RAG 项目中是如何做文档切分的？",
      "evaluation_points": ["chunk size", "overlap", "语义完整性", "召回效果"]
    }
  ]
}
```

### 获取项目题目

```http
GET /api/v1/projects/{project_id}/questions
```

查询参数：

```text
type: optional
difficulty: optional
```

## 7. Interviews

### 创建面试

```http
POST /api/v1/projects/{project_id}/interviews
```

请求：

```json
{
  "mode": "agent_basic",
  "difficulty": "intern"
}
```

响应：

```json
{
  "session_id": "uuid",
  "status": "created"
}
```

### 开始面试

```http
POST /api/v1/interviews/{session_id}/start
```

响应：

```json
{
  "session_id": "uuid",
  "first_question": "请先介绍一下你做过的一个 Python 或 Agent 项目。"
}
```

### 提交回答

```http
POST /api/v1/interviews/{session_id}/answers
```

请求：

```json
{
  "answer": "我做过一个基于 FastAPI 和向量数据库的文档问答系统..."
}
```

响应：

```json
{
  "feedback": "回答说明了项目背景，但缺少技术细节。",
  "next_question": "你是如何设计文档切分和向量检索流程的？",
  "should_continue": true
}
```

### 结束面试

```http
POST /api/v1/interviews/{session_id}/finish
```

响应：

```json
{
  "session_id": "uuid",
  "status": "completed"
}
```

### 生成报告

```http
POST /api/v1/interviews/{session_id}/report
```

响应：

```json
{
  "id": "uuid",
  "overall_score": 74,
  "scores": {
    "python_foundation": 78,
    "backend_engineering": 72,
    "database_understanding": 68,
    "agent_understanding": 75,
    "project_depth": 70,
    "communication": 80
  },
  "strengths": ["表达清晰", "能说明项目整体流程"],
  "weaknesses": ["RAG 评估方法不够清楚", "数据库和缓存设计细节不足"],
  "recommended_topics": ["FastAPI 依赖注入", "PostgreSQL 索引", "RAG 召回评估"]
}
```

### 获取面试消息

```http
GET /api/v1/interviews/{session_id}/messages
```

### 获取面试报告

```http
GET /api/v1/interviews/{session_id}/report
```

## 8. Tasks

异步任务接口用于查询 Celery 任务状态。

### 获取任务状态

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

推荐异步接口返回：

```json
{
  "task_id": "uuid",
  "status": "pending"
}
```
