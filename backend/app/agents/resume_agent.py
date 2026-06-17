"""为未来的简历分析 Agent 预留位置。"""
import json
import dashscope
import os
resume_prompt="""
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
"""

class ResumeAgent:
    def __init__(self, resume_text: str, target_direction: str):
        self.resume_text = resume_text
        self.target_direction = target_direction

    def ResumeAnalyze(self) -> dict:
        """分析简历，返回 JSON 结果。"""
        prompt = resume_prompt.format(
            resume_text=self.resume_text,
            target_direction=self.target_direction,
        )
        messages = [
            {"role": "system", "content": prompt},
        ]
        response=dashscope.Generation.call(
            model="Qwen3.7-max",
            api_key=os.getenv("DASHSCOPE_API_KEY"),
            messages=messages,
            temperature=0,
            result_format="message",
            response_format={"type": "json_object"}
        )
        content=response.output.choices[0].message.content
        return json.loads(content)

    def judge_candidate(self) -> bool:
        """判断简历是否符合目标方向。"""
        result = self.analyze()
        return result["detected_direction"] == self.target_direction
