"""EvaluatorAgent：根据完整面试记录评分。"""

import json
from typing import Any

from backend.app.agents.base import BaseLLMAgent

EVALUATOR_PROMPT = """你是一名技术面试评估官。

请根据完整面试记录，评估候选人在 Python 后端 / Agent 方向的表现。

面试模式：
{mode}

简历分析：
{resume_analysis}

JD 分析：
{jd_analysis}

面试记录：
{messages}

请严格输出 JSON，不要输出 Markdown。

输出字段：
- overall_score: 0 到 100 的整数
- scores:
  - python_foundation: 0-100
  - backend_engineering: 0-100
  - database_understanding: 0-100
  - agent_understanding: 0-100
  - project_depth: 0-100
  - communication: 0-100
- strengths: string[]
- weaknesses: string[]
- suggestions: string[]
- recommended_topics: string[]
- improved_answers: object[]
  - question: 原问题
  - improved_answer: 改进版回答

要求：
1. 评分必须基于候选人实际回答。
2. 不要输出空泛建议。
3. weaknesses 中要指出具体缺失点。
4. improved_answers 只针对候选人回答明显不足的问题。
"""

EXPECTED_DIMENSIONS = (
    "python_foundation",
    "backend_engineering",
    "database_understanding",
    "agent_understanding",
    "project_depth",
    "communication",
)


class EvaluatorAgent(BaseLLMAgent):
    """面试评估 Agent，对完整面试记录做多维度评分。"""

    def __init__(
        self,
        mode: str,
        messages: list[dict[str, Any]],
        resume_analysis: dict[str, Any] | None = None,
        jd_analysis: dict[str, Any] | None = None,
        model: str = "qwen3-max-latest",
        api_key: str | None = None,
    ):
        super().__init__(model=model, api_key=api_key)
        self.mode = mode
        self.messages = messages
        self.resume_analysis = resume_analysis
        self.jd_analysis = jd_analysis

    def _build_prompt(self) -> str:
        return EVALUATOR_PROMPT.format(
            mode=self.mode,
            resume_analysis=json.dumps(self.resume_analysis or {}, ensure_ascii=False),
            jd_analysis=json.dumps(self.jd_analysis or {}, ensure_ascii=False),
            messages=json.dumps(self.messages, ensure_ascii=False, indent=2),
        )

    def _validate_output(self, result: dict[str, Any]) -> None:
        # 总分校验
        overall = result.get("overall_score")
        if not isinstance(overall, (int, float)) or not (0 <= overall <= 100):
            raise ValueError(f"overall_score must be 0-100, got {overall!r}")
        result["overall_score"] = int(overall)

        # 维度分校验
        scores = result.get("scores")
        if not isinstance(scores, dict):
            raise ValueError("scores is required and must be an object")
        for dim in EXPECTED_DIMENSIONS:
            if dim not in scores:
                scores[dim] = 0
            s = scores[dim]
            if not isinstance(s, (int, float)) or not (0 <= s <= 100):
                raise ValueError(f"scores.{dim} must be 0-100, got {s!r}")
            scores[dim] = int(s)

        # 数组字段兜底
        self._ensure_array_fields(
            result,
            ("strengths", "weaknesses", "suggestions", "recommended_topics"),
        )

        # improved_answers 兜底
        improved = result.get("improved_answers")
        if not isinstance(improved, list):
            result["improved_answers"] = []
