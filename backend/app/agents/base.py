"""BaseLLMAgent：LLM Agent 抽象基类。

所有 Agent 共享以下模式：
1. 子类实现 `_build_prompt()` 构造提示词
2. 子类实现 `_validate_output()` 校验输出字段
3. 基类提供 `_call_llm()` LLM 调用和 `analyze()` 重试编排
"""

import json
import logging
import os
from abc import ABC, abstractmethod
from typing import Any

import dashscope

from app.core.config import settings

logger = logging.getLogger(__name__)


class BaseLLMAgent(ABC):
    """LLM Agent 抽象基类。

    子类只需关注两个差异点：Prompt 模板和输出字段校验。
    LLM 调用、JSON 解析、重试编排全部由基类统一处理。
    """

    # 子类覆盖：合法的方向枚举值
    VALID_DIRECTIONS: set[str] = {"python_backend", "agent_engineer", "llm_application", "unknown"}

    def __init__(self, model: str | None = None, api_key: str | None = None):
        self.model = model or settings.llm_model
        self.api_key = api_key or settings.llm_api_key or os.getenv("LLM_API_KEY")
        self._label = self.__class__.__name__

    # ── 子类必须实现 ──────────────────────────────────

    @abstractmethod
    def _build_prompt(self) -> str:
        """子类实现：根据自身输入构造 prompt 字符串。"""
        ...

    @abstractmethod
    def _validate_output(self, result: dict[str, Any]) -> None:
        """子类实现：校验 LLM 输出的字段类型和取值，失败抛 ValueError。

        允许子类在回调中直接修改 result 做兜底（如数组字段设为 []）。
        """
        ...

    # ── 基类统一实现 ──────────────────────────────────

    def _call_llm(self) -> str:
        """调用 LLM，返回原始 JSON 字符串。"""
        prompt = self._build_prompt()
        response = dashscope.Generation.call(
            model=self.model,
            api_key=self.api_key,
            messages=[{"role": "system", "content": prompt}],
            temperature=0,
            result_format="message",
            response_format={"type": "json_object"},
        )
        status_code = getattr(response, "status_code", None)
        code = getattr(response, "code", None)
        message = getattr(response, "message", None)
        if status_code and status_code >= 400:
            raise RuntimeError(f"LLM call failed ({status_code} {code}): {message}")

        output = getattr(response, "output", None)
        choices = getattr(output, "choices", None)
        if not choices:
            raise RuntimeError(
                f"LLM returned no choices (status={status_code}, code={code}, message={message})"
            )

        content = choices[0].message.content
        if content is None:
            raise RuntimeError("LLM returned empty response")
        return content

    def analyze(self, max_retries: int = 2) -> dict[str, Any]:
        """调用 LLM 分析，内置 JSON 解析与 schema 校验重试。"""
        last_error: str | None = None
        for attempt in range(max_retries):
            try:
                raw_output = self._call_llm()
                result = json.loads(raw_output)
                self._validate_output(result)
                return result
            except json.JSONDecodeError as exc:
                last_error = f"JSON decode failed: {exc}"
                logger.warning("%s attempt %d/%d: %s", self._label, attempt + 1, max_retries, last_error)
            except ValueError as exc:
                last_error = str(exc)
                logger.warning("%s attempt %d/%d: %s", self._label, attempt + 1, max_retries, last_error)
        raise RuntimeError(f"{self._label} failed after {max_retries} attempts: {last_error}")

    # ── 校验辅助方法 ─────────────────────────────────

    def _validate_direction(self, result: dict[str, Any], field: str = "detected_direction") -> str:
        """抽取 direction 字段并校验合法性，失败抛 ValueError。"""
        direction = result.get(field)
        if not isinstance(direction, str) or direction not in self.VALID_DIRECTIONS:
            raise ValueError(
                f"Invalid {field}: {direction!r}, must be one of {self.VALID_DIRECTIONS}"
            )
        return direction

    @staticmethod
    def _ensure_array_fields(result: dict[str, Any], fields: tuple[str, ...]) -> None:
        """数组字段缺失或类型不对时兜底为空列表。"""
        for field in fields:
            if field not in result or not isinstance(result.get(field), list):
                result[field] = []
