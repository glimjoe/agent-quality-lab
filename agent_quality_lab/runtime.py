"""Bounded model/tool loop. Authentication context stays outside model arguments."""

from __future__ import annotations

import copy
import json
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Protocol


class ToolError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class ToolCall:
    id: str
    name: str
    arguments: str


@dataclass
class Completion:
    text: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)
    reasoning_content: str | None = None
    usage: dict = field(default_factory=dict)
    response_id: str | None = None


class Model(Protocol):
    def complete(self, messages: list[dict], tools: list[dict]) -> Completion: ...


@dataclass
class Tool:
    name: str
    description: str
    parameters: dict[str, str]
    handler: Callable[..., dict]

    def specification(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        name: {"type": "string", "description": description}
                        for name, description in self.parameters.items()
                    },
                    "required": list(self.parameters),
                    "additionalProperties": False,
                },
            },
        }

    def invoke(self, arguments: Any) -> dict:
        if not isinstance(arguments, dict) or set(arguments) != set(self.parameters):
            raise ToolError("invalid_arguments", "工具参数必须与定义完全一致。")
        if any(not isinstance(value, str) or not value.strip() for value in arguments.values()):
            raise ToolError("invalid_arguments", "工具参数必须是非空字符串。")
        return self.handler(**arguments)


@dataclass
class TurnResult:
    status: str
    answer: str
    model_calls: int
    tool_calls: int


class Agent:
    def __init__(
        self, model: Model, tools: list[Tool], system_prompt: str,
        *, max_model_calls: int = 8, max_tool_calls: int = 12,
    ):
        if max_model_calls < 1 or max_tool_calls < 1:
            raise ValueError("Call limits must be positive")
        self.model = model
        self.tools = {tool.name: tool for tool in tools}
        if len(self.tools) != len(tools):
            raise ValueError("Tool names must be unique")
        self.messages = [{"role": "system", "content": system_prompt}]
        self.events: list[dict] = []
        self.max_model_calls = max_model_calls
        self.max_tool_calls = max_tool_calls
        self._call_ids: set[str] = set()

    def record(self, event: str, **payload: Any) -> None:
        self.events.append({"sequence": len(self.events) + 1, "event": event, **copy.deepcopy(payload)})

    def run(self, user_input: str) -> TurnResult:
        if not isinstance(user_input, str) or not user_input.strip():
            raise ValueError("User input must not be empty")
        self.messages.append({"role": "user", "content": user_input})
        self.record("user_message", text=user_input)
        tool_count = 0
        specs = [tool.specification() for tool in self.tools.values()]
        for model_count in range(1, self.max_model_calls + 1):
            started = time.perf_counter()
            try:
                reply = self.model.complete(copy.deepcopy(self.messages), copy.deepcopy(specs))
                ids = [call.id for call in reply.tool_calls]
                if any(not item for item in ids) or len(ids) != len(set(ids)) or self._call_ids.intersection(ids):
                    raise ValueError("Invalid or reused tool call ID")
                if not reply.tool_calls and not reply.text.strip():
                    raise ValueError("Empty model response")
            except Exception as error:
                self.record("model_error", error_type=type(error).__name__, code=getattr(error, "code", None))
                return TurnResult("model_error", "模型调用失败，未将本轮标记为成功。", model_count, tool_count)
            self.record("model_response", text=reply.text, tool_calls=[vars(call) for call in reply.tool_calls],
                        usage=reply.usage, response_id=reply.response_id,
                        duration_ms=round((time.perf_counter() - started) * 1000, 3))
            if tool_count + len(reply.tool_calls) > self.max_tool_calls:
                self.record("budget_exhausted", limit="tool_calls")
                return TurnResult("budget_exhausted", "达到工具调用上限，本批操作未执行。", model_count, tool_count)
            assistant_message: dict = {"role": "assistant", "content": reply.text}
            if reply.reasoning_content is not None:
                assistant_message["reasoning_content"] = reply.reasoning_content
            if reply.tool_calls:
                assistant_message["tool_calls"] = [
                    {"id": call.id, "type": "function", "function": {"name": call.name, "arguments": call.arguments}}
                    for call in reply.tool_calls
                ]
            self.messages.append(assistant_message)
            if not reply.tool_calls:
                return TurnResult("responded", reply.text, model_count, tool_count)
            self._call_ids.update(ids)
            for call in reply.tool_calls:
                tool_count += 1
                started = time.perf_counter()
                try:
                    try:
                        arguments = json.loads(call.arguments)
                    except (json.JSONDecodeError, TypeError) as error:
                        raise ToolError("invalid_arguments", "工具参数不是有效的 JSON。") from error
                    if call.name not in self.tools:
                        raise ToolError("unknown_tool", "该工具未开放。")
                    output = {"ok": True, "data": self.tools[call.name].invoke(arguments)}
                except ToolError as error:
                    output = {"ok": False, "error": {"code": error.code, "message": str(error)}}
                except Exception as error:
                    output = {"ok": False, "error": {"code": "tool_internal_error", "message": "工具内部错误，执行结果须核实。"}}
                    self.record("tool_internal_error", name=call.name, error_type=type(error).__name__)
                self.record("tool_result", call_id=call.id, name=call.name, arguments=call.arguments,
                            output=output, duration_ms=round((time.perf_counter() - started) * 1000, 3))
                self.messages.append({"role": "tool", "tool_call_id": call.id,
                                      "content": json.dumps(output, ensure_ascii=False)})
        self.record("budget_exhausted", limit="model_calls")
        return TurnResult("budget_exhausted", "达到模型调用上限；请核查已执行操作，勿假定任务完成。", self.max_model_calls, tool_count)
