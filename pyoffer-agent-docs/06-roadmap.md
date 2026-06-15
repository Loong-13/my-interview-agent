# 06. 开发路线图与任务拆分

## 1. 开发阶段总览

### Phase 1: 文本版 MVP

目标：跑通从简历上传到模拟面试报告的完整闭环。

功能：

- 用户注册 / 登录
- 项目管理
- 简历上传与解析
- JD 保存与分析
- 匹配报告
- 面试题生成
- 文本模拟面试
- 面试报告

### Phase 2: 题库与训练增强

目标：让系统更适合 Python 后端和 Agent 应届生训练。

功能：

- Python 基础专项练习
- FastAPI 专项练习
- 数据库专项练习
- RAG 专项练习
- Agent 专项练习
- 错题本
- 能力雷达图

### Phase 3: 资料上传与 RAG

目标：允许用户上传面试资料和项目文档，并让 AI 基于资料提问。

功能：

- 上传 PDF / DOCX / TXT
- 文档解析
- chunk 切分
- embedding
- pgvector 检索
- 基于资料生成题目
- 面试中引用资料追问

### Phase 4: 语音面试

目标：把文本面试升级为语音面试。

功能：

- 浏览器录音
- 音频上传
- STT 语音转文字
- TTS 语音播放问题
- 面试回放
- 语音表达评分

## 2. Phase 1 任务拆分

### 2.1 后端基础

- 初始化 FastAPI 项目
- 配置 Pydantic Settings
- 配置 SQLAlchemy
- 配置 Alembic
- 配置 PostgreSQL
- 配置 Redis
- 配置 Celery
- 统一异常响应
- 统一日志

验收标准：

- `/health` 可访问
- 数据库连接正常
- Alembic migration 可执行
- Celery worker 可以启动并执行测试任务

### 2.2 用户鉴权

- 注册接口
- 登录接口
- JWT 生成
- 当前用户接口
- 密码哈希
- 路由鉴权依赖

验收标准：

- 用户可以注册登录
- 未登录不能访问项目接口

### 2.3 项目管理

- 创建项目
- 项目列表
- 项目详情
- 更新项目
- 归档项目

验收标准：

- 用户只能访问自己的项目
- 项目支持 direction 和 experience_level

### 2.4 简历上传与解析

- 支持 PDF 上传
- 支持 DOCX 上传
- 文件类型校验
- 文件大小限制
- 文本提取
- 保存 raw_text

验收标准：

- 上传简历后可以看到提取文本
- 解析失败有明确错误状态

### 2.5 AI 接入

- LLM client 封装
- Prompt 模板加载
- JSON 输出解析
- Pydantic 校验
- 简单重试
- Celery 异步任务封装
- 任务状态查询接口

验收标准：

- ResumeAgent 可以返回结构化分析
- JDAnalyzerAgent 可以返回结构化分析
- 长耗时 AI 任务可以通过 task_id 查询状态

### 2.6 匹配报告

- JD 保存
- JD 分析
- 读取最新简历分析
- 调用 MatchAgent
- 保存 match_report

验收标准：

- 能生成 match_score
- 能输出 matched_skills、missing_skills、interview_focus

### 2.7 面试题生成

- 支持选择 mode
- 支持 difficulty
- 支持 count
- 调用 QuestionGeneratorAgent
- 保存 questions

验收标准：

- 能生成 5-10 道和项目相关的问题
- 每道题有 evaluation_points

### 2.8 文本模拟面试

- 创建 interview_session
- 开始面试
- 保存 interviewer 消息
- 保存 candidate 回答
- 调用 InterviewerAgent 追问
- 结束面试

验收标准：

- 能完成至少 5 轮问答
- AI 会基于上一轮回答追问

### 2.9 面试报告

- 读取完整消息记录
- 调用 EvaluatorAgent
- 保存 interview_report
- 获取报告详情

验收标准：

- 报告包含总分、维度分、优点、问题、建议
- 推荐主题和面试内容相关

## 3. 前端页面任务

### 3.1 基础布局

- 登录页
- 注册页
- 项目列表页
- 项目详情页
- 顶部导航
- 登录态处理

### 3.2 项目功能

- 创建项目表单
- 项目卡片
- 项目详情信息

### 3.3 简历与 JD 分析

- 简历上传组件
- JD 输入框
- 分析按钮
- 匹配报告展示
- 技能标签展示

### 3.4 模拟面试

- 面试模式选择
- 对话消息列表
- 回答输入框
- 提交回答
- 结束面试
- 报告入口

### 3.5 报告页

- 总分展示
- 维度评分
- 优点
- 问题
- 推荐复习主题
- 改进版回答

## 4. 推荐开发顺序

```text
后端 health + DB
  ↓
Auth
  ↓
Projects
  ↓
Resume upload + parse
  ↓
Celery worker + tasks
  ↓
LLM client + ResumeAgent
  ↓
JDAnalyzerAgent
  ↓
MatchAgent
  ↓
QuestionGeneratorAgent
  ↓
InterviewerAgent
  ↓
EvaluatorAgent
  ↓
前端联调
```

## 5. MVP 验收标准

MVP 完成时，必须能完成这个流程：

1. 新用户注册登录
2. 创建一个 Agent 实习项目
3. 上传一份简历
4. 粘贴一段 Agent 岗位 JD
5. 生成匹配报告
6. 生成 10 道面试题
7. 完成 5 轮文本面试
8. 生成面试报告

## 6. 后续增强方向

### 产品增强

- 简历改写版本管理
- 面试历史对比
- 能力趋势图
- 练习计划
- 错题本

### 工程增强

- Celery 异步任务
- RAG 文档库
- WebSocket 面试
- 语音输入输出
- LLM 成本统计
- 用户限流

### AI 质量增强

- 标准题库混合生成
- 引用简历证据
- 多模型评估
- 报告质量打分
- Prompt A/B 测试
