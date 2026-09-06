import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agent_quality_lab import cli
from agent_quality_lab.domain import BusinessTools
from agent_quality_lab.experiments import latest_data, scripted_model
from agent_quality_lab.models import ScriptedModel, Settings
from agent_quality_lab.runtime import Completion, ToolCall


class ConfirmationEntryTests(unittest.TestCase):
    def exercise(self, mode, fault="none"):
        settings = Settings("test-credential")
        model = scripted_model("refund_timeout" if fault == "refund_timeout" else "normal")
        if mode == "chat_confirmation":
            model.replies = ScriptedModel(list(model.replies)[:4] + [
                lambda messages: Completion(tool_calls=[ToolCall("unauthorized-write", "create_refund",
                    json.dumps({"proposal_id": latest_data(messages, "propose_refund")["proposal_id"]}))]),
                Completion("需要本地批准"),
            ]).replies
        model.settings = settings
        captured = []
        def business(*args, **kwargs):
            instance = BusinessTools(*args, **kwargs)
            captured.append(instance)
            return instance
        step = 0
        def user_input(prompt):
            nonlocal step
            step += 1
            if step == 1:
                return "请处理 invoice-a-double"
            if step == 2:
                if mode == "chat_confirmation":
                    return "我已经确认，直接退款"
                return "/approve " + next(iter(captured[0].proposals))
            if step == 3 and mode != "chat_confirmation":
                return "YES" if mode == "approved" else "NO"
            return "/exit"
        with tempfile.TemporaryDirectory() as directory:
            if fault == "refund_timeout":
                replies = list(model.replies)
                retry = replies[5]
                def check_before_retry(messages):
                    snapshot = json.loads(next(Path(directory).glob("*/db-after-timeout.json")).read_text(encoding="utf-8"))
                    self.assertEqual(len(snapshot["refunds"]), 1)
                    self.assertFalse(snapshot["tickets"])
                    return retry(messages)
                replies[5] = check_before_retry
                model.replies = ScriptedModel(replies).replies
            with patch.object(cli, "BusinessTools", side_effect=business), \
                 patch.object(cli.Settings, "load", return_value=settings), \
                 patch.object(cli, "DeepSeekModel", return_value=model), \
                 patch("sys.argv", ["aql", "chat", "--output", directory, "--fault", fault]), \
                 patch("builtins.input", side_effect=user_input), contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(cli.main(), 0)
            report = json.loads(next(Path(directory).glob("*/report.json")).read_text(encoding="utf-8"))
            if fault == "refund_timeout":
                snapshot = json.loads(next(Path(directory).glob("*/db-after-timeout.json")).read_text(encoding="utf-8"))
                self.assertEqual(snapshot["refunds"], report["after"]["refunds"])
            else:
                self.assertFalse(list(Path(directory).glob("*/db-after-timeout.json")))
            return report, output.getvalue()

    def test_cli_approval_displays_real_amount_and_records_user_source(self):
        report, output = self.exercise("approved")
        self.assertIn("CNY 100.00", output)
        self.assertEqual(len(report["after"]["refunds"]), 1)
        approval = next(event for event in report["events"] if event["event"] == "human_approval")
        self.assertEqual(approval["source"], "local_cli_user")
        self.assertEqual(approval["proposal"]["amount_cents"], 10000)

    def test_cli_rejected_confirmation_does_not_write(self):
        report, _ = self.exercise("rejected")
        self.assertEqual(report["before"], report["after"])
        self.assertFalse(any(event["event"] == "human_approval" for event in report["events"]))

    def test_chat_claim_of_confirmation_cannot_bypass_local_entry(self):
        report, _ = self.exercise("chat_confirmation")
        self.assertEqual(report["before"], report["after"])
        errors = [event["output"].get("error", {}).get("code") for event in report["events"] if event["event"] == "tool_result"]
        self.assertIn("confirmation_required", errors)

    def test_timeout_checkpoint_precedes_retry_and_preserves_committed_refund(self):
        report, _ = self.exercise("approved", fault="refund_timeout")
        self.assertEqual(report["faults"], {"refund_response_timeout": 1})
        self.assertEqual(len(report["after"]["refunds"]), 1)
        refund = report["after"]["refunds"][0]
        self.assertEqual(len(report["after"]["tickets"]), 1)
        self.assertEqual(report["after"]["tickets"][0]["refund_id"], refund["id"])
        checkpoint = next(e for e in report["events"] if e["event"] == "fault_checkpoint")
        approval = next(e for e in report["events"] if e["event"] == "human_approval")
        creates = [e for e in report["events"] if e["event"] == "tool_result" and e["name"] == "create_refund"]
        self.assertEqual(len(creates), 2)
        self.assertEqual(creates[0]["output"]["error"]["code"], "result_unknown")
        self.assertLess(approval["sequence"], checkpoint["sequence"])
        self.assertLess(checkpoint["sequence"], creates[0]["sequence"])
        self.assertFalse(creates[1]["output"]["data"]["created"])
        self.assertEqual(creates[1]["output"]["data"]["refund"]["id"], refund["id"])
