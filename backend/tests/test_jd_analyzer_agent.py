"""JDAnalyzerAgent 单元测试。

测试覆盖：
1. Prompt 格式正确填充
2. JSON 输出校验逻辑
3. 非法 direction 拒绝
4. 数组字段兜底
5. 完整 analyze 流程
6. 重试机制
"""

import json
from unittest.mock import patch

import pytest

from backend.app.agents.jd_analyzer_agent import JDAnalyzerAgent

# ── 模拟 LLM 返回合法 JSON ─────────────────────────────


VALID_MOCK_RESPONSE = {
    "direction": "agent_engineer",
    "required_skills": ["Python", "RAG", "Prompt Engineering", "FastAPI"],
    "bonus_skills": ["LangGraph", "Docker", "PostgreSQL"],
    "interview_topics": ["Agent 工具调用机制", "RAG 检索流程", "FastAPI 依赖注入"],
    "risk_notes": ["JD 对 Agent 框架要求不明确，需进一步确认"],
}


@pytest.fixture
def agent():
    return JDAnalyzerAgent(jd_text="测试 JD")


# ── Prompt 填充 ────────────────────────────────────────


def test_build_prompt_fills_template(agent):
    prompt = agent._build_prompt()
    assert "测试 JD" in prompt


# ── JSON 校验 ──────────────────────────────────────────


def test_validate_valid_output(agent):
    agent._validate_output(VALID_MOCK_RESPONSE)  # 不抛异常即通过


def test_validate_invalid_direction(agent):
    with pytest.raises(ValueError, match="Invalid direction"):
        agent._validate_output({"direction": "frontend"})


def test_validate_missing_direction(agent):
    with pytest.raises(ValueError, match="Invalid direction"):
        agent._validate_output({})


def test_validate_arrays_get_defaults(agent):
    """数组字段缺失时应自动兜底为空列表。"""
    data = {"direction": "agent_engineer"}
    agent._validate_output(data)
    assert data["required_skills"] == []
    assert data["bonus_skills"] == []
    assert data["interview_topics"] == []
    assert data["risk_notes"] == []


# ── Analyze 完整流程 ───────────────────────────────────


@patch.object(JDAnalyzerAgent, "_call_llm")
def test_analyze_returns_valid_json(mock_call, agent):
    mock_call.return_value = json.dumps(VALID_MOCK_RESPONSE, ensure_ascii=False)
    result = agent.analyze()
    assert result["direction"] == "agent_engineer"
    assert result["required_skills"] == ["Python", "RAG", "Prompt Engineering", "FastAPI"]
    assert result["bonus_skills"] == ["LangGraph", "Docker", "PostgreSQL"]
    assert len(result["interview_topics"]) == 3
    assert len(result["risk_notes"]) == 1


@patch.object(JDAnalyzerAgent, "_call_llm")
def test_analyze_retries_on_json_error(mock_call, agent):
    """首次 JSON 解析失败，重试后成功。"""
    mock_call.side_effect = [
        '{"direction": "agent_engineer", invalid json',
        json.dumps(VALID_MOCK_RESPONSE, ensure_ascii=False),
    ]
    result = agent.analyze(max_retries=2)
    assert mock_call.call_count == 2
    assert result["direction"] == "agent_engineer"


@patch.object(JDAnalyzerAgent, "_call_llm")
def test_analyze_retries_then_fails(mock_call, agent):
    """所有重试都失败时抛出 RuntimeError。"""
    mock_call.return_value = "not valid json at all"
    with pytest.raises(RuntimeError, match="JDAnalyzerAgent failed after"):
        agent.analyze(max_retries=2)
    assert mock_call.call_count == 2
