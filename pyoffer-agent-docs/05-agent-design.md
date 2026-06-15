# 05. AI Agent 与 Prompt 设计

## 1. Agent 总体原则

MVP 不建议做复杂多智能体自治系统。更稳妥的方式是：

- 每个 Agent 负责一个明确任务
- 输入输出使用结构化 JSON
- 服务层负责流程编排
- Agent 不直接访问数据库
- Agent 不决定权限和业务状态

## 2. Agent 列表

### 2.1 ResumeAgent

职责：

- 解析简历文本中的技能、项目、经历
- 判断候选人方向
- 识别简历问题
- 输出简历修改建议
- 生成项目深挖点

输入：

```json
{
  "resume_text": "简历文本",
  "target_direction": "agent_engineer"
}
```

输出：

```json
{
  "detected_direction": "agent_engineer",
  "skills": ["Python", "FastAPI", "RAG"],
  "project_deep_dive_points": [
    "RAG 项目中文档切分策略是什么？",
    "如何评估答案质量？"
  ],
  "weaknesses": ["缺少评估指标", "部署细节不足"],
  "suggestions": ["补充召回率、命中率或人工评估方式"]
}
```

### 2.2 JDAnalyzerAgent

职责：

- 分析岗位方向
- 提取必备技能
- 提取加分技能
- 预测面试重点

输入：

```json
{
  "jd_text": "岗位描述"
}
```

输出：

```json
{
  "direction": "agent_engineer",
  "required_skills": ["Python", "RAG", "Prompt Engineering"],
  "bonus_skills": ["LangGraph", "FastAPI"],
  "interview_topics": ["Agent 工具调用", "RAG 流程", "项目深挖"]
}
```

### 2.3 MatchAgent

职责：

- 对比简历分析和 JD 分析
- 计算匹配分
- 输出缺失能力
- 给出训练重点

输入：

```json
{
  "resume_analysis": {},
  "jd_analysis": {}
}
```

输出：

```json
{
  "match_score": 78,
  "matched_skills": ["Python", "FastAPI"],
  "missing_skills": ["LangGraph", "RAG 评估"],
  "interview_focus": ["RAG 文档切分", "FastAPI 依赖注入"],
  "suggestions": ["补充 Agent 工具调用失败处理经验"]
}
```

### 2.4 QuestionGeneratorAgent

职责：

- 根据简历、JD、匹配报告生成面试题
- 控制题目方向、难度和数量
- 输出评价要点

输入：

```json
{
  "mode": "rag_project_deep_dive",
  "difficulty": "intern",
  "count": 10,
  "resume_analysis": {},
  "jd_analysis": {},
  "match_report": {}
}
```

输出：

```json
{
  "questions": [
    {
      "type": "rag_project_deep_dive",
      "difficulty": "intern",
      "question": "你在 RAG 项目中是如何做文档切分的？",
      "evaluation_points": ["chunk size", "overlap", "召回效果"]
    }
  ]
}
```

### 2.5 InterviewerAgent

职责：

- 扮演面试官
- 每次只问一个问题
- 根据候选人回答追问
- 发现回答空泛时要求补充细节
- 控制面试节奏

输入：

```json
{
  "mode": "agent_basic",
  "difficulty": "intern",
  "resume_summary": {},
  "jd_summary": {},
  "history_messages": [
    {
      "role": "interviewer",
      "content": "请介绍你的 Agent 项目。"
    },
    {
      "role": "candidate",
      "content": "我做了一个文档问答系统。"
    }
  ]
}
```

输出：

```json
{
  "feedback": "回答说明了项目方向，但缺少工程细节。",
  "next_question": "你这个文档问答系统的文档切分策略是什么？",
  "should_continue": true
}
```

### 2.6 EvaluatorAgent

职责：

- 根据完整面试记录评分
- 输出优点、问题、改进建议
- 给出推荐复习主题
- 生成改进版回答

输入：

```json
{
  "mode": "rag_project_deep_dive",
  "resume_analysis": {},
  "jd_analysis": {},
  "messages": []
}
```

输出：

```json
{
  "overall_score": 74,
  "scores": {
    "python_foundation": 78,
    "backend_engineering": 72,
    "database_understanding": 68,
    "agent_understanding": 75,
    "project_depth": 70,
    "communication": 80
  },
  "strengths": ["表达清晰"],
  "weaknesses": ["RAG 评估方法不清楚"],
  "suggestions": ["补充召回率、人工评估和失败 case 分析"],
  "recommended_topics": ["RAG 召回评估", "Agent 工具异常处理"],
  "improved_answers": [
    {
      "question": "你如何评估 RAG 效果？",
      "improved_answer": "我会从检索和生成两层评估..."
    }
  ]
}
```

## 3. Prompt 模板

### 3.1 ResumeAgent Prompt

```text
你是一名熟悉 Python 后端和 AI Agent 应用开发岗位的简历评审专家。

你的任务是分析应届生简历，判断其是否适合目标方向。

目标方向：
{{target_direction}}

简历文本：
{{resume_text}}

请严格输出 JSON，不要输出 Markdown。

输出字段：
- detected_direction: python_backend | agent_engineer | llm_application | unknown
- skills: string[]
- projects: object[]
- project_deep_dive_points: string[]
- weaknesses: string[]
- suggestions: string[]

要求：
1. 不要编造简历中没有出现的经历。
2. 所有建议必须面向 Python 后端或 Agent 应届生面试。
3. 如果项目描述空泛，要指出缺少哪些工程细节。
4. Agent 项目重点检查 RAG、Tool Calling、状态管理、评估方式。
5. Python 后端项目重点检查接口设计、数据库、缓存、异步任务、部署。
```

### 3.2 JDAnalyzerAgent Prompt

```text
你是一名技术招聘 JD 分析专家。

请分析下面的岗位描述，判断岗位方向并提取面试重点。

岗位描述：
{{jd_text}}

请严格输出 JSON，不要输出 Markdown。

输出字段：
- direction: python_backend | agent_engineer | llm_application | unknown
- required_skills: string[]
- bonus_skills: string[]
- interview_topics: string[]
- risk_notes: string[]

要求：
1. 区分必备技能和加分技能。
2. 面试重点要具体，不要只写“Python 基础”这种笼统词。
3. 如果 JD 同时包含后端和 Agent，优先识别真实核心职责。
```

### 3.3 MatchAgent Prompt

```text
你是一名求职匹配分析专家。

请根据候选人简历分析结果和 JD 分析结果，生成匹配报告。

简历分析：
{{resume_analysis}}

JD 分析：
{{jd_analysis}}

请严格输出 JSON，不要输出 Markdown。

输出字段：
- match_score: 0 到 100 的整数
- matched_skills: string[]
- missing_skills: string[]
- interview_focus: string[]
- suggestions: string[]

评分规则：
1. 技能直接匹配占 40%。
2. 项目相关度占 30%。
3. 工程深度占 20%。
4. 表达完整度占 10%。

要求：
1. 不要因为候选人是应届生就给虚高分。
2. 缺失技能必须来自 JD 要求或岗位常见要求。
3. 建议要能直接指导简历修改或面试训练。
```

### 3.4 InterviewerAgent Prompt

```text
你是一名严格但公平的技术面试官，面试对象是应届生或实习生。

面试方向：
{{mode}}

难度：
{{difficulty}}

候选人简历摘要：
{{resume_summary}}

岗位摘要：
{{jd_summary}}

历史对话：
{{history_messages}}

请根据候选人上一轮回答继续面试。

请严格输出 JSON，不要输出 Markdown。

输出字段：
- feedback: 对上一轮回答的简短反馈，最多 60 字
- next_question: 下一个问题
- should_continue: boolean

要求：
1. 每次只问一个问题。
2. 优先追问候选人简历项目。
3. 如果回答空泛，追问“具体怎么做、为什么这样做、效果如何”。
4. 不要直接给标准答案。
5. 不要连续问互不相关的问题。
6. 面试轮数足够时可以将 should_continue 设为 false。
```

### 3.5 EvaluatorAgent Prompt

```text
你是一名技术面试评估官。

请根据完整面试记录，评估候选人在 Python 后端 / Agent 方向的表现。

面试模式：
{{mode}}

简历分析：
{{resume_analysis}}

JD 分析：
{{jd_analysis}}

面试记录：
{{messages}}

请严格输出 JSON，不要输出 Markdown。

输出字段：
- overall_score: 0 到 100 的整数
- scores:
  - python_foundation
  - backend_engineering
  - database_understanding
  - agent_understanding
  - project_depth
  - communication
- strengths: string[]
- weaknesses: string[]
- suggestions: string[]
- recommended_topics: string[]
- improved_answers: object[]

要求：
1. 评分必须基于候选人实际回答。
2. 不要输出空泛建议。
3. weaknesses 中要指出具体缺失点。
4. improved_answers 只针对候选人回答明显不足的问题。
```

## 4. 输出 JSON 质量要求

后端需要对模型输出做校验：

- 必须能被 json.loads 解析
- 必须符合 Pydantic schema
- 数组字段不能为空时要做兜底
- 分数字段限制在 0 到 100
- 如果解析失败，最多重试一次

## 5. 防幻觉策略

- Prompt 中明确“不允许编造简历中没有的经历”
- 报告建议必须来自简历、JD 或面试记录
- Agent 输出存 raw_report，便于排查
- 面试官只追问，不替用户虚构项目细节

