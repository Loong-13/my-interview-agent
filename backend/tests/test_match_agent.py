"""MatchAgent 单元测试。"""

import json
from unittest.mock import patch

import pytest

from backend.app.agents.match_agent import MatchAgent

VALID_MOCK_RESPONSE = {
    "match_score": 65,
    "matched_skills": ["Python", "FastAPI"],
    "missing_skills": ["LangGraph", "Docker"],
    "interview_focus": ["RAG 检索流程", "Agent 工具调用"],
    "suggestions": ["补充 LangGraph 项目经验", "学习容器化部署"],
}


@pytest.fixture
def agent():
    return MatchAgent(
        resume_analysis={"detected_direction": "agent_engineer", "skills": ["Python", "FastAPI"]},
        jd_analysis={"direction": "agent_engineer", "required_skills": ["Python", "LangGraph"]},
    )


def test_build_prompt_fills_template(agent):
    prompt = agent._build_prompt()
    assert "agent_engineer" in prompt
    assert "LangGraph" in prompt


def test_validate_valid_output(agent):
    agent._validate_output(VALID_MOCK_RESPONSE)


def test_validate_invalid_score(agent):
    with pytest.raises(ValueError, match="match_score"):
        agent._validate_output({"match_score": 150})


def test_validate_missing_score(agent):
    with pytest.raises(ValueError, match="match_score"):
        agent._validate_output({})


def test_validate_arrays_get_defaults(agent):
    data = {"match_score": 50}
    agent._validate_output(data)
    assert data["matched_skills"] == []
    assert data["missing_skills"] == []
    assert data["interview_focus"] == []
    assert data["suggestions"] == []


@patch.object(MatchAgent, "_call_llm")
def test_analyze_returns_valid_json(mock_call, agent):
    mock_call.return_value = json.dumps(VALID_MOCK_RESPONSE, ensure_ascii=False)
    result = agent.analyze()
    assert result["match_score"] == 65
    assert result["matched_skills"] == ["Python", "FastAPI"]
    assert result["missing_skills"] == ["LangGraph", "Docker"]


@patch.object(MatchAgent, "_call_llm")
def test_analyze_retries_then_fails(mock_call, agent):
    mock_call.return_value = "not valid json"
    with pytest.raises(RuntimeError, match="MatchAgent failed after"):
        agent.analyze(max_retries=2)
