"""JDAnalyzerAgent：分析岗位描述文本，输出结构化 JD 分析结果。"""

from typing import Any

from backend.app.agents.base import BaseLLMAgent

JD_PROMPT = """你是一名技术招聘 JD 分析专家。

请分析下面的岗位描述，判断岗位方向并提取面试重点。

岗位描述：
{jd_text}

请严格输出 JSON，不要输出 Markdown。

输出字段：
- direction: python_backend | agent_engineer | llm_application | unknown
- required_skills: string[]
- bonus_skills: string[]
- interview_topics: string[]
- risk_notes: string[]

要求：
1. 区分必备技能和加分技能。
2. 面试重点要具体，不要只写"Python 基础"这种笼统词。
3. 如果 JD 同时包含后端和 Agent，优先识别真实核心职责。
"""


class JDAnalyzerAgent(BaseLLMAgent):
    """JD 分析 Agent，调用 LLM 对岗位描述做结构化分析。"""

    def __init__(
        self,
        jd_text: str,
        model: str = "qwen3-max-latest",
        api_key: str | None = None,
    ):
        super().__init__(model=model, api_key=api_key)
        self.jd_text = jd_text

    def _build_prompt(self) -> str:
        return JD_PROMPT.format(jd_text=self.jd_text)

    def _validate_output(self, result: dict[str, Any]) -> None:
        self._validate_direction(result, field="direction")
        self._ensure_array_fields(
            result,
            ("required_skills", "bonus_skills", "interview_topics", "risk_notes"),
        )
