"""QuestionGeneratorAgent：根据项目上下文生成面试题。"""

import json
from typing import Any

from app.agents.base import BaseLLMAgent

QUESTION_PROMPT = """你是一名熟悉 Python 后端、FastAPI、数据库、RAG 和 Agent 面试的题目生成专家。

你的任务是基于候选人的求职项目、岗位要求、匹配报告，生成高质量面试题。

面试模式：
{mode}

难度：
{difficulty}

题目数量：
{count}

简历分析：
{resume_analysis}

JD 分析：
{jd_analysis}

匹配报告：
{match_report}

知识库检索片段：
{retrieved_knowledge}

结构化题库条目：
{question_bank_items}

请严格输出 JSON，不要输出 Markdown。

输出字段：
- questions: object[]
  - type: 与入参 mode 一致
  - difficulty: 与入参 difficulty 一致
  - question: 面试问题
  - reference_answer: 参考答案
  - evaluation_points: string[] 评价要点
  - source_refs: string[] 可选，引用的 chunk_id 或 question_bank_item_id

要求：
1. 题目必须优先覆盖匹配报告中的 missing_skills 和 interview_focus。
2. 不要整段复制原文，要改写成面试官自然会问的问题。
3. 参考答案必须贴合应届生面试表达，不能过度学术化。
4. 至少 30% 题目要结合用户简历项目或目标 JD。
5. 如果使用知识库资料，必须在 source_refs 中记录来源 ID。
6. 生成正好 {count} 道题。
"""


class QuestionGeneratorAgent(BaseLLMAgent):
    """面试题生成 Agent，根据项目上下文生成面试题。"""

    def __init__(
        self,
        mode: str,
        difficulty: str,
        count: int,
        resume_analysis: dict[str, Any] | None = None,
        jd_analysis: dict[str, Any] | None = None,
        match_report: dict[str, Any] | None = None,
        retrieved_knowledge: list[dict[str, Any]] | None = None,
        question_bank_items: list[dict[str, Any]] | None = None,
        model: str = "qwen3-max-latest",
        api_key: str | None = None,
    ):
        super().__init__(model=model, api_key=api_key)
        self.mode = mode
        self.difficulty = difficulty
        self.count = count
        self.resume_analysis = resume_analysis
        self.jd_analysis = jd_analysis
        self.match_report = match_report
        self.retrieved_knowledge = retrieved_knowledge or []
        self.question_bank_items = question_bank_items or []

    def _build_prompt(self) -> str:
        return QUESTION_PROMPT.format(
            mode=self.mode,
            difficulty=self.difficulty,
            count=self.count,
            resume_analysis=json.dumps(self.resume_analysis or {}, ensure_ascii=False),
            jd_analysis=json.dumps(self.jd_analysis or {}, ensure_ascii=False),
            match_report=json.dumps(self.match_report or {}, ensure_ascii=False),
            retrieved_knowledge=json.dumps(self.retrieved_knowledge, ensure_ascii=False),
            question_bank_items=json.dumps(self.question_bank_items, ensure_ascii=False),
        )

    def _validate_output(self, result: dict[str, Any]) -> None:
        questions = result.get("questions")
        if not isinstance(questions, list):
            raise ValueError("questions must be a list")
        if len(questions) == 0:
            raise ValueError("questions must not be empty")

        required_keys = {"question", "evaluation_points"}
        for i, q in enumerate(questions):
            if not isinstance(q, dict):
                raise ValueError(f"questions[{i}] must be an object")
            for key in required_keys:
                if key not in q:
                    q[key] = [] if key == "evaluation_points" else ""

            # 兜底字段，避免模型漏填导致保存失败。
            q.setdefault("type", self.mode)
            q.setdefault("difficulty", self.difficulty)
            q.setdefault("reference_answer", "")
            q.setdefault("source_refs", [])
            if not isinstance(q.get("evaluation_points"), list):
                q["evaluation_points"] = []
            if not isinstance(q.get("source_refs"), list):
                q["source_refs"] = []
