"""QuestionGeneratorAgent 单元测试。"""

import json
from unittest.mock import patch

import pytest

from backend.app.agents.question_generator_agent import QuestionGeneratorAgent

VALID_MOCK_RESPONSE = {
    "questions": [
        {
            "type": "agent_basic",
            "difficulty": "intern",
            "question": "请解释 Agent 中 Tool Calling 的工作流程。",
            "reference_answer": "Tool Calling 是 LLM 根据用户意图选择并调用外部工具的能力。",
            "evaluation_points": ["工具选择逻辑", "参数构造", "错误处理"],
        },
        {
            "question": "RAG 系统中如何评估检索效果？",
            "evaluation_points": ["recall@k", "MRR"],
        },
    ],
}


@pytest.fixture
def agent():
    return QuestionGeneratorAgent(
        mode="agent_basic",
        difficulty="intern",
        count=3,
        resume_analysis={"skills": ["Python"]},
    )


def test_build_prompt_fills_template(agent):
    prompt = agent._build_prompt()
    assert "agent_basic" in prompt
    assert "intern" in prompt


def test_validate_valid_output(agent):
    agent._validate_output(VALID_MOCK_RESPONSE)


def test_validate_empty_questions(agent):
    with pytest.raises(ValueError, match="questions must not be empty"):
        agent._validate_output({"questions": []})


def test_validate_missing_questions(agent):
    with pytest.raises(ValueError, match="questions must be a list"):
        agent._validate_output({})


def test_validate_fields_default_fill(agent):
    """缺失字段应被自动填充兜底值。"""
    data = {"questions": [{"question": "测试题"}]}
    agent._validate_output(data)
    q = data["questions"][0]
    assert q["evaluation_points"] == []
    assert q["reference_answer"] == ""
    assert q["type"] == "agent_basic"
    assert q["difficulty"] == "intern"


@patch.object(QuestionGeneratorAgent, "_call_llm")
def test_analyze_returns_valid_json(mock_call, agent):
    mock_call.return_value = json.dumps(VALID_MOCK_RESPONSE, ensure_ascii=False)
    result = agent.analyze()
    assert len(result["questions"]) == 2
    assert result["questions"][0]["question"]


@patch.object(QuestionGeneratorAgent, "_call_llm")
def test_analyze_retries_then_fails(mock_call, agent):
    mock_call.return_value = "not json"
    with pytest.raises(RuntimeError, match="QuestionGeneratorAgent failed after"):
        agent.analyze(max_retries=2)
