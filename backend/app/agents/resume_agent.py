"""ResumeAgent：分析简历文本，输出结构化分析结果。"""

from typing import Any

from app.agents.base import BaseLLMAgent

RESUME_PROMPT = """你是一名熟悉 Python 后端和 AI Agent 应用开发岗位的简历评审专家。

你的任务是分析应届生简历，判断其是否适合目标方向。

目标方向：
{target_direction}

简历文本：
{resume_text}

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
"""


class ResumeAgent(BaseLLMAgent):
    """简历分析 Agent，调用 LLM 对简历文本做结构化分析。"""

    def __init__(
        self,
        resume_text: str,
        target_direction: str = "agent_engineer",
        model: str = "qwen3-max-latest",
        api_key: str | None = None,
    ):
        super().__init__(model=model, api_key=api_key)
        self.resume_text = resume_text
        self.target_direction = target_direction

    def _build_prompt(self) -> str:
        return RESUME_PROMPT.format(
            target_direction=self.target_direction,
            resume_text=self.resume_text,
        )

    def _validate_output(self, result: dict[str, Any]) -> None:
        self._validate_direction(result, field="detected_direction")
        self._ensure_array_fields(
            result,
            ("skills", "project_deep_dive_points", "weaknesses", "suggestions"),
        )
        if "projects" not in result or not isinstance(result.get("projects"), list):
            result["projects"] = []

    def judge_candidate(self) -> bool:
        """判断简历方向是否与目标方向匹配。"""
        analysis = self.analyze()
        return analysis.get("detected_direction") == self.target_direction
