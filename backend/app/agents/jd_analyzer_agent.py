"""为未来的岗位描述分析 Agent 预留位置。"""
import dashscope
import os
import json
jd_prompt="""
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
"""

class JDAnalyzerAgent:
    def __init__(self, jd_text: str):
        self.jd_text = jd_text

    def JDAnalyze(self) -> dict:
        """分析 JD，返回 JSON 结果。"""
        prompt = jd_prompt.format(jd_text=self.jd_text)
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
        content = response.output.choices[0].message.content
        return json.loads(content)