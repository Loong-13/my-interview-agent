"""InterviewerAgent 单元测试。"""

import json
from unittest.mock import patch

import pytest

from backend.app.agents.interviewer_agent import InterviewerAgent

VALID_MOCK_RESPONSE = {
    "feedback": "回答说明了项目方向，但缺少工程细节。",
    "next_question": "你这个项目的文档切分策略是什么？chunk size 是怎么决定的？",
    "should_continue": True,
}


@pytest.fixture
def agent():
    return InterviewerAgent(
        mode="agent_basic",
        difficulty="intern",
        history_messages=[
            {"role": "interviewer", "content": "请介绍你的 Agent 项目。"},
            {"role": "candidate", "content": "我做了一个文档问答系统。"},
        ],
    )


def test_build_prompt_fills_template(agent):
    prompt = agent._build_prompt()
    assert "agent_basic" in prompt
    assert "文档问答系统" in prompt


def test_validate_valid_output(agent):
    agent._validate_output(VALID_MOCK_RESPONSE)


def test_validate_missing_feedback(agent):
    with pytest.raises(ValueError, match="feedback"):
        agent._validate_output({"next_question": "?", "should_continue": True})


def test_validate_missing_next_question(agent):
    with pytest.raises(ValueError, match="next_question"):
        agent._validate_output({"feedback": "OK", "should_continue": True})


def test_should_continue_string_coercion(agent):
    """LLM 返回字符串 "true" 时应被转为 bool。"""
    data = {"feedback": "OK", "next_question": "继续？", "should_continue": "true"}
    agent._validate_output(data)
    assert data["should_continue"] is True


@patch.object(InterviewerAgent, "_call_llm")
def test_analyze_returns_valid_json(mock_call, agent):
    mock_call.return_value = json.dumps(VALID_MOCK_RESPONSE, ensure_ascii=False)
    result = agent.analyze()
    assert result["feedback"] == "回答说明了项目方向，但缺少工程细节。"
    assert "文档切分" in result["next_question"]
    assert result["should_continue"] is True


@patch.object(InterviewerAgent, "_call_llm")
def test_analyze_retries_then_fails(mock_call, agent):
    mock_call.return_value = "not json"
    with pytest.raises(RuntimeError, match="InterviewerAgent failed after"):
        agent.analyze(max_retries=2)
