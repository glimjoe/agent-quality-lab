"""DeepSeek adapter and an explicitly scripted test double."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from .runtime import Completion, ToolCall


@dataclass(frozen=True)
class Settings:
    api_key: str = field(repr=False)
    model: str = "deepseek-v4-flash"
    base_url: str = "https://api.deepseek.com"

    @classmethod
    def load(cls, env_file: Path = Path(".env")) -> Settings:
        values: dict[str, str] = {}
        if env_file.is_file():
            for line in env_file.read_text(encoding="utf-8-sig").splitlines():
                if not line.strip() or line.lstrip().startswith("#"):
                    continue
                key, separator, value = line.partition("=")
                if separator:
                    values[key.strip()] = value.strip().strip("\"'")
        def setting(name: str, default: str = "") -> str:
            return os.environ.get(name, values.get(name, default)).strip()
        key = setting("DEEPSEEK_API_KEY")
        if not key:
            raise ValueError("DEEPSEEK_API_KEY 未配置；请在本地 .env 中设置，勿提交密钥。")
        return cls(key, setting("DEEPSEEK_MODEL", "deepseek-v4-flash"),
                   setting("DEEPSEEK_BASE_URL", "https://api.deepseek.com"))


class ModelError(Exception):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # Credentials are never forwarded to a redirected destination.
        return None


class DeepSeekModel:
    def __init__(self, settings: Settings, *, timeout: float = 45):
        parsed = urllib.parse.urlsplit(settings.base_url)
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ValueError("DEEPSEEK_BASE_URL must be an HTTPS base URL without credentials, query or fragment")
        self.settings = settings
        self.timeout = timeout
        self.opener = urllib.request.build_opener(NoRedirect())

    def complete(self, messages: list[dict], tools: list[dict]) -> Completion:
        payload = {
            "model": self.settings.model, "messages": messages, "tools": tools,
            "tool_choice": "auto", "stream": False, "max_tokens": 2048,
            "temperature": 0, "thinking": {"type": "disabled"},
        }
        request = urllib.request.Request(
            self.settings.base_url.rstrip("/") + "/chat/completions",
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={"Authorization": "Bearer " + self.settings.api_key,
                     "Content-Type": "application/json", "Accept": "application/json"},
            method="POST",
        )
        try:
            with self.opener.open(request, timeout=self.timeout) as response:
                data = json.load(response)
        except urllib.error.HTTPError as error:
            raise ModelError(f"http_{error.code}") from None
        except (urllib.error.URLError, TimeoutError, OSError):
            raise ModelError("network_error") from None
        except (ValueError, UnicodeError):
            raise ModelError("invalid_response") from None
        try:
            choice = data["choices"][0]
            if choice["finish_reason"] not in ("stop", "tool_calls"):
                raise ModelError("incomplete_response")
            message = choice["message"]
            calls = [ToolCall(call["id"], call["function"]["name"], call["function"]["arguments"])
                     for call in message.get("tool_calls") or []]
            return Completion(message.get("content") or "", calls, message.get("reasoning_content"),
                              data.get("usage") or {}, data.get("id"))
        except (KeyError, IndexError, TypeError):
            raise ModelError("invalid_response") from None


class ScriptedModel:
    """Prewritten responses for engineering tests; no LLM or autonomous decisions."""

    def __init__(self, replies: list[Completion | Callable[[list[dict]], Completion]]):
        self.replies = deque(replies)

    def complete(self, messages: list[dict], tools: list[dict]) -> Completion:
        if not self.replies:
            raise ModelError("script_exhausted")
        reply = self.replies.popleft()
        return reply(messages) if callable(reply) else reply
