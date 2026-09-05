import io
import json
import os
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import Mock, patch

from agent_quality_lab.models import DeepSeekModel, ModelError, NoRedirect, Settings


class AdapterTests(unittest.TestCase):
    def setUp(self):
        self.model = DeepSeekModel(Settings("test-credential"))

    def response(self, message=None, finish="stop"):
        return {"id": "response-1", "choices": [{"message": message or {"content": "hello"}, "finish_reason": finish}],
                "usage": {"prompt_tokens": 10, "completion_tokens": 5}}

    def install_response(self, data):
        self.model.opener = Mock()
        self.model.opener.open.return_value = io.BytesIO(json.dumps(data).encode())

    def test_request_configuration_and_tool_call_parsing(self):
        self.install_response(self.response({"content": None, "tool_calls": [{"id": "c1", "function": {
            "name": "get_invoice", "arguments": '{"invoice_id":"a"}'}}]}, "tool_calls"))
        result = self.model.complete([{"role": "user", "content": "query"}], [])
        request = self.model.opener.open.call_args.args[0]
        self.assertEqual(request.full_url, "https://api.deepseek.com/chat/completions")
        self.assertEqual(request.get_header("Authorization"), "Bearer test-credential")
        payload = json.loads(request.data)
        self.assertEqual(payload["model"], "deepseek-v4-flash")
        self.assertEqual(payload["thinking"], {"type": "disabled"})
        self.assertEqual(payload["tool_choice"], "auto")
        self.assertEqual(result.tool_calls[0].name, "get_invoice")
        self.assertEqual(result.usage["completion_tokens"], 5)

    def test_truncated_or_missing_response_is_failure(self):
        for data, code in [(self.response(finish="length"), "incomplete_response"), ({}, "invalid_response")]:
            with self.subTest(code=code):
                self.install_response(data)
                with self.assertRaises(ModelError) as raised:
                    self.model.complete([], [])
                self.assertEqual(raised.exception.code, code)

    def test_http_and_network_errors_are_sanitized(self):
        for error, code in [(urllib.error.HTTPError("https://example.invalid", 401, "private-value", {}, None), "http_401"),
                            (urllib.error.URLError("private-value"), "network_error")]:
            with self.subTest(code=code):
                self.model.opener = Mock()
                self.model.opener.open.side_effect = error
                with self.assertRaises(ModelError) as raised:
                    self.model.complete([], [])
                self.assertEqual(str(raised.exception), code)

    def test_redirect_is_not_followed(self):
        self.assertIsNone(NoRedirect().redirect_request(None, None, 302, "", {}, "https://example.invalid"))

    def test_base_url_rejects_plaintext_and_embedded_credentials(self):
        for url in ("http://example.invalid", "https://user:password@example.invalid", "https://example.invalid?key=value"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                DeepSeekModel(Settings("test", base_url=url))

    def test_settings_loads_file_and_environment_without_repr_secret(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {}, clear=True):
            path = Path(directory) / ".env"
            path.write_text("DEEPSEEK_API_KEY=file-test-value\n", encoding="utf-8")
            settings = Settings.load(path)
            self.assertEqual(settings.api_key, "file-test-value")
            self.assertNotIn("file-test-value", repr(settings))
            with patch.dict(os.environ, {"DEEPSEEK_API_KEY": "environment-test-value"}):
                self.assertEqual(Settings.load(path).api_key, "environment-test-value")
            path.write_text("DEEPSEEK_API_KEY=\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                Settings.load(path)
