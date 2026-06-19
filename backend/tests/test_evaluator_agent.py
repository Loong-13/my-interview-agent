"""EvaluatorAgent 单元测试。"""

import json
from unittest.mock import patch

import pytest

from backend.app.agents.evaluator_agent import EvaluatorAgent

VALID_MOCK_RESPONSE = {
    "overall_score": 72,
    "scores": {
        "python_foundation": 75,
        "backend_engineering": 70,
        "database_understanding": 68,
        "agent_understanding": 72,
        "project_depth": 70,
        "communication": 78,
    },
    "strengths": ["表达清晰"],
    "weaknesses": ["RAG 评估方法不清楚"],
    "suggestions": ["补充召回率评估"],
    "recommended_topics": ["RAG 召回评估", "Agent 异常处理"],
    "improved_answers": [
        {"question": "如何评估 RAG 效果？", "improved_answer": "从检索和生成两层评估。"}
    ],
}


@pytest.fixture
def agent():
    return EvaluatorAgent(
        mode="agent_basic",
        messages=[
            {"role": "interviewer", "content": "介绍你的项目"},
            {"role": "candidate", "content": "做了一个 RAG 问答系统"},
        ],
    )


def test_build_prompt_fills_template(agent):
    prompt = agent._build_prompt()
    assert "agent_basic" in prompt
    assert "RAG 问答系统" in prompt


def test_validate_valid_output(agent):
    agent._validate_output(VALID_MOCK_RESPONSE)


def test_validate_invalid_overall_score(agent):
    with pytest.raises(ValueError, match="overall_score"):
        agent._validate_output({"overall_score": 999, "scores": {}})


def test_validate_missing_scores(agent):
    """缺失维度分应被兜底为 0。"""
    data = {"overall_score": 70, "scores": {}}
    agent._validate_output(data)
    assert data["scores"]["python_foundation"] == 0
    assert data["scores"]["communication"] == 0


def test_validate_invalid_dimension_score(agent):
    with pytest.raises(ValueError, match="scores.python_foundation"):
        agent._validate_output({
            "overall_score": 70,
            "scores": {"python_foundation": 999},
        })


def test_validate_arrays_get_defaults(agent):
    data = {"overall_score": 50, "scores": {}}
    agent._validate_output(data)
    assert data["strengths"] == []
    assert data["weaknesses"] == []
    assert data["suggestions"] == []
    assert data["improved_answers"] == []


@patch.object(EvaluatorAgent, "_call_llm")
def test_analyze_returns_valid_json(mock_call, agent):
    mock_call.return_value = json.dumps(VALID_MOCK_RESPONSE, ensure_ascii=False)
    result = agent.analyze()
    assert result["overall_score"] == 72
    assert result["scores"]["communication"] == 78
    assert len(result["improved_answers"]) == 1


@patch.object(EvaluatorAgent, "_call_llm")
def test_analyze_retries_then_fails(mock_call, agent):
    mock_call.return_value = "not json"
    with pytest.raises(RuntimeError, match="EvaluatorAgent failed after"):
        agent.analyze(max_retries=2)
