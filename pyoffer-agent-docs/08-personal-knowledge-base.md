# 08. 个人知识库搭建开发文档

个人知识库用于让用户上传自己的八股文、面经、项目复习资料、历史面试题和课程笔记，并把这些资料转化为可检索、可出题、可复习的训练资产。

MVP 中不要把知识库做成复杂内容管理系统。优先目标是：

1. 能上传或粘贴资料
2. 能解析文本
3. 能切分 chunk
4. 能生成 embedding 并写入 pgvector
5. 能抽取或手动维护结构化题目
6. 能基于知识库检索结果生成面试题

## 1. 功能边界

### 1.1 MVP 要做

- 创建知识库集合
- 上传 PDF / DOCX / TXT / Markdown
- 粘贴文本资料
- 查看文档解析和索引状态
- 文档切分为 knowledge_chunks
- 调用 Embedding API 写入 pgvector
- 手动新增题库题目
- 批量导入简单 Q/A 格式题目
- 基于 query 检索知识片段
- 基于知识库生成项目训练题

### 1.2 MVP 暂不做

- 多人协作知识库
- 公共知识市场
- 复杂权限继承
- 富文本编辑器
- 自动知识图谱
- 文档版本 diff
- 多 embedding 模型混合检索
- 大规模增量索引调度平台

## 2. 核心概念

### 2.1 knowledge_collections

知识库集合。用于把资料按用途分组，例如：

- Python 后端八股文
- FastAPI 高频题
- PostgreSQL / Redis 专项
- RAG 项目复习
- Agent 面试题

集合归属于用户，不直接绑定项目。一个求职项目可以在生成题目时选择一个或多个集合。

### 2.2 knowledge_documents

用户上传或粘贴的原始资料。文档负责保存原始文本、文件信息、解析状态和索引状态。

文档类型建议：

```text
interview_notes
question_bank
experience_post
project_doc
course_note
other
```

### 2.3 knowledge_chunks

文档切分后的知识片段。每个 chunk 保存文本、元数据和向量，用于语义检索。

chunk 不一定是一道题，它可以是一段知识说明、一段项目复盘、一段面经回答或一个 Q/A 片段。

### 2.4 question_bank_items

结构化题库。适合保存明确的题目、参考答案、评价点、标签和难度。

知识库和题库的关系：

- 知识库 chunk 适合 RAG 检索和上下文增强
- 题库 item 适合专项练习、列表复习、错题本和收藏
- 文档索引时可以从 chunk 中抽取题库 item，但不要强依赖自动抽取

## 3. 总体流程

```text
用户创建知识库集合
  ↓
上传文件或粘贴文本
  ↓
创建 knowledge_documents
  ↓
提交 knowledge_document.index Celery 任务
  ↓
解析文件得到 raw_text
  ↓
文本清洗
  ↓
chunk 切分
  ↓
调用 Embedding API
  ↓
写入 knowledge_chunks
  ↓
可选：抽取 question_bank_items
  ↓
更新文档状态为 indexed
```

基于知识库生成题目：

```text
用户在项目中选择训练模式、难度、题量、知识库集合
  ↓
读取项目上下文：简历分析、JD 分析、匹配报告
  ↓
构造检索 query
  ↓
检索 knowledge_chunks 和 question_bank_items
  ↓
调用 QuestionGeneratorAgent
  ↓
保存到 questions
  ↓
记录 source_chunk_ids / question_bank_item_id
```

## 4. 后端模块建议

```text
backend/app/
  api/v1/
    knowledge.py
    question_bank.py
  models/
    knowledge.py
  schemas/
    knowledge.py
    question_bank.py
  services/
    knowledge_base_service.py
    question_bank_service.py
  agents/
    knowledge_retriever.py
    question_generator_agent.py
  workers/tasks/
    knowledge_tasks.py
  utils/
    document_parser.py
    text_chunker.py
    embedding_client.py
```

### 4.1 API 层

API 层只做：

- 鉴权
- 参数校验
- 文件类型和大小校验
- 创建数据库记录
- 提交异步任务
- 返回 task_id

不要在 API 请求里直接解析大文件、生成 embedding 或调用 LLM。

### 4.2 Service 层

Service 层负责业务规则：

- 校验 collection / document 属于当前用户
- 创建文档记录
- 创建题库条目
- 组合检索 query
- 调用 KnowledgeRetriever
- 调用 QuestionGeneratorAgent
- 写入 questions

### 4.3 Worker 层

Worker 层负责耗时任务：

- 文件解析
- 文本清洗
- chunk 切分
- embedding 生成
- 批量写入向量
- Q/A 题目抽取
- 更新任务状态和文档状态

## 5. 数据库设计引用

核心表已在 [03-database.md](./03-database.md) 中定义：

- `knowledge_collections`
- `knowledge_documents`
- `knowledge_chunks`
- `question_bank_items`
- `question_bank_item_embeddings`

建议补充以下字段，便于后续排查索引质量：

```sql
alter table knowledge_documents
  add column if not exists parse_error text,
  add column if not exists chunk_count integer not null default 0,
  add column if not exists indexed_at timestamptz;

alter table knowledge_chunks
  add column if not exists embedding_model varchar(100),
  add column if not exists content_hash varchar(64);
```

`content_hash` 用于去重，推荐对清洗后的 chunk content 做 sha256。

## 6. 文档状态机

`knowledge_documents.status` 推荐状态：

```text
uploaded
parsing
parsed
chunking
embedding
indexed
failed
```

状态流转：

```text
uploaded
  ↓
parsing
  ↓
parsed
  ↓
chunking
  ↓
embedding
  ↓
indexed
```

失败时统一进入 `failed`，并写入 `parse_error` 或任务错误信息。

## 7. 文档解析

### 7.1 支持格式

MVP 推荐：

```text
pdf
docx
txt
md
markdown
```

解析策略：

- PDF：PyMuPDF 提取文本
- DOCX：python-docx 提取段落文本
- TXT / Markdown：按 UTF-8 读取，失败时尝试常见编码
- 粘贴文本：直接写入 raw_text，跳过文件解析

### 7.2 文本清洗

清洗目标是减少噪音，不要过度改写用户资料。

建议处理：

- 统一换行
- 去掉连续 3 行以上空行
- 去掉页眉页脚中明显重复的页码
- 去掉不可见控制字符
- 保留 Markdown 标题
- 保留 Q/A 标记

不要处理：

- 不要自动翻译
- 不要重写原文
- 不要删除代码块
- 不要删除技术名词

## 8. Chunk 切分策略

### 8.1 普通文档切分

推荐规则：

```text
目标 chunk 大小：500-900 中文字
overlap：80-150 中文字
最大 chunk：1200 中文字
最小 chunk：100 中文字
```

优先按结构切分：

1. Markdown 标题
2. Q/A 边界
3. 空行段落
4. 句号、问号、分号
5. 固定长度兜底

### 8.2 面试题文档切分

如果文档中存在明显题目格式：

```text
Q:
A:
问题：
答案：
### 题目
```

优先把一组 Q/A 放入同一个 chunk，避免题目和答案被拆开。

### 8.3 chunk metadata

推荐 metadata：

```json
{
  "section_title": "FastAPI 依赖注入",
  "chunk_type": "qa",
  "source": "document",
  "page": 3,
  "tags": ["FastAPI", "Depends"]
}
```

推荐 chunk_type：

```text
plain_text
qa
code
project_note
experience
```

## 9. Embedding 与索引

### 9.1 embedding 输入

不要只 embedding 原始 content。推荐拼接少量上下文：

```text
标题：{document_title}
章节：{section_title}
类型：{content_type}
内容：{chunk_content}
```

这样可以提升短 chunk 的可检索性。

### 9.2 批量策略

Worker 中按批处理：

```text
batch_size: 16-64
失败重试：只重试外部服务超时或 5xx
单文档任务失败：不影响其他文档
```

### 9.3 向量检索

pgvector cosine 检索示例：

```sql
select
  id,
  document_id,
  title,
  content,
  1 - (embedding <=> :query_embedding) as score
from knowledge_chunks
where user_id = :user_id
  and (:collection_ids is null or collection_id = any(:collection_ids))
order by embedding <=> :query_embedding
limit :top_k;
```

MVP 可先只做向量检索，后续再增加关键词 BM25 或 hybrid search。

## 10. 题库抽取

### 10.1 手动题库优先

MVP 中题库质量比自动化更重要。建议优先支持：

- 手动新增题目
- Markdown Q/A 批量导入
- CSV / JSON 后续再做

### 10.2 自动抽取策略

自动抽取可作为异步任务的可选步骤：

```text
knowledge_document.extract_questions
```

输入：

```json
{
  "document_id": "uuid",
  "collection_id": "uuid"
}
```

处理：

1. 读取文档 chunks
2. 识别 Q/A 格式片段
3. 对非结构化片段调用 LLM 抽取题目
4. 校验 question / reference_answer / tags
5. 写入 question_bank_items

注意：

- 不要从每个 chunk 强行抽题
- 抽取结果默认 source 为 `document_extract`
- 可以给 quality_score 初始值，例如 60-80
- 前端允许用户编辑和删除抽取结果

## 11. KnowledgeRetriever 设计

`KnowledgeRetriever` 不应该直接决定业务流程，它只负责根据输入上下文返回可用检索结果。

输入建议：

```json
{
  "user_id": "uuid",
  "collection_ids": ["uuid"],
  "project_context": {
    "direction": "agent_engineer",
    "required_skills": ["RAG", "FastAPI"],
    "missing_skills": ["RAG 评估"],
    "interview_focus": ["文档切分", "向量检索"]
  },
  "mode": "rag_project_deep_dive",
  "difficulty": "intern",
  "top_k": 8
}
```

输出建议：

```json
{
  "retrieval_query": "Agent 工程 实习 RAG 评估 文档切分 向量检索",
  "knowledge_chunks": [
    {
      "chunk_id": "uuid",
      "document_id": "uuid",
      "content": "RAG 评估可以从检索和生成两层看...",
      "score": 0.86,
      "metadata": {}
    }
  ],
  "question_bank_items": [
    {
      "id": "uuid",
      "question": "如何评估 RAG 系统的检索效果？",
      "reference_answer": "可以看 recall@k、MRR、hit rate...",
      "tags": ["RAG", "评估"]
    }
  ]
}
```

检索 query 构造优先级：

1. 用户传入 focus
2. match_report.missing_skills
3. match_report.interview_focus
4. jd_analysis.required_skills
5. project.direction 和 mode

## 12. 基于知识库生成题目

接口见 [04-api.md](./04-api.md)：

```http
POST /api/v1/projects/{project_id}/questions/generate-from-knowledge
```

生成流程：

1. 校验 project 属于当前用户
2. 校验 collection_ids 属于当前用户
3. 读取项目上下文
4. 调用 KnowledgeRetriever
5. 调用 QuestionGeneratorAgent
6. 保存 questions
7. 写入 source_chunk_ids 和 question_bank_item_id

题目生成 Prompt 要求：

- 优先覆盖 missing_skills 和 interview_focus
- 至少 30% 题目结合用户项目或 JD
- 如果引用知识库资料，记录 source_refs
- 不要整段复制知识库原文
- 参考答案要适合应届生面试表达

## 13. 前端页面建议

### 13.1 知识库集合页

功能：

- 创建集合
- 查看集合列表
- 查看文档数量、题目数量、最近索引时间
- 进入集合详情

### 13.2 集合详情页

Tab 建议：

```text
资料
题库
搜索
设置
```

资料 Tab：

- 上传文件
- 粘贴文本
- 文档列表
- 解析状态
- 索引状态
- 失败原因

题库 Tab：

- 手动新增题目
- 批量导入
- 标签筛选
- 难度筛选
- 编辑参考答案

搜索 Tab：

- 输入 query
- 展示 chunk 内容
- 展示相似度 score
- 展示来源文档

设置 Tab：

- 集合名称
- 描述
- 删除集合

### 13.3 项目出题入口

在项目详情的“生成面试题”区域增加：

- 是否使用知识库
- collection 多选
- focus 输入
- 生成后展示来源标记

## 14. 权限与安全

必须保证：

- 用户只能访问自己的 collection、document、chunk、question_bank_item
- 检索时必须带 user_id 过滤
- 生成题目时 collection_ids 必须属于当前用户
- 日志不打印完整文档内容
- 上传文件限制大小和类型
- 解析失败不返回系统路径

建议限制：

```text
单文件大小：10-20MB
单用户 MVP 文档数：100
单文档 chunk 数：1000
单次检索 top_k：最多 20
```

## 15. 开发顺序

推荐按下面顺序开发：

```text
knowledge_collections CRUD
  ↓
knowledge_documents 上传 / 粘贴文本
  ↓
knowledge_document.index Celery 任务骨架
  ↓
文档解析 raw_text
  ↓
text_chunker
  ↓
Embedding client
  ↓
knowledge_chunks pgvector 写入
  ↓
knowledge/search
  ↓
question_bank_items 手动 CRUD
  ↓
Q/A Markdown 批量导入
  ↓
KnowledgeRetriever
  ↓
generate-from-knowledge
```

## 16. 验收标准

个人知识库一期完成时，应该能跑通：

1. 用户创建“FastAPI 面试题”集合
2. 上传或粘贴一份 FastAPI 八股文
3. 后台任务完成解析、切分、向量化
4. 用户搜索“依赖注入”能返回相关 chunk
5. 用户手动或批量导入 5 道题
6. 在某个求职项目中选择该集合生成 10 道题
7. 生成题目中记录知识库来源
8. 用户只能检索自己的知识库内容

## 17. 常见实现取舍

### 17.1 先做题库还是先做向量库

建议先做向量库骨架，再做手动题库。

原因是知识库增强出题依赖检索链路；但高质量训练又依赖结构化题库。两者都要有，MVP 可以浅做。

### 17.2 是否需要 LangGraph

个人知识库一期不需要 LangGraph。普通 Celery 任务足够表达：

```text
parse -> clean -> chunk -> embed -> save
```

等后续出现检索-生成-评估-再检索的循环，再考虑把知识库问答或出题链路迁到 LangGraph。

### 17.3 是否要自动总结整篇文档

MVP 不必做。优先保证 chunk 可检索、题目可生成。文档摘要可以后续作为 `knowledge_documents.summary` 增强字段。
