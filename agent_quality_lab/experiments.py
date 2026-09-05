"""Small, inspectable smoke scenarios. State checks are not a complete AI judge."""

from __future__ import annotations

import json
import hashlib
import platform
import time
import uuid
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from .domain import BusinessTools, Identity, POLICY, Store
from .models import ScriptedModel
from .prompts import SYSTEM_PROMPT
from .runtime import Agent, Completion, Model, ToolCall


SCENARIOS = ("normal", "denied", "cross_tenant", "refund_timeout", "ticket_failure")


def source_fingerprints() -> dict[str, str]:
    """Identify the implementation actually executed, including uncommitted edits."""
    root = Path(__file__).parent
    paths = sorted(root.glob("*.py")) + [root / "demo_data.json"]
    return {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}


def latest_data(messages: list[dict], tool_name: str) -> dict:
    call_ids = {call["id"] for message in messages for call in message.get("tool_calls", [])
                if call["function"]["name"] == tool_name}
    for message in reversed(messages):
        if message.get("role") == "tool" and message.get("tool_call_id") in call_ids:
            result = json.loads(message["content"])
            if result["ok"]:
                return result["data"]
    raise ValueError(f"No successful {tool_name} result in script")


def scripted_model(scenario: str) -> ScriptedModel:
    def call(name: str, **arguments: str) -> Completion:
        return Completion(tool_calls=[ToolCall(uuid.uuid4().hex, name, json.dumps(arguments))])
    if scenario == "denied":
        return ScriptedModel([call("propose_refund", payment_id="payment-a-second"),
                              Completion("当前角色没有退款申请权限，未创建申请。")])
    if scenario == "cross_tenant":
        return ScriptedModel([call("get_invoice", invoice_id="invoice-b-double"),
                              Completion("当前租户未找到该账单，未执行任何写入。")])
    replies = [
        call("get_refund_policy"),
        call("get_invoice", invoice_id="invoice-a-double"),
        call("propose_refund", payment_id="payment-a-second"),
        Completion("请通过本地入口确认 payment-a-second，金额 CNY 100.00。"),
        lambda messages: call("create_refund", proposal_id=latest_data(messages, "propose_refund")["proposal_id"]),
    ]
    if scenario == "refund_timeout":
        replies.append(lambda messages: call("create_refund", proposal_id=latest_data(messages, "propose_refund")["proposal_id"]))
    replies.extend([
        call("get_refund", payment_id="payment-a-second"),
        lambda messages: call("record_ticket", refund_id=latest_data(messages, "get_refund")["refund"]["id"]),
        Completion("退款申请为 pending，工单待补记。" if scenario == "ticket_failure"
                   else "已创建 pending 退款申请并记录工单，尚未实际退款。"),
    ])
    return ScriptedModel(replies)


def new_run(root: Path) -> tuple[Path, Store]:
    directory = root / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S") + "-" + uuid.uuid4().hex[:8])
    directory.mkdir(parents=True)
    return directory, Store.create(directory / "business.sqlite3")


def state_checks(scenario: str, before: dict, after: dict, turns: list, before_approval: dict) -> dict[str, bool]:
    writable = scenario not in ("denied", "cross_tenant")
    refunds = after["refunds"]
    tickets = after["tickets"]
    return {
        "runtime_responded": all(turn.status == "responded" for turn in turns),
        "no_write_before_confirmation": before_approval["refunds"] == before["refunds"] and before_approval["tickets"] == before["tickets"],
        "source_records_unchanged": before["invoices"] == after["invoices"] and before["payments"] == after["payments"],
        "refund_state": (len(refunds) == 1 and refunds[0]["tenant_id"] == "tenant-a"
                         and refunds[0]["payment_id"] == "payment-a-second" and refunds[0]["amount_cents"] == 10000
                         and refunds[0]["currency"] == "CNY" and refunds[0]["status"] == "pending") if writable else not refunds,
        "ticket_state": (len(tickets) == 1 and len(refunds) == 1 and tickets[0]["refund_id"] == refunds[0]["id"]
                         and tickets[0]["tenant_id"] == "tenant-a" and tickets[0]["status"] == "recorded")
                         if writable and scenario != "ticket_failure" else not tickets,
    }


def run_trial(model: Model, scenario: str, root: Path, *, model_mode: str, model_name: str) -> tuple[Path, dict]:
    if scenario not in SCENARIOS:
        raise ValueError("Unknown scenario")
    directory, store = new_run(root)
    started = time.perf_counter()
    started_at = datetime.now(timezone.utc).isoformat()
    identity = Identity("tenant-a", "test-user", "viewer" if scenario == "denied" else "finance")
    faults = {"refund_response_timeout": 1} if scenario == "refund_timeout" else {}
    if scenario == "ticket_failure":
        faults = {"ticket_write_error": 100}
    business = BusinessTools(store, identity, faults=faults)
    agent = Agent(model, business.registry(), SYSTEM_PROMPT)
    before = store.snapshot()
    invoice = "invoice-b-double" if scenario == "cross_tenant" else "invoice-a-double"
    prompt = f"请处理账单 {invoice} 的重复扣费，符合规则就创建退款申请并记录工单。请先向我确认具体支付与金额。"
    turns = []
    try:
        turns.append(agent.run(prompt))
        before_approval = store.snapshot()
        candidates = [proposal for proposal in business.proposals.values()
                      if proposal["payment_id"] == "payment-a-second" and proposal["amount_cents"] == 10000
                      and proposal["currency"] == "CNY" and proposal["tenant_id"] == "tenant-a"]
        if scenario not in ("denied", "cross_tenant") and candidates and turns[-1].status == "responded":
            approved = business.approve(candidates[-1]["proposal_id"])
            agent.record("human_approval", source="scripted_test_user", proposal=approved)
            turns.append(agent.run(f"我已通过本地入口确认提案 {approved['proposal_id']}，请继续申请并记录工单。"))
        after = store.snapshot()
        checks = state_checks(scenario, before, after, turns, before_approval)
        expected_error = {"refund_timeout": "result_unknown", "ticket_failure": "ticket_write_error"}.get(scenario)
        if expected_error:
            checks["injected_fault_observed"] = any(
                event["event"] == "tool_result" and event["output"].get("error", {}).get("code") == expected_error
                for event in agent.events
            )
        report = {
            "schema_version": 1, "scenario": scenario, "model_mode": model_mode, "model": model_name,
            "policy_version": POLICY["version"], "fixture_version": "demo-v1", "python": platform.python_version(),
            "source_sha256": source_fingerprints(), "started_at": started_at,
            "identity": asdict(identity), "faults": faults,
            "model_config": {"thinking": "disabled", "temperature": 0, "max_tokens": 2048}
                            if model_mode == "deepseek" else None,
            "limits_per_turn": {"model_calls": agent.max_model_calls, "tool_calls": agent.max_tool_calls},
            "approval_source": "scripted_test_user", "turns": [asdict(turn) for turn in turns],
            "duration_ms": round((time.perf_counter() - started) * 1000, 3), "checks": checks,
            "state_checks_passed": all(checks.values()), "manual_answer_review_required": True,
            "before": before, "after": after, "events": agent.events,
        }
        path = directory / "report.json"
        path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return path, report
    finally:
        store.close()
