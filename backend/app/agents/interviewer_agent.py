"""InterviewerAgent：扮演面试官，追问候选人。"""

import json
from typing import Any

from app.agents.base import BaseLLMAgent

INTERVIEWER_PROMPT = """你是一名严格但公平的技术面试官，面试对象是应届生或实习生。

面试方向：
{mode}

难度：
{difficulty}

候选人简历摘要：
{resume_summary}

岗位摘要：
{jd_summary}

历史对话：
{history_messages}

请根据候选人上一轮回答继续面试。

请严格输出 JSON，不要输出 Markdown。

输出字段：
- feedback: 对上一轮回答的简短反馈，最多 60 字
- next_question: 下一个问题
- should_continue: boolean

要求：
1. 每次只问一个问题。
2. 优先追问候选人简历项目。
3. 如果回答空泛，追问"具体怎么做、为什么这样做、效果如何"。
4. 不要直接给标准答案。
5. 不要连续问互不相关的问题。
6. 面试轮数足够时可以将 should_continue 设为 false。
"""


class InterviewerAgent(BaseLLMAgent):
    """面试官 Agent，在面试中扮演技术面试官角色。

    注意：面试官 Agent 是同步调用（非 Celery），用户在等待下一题。
    """

    def __init__(
        self,
        mode: str,
        difficulty: str,
        history_messages: list[dict[str, str]],
        resume_summary: dict[str, Any] | None = None,
        jd_summary: dict[str, Any] | None = None,
        model: str | None = None,
        api_key: str | None = None,
    ):
        super().__init__(model=model, api_key=api_key)
        self.mode = mode
        self.difficulty = difficulty
        self.history_messages = history_messages
        self.resume_summary = resume_summary
        self.jd_summary = jd_summary

    def _build_prompt(self) -> str:
        return INTERVIEWER_PROMPT.format(
            mode=self.mode,
            difficulty=self.difficulty,
            resume_summary=json.dumps(self.resume_summary or {}, ensure_ascii=False),
            jd_summary=json.dumps(self.jd_summary or {}, ensure_ascii=False),
            history_messages=json.dumps(self.history_messages, ensure_ascii=False, indent=2),
        )

    def _validate_output(self, result: dict[str, Any]) -> None:
        feedback = result.get("feedback")
        next_question = result.get("next_question")
        should_continue = result.get("should_continue")

        if not isinstance(feedback, str) or not feedback:
            raise ValueError("feedback is required and must be a non-empty string")
        if not isinstance(next_question, str) or not next_question:
            raise ValueError("next_question is required and must be a non-empty string")
        if not isinstance(should_continue, bool):
            # 兜底：如果 LLM 输出字符串，转为 bool
            if isinstance(should_continue, str):
                result["should_continue"] = should_continue.lower() in ("true", "yes", "1")
            else:
                result["should_continue"] = True
