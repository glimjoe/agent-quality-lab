from __future__ import annotations

import argparse
import json
import sqlite3
from dataclasses import asdict
from pathlib import Path

from .domain import BusinessTools, Identity
from .experiments import SCENARIOS, new_run, run_trial, scripted_model
from .models import DeepSeekModel, Settings
from .money import format_amount
from .prompts import SYSTEM_PROMPT
from .runtime import Agent, ToolError


def chat(args: argparse.Namespace) -> int:
    model = DeepSeekModel(Settings.load())
    directory, store = new_run(args.output)
    faults = {"refund_response_timeout": 1} if args.fault == "refund_timeout" else {}
    business = BusinessTools(store, Identity(args.tenant, "local-user", args.role), faults=faults)
    tools = business.registry()
    if faults:
        create_tool = next(tool for tool in tools if tool.name == "create_refund")
        create_handler = create_tool.handler
        def create_with_checkpoint(proposal_id):
            try:
                return create_handler(proposal_id=proposal_id)
            except ToolError as error:
                if error.code == "result_unknown":
                    # A separate read-only connection proves the transaction committed.
                    path = (directory / "business.sqlite3").resolve()
                    db = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)
                    db.row_factory = sqlite3.Row
                    try:
                        data = {table: [dict(row) for row in db.execute(f"SELECT * FROM {table} ORDER BY tenant_id,id")]
                                for table in ("invoices", "payments", "refunds", "tickets")}
                    finally:
                        db.close()
                    with (directory / "db-after-timeout.json").open("x", encoding="utf-8", newline="\n") as stream:
                        json.dump(data, stream, ensure_ascii=False, indent=2)
                        stream.write("\n")
                    agent.record("fault_checkpoint", name="create_refund", proposal_id=proposal_id,
                                 error_code=error.code, snapshot_file="db-after-timeout.json")
                raise
        create_tool.handler = create_with_checkpoint
    agent = Agent(model, tools, SYSTEM_PROMPT)
    before = store.snapshot()
    turns = []
    print(f"实验目录：{directory}\n身份：{args.tenant} / {args.role}（本地模拟身份）")
    if faults:
        print("故障注入：退款申请提交后首次响应超时；自动保存恢复前数据库快照。")
    print("输入任务；/approve 提案ID 确认退款对象和金额；/exit 退出。")
    try:
        while True:
            try:
                text = input("你> ").strip()
            except EOFError:
                break
            if text == "/exit":
                break
            if not text:
                continue
            if text.startswith("/approve "):
                proposal_id = text.split(maxsplit=1)[1]
                proposal = business.proposals.get(proposal_id)
                if proposal is None:
                    print("当前会话没有这个提案。")
                    continue
                print(f"支付：{proposal['payment_id']}；金额：{format_amount(proposal['amount_cents'], proposal['currency'])}")
                if input("输入 YES 确认这笔申请：").strip() != "YES":
                    print("未批准。")
                    continue
                approved = business.approve(proposal_id)
                agent.record("human_approval", source="local_cli_user", proposal=approved)
                text = f"我已通过本地入口确认提案 {proposal_id}，请继续。"
            result = agent.run(text)
            turns.append(asdict(result))
            print(f"Agent [{result.status}]> {result.answer}")
            for proposal in business.proposals.values():
                if not proposal["approved"]:
                    print(f"待确认：/approve {proposal['proposal_id']} | {proposal['payment_id']} | {format_amount(proposal['amount_cents'], proposal['currency'])}")
            (directory / "report.json").write_text(json.dumps({"model_mode": "deepseek", "model": model.settings.model,
                "identity": asdict(business.identity), "faults": faults, "turns": turns, "before": before, "after": store.snapshot(),
                "events": agent.events}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return 0
    finally:
        store.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Agent Quality Lab：模拟业务与 Agent 测试")
    commands = parser.add_subparsers(dest="command", required=True)
    evaluation = commands.add_parser("evaluate", help="运行固定测试场景，输出状态断言与调用记录")
    evaluation.add_argument("--model", choices=("scripted", "deepseek"), default="scripted")
    evaluation.add_argument("--scenario", choices=("all", *SCENARIOS), default="all")
    evaluation.add_argument("--trials", type=int, default=1)
    evaluation.add_argument("--output", type=Path, default=Path(".local/runs"))
    interactive = commands.add_parser("chat", help="与真实 DeepSeek Agent 交互")
    interactive.add_argument("--tenant", choices=("tenant-a", "tenant-b"), default="tenant-a")
    interactive.add_argument("--role", choices=("finance", "viewer"), default="finance")
    interactive.add_argument("--fault", choices=("none", "refund_timeout"), default="none",
                             help="模拟申请提交后首次响应超时，并保存恢复前快照（默认不注入）")
    interactive.add_argument("--output", type=Path, default=Path(".local/runs"))
    args = parser.parse_args()
    try:
        if args.command == "chat":
            return chat(args)
        if args.trials < 1:
            parser.error("--trials must be positive")
        settings = Settings.load() if args.model == "deepseek" else None
        scenarios = SCENARIOS if args.scenario == "all" else (args.scenario,)
        passed = 0
        total = 0
        for scenario in scenarios:
            for trial in range(args.trials):
                model = DeepSeekModel(settings) if settings else scripted_model(scenario)
                path, report = run_trial(model, scenario, args.output, model_mode=args.model,
                                         model_name=settings.model if settings else "scripted-test-double")
                total += 1
                passed += int(report["state_checks_passed"])
                print(json.dumps({"scenario": scenario, "trial": trial + 1,
                                  "state_checks_passed": report["state_checks_passed"], "report": str(path)}, ensure_ascii=False), flush=True)
        print(f"状态检查：{passed}/{total}；最终回答仍需人工评审。模型模式：{args.model}")
        return 0 if passed == total else 1
    except (ValueError, ToolError) as error:
        parser.exit(2, f"配置或操作错误：{error}\n")


if __name__ == "__main__":
    raise SystemExit(main())
