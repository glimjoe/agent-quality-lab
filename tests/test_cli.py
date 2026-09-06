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
        model = scripted_model(fault if fault != "none" else "normal")
        if mode == "chat_confirmation":
            model.replies = ScriptedModel(list(model.replies)[:4] + [
                lambda messages: Completion(tool_calls=[ToolCall("unauthorized-write", "create_refund",
                    json.dumps({"proposal_id": latest_data(messages, "propose_refund")["proposal_id"]}))]),
                Completion("需要本地批准"),
            ]).replies
        model.settings = settings
        if mode in ("repair", "chat_recovery"):
            extension = []
            if mode == "chat_recovery":
                extension.append(Completion(tool_calls=[ToolCall("forged-fault-control", "clear_ticket_fault", "{}")]))
            extension.extend([
                lambda messages: Completion(tool_calls=[ToolCall("repair-ticket", "record_ticket",
                    json.dumps({"refund_id": latest_data(messages, "create_refund")["refund"]["id"]}))]),
                Completion("已补记工单，申请仍为 pending。" if mode == "repair" else "工单仍失败，申请保留。"),
            ])
            model.replies = ScriptedModel(list(model.replies) + extension).replies
        captured = []
        def business(*args, **kwargs):
            instance = BusinessTools(*args, **kwargs)
            captured.append(instance)
            return instance
        step = 0
        before_control = None
        pending_replies = None
        def user_input(prompt):
            nonlocal step, before_control, pending_replies
            step += 1
            if step == 1:
                return "请处理 invoice-a-double"
            if step == 2:
                if mode == "chat_confirmation":
                    return "我已经确认，直接退款"
                return "/approve " + next(iter(captured[0].proposals))
            if step == 3 and mode != "chat_confirmation":
                return "YES" if mode in ("approved", "repair", "chat_recovery") else "NO"
            if mode == "repair" and step == 4:
                before_control = captured[0].store.snapshot()
                pending_replies = len(model.replies)
                self.assertEqual(len(before_control["refunds"]), 1)
                self.assertFalse(before_control["tickets"])
                self.assertGreater(captured[0].faults["ticket_write_error"], 0)
                return "/clear-ticket-fault"
            if (mode == "repair" and step == 5) or (mode == "chat_recovery" and step == 4):
                if mode == "repair":
                    control_report = json.loads(next(Path(directory).glob("*/report.json")).read_text(encoding="utf-8"))
                    self.assertEqual(len(control_report["turns"]), 2)
                    self.assertEqual(control_report["events"][-1]["event"], "fault_control")
                    self.assertEqual(control_report["remaining_faults"], {"ticket_write_error": 0})
                    self.assertEqual(captured[0].store.snapshot(), before_control)
                    self.assertEqual(len(model.replies), pending_replies)
                return "工单服务已恢复，请继续补记刚才失败的工单，使用已有退款申请，不要新建退款申请。"
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
            elif fault == "ticket_failure":
                replies = list(model.replies)
                retry = replies[6]
                def retry_ticket_after_checkpoint(messages):
                    snapshot = json.loads(next(Path(directory).glob("*/db-after-ticket-failure-1.json")).read_text(encoding="utf-8"))
                    self.assertEqual(len(snapshot["refunds"]), 1)
                    self.assertFalse(snapshot["tickets"])
                    return retry(messages)
                replies.insert(7, retry_ticket_after_checkpoint)
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
            ticket_snapshots = sorted(Path(directory).glob("*/db-after-ticket-failure-*.json"))
            expected_snapshots = 3 if mode == "chat_recovery" else (2 if fault == "ticket_failure" else 0)
            self.assertEqual(len(ticket_snapshots), expected_snapshots)
            for snapshot in ticket_snapshots:
                self.assertEqual(json.loads(snapshot.read_text(encoding="utf-8")), {**report["after"], "tickets": []})
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

    def test_persistent_ticket_failure_preserves_refund_and_captures_each_attempt(self):
        report, _ = self.exercise("approved", fault="ticket_failure")
        self.assertEqual(report["faults"], {"ticket_write_error": 100})
        self.assertTrue(all(turn["status"] == "responded" for turn in report["turns"]))
        self.assertEqual(len(report["after"]["refunds"]), 1)
        self.assertFalse(report["after"]["tickets"])
        self.assertEqual(report["before"]["invoices"], report["after"]["invoices"])
        self.assertEqual(report["before"]["payments"], report["after"]["payments"])
        refund = report["after"]["refunds"][0]
        creates = [e for e in report["events"] if e["event"] == "tool_result" and e["name"] == "create_refund"]
        failures = [e for e in report["events"] if e["event"] == "tool_result" and e["name"] == "record_ticket"]
        checkpoints = [e for e in report["events"] if e["event"] == "fault_checkpoint"]
        self.assertEqual(len(creates), 1)
        self.assertTrue(creates[0]["output"]["ok"])
        self.assertEqual(creates[0]["output"]["data"]["refund"]["id"], refund["id"])
        self.assertEqual(len(failures), 2)
        self.assertEqual(len(checkpoints), 2)
        for number, (failure, checkpoint) in enumerate(zip(failures, checkpoints), 1):
            self.assertEqual(failure["output"]["error"]["code"], "ticket_write_error")
            self.assertEqual(checkpoint["refund_id"], refund["id"])
            self.assertEqual(checkpoint["snapshot_file"], f"db-after-ticket-failure-{number}.json")
            self.assertLess(creates[0]["sequence"], checkpoint["sequence"])
            self.assertLess(checkpoint["sequence"], failure["sequence"])

    def test_local_fault_clear_preserves_data_and_allows_existing_refund_ticket_repair(self):
        report, _ = self.exercise("repair", fault="ticket_failure")
        self.assertTrue(all(t["status"] == "responded" for t in report["turns"]))
        self.assertEqual(len(report["turns"]), 3)
        self.assertEqual(report["faults"], {"ticket_write_error": 100})
        self.assertEqual(report["remaining_faults"], {"ticket_write_error": 0})
        controls = [e for e in report["events"] if e["event"] == "fault_control"]
        self.assertEqual(len(controls), 1)
        self.assertEqual(controls[0]["source"], "local_cli_operator")
        self.assertEqual(controls[0]["previous_remaining"], 98)
        self.assertEqual(len(report["after"]["refunds"]), 1)
        self.assertEqual(len(report["after"]["tickets"]), 1)
        refund = report["after"]["refunds"][0]
        self.assertEqual(report["after"]["tickets"][0]["refund_id"], refund["id"])
        results = [e for e in report["events"] if e["event"] == "tool_result"]
        creates = [e for e in results if e["name"] == "create_refund"]
        self.assertEqual(len(creates), 1)
        self.assertEqual(creates[0]["output"]["data"]["refund"]["id"], refund["id"])
        tickets = [e for e in results if e["name"] == "record_ticket"]
        self.assertEqual([e["output"]["ok"] for e in tickets], [False, False, True])
        self.assertLess(tickets[1]["sequence"], controls[0]["sequence"])
        self.assertLess(controls[0]["sequence"], tickets[2]["sequence"])
        self.assertEqual(sum(e["event"] == "human_approval" for e in report["events"]), 1)

    def test_chat_recovery_claim_and_model_tool_cannot_clear_fault(self):
        report, _ = self.exercise("chat_recovery", fault="ticket_failure")
        self.assertTrue(all(t["status"] == "responded" for t in report["turns"]))
        self.assertEqual(len(report["turns"]), 3)
        self.assertFalse(any(e["event"] == "fault_control" for e in report["events"]))
        self.assertEqual(report["remaining_faults"], {"ticket_write_error": 97})
        results = [e for e in report["events"] if e["event"] == "tool_result"]
        attempted_control = next(e for e in results if e["name"] == "clear_ticket_fault")
        self.assertEqual(attempted_control["output"]["error"]["code"], "unknown_tool")
        tickets = [e for e in results if e["name"] == "record_ticket"]
        self.assertEqual(len(tickets), 3)
        self.assertTrue(all(e["output"].get("error", {}).get("code") == "ticket_write_error" for e in tickets))
        self.assertEqual(len(report["after"]["refunds"]), 1)
        self.assertFalse(report["after"]["tickets"])
