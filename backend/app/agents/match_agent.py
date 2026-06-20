"""MatchAgent：对比简历分析和 JD 分析，输出匹配报告。"""

import json
from typing import Any

from app.agents.base import BaseLLMAgent

MATCH_PROMPT = """你是一名求职匹配分析专家。

请根据候选人简历分析结果和 JD 分析结果，生成匹配报告。

简历分析：
{resume_analysis}

JD 分析：
{jd_analysis}

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
"""


class MatchAgent(BaseLLMAgent):
    """匹配分析 Agent，对比简历和 JD 计算匹配分。"""

    def __init__(
        self,
        resume_analysis: dict[str, Any],
        jd_analysis: dict[str, Any],
        model: str | None = None,
        api_key: str | None = None,
    ):
        super().__init__(model=model, api_key=api_key)
        self.resume_analysis = resume_analysis
        self.jd_analysis = jd_analysis

    def _build_prompt(self) -> str:
        return MATCH_PROMPT.format(
            resume_analysis=json.dumps(self.resume_analysis, ensure_ascii=False, indent=2),
            jd_analysis=json.dumps(self.jd_analysis, ensure_ascii=False, indent=2),
        )

    def _validate_output(self, result: dict[str, Any]) -> None:
        score = result.get("match_score")
        if not isinstance(score, (int, float)) or not (0 <= score <= 100):
            raise ValueError(f"match_score must be 0-100 integer, got {score!r}")
        result["match_score"] = int(score)

        self._ensure_array_fields(
            result,
            ("matched_skills", "missing_skills", "interview_focus", "suggestions"),
        )
