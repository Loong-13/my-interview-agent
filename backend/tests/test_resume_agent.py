"""ResumeAgent 单元测试。

测试覆盖：
1. Prompt 格式正确填充
2. JSON 输出校验逻辑
3. 非法 direction 拒绝
4. 数组字段兜底
"""

import json
from unittest.mock import patch

import pytest

from backend.app.agents.resume_agent import ResumeAgent

# ── 模拟 LLM 返回合法 JSON ─────────────────────────────


VALID_MOCK_RESPONSE = {
    "detected_direction": "agent_engineer",
    "skills": ["Python", "FastAPI", "RAG", "PostgreSQL"],
    "projects": [
        {
            "name": "AI 文档问答系统",
            "tech_stack": ["FastAPI", "pgvector", "OpenAI"],
            "description": "基于 RAG 的智能问答平台",
        }
    ],
    "project_deep_dive_points": [
        "你在 RAG 项目中如何选择 chunk size？",
        "你如何处理向量检索召回不准的问题？",
    ],
    "weaknesses": ["缺少 RAG 评估指标", "数据库设计描述不足"],
    "suggestions": ["补充召回率评估方法", "说明接口鉴权和部署方式"],
}


@pytest.fixture
def agent():
    return ResumeAgent(resume_text="测试简历", target_direction="agent_engineer")


# ── Prompt 填充 ────────────────────────────────────────


def test_build_prompt_fills_template(agent):
    prompt = agent._build_prompt()
    assert "agent_engineer" in prompt
    assert "测试简历" in prompt


# ── JSON 校验 ──────────────────────────────────────────


def test_validate_valid_output(agent):
    agent._validate_output(VALID_MOCK_RESPONSE)  # 不抛异常即通过


def test_validate_invalid_direction(agent):
    with pytest.raises(ValueError, match="Invalid detected_direction"):
        agent._validate_output({"detected_direction": "frontend_engineer"})


def test_validate_missing_direction(agent):
    with pytest.raises(ValueError, match="Invalid detected_direction"):
        agent._validate_output({})


def test_validate_arrays_get_defaults(agent):
    """数组字段缺失时应自动兜底为空列表。"""
    data = {"detected_direction": "python_backend"}
    agent._validate_output(data)
    assert data["skills"] == []
    assert data["project_deep_dive_points"] == []
    assert data["weaknesses"] == []
    assert data["suggestions"] == []
    assert data["projects"] == []


# ── Analyze 完整流程 ───────────────────────────────────


@patch.object(ResumeAgent, "_call_llm")
def test_analyze_returns_valid_json(mock_call, agent):
    mock_call.return_value = json.dumps(VALID_MOCK_RESPONSE, ensure_ascii=False)
    result = agent.analyze()
    assert result["detected_direction"] == "agent_engineer"
    assert result["skills"] == ["Python", "FastAPI", "RAG", "PostgreSQL"]
    assert len(result["project_deep_dive_points"]) == 2
    assert len(result["suggestions"]) == 2


@patch.object(ResumeAgent, "_call_llm")
def test_analyze_retries_on_json_error(mock_call, agent):
    """首次 JSON 解析失败，重试后成功。"""
    mock_call.side_effect = [
        '{"detected_direction": "agent_engineer", invalid json',
        json.dumps(VALID_MOCK_RESPONSE, ensure_ascii=False),
    ]
    result = agent.analyze(max_retries=2)
    assert mock_call.call_count == 2
    assert result["detected_direction"] == "agent_engineer"


@patch.object(ResumeAgent, "_call_llm")
def test_analyze_retries_then_fails(mock_call, agent):
    """所有重试都失败时抛出 RuntimeError。"""
    mock_call.return_value = "not valid json at all"
    with pytest.raises(RuntimeError, match="ResumeAgent failed after"):
        agent.analyze(max_retries=2)
    assert mock_call.call_count == 2


# ── judge_candidate ────────────────────────────────────


@patch.object(ResumeAgent, "analyze")
def test_judge_candidate_match(mock_analyze, agent):
    mock_analyze.return_value = {"detected_direction": "agent_engineer"}
    assert agent.judge_candidate() is True


@patch.object(ResumeAgent, "analyze")
def test_judge_candidate_mismatch(mock_analyze, agent):
    mock_analyze.return_value = {"detected_direction": "python_backend"}
    assert agent.judge_candidate() is False
