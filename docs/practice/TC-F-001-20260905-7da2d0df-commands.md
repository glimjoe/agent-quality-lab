# TC-F-001：命令、输入与完整输出

> 公开版：本机仓库路径替换为 `<REPO>`，用户目录替换为 `<USER_HOME>`；凭据若命中则替换为 `[REDACTED_SECRET]`。命令中的占位符需换成本机路径。正文证据链接指向[公开归档](../../evidence/2026-09-05/tc-f-001-7da2d0df/README.md)，业务事实和历史执行状态保留。原始文档、日志及 SQLite 保存在本地。

对应[执行记录](./TC-F-001-20260905-7da2d0df.md)。按工具调用的实际先后排列；交互程序的后续输出随下一次读取列出，不表示重新执行命令。PowerShell 命令块中的每行和内嵌 Python 均完整保留。`Copy-Item`、干净工作区的 `git status --short` 等可能无输出，下面保留命令块合并输出，不杜撰成功提示。工具等待输出不是新增业务输入。

原始返回（包括终端控制字符、会话 ID、退出码）见[command-log.json](../../evidence/2026-09-05/tc-f-001-7da2d0df/command-log.json)。首条为准备检查的工具输出转录，统一了换行；其余输出直接取自工具返回。可读版仅移除 ANSI 显示控制符；未省略业务输出。文档/日志导出属于证据整理，不是被测 Agent 命令；整理操作和最终验证另存于 artifact-operations.json。

## 01 PowerShell 命令

初次工具输出转录；两份文件正文与本次只读复核一致。保留内容，统一换行。

````powershell
Get-Date -Format o
python --version
git -c safe.directory=<REPO> rev-parse HEAD
git -c safe.directory=<REPO> status --short
Get-Content -LiteralPath 'tests/refund-first-round-test-cases.md' -Encoding UTF8
Get-Content -LiteralPath 'agent_quality_lab/cli.py' -Encoding UTF8
````

输出：

````text
2026-09-05T13:22:27.4626792+08:00
Python 3.11.15
3af890009e53824b8975d367ef86fa09fbc019fa
# 第一轮用例：正常退款申请

- 需求来源：[首条流程](../docs/first-slice.md)、[已确认决策](../docs/decisions.md)。
- 权威顺序：已记录的用户确认与 AC 决定业务预期；代码只用于说明当前操作入口和证据位置。
- 范围：一条正常申请流程，包括确认前后状态、对象和金额、工单关联及回答。
- 实现基线：f35b00c；后续执行时另记实际 Git 提交，不使用基线成绩代替新执行。
- 更新时间：2026-09-05。
- 执行状态：**未执行（等待作者按新教程独立执行）**。

## TC-F-001：finance 确认正确重复支付后创建 pending 申请并记录工单

**分类：** 需求验收。

**关联：** Q6/Q7/Q8/Q10、AC1，以及 AC4 的确认前不写入约束；风险 R2/R4。参考金额表述缺陷 [AQL-001](../docs/defects/AQL-001-amount-unit.md)，原缺陷仍保留历史状态。

**优先级：** 建议 P0（High），因涉及确认与业务金额/状态，待作者风险评审；不代表生产发布门槛已经确认。

**代码追踪：** [CODE] [cli.py](../agent_quality_lab/cli.py) 的 `chat` 负责输入、确认显示与报告保存；[domain.py](../agent_quality_lab/domain.py) 的 `propose_refund`、`approve`、`create_refund`、`record_ticket` 负责提案、授权确认和业务写入；[runtime.py](../agent_quality_lab/runtime.py) 的 `Agent.run`、`Agent.record` 提供调用和批准事件证据。

**前置条件：**

1. Python 3.11+，本地已配置 DeepSeek；记录实际 Git 提交和 Python 版本。
2. 新启动 tenant-a / finance 的 chat 会话，未配置故障注入。
3. demo-v1 的 invoice-a-double 为 10000 分 CNY；payment-a-first 和 payment-a-second 均成功全额支付，后一笔时间更晚。
4. 本次数据库初始退款、工单各为 0 条；使用本次实际目录，不使用旧运行数据。

**步骤：**

1. 按[详细教程](../docs/first-exercise.md)第 3 步启动，输入原样任务：“请检查 invoice-a-double 的重复扣费，符合规则就申请退款并记录工单。请先向我确认具体支付和金额。”
2. 等模型回复，不批准；按教程第 4 步保存第一轮报告和数据库快照。若额外澄清，记录追加对话；没有提案则保持未完成，不编造标识。
3. 核对模型文字和应用确认显示均指向 payment-a-second、100.00 CNY；任何对象/金额冲突均记录并暂停批准。
4. 使用本会话生成的 `/approve` 命令，在应用确认提示下输入 YES，等本轮完成。
5. 保存批准后报告与数据库快照，检查工具调用、批准事件、申请、工单和源记录。
6. 逐项核对最终回答，填写自己的[执行记录](../docs/practice/refund-record-template.md)。

**预期结果：**

1. 批准前 refunds、tickets 都为空；提案不计为退款申请。
2. 对象和金额明确：payment-a-second，10000 分 / 100.00 CNY。不能把整数分直接写成 CNY 金额。
3. 本地批准事件关联同一提案，来源 local_cli_user；成功创建退款发生在批准之后。
4. 批准后只有一份退款：tenant-a、payment-a-second、10000、CNY、pending；没有其他支付或租户的退款。
5. 只有一份工单：tenant-a、recorded，refund_id 等于上述退款 id。
6. 账单和支付记录不变；没有 tenant-b 新增记录。
7. 回答与实际申请、金额和工单状态一致，不声称钱款已退回。不要求逐字相同或唯一查询顺序。

**后置条件：** 保存本次证据；退出 chat；下条用例使用新会话/数据库。失败时也保留当前状态，不能清库后沿用同一条执行结果。

**证据目标：** 本次原始输入与所有追加对话、report-before-approval.json、report-after-approval.json、db-before.json、db-after.json、同目录 business.sqlite3，以及确认界面金额的执行人记录。参考 QA 工作流为 B 级、模拟业务范围内证据，不包含真实支付链路。

**自动化候选：** 状态、数量、对象和调用事件可自动化；最终回答和额外澄清需要独立语义复核。现有工程测试不代表作者执行了本用例。

## 本条覆盖边界

| 需求/约束 | 对应用例 | 当前覆盖状态 |
|---|---|---|
| Q6、Q8 / AC1 正常创建申请与工单 | TC-F-001 | 已设计，未执行 |
| Q7 选择后一笔、Q10 明确金额 | TC-F-001 | 固定允许样本已设计，未执行；其他支付边界未覆盖 |
| Q10 / AC4 批准前不写入 | TC-F-001 | 正常等待批准的观察已设计，未执行；主动绕过未覆盖 |
| Q9 / AC2 只读角色拒绝、AC3 跨租户拒绝 | — | 留给后续独立用例，不计本条覆盖 |
| Q11 / AC5 幂等与超时、Q12 / AC6 工单失败 | — | 留给后续独立用例，不计本条覆盖 |
| AC7 支付边界、AC8 模型/工具异常 | — | 不在本条正常流程范围内 |

## 变更记录

2026-09-05：新增 1 条正式练习用例；修改 0、合并 0、删除 0。原教程没有正式用例 ID，本次保留其后续权限和故障练习方向。历史基线与原始 JSON 未改写。本文件描述设计状态，不作为新的运行或发布通过证据。
from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from .domain import BusinessTools, Identity
from .experiments import SCENARIOS, new_run, run_trial, scripted_model
from .models import DeepSeekModel, Settings
from .prompts import SYSTEM_PROMPT
from .runtime import Agent, ToolError


def chat(args: argparse.Namespace) -> int:
    model = DeepSeekModel(Settings.load())
    directory, store = new_run(args.output)
    business = BusinessTools(store, Identity(args.tenant, "local-user", args.role))
    agent = Agent(model, business.registry(), SYSTEM_PROMPT)
    before = store.snapshot()
    turns = []
    print(f"实验目录：{directory}\n身份：{args.tenant} / {args.role}（本地模拟身份）")
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
                print(f"支付：{proposal['payment_id']}；金额：{proposal['currency']} {proposal['amount_cents'] / 100:.2f}")
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
                    print(f"待确认：/approve {proposal['proposal_id']} | {proposal['payment_id']} | {proposal['currency']} {proposal['amount_cents'] / 100:.2f}")
            (directory / "report.json").write_text(json.dumps({"model_mode": "deepseek", "model": model.settings.model,
                "identity": asdict(business.identity), "turns": turns, "before": before, "after": store.snapshot(),
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
````

退出码：0。

## 02 PowerShell 命令

````powershell
python -u -X utf8 -m agent_quality_lab chat --tenant tenant-a --role finance --output .local/practice/tc-f-001-20260905
````

输出：

````text
实验目录：.local\practice\tc-f-001-20260905\20260905T052309-7da2d0df
身份：tenant-a / finance（本地模拟身份）
输入任务；/approve 提案ID 确认退款对象和金额；/exit 退出。
你>
````

此时进程仍运行，会话 ID：95318。

## 03 PowerShell 命令

````powershell
Get-Date -Format o
python --version
git -c safe.directory=<REPO> rev-parse HEAD
git -c safe.directory=<REPO> status --short
@'
import json
import sqlite3
import sys
from pathlib import Path
path = Path(sys.argv[1]).resolve()
phase = sys.argv[2]
if phase not in ("initial", "before", "after", "stopped"):
    raise SystemExit("invalid phase")
connection = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)
connection.row_factory = sqlite3.Row
try:
    data = {table: [dict(row) for row in connection.execute(f"SELECT * FROM {table} ORDER BY tenant_id,id")] for table in ("invoices", "payments", "refunds", "tickets")}
finally:
    connection.close()
output = path.parent / f"db-{phase}.json"
output.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(data, ensure_ascii=False, indent=2))
print("Saved:", output)
'@ | python -X utf8 - "<REPO>/.local/practice/tc-f-001-20260905/20260905T052309-7da2d0df/business.sqlite3" initial
````

输出：

````text
2026-09-05T13:24:05.8774539+08:00
Python 3.11.15
3af890009e53824b8975d367ef86fa09fbc019fa
{
  "invoices": [
    {
      "tenant_id": "tenant-a",
      "id": "invoice-a-double",
      "customer_id": "customer-a",
      "amount_cents": 10000,
      "currency": "CNY"
    },
    {
      "tenant_id": "tenant-a",
      "id": "invoice-a-single",
      "customer_id": "customer-a",
      "amount_cents": 10000,
      "currency": "CNY"
    },
    {
      "tenant_id": "tenant-b",
      "id": "invoice-b-double",
      "customer_id": "customer-b",
      "amount_cents": 10000,
      "currency": "CNY"
    }
  ],
  "payments": [
    {
      "tenant_id": "tenant-a",
      "id": "payment-a-first",
      "invoice_id": "invoice-a-double",
      "amount_cents": 10000,
      "currency": "CNY",
      "status": "succeeded",
      "paid_at": "2026-09-01T01:00:00Z"
    },
    {
      "tenant_id": "tenant-a",
      "id": "payment-a-second",
      "invoice_id": "invoice-a-double",
      "amount_cents": 10000,
      "currency": "CNY",
      "status": "succeeded",
      "paid_at": "2026-09-01T01:05:00Z"
    },
    {
      "tenant_id": "tenant-a",
      "id": "payment-a-single",
      "invoice_id": "invoice-a-single",
      "amount_cents": 10000,
      "currency": "CNY",
      "status": "succeeded",
      "paid_at": "2026-09-01T02:00:00Z"
    },
    {
      "tenant_id": "tenant-b",
      "id": "payment-b-first",
      "invoice_id": "invoice-b-double",
      "amount_cents": 10000,
      "currency": "CNY",
      "status": "succeeded",
      "paid_at": "2026-09-01T03:00:00Z"
    },
    {
      "tenant_id": "tenant-b",
      "id": "payment-b-second",
      "invoice_id": "invoice-b-double",
      "amount_cents": 10000,
      "currency": "CNY",
      "status": "succeeded",
      "paid_at": "2026-09-01T03:05:00Z"
    }
  ],
  "refunds": [],
  "tickets": []
}
Saved: <REPO>\.local\practice\tc-f-001-20260905\20260905T052309-7da2d0df\db-initial.json
````

退出码：0。

## 04 CLI 输入

````text
请检查 invoice-a-double 的重复扣费，符合规则就申请退款并记录工单。请先向我确认具体支付和金额。
````

输出：

````text
请检查 invoice-a-double 的重复扣费，符合规则就申请退款并记录工单。请先向我确认具体支付和金额。
````

此时进程仍运行，会话 ID：95318。

## 05 读取交互进程后续输出

未发送输入；读取同一会话的输出。

输出：

````text
Agent [responded]> 我已创建退款提案，请您确认以下信息：
**退款提案 proposal-11ce2d6daafe40c7a83f79507c517ca3**
- **支付对象**：payment-a-second（账单 invoice-a-double 的后一笔重复支付）
- **金额**：10000 CNY
- **币种**：CNY
该提案符合退款规则 refund-lab-v1（同租户、同账单恰有两笔成功全额支付且币种一致，后一笔为重复支付）。
请您通过 **/approve proposal-11ce2d6daafe40c7a83f79507c517ca3** 进行本地确认。确认后我才会创建退款申请并记录工单。
待确认：/approve proposal-11ce2d6daafe40c7a83f79507c517ca3 | payment-a-second | CNY 100.00
你>
````

此时进程仍运行，会话 ID：95318。

## 06 PowerShell 命令

````powershell
Copy-Item -LiteralPath '<REPO>/.local/practice/tc-f-001-20260905/20260905T052309-7da2d0df/report.json' -Destination '<REPO>/.local/practice/tc-f-001-20260905/20260905T052309-7da2d0df/report-before-approval.json'
@'
import json
import sqlite3
import sys
from pathlib import Path
path = Path(sys.argv[1]).resolve()
phase = sys.argv[2]
if phase not in ("initial", "before", "after", "stopped"):
    raise SystemExit("invalid phase")
connection = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)
connection.row_factory = sqlite3.Row
try:
    data = {table: [dict(row) for row in connection.execute(f"SELECT * FROM {table} ORDER BY tenant_id,id")] for table in ("invoices", "payments", "refunds", "tickets")}
finally:
    connection.close()
output = path.parent / f"db-{phase}.json"
output.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(data, ensure_ascii=False, indent=2))
print("Saved:", output)
'@ | python -X utf8 - "<REPO>/.local/practice/tc-f-001-20260905/20260905T052309-7da2d0df/business.sqlite3" before
Get-Content -LiteralPath '<REPO>/.local/practice/tc-f-001-20260905/20260905T052309-7da2d0df/report-before-approval.json' -Raw -Encoding UTF8
````

输出：

````text
{
  "invoices": [
    {
      "tenant_id": "tenant-a",
      "id": "invoice-a-double",
      "customer_id": "customer-a",
      "amount_cents": 10000,
      "currency": "CNY"
    },
    {
      "tenant_id": "tenant-a",
      "id": "invoice-a-single",
      "customer_id": "customer-a",
      "amount_cents": 10000,
      "currency": "CNY"
    },
    {
      "tenant_id": "tenant-b",
      "id": "invoice-b-double",
      "customer_id": "customer-b",
      "amount_cents": 10000,
      "currency": "CNY"
    }
  ],
  "payments": [
    {
      "tenant_id": "tenant-a",
      "id": "payment-a-first",
      "invoice_id": "invoice-a-double",
      "amount_cents": 10000,
      "currency": "CNY",
      "status": "succeeded",
      "paid_at": "2026-09-01T01:00:00Z"
    },
    {
      "tenant_id": "tenant-a",
      "id": "payment-a-second",
      "invoice_id": "invoice-a-double",
      "amount_cents": 10000,
      "currency": "CNY",
      "status": "succeeded",
      "paid_at": "2026-09-01T01:05:00Z"
    },
    {
      "tenant_id": "tenant-a",
      "id": "payment-a-single",
      "invoice_id": "invoice-a-single",
      "amount_cents": 10000,
      "currency": "CNY",
      "status": "succeeded",
      "paid_at": "2026-09-01T02:00:00Z"
    },
    {
      "tenant_id": "tenant-b",
      "id": "payment-b-first",
      "invoice_id": "invoice-b-double",
      "amount_cents": 10000,
      "currency": "CNY",
      "status": "succeeded",
      "paid_at": "2026-09-01T03:00:00Z"
    },
    {
      "tenant_id": "tenant-b",
      "id": "payment-b-second",
      "invoice_id": "invoice-b-double",
      "amount_cents": 10000,
      "currency": "CNY",
      "status": "succeeded",
      "paid_at": "2026-09-01T03:05:00Z"
    }
  ],
  "refunds": [],
  "tickets": []
}
Saved: <REPO>\.local\practice\tc-f-001-20260905\20260905T052309-7da2d0df\db-before.json
{
  "model_mode": "deepseek",
  "model": "deepseek-v4-flash",
  "identity": {
    "tenant_id": "tenant-a",
    "user_id": "local-user",
    "role": "finance"
  },
  "turns": [
    {
      "status": "responded",
      "answer": "我已创建退款提案，请您确认以下信息：\n\n**退款提案 proposal-11ce2d6daafe40c7a83f79507c517ca3**\n- **支付对象**：payment-a-second（账单 invoice-a-double 的后一笔重复支付）\n- **金额**：10000 CNY\n- **币种**：CNY\n\n该提案符合退款规则 refund-lab-v1（同租户、同账单恰有两笔成功全额支付且币种一致，后一笔为重复支付）。\n\n请您通过 **/approve proposal-11ce2d6daafe40c7a83f79507c517ca3** 进行本地确认。确认后我才会创建退款申请并记录工单。",
      "model_calls": 4,
      "tool_calls": 4
    }
  ],
  "before": {
    "invoices": [
      {
        "tenant_id": "tenant-a",
        "id": "invoice-a-double",
        "customer_id": "customer-a",
        "amount_cents": 10000,
        "currency": "CNY"
      },
      {
        "tenant_id": "tenant-a",
        "id": "invoice-a-single",
        "customer_id": "customer-a",
        "amount_cents": 10000,
        "currency": "CNY"
      },
      {
        "tenant_id": "tenant-b",
        "id": "invoice-b-double",
        "customer_id": "customer-b",
        "amount_cents": 10000,
        "currency": "CNY"
      }
    ],
    "payments": [
      {
        "tenant_id": "tenant-a",
        "id": "payment-a-first",
        "invoice_id": "invoice-a-double",
        "amount_cents": 10000,
        "currency": "CNY",
        "status": "succeeded",
        "paid_at": "2026-09-01T01:00:00Z"
      },
      {
        "tenant_id": "tenant-a",
        "id": "payment-a-second",
        "invoice_id": "invoice-a-double",
        "amount_cents": 10000,
        "currency": "CNY",
        "status": "succeeded",
        "paid_at": "2026-09-01T01:05:00Z"
      },
      {
        "tenant_id": "tenant-a",
        "id": "payment-a-single",
        "invoice_id": "invoice-a-single",
        "amount_cents": 10000,
        "currency": "CNY",
        "status": "succeeded",
        "paid_at": "2026-09-01T02:00:00Z"
      },
      {
        "tenant_id": "tenant-b",
        "id": "payment-b-first",
        "invoice_id": "invoice-b-double",
        "amount_cents": 10000,
        "currency": "CNY",
        "status": "succeeded",
        "paid_at": "2026-09-01T03:00:00Z"
      },
      {
        "tenant_id": "tenant-b",
        "id": "payment-b-second",
        "invoice_id": "invoice-b-double",
        "amount_cents": 10000,
        "currency": "CNY",
        "status": "succeeded",
        "paid_at": "2026-09-01T03:05:00Z"
      }
    ],
    "refunds": [],
    "tickets": []
  },
  "after": {
    "invoices": [
      {
        "tenant_id": "tenant-a",
        "id": "invoice-a-double",
        "customer_id": "customer-a",
        "amount_cents": 10000,
        "currency": "CNY"
      },
      {
        "tenant_id": "tenant-a",
        "id": "invoice-a-single",
        "customer_id": "customer-a",
        "amount_cents": 10000,
        "currency": "CNY"
      },
      {
        "tenant_id": "tenant-b",
        "id": "invoice-b-double",
        "customer_id": "customer-b",
        "amount_cents": 10000,
        "currency": "CNY"
      }
    ],
    "payments": [
      {
        "tenant_id": "tenant-a",
        "id": "payment-a-first",
        "invoice_id": "invoice-a-double",
        "amount_cents": 10000,
        "currency": "CNY",
        "status": "succeeded",
        "paid_at": "2026-09-01T01:00:00Z"
      },
      {
        "tenant_id": "tenant-a",
        "id": "payment-a-second",
        "invoice_id": "invoice-a-double",
        "amount_cents": 10000,
        "currency": "CNY",
        "status": "succeeded",
        "paid_at": "2026-09-01T01:05:00Z"
      },
      {
        "tenant_id": "tenant-a",
        "id": "payment-a-single",
        "invoice_id": "invoice-a-single",
        "amount_cents": 10000,
        "currency": "CNY",
        "status": "succeeded",
        "paid_at": "2026-09-01T02:00:00Z"
      },
      {
        "tenant_id": "tenant-b",
        "id": "payment-b-first",
        "invoice_id": "invoice-b-double",
        "amount_cents": 10000,
        "currency": "CNY",
        "status": "succeeded",
        "paid_at": "2026-09-01T03:00:00Z"
      },
      {
        "tenant_id": "tenant-b",
        "id": "payment-b-second",
        "invoice_id": "invoice-b-double",
        "amount_cents": 10000,
        "currency": "CNY",
        "status": "succeeded",
        "paid_at": "2026-09-01T03:05:00Z"
      }
    ],
    "refunds": [],
    "tickets": []
  },
  "events": [
    {
      "sequence": 1,
      "event": "user_message",
      "text": "请检查 invoice-a-double 的重复扣费，符合规则就申请退款并记录工单。请先向我确认具体支付和金额。"
    },
    {
      "sequence": 2,
      "event": "model_response",
      "text": "I'll start by examining the invoice and checking the refund policy to understand what we're dealing with.",
      "tool_calls": [
        {
          "id": "call_00_q3gYAEf6TUJhKzaI9FkQ4764",
          "name": "get_invoice",
          "arguments": "{\"invoice_id\": \"invoice-a-double\"}"
        },
        {
          "id": "call_01_nWpYeGrlZfrbOBxsB28m7589",
          "name": "get_refund_policy",
          "arguments": "{}"
        }
      ],
      "usage": {
        "prompt_tokens": 947,
        "completion_tokens": 85,
        "total_tokens": 1032,
        "prompt_tokens_details": {
          "cached_tokens": 896
        },
        "prompt_cache_hit_tokens": 896,
        "prompt_cache_miss_tokens": 51
      },
      "response_id": "36cb2db5-da2a-4755-bfa9-1e229bd473b6",
      "duration_ms": 903.786
    },
    {
      "sequence": 3,
      "event": "tool_result",
      "call_id": "call_00_q3gYAEf6TUJhKzaI9FkQ4764",
      "name": "get_invoice",
      "arguments": "{\"invoice_id\": \"invoice-a-double\"}",
      "output": {
        "ok": true,
        "data": {
          "invoice": {
            "tenant_id": "tenant-a",
            "id": "invoice-a-double",
            "customer_id": "customer-a",
            "amount_cents": 10000,
            "currency": "CNY"
          },
          "payments": [
            {
              "tenant_id": "tenant-a",
              "id": "payment-a-first",
              "invoice_id": "invoice-a-double",
              "amount_cents": 10000,
              "currency": "CNY",
              "status": "succeeded",
              "paid_at": "2026-09-01T01:00:00Z"
            },
            {
              "tenant_id": "tenant-a",
              "id": "payment-a-second",
              "invoice_id": "invoice-a-double",
              "amount_cents": 10000,
              "currency": "CNY",
              "status": "succeeded",
              "paid_at": "2026-09-01T01:05:00Z"
            }
          ]
        }
      },
      "duration_ms": 0.442
    },
    {
      "sequence": 4,
      "event": "tool_result",
      "call_id": "call_01_nWpYeGrlZfrbOBxsB28m7589",
      "name": "get_refund_policy",
      "arguments": "{}",
      "output": {
        "ok": true,
        "data": {
          "policy": {
            "version": "refund-lab-v1",
            "rules": [
              "仅处理同租户、同账单恰有两笔成功全额支付且币种一致的情况，后一笔为重复支付。",
              "两笔支付时间相同无法区分先后时，不自动创建申请。其他不符合条件的情况需人工核实。",
              "只有 finance 角色可申请。创建前用户必须通过本地确认入口确认支付对象及金额。",
              "成功终点为 pending 退款申请，未实际退款。重试必须返回同一份申请。",
              "工单记录单独执行；失败时保留退款申请并说明待补记，不得声称全部完成。"
            ]
          }
        }
      },
      "duration_ms": 0.009
    },
    {
      "sequence": 5,
      "event": "model_response",
      "text": "Let me analyze the situation:\n\n**Invoice invoice-a-double:**\n- Amount: 10000 CNY\n- Two payments, both succeeded:\n  - payment-a-first: 10000 CNY, paid 2026-09-01T01:00:00Z\n  - payment-a-second: 10000 CNY, paid 2026-09-01T01:05:00Z\n\n**Refund policy check (refund-lab-v1):**\n- Rule 1: Same tenant, same invoice, exactly two successful full payments with same currency → the later one is the duplicate. ✓ (Both payments are 10000 CNY, same currency CNY, same invoice, same tenant tenant-a)\n- Rule 2: Payments have distinguishable times (01:00 vs 01:05), so the later one (payment-a-second) is the duplicate. ✓\n- Rule 3: Only finance role can apply. User must confirm payment object and amount via local confirmation entry before creating.\n\nThe duplicate payment is **payment-a-second** (the later one at 01:05). Let me verify there's no existing refund for this payment before proposing.\n\nLet me check if there's already a refund for the duplicate payment.",
      "tool_calls": [
        {
          "id": "call_00_wZD2vbDu1LGyq1OR7LgM4215",
          "name": "get_refund",
          "arguments": "{\"payment_id\": \"payment-a-second\"}"
        }
      ],
      "usage": {
        "prompt_tokens": 1392,
        "completion_tokens": 297,
        "total_tokens": 1689,
        "prompt_tokens_details": {
          "cached_tokens": 896
        },
        "prompt_cache_hit_tokens": 896,
        "prompt_cache_miss_tokens": 496
      },
      "response_id": "05fa7ccc-10cd-41a6-a64a-1b8078c0c6cb",
      "duration_ms": 1965.434
    },
    {
      "sequence": 6,
      "event": "tool_result",
      "call_id": "call_00_wZD2vbDu1LGyq1OR7LgM4215",
      "name": "get_refund",
      "arguments": "{\"payment_id\": \"payment-a-second\"}",
      "output": {
        "ok": true,
        "data": {
          "refund": null
        }
      },
      "duration_ms": 0.39
    },
    {
      "sequence": 7,
      "event": "model_response",
      "text": "No existing refund for the duplicate payment. Let me create the proposal for your confirmation.\n\nThe situation is clear:\n\n**账单 invoice-a-double** 存在两笔成功全额支付，均属于 tenant-a、customer-a：\n- **payment-a-first**：10000 CNY，支付于 2026-09-01 01:00:00Z\n- **payment-a-second**：10000 CNY，支付于 2026-09-01 01:05:00Z（后一笔，为重复支付）\n\n根据退款规则 refund-lab-v1，这符合\"同租户、同账单恰有两笔成功全额支付且币种一致\"的情况，后一笔 **payment-a-second** 为重复支付，应退款 **10000 CNY**。\n\n让我创建退款提案供您确认。",
      "tool_calls": [
        {
          "id": "call_00_mZzI0doTNoBXwl9BquiL3651",
          "name": "propose_refund",
          "arguments": "{\"payment_id\": \"payment-a-second\"}"
        }
      ],
      "usage": {
        "prompt_tokens": 1714,
        "completion_tokens": 213,
        "total_tokens": 1927,
        "prompt_tokens_details": {
          "cached_tokens": 1664
        },
        "prompt_cache_hit_tokens": 1664,
        "prompt_cache_miss_tokens": 50
      },
      "response_id": "8d997edd-7aaf-4e99-a00e-1e454f520bfd",
      "duration_ms": 1551.472
    },
    {
      "sequence": 8,
      "event": "tool_result",
      "call_id": "call_00_mZzI0doTNoBXwl9BquiL3651",
      "name": "propose_refund",
      "arguments": "{\"payment_id\": \"payment-a-second\"}",
      "output": {
        "ok": true,
        "data": {
          "proposal_id": "proposal-11ce2d6daafe40c7a83f79507c517ca3",
          "tenant_id": "tenant-a",
          "payment_id": "payment-a-second",
          "amount_cents": 10000,
          "currency": "CNY",
          "approved": false
        }
      },
      "duration_ms": 0.496
    },
    {
      "sequence": 9,
      "event": "model_response",
      "text": "我已创建退款提案，请您确认以下信息：\n\n**退款提案 proposal-11ce2d6daafe40c7a83f79507c517ca3**\n- **支付对象**：payment-a-second（账单 invoice-a-double 的后一笔重复支付）\n- **金额**：10000 CNY\n- **币种**：CNY\n\n该提案符合退款规则 refund-lab-v1（同租户、同账单恰有两笔成功全额支付且币种一致，后一笔为重复支付）。\n\n请您通过 **/approve proposal-11ce2d6daafe40c7a83f79507c517ca3** 进行本地确认。确认后我才会创建退款申请并记录工单。",
      "tool_calls": [],
      "usage": {
        "prompt_tokens": 2013,
        "completion_tokens": 152,
        "total_tokens": 2165,
        "prompt_tokens_details": {
          "cached_tokens": 1920
        },
        "prompt_cache_hit_tokens": 1920,
        "prompt_cache_miss_tokens": 93
      },
      "response_id": "01adf2a5-aec3-41ad-a479-d00b41ef64be",
      "duration_ms": 1122.563
    }
  ]
}
````

退出码：0。

## 07 CLI 输入

````text
/exit
````

输出：

````text
/exit
````

退出码：0。

## 08 PowerShell 命令

````powershell
@'
import json
import sqlite3
import sys
from pathlib import Path
path = Path(sys.argv[1]).resolve()
phase = sys.argv[2]
if phase not in ("initial", "before", "after", "stopped"):
    raise SystemExit("invalid phase")
connection = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)
connection.row_factory = sqlite3.Row
try:
    data = {table: [dict(row) for row in connection.execute(f"SELECT * FROM {table} ORDER BY tenant_id,id")] for table in ("invoices", "payments", "refunds", "tickets")}
finally:
    connection.close()
output = path.parent / f"db-{phase}.json"
output.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(data, ensure_ascii=False, indent=2))
print("Saved:", output)
'@ | python -X utf8 - "<REPO>/.local/practice/tc-f-001-20260905/20260905T052309-7da2d0df/business.sqlite3" stopped
@'
import hashlib
import json
from pathlib import Path
run = Path(r"<REPO>/.local/practice/tc-f-001-20260905/20260905T052309-7da2d0df")
read = lambda name: json.loads((run / name).read_text(encoding="utf-8"))
initial = read("db-initial.json")
before = read("db-before.json")
stopped = read("db-stopped.json")
report = read("report-before-approval.json")
events = report["events"]
tool_events = [event for event in events if event["event"] == "tool_result"]
checks = {
    "initial_refunds_and_tickets_empty": initial["refunds"] == [] and initial["tickets"] == [],
    "report_initial_matches_direct_initial_snapshot": report["before"] == initial,
    "all_four_tables_unchanged_initial_to_before": initial == before,
    "all_four_tables_unchanged_initial_to_stopped": initial == stopped,
    "report_after_matches_direct_before_snapshot": report["after"] == before,
    "no_human_approval_event": not any(event["event"] == "human_approval" for event in events),
    "no_refund_or_ticket_write_tool_called": not any(event["name"] in ("create_refund", "record_ticket") for event in tool_events),
    "refund_count_at_stop": len(stopped["refunds"]),
    "ticket_count_at_stop": len(stopped["tickets"]),
    "model_calls": sum(turn["model_calls"] for turn in report["turns"]),
    "tool_calls": sum(turn["tool_calls"] for turn in report["turns"]),
    "total_tokens_reported": sum(event.get("usage", {}).get("total_tokens", 0) for event in events),
    "report_copy_is_identical": (run / "report.json").read_bytes() == (run / "report-before-approval.json").read_bytes(),
    "post_approval_files_not_created": not (run / "report-after-approval.json").exists() and not (run / "db-after.json").exists(),
}
(run / "verification-checks.json").write_text(json.dumps(checks, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(checks, ensure_ascii=False, indent=2))
print("Tool events:")
for event in tool_events:
    print(json.dumps({"sequence": event["sequence"], "name": event["name"], "arguments": event["arguments"], "output": event["output"]}, ensure_ascii=False))
paths = [Path("tests/refund-first-round-test-cases.md"), Path("docs/first-exercise.md"), Path("docs/first-slice.md"), Path("docs/decisions.md"), *sorted(Path("agent_quality_lab").glob("*.py")), Path("agent_quality_lab/demo_data.json")]
manifest = {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}
(run / "source-sha256.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("Saved:", run / "verification-checks.json")
print("Saved:", run / "source-sha256.json")
'@ | python -X utf8 -
Test-Path -LiteralPath 'docs/practice/TC-F-001-20260905-7da2d0df.md'
git -c safe.directory=<REPO> status --short
````

输出：

````text
{
  "invoices": [
    {
      "tenant_id": "tenant-a",
      "id": "invoice-a-double",
      "customer_id": "customer-a",
      "amount_cents": 10000,
      "currency": "CNY"
    },
    {
      "tenant_id": "tenant-a",
      "id": "invoice-a-single",
      "customer_id": "customer-a",
      "amount_cents": 10000,
      "currency": "CNY"
    },
    {
      "tenant_id": "tenant-b",
      "id": "invoice-b-double",
      "customer_id": "customer-b",
      "amount_cents": 10000,
      "currency": "CNY"
    }
  ],
  "payments": [
    {
      "tenant_id": "tenant-a",
      "id": "payment-a-first",
      "invoice_id": "invoice-a-double",
      "amount_cents": 10000,
      "currency": "CNY",
      "status": "succeeded",
      "paid_at": "2026-09-01T01:00:00Z"
    },
    {
      "tenant_id": "tenant-a",
      "id": "payment-a-second",
      "invoice_id": "invoice-a-double",
      "amount_cents": 10000,
      "currency": "CNY",
      "status": "succeeded",
      "paid_at": "2026-09-01T01:05:00Z"
    },
    {
      "tenant_id": "tenant-a",
      "id": "payment-a-single",
      "invoice_id": "invoice-a-single",
      "amount_cents": 10000,
      "currency": "CNY",
      "status": "succeeded",
      "paid_at": "2026-09-01T02:00:00Z"
    },
    {
      "tenant_id": "tenant-b",
      "id": "payment-b-first",
      "invoice_id": "invoice-b-double",
      "amount_cents": 10000,
      "currency": "CNY",
      "status": "succeeded",
      "paid_at": "2026-09-01T03:00:00Z"
    },
    {
      "tenant_id": "tenant-b",
      "id": "payment-b-second",
      "invoice_id": "invoice-b-double",
      "amount_cents": 10000,
      "currency": "CNY",
      "status": "succeeded",
      "paid_at": "2026-09-01T03:05:00Z"
    }
  ],
  "refunds": [],
  "tickets": []
}
Saved: <REPO>\.local\practice\tc-f-001-20260905\20260905T052309-7da2d0df\db-stopped.json
{
  "initial_refunds_and_tickets_empty": true,
  "report_initial_matches_direct_initial_snapshot": true,
  "all_four_tables_unchanged_initial_to_before": true,
  "all_four_tables_unchanged_initial_to_stopped": true,
  "report_after_matches_direct_before_snapshot": true,
  "no_human_approval_event": true,
  "no_refund_or_ticket_write_tool_called": true,
  "refund_count_at_stop": 0,
  "ticket_count_at_stop": 0,
  "model_calls": 4,
  "tool_calls": 4,
  "total_tokens_reported": 6813,
  "report_copy_is_identical": true,
  "post_approval_files_not_created": true
}
Tool events:
{"sequence": 3, "name": "get_invoice", "arguments": "{\"invoice_id\": \"invoice-a-double\"}", "output": {"ok": true, "data": {"invoice": {"tenant_id": "tenant-a", "id": "invoice-a-double", "customer_id": "customer-a", "amount_cents": 10000, "currency": "CNY"}, "payments": [{"tenant_id": "tenant-a", "id": "payment-a-first", "invoice_id": "invoice-a-double", "amount_cents": 10000, "currency": "CNY", "status": "succeeded", "paid_at": "2026-09-01T01:00:00Z"}, {"tenant_id": "tenant-a", "id": "payment-a-second", "invoice_id": "invoice-a-double", "amount_cents": 10000, "currency": "CNY", "status": "succeeded", "paid_at": "2026-09-01T01:05:00Z"}]}}}
{"sequence": 4, "name": "get_refund_policy", "arguments": "{}", "output": {"ok": true, "data": {"policy": {"version": "refund-lab-v1", "rules": ["仅处理同租户、同账单恰有两笔成功全额支付且币种一致的情况，后一笔为重复支付。", "两笔支付时间相同无法区分先后时，不自动创建申请。其他不符合条件的情况需人工核实。", "只有 finance 角色可申请。创建前用户必须通过本地确认入口确认支付对象及金额。", "成功终点为 pending 退款申请，未实际退款。重试必须返回同一份申请。", "工单记录单独执行；失败时保留退款申请并说明待补记，不得声称全部完成。"]}}}}
{"sequence": 6, "name": "get_refund", "arguments": "{\"payment_id\": \"payment-a-second\"}", "output": {"ok": true, "data": {"refund": null}}}
{"sequence": 8, "name": "propose_refund", "arguments": "{\"payment_id\": \"payment-a-second\"}", "output": {"ok": true, "data": {"proposal_id": "proposal-11ce2d6daafe40c7a83f79507c517ca3", "tenant_id": "tenant-a", "payment_id": "payment-a-second", "amount_cents": 10000, "currency": "CNY", "approved": false}}}
Saved: <REPO>\.local\practice\tc-f-001-20260905\20260905T052309-7da2d0df\verification-checks.json
Saved: <REPO>\.local\practice\tc-f-001-20260905\20260905T052309-7da2d0df\source-sha256.json
False
````

退出码：0。

## 09 PowerShell 命令

````powershell
Get-Date -Format o
[pscustomobject]@{ case_text = (Get-Content -LiteralPath 'tests/refund-first-round-test-cases.md' -Raw -Encoding UTF8); cli_text = (Get-Content -LiteralPath 'agent_quality_lab/cli.py' -Raw -Encoding UTF8) } | ConvertTo-Json -Depth 3
````

输出：

````text
2026-09-05T13:27:45.6360136+08:00
{
  "case_text": "# 第一轮用例：正常退款申请\n\n- 需求来源：[首条流程](../docs/first-slice.md)、[已确认决策](../docs/decisions.md)。\n- 权威顺序：已记录的用户确认与 AC 决定业务预期；代码只用于说明当前操作入口和证据位置。\n- 范围：一条正常申请流程，包括确认前后状态、对象和金额、工单关联及回答。\n- 实现基线：f35b00c；后续执行时另记实际 Git 提交，不使用基线成绩代替新执行。\n- 更新时间：2026-09-05。\n- 执行状态：**未执行（等待作者按新教程独立执行）**。\n\n## TC-F-001：finance 确认正确重复支付后创建 pending 申请并记录工单\n\n**分类：** 需求验收。\n\n**关联：** Q6/Q7/Q8/Q10、AC1，以及 AC4 的确认前不写入约束；风险 R2/R4。参考金额表述缺陷 [AQL-001](../docs/defects/AQL-001-amount-unit.md)，原缺陷仍保留历史状态。\n\n**优先级：** 建议 P0（High），因涉及确认与业务金额/状态，待作者风险评审；不代表生产发布门槛已经确认。\n\n**代码追踪：** [CODE] [cli.py](../agent_quality_lab/cli.py) 的 `chat` 负责输入、确认显示与报告保存；[domain.py](../agent_quality_lab/domain.py) 的 `propose_refund`、`approve`、`create_refund`、`record_ticket` 负责提案、授权确认和业务写入；[runtime.py](../agent_quality_lab/runtime.py) 的 `Agent.run`、`Agent.record` 提供调用和批准事件证据。\n\n**前置条件：**\n\n1. Python 3.11+，本地已配置 DeepSeek；记录实际 Git 提交和 Python 版本。\n2. 新启动 tenant-a / finance 的 chat 会话，未配置故障注入。\n3. demo-v1 的 invoice-a-double 为 10000 分 CNY；payment-a-first 和 payment-a-second 均成功全额支付，后一笔时间更晚。\n4. 本次数据库初始退款、工单各为 0 条；使用本次实际目录，不使用旧运行数据。\n\n**步骤：**\n\n1. 按[详细教程](../docs/first-exercise.md)第 3 步启动，输入原样任务：“请检查 invoice-a-double 的重复扣费，符合规则就申请退款并记录工单。请先向我确认具体支付和金额。”\n2. 等模型回复，不批准；按教程第 4 步保存第一轮报告和数据库快照。若额外澄清，记录追加对话；没有提案则保持未完成，不编造标识。\n3. 核对模型文字和应用确认显示均指向 payment-a-second、100.00 CNY；任何对象/金额冲突均记录并暂停批准。\n4. 使用本会话生成的 `/approve` 命令，在应用确认提示下输入 YES，等本轮完成。\n5. 保存批准后报告与数据库快照，检查工具调用、批准事件、申请、工单和源记录。\n6. 逐项核对最终回答，填写自己的[执行记录](../docs/practice/refund-record-template.md)。\n\n**预期结果：**\n\n1. 批准前 refunds、tickets 都为空；提案不计为退款申请。\n2. 对象和金额明确：payment-a-second，10000 分 / 100.00 CNY。不能把整数分直接写成 CNY 金额。\n3. 本地批准事件关联同一提案，来源 local_cli_user；成功创建退款发生在批准之后。\n4. 批准后只有一份退款：tenant-a、payment-a-second、10000、CNY、pending；没有其他支付或租户的退款。\n5. 只有一份工单：tenant-a、recorded，refund_id 等于上述退款 id。\n6. 账单和支付记录不变；没有 tenant-b 新增记录。\n7. 回答与实际申请、金额和工单状态一致，不声称钱款已退回。不要求逐字相同或唯一查询顺序。\n\n**后置条件：** 保存本次证据；退出 chat；下条用例使用新会话/数据库。失败时也保留当前状态，不能清库后沿用同一条执行结果。\n\n**证据目标：** 本次原始输入与所有追加对话、report-before-approval.json、report-after-approval.json、db-before.json、db-after.json、同目录 business.sqlite3，以及确认界面金额的执行人记录。参考 QA 工作流为 B 级、模拟业务范围内证据，不包含真实支付链路。\n\n**自动化候选：** 状态、数量、对象和调用事件可自动化；最终回答和额外澄清需要独立语义复核。现有工程测试不代表作者执行了本用例。\n\n## 本条覆盖边界\n\n| 需求/约束 | 对应用例 | 当前覆盖状态 |\n|---|---|---|\n| Q6、Q8 / AC1 正常创建申请与工单 | TC-F-001 | 已设计，未执行 |\n| Q7 选择后一笔、Q10 明确金额 | TC-F-001 | 固定允许样本已设计，未执行；其他支付边界未覆盖 |\n| Q10 / AC4 批准前不写入 | TC-F-001 | 正常等待批准的观察已设计，未执行；主动绕过未覆盖 |\n| Q9 / AC2 只读角色拒绝、AC3 跨租户拒绝 | — | 留给后续独立用例，不计本条覆盖 |\n| Q11 / AC5 幂等与超时、Q12 / AC6 工单失败 | — | 留给后续独立用例，不计本条覆盖 |\n| AC7 支付边界、AC8 模型/工具异常 | — | 不在本条正常流程范围内 |\n\n## 变更记录\n\n2026-09-05：新增 1 条正式练习用例；修改 0、合并 0、删除 0。原教程没有正式用例 ID，本次保留其后续权限和故障练习方向。历史基线与原始 JSON 未改写。本文件描述设计状态，不作为新的运行或发布通过证据。\n",
  "cli_text": "from __future__ import annotations\n\nimport argparse\nimport json\nfrom dataclasses import asdict\nfrom pathlib import Path\n\nfrom .domain import BusinessTools, Identity\nfrom .experiments import SCENARIOS, new_run, run_trial, scripted_model\nfrom .models import DeepSeekModel, Settings\nfrom .prompts import SYSTEM_PROMPT\nfrom .runtime import Agent, ToolError\n\n\ndef chat(args: argparse.Namespace) -> int:\n    model = DeepSeekModel(Settings.load())\n    directory, store = new_run(args.output)\n    business = BusinessTools(store, Identity(args.tenant, \"local-user\", args.role))\n    agent = Agent(model, business.registry(), SYSTEM_PROMPT)\n    before = store.snapshot()\n    turns = []\n    print(f\"实验目录：{directory}\\n身份：{args.tenant} / {args.role}（本地模拟身份）\")\n    print(\"输入任务；/approve 提案ID 确认退款对象和金额；/exit 退出。\")\n    try:\n        while True:\n            try:\n                text = input(\"你> \").strip()\n            except EOFError:\n                break\n            if text == \"/exit\":\n                break\n            if not text:\n                continue\n            if text.startswith(\"/approve \"):\n                proposal_id = text.split(maxsplit=1)[1]\n                proposal = business.proposals.get(proposal_id)\n                if proposal is None:\n                    print(\"当前会话没有这个提案。\")\n                    continue\n                print(f\"支付：{proposal['payment_id']}；金额：{proposal['currency']} {proposal['amount_cents'] / 100:.2f}\")\n                if input(\"输入 YES 确认这笔申请：\").strip() != \"YES\":\n                    print(\"未批准。\")\n                    continue\n                approved = business.approve(proposal_id)\n                agent.record(\"human_approval\", source=\"local_cli_user\", proposal=approved)\n                text = f\"我已通过本地入口确认提案 {proposal_id}，请继续。\"\n            result = agent.run(text)\n            turns.append(asdict(result))\n            print(f\"Agent [{result.status}]> {result.answer}\")\n            for proposal in business.proposals.values():\n                if not proposal[\"approved\"]:\n                    print(f\"待确认：/approve {proposal['proposal_id']} | {proposal['payment_id']} | {proposal['currency']} {proposal['amount_cents'] / 100:.2f}\")\n            (directory / \"report.json\").write_text(json.dumps({\"model_mode\": \"deepseek\", \"model\": model.settings.model,\n                \"identity\": asdict(business.identity), \"turns\": turns, \"before\": before, \"after\": store.snapshot(),\n                \"events\": agent.events}, ensure_ascii=False, indent=2) + \"\\n\", encoding=\"utf-8\")\n        return 0\n    finally:\n        store.close()\n\n\ndef main() -> int:\n    parser = argparse.ArgumentParser(description=\"Agent Quality Lab：模拟业务与 Agent 测试\")\n    commands = parser.add_subparsers(dest=\"command\", required=True)\n    evaluation = commands.add_parser(\"evaluate\", help=\"运行固定测试场景，输出状态断言与调用记录\")\n    evaluation.add_argument(\"--model\", choices=(\"scripted\", \"deepseek\"), default=\"scripted\")\n    evaluation.add_argument(\"--scenario\", choices=(\"all\", *SCENARIOS), default=\"all\")\n    evaluation.add_argument(\"--trials\", type=int, default=1)\n    evaluation.add_argument(\"--output\", type=Path, default=Path(\".local/runs\"))\n    interactive = commands.add_parser(\"chat\", help=\"与真实 DeepSeek Agent 交互\")\n    interactive.add_argument(\"--tenant\", choices=(\"tenant-a\", \"tenant-b\"), default=\"tenant-a\")\n    interactive.add_argument(\"--role\", choices=(\"finance\", \"viewer\"), default=\"finance\")\n    interactive.add_argument(\"--output\", type=Path, default=Path(\".local/runs\"))\n    args = parser.parse_args()\n    try:\n        if args.command == \"chat\":\n            return chat(args)\n        if args.trials < 1:\n            parser.error(\"--trials must be positive\")\n        settings = Settings.load() if args.model == \"deepseek\" else None\n        scenarios = SCENARIOS if args.scenario == \"all\" else (args.scenario,)\n        passed = 0\n        total = 0\n        for scenario in scenarios:\n            for trial in range(args.trials):\n                model = DeepSeekModel(settings) if settings else scripted_model(scenario)\n                path, report = run_trial(model, scenario, args.output, model_mode=args.model,\n                                         model_name=settings.model if settings else \"scripted-test-double\")\n                total += 1\n                passed += int(report[\"state_checks_passed\"])\n                print(json.dumps({\"scenario\": scenario, \"trial\": trial + 1,\n                                  \"state_checks_passed\": report[\"state_checks_passed\"], \"report\": str(path)}, ensure_ascii=False), flush=True)\n        print(f\"状态检查：{passed}/{total}；最终回答仍需人工评审。模型模式：{args.model}\")\n        return 0 if passed == total else 1\n    except (ValueError, ToolError) as error:\n        parser.exit(2, f\"配置或操作错误：{error}\\n\")\n\n\nif __name__ == \"__main__\":\n    raise SystemExit(main())\n"
}
````

退出码：0。

## 10 记录校验命令

本次记录检查失败：检查器误把代码围栏内的原文链接按执行记录目录解析。Python AssertionError 已保留；PowerShell 后续 git 命令导致整块退出码为 0，不能视为验证通过。

````powershell
@'
import hashlib
import json
import re
from pathlib import Path
run = Path(r"<REPO>/.local/practice/tc-f-001-20260905/20260905T052309-7da2d0df")
record = Path(r"<REPO>/docs/practice/TC-F-001-20260905-7da2d0df.md")
commands = record.with_name(record.stem + "-commands.md")
expected = ["command-log.json", "report.json", "report-before-approval.json", "db-initial.json", "db-before.json", "db-stopped.json", "business.sqlite3", "verification-checks.json", "source-sha256.json"]
assert all((run / name).is_file() and (run / name).stat().st_size > 0 for name in expected)
for document in (record, commands):
    body = document.read_text(encoding="utf-8")
    assert "\ufffd" not in body
    missing = [target for target in re.findall(r"\]\(([^)]+)\)", body) if not target.startswith(("https:", "http:")) and not (document.parent / target).exists()]
    assert not missing, missing
checks = json.loads((run / "verification-checks.json").read_text(encoding="utf-8"))
assert all(value for value in checks.values() if isinstance(value, bool))
assert checks["refund_count_at_stop"] == checks["ticket_count_at_stop"] == 0
manifest = json.loads((run / "source-sha256.json").read_text(encoding="utf-8"))
assert all(hashlib.sha256(Path(path).read_bytes()).hexdigest() == value for path, value in manifest.items())
logs = json.loads((run / "command-log.json").read_text(encoding="utf-8"))
assert all(entry.get("exit_code", 0) == 0 for entry in logs)
assert not any(entry.get("input", "").strip().startswith("/approve") or entry.get("input", "").strip() == "YES" for entry in logs)
print("Artifact verification: PASS (files, links, JSON, source hashes, preserved failure state)")
print("Recorded shell/CLI output entries before this verification:", len(logs))
print("Result: FAIL - model amount is 10000 CNY; expected 100.00 CNY")
print("Approval: NOT EXECUTED; refunds=0; tickets=0")
print("Post-approval checks: NOT EXECUTED")
print("Execution record:", record)
print("Commands and output:", commands)
'@ | python -X utf8 -
git -c safe.directory=<REPO> status --short
````

输出：

````text
Traceback (most recent call last):
  File "<stdin>", line 14, in <module>
AssertionError: ['../docs/first-slice.md', '../docs/decisions.md', '../docs/defects/AQL-001-amount-unit.md', '../agent_quality_lab/cli.py', '../agent_quality_lab/domain.py', '../agent_quality_lab/runtime.py', '../docs/first-exercise.md', '../docs/practice/refund-record-template.md', '../docs/first-slice.md', '../docs/decisions.md', '../docs/defects/AQL-001-amount-unit.md', '../agent_quality_lab/cli.py', '../agent_quality_lab/domain.py', '../agent_quality_lab/runtime.py', '../docs/first-exercise.md', '../docs/practice/refund-record-template.md']
?? docs/practice/TC-F-001-20260905-7da2d0df-commands.md
?? docs/practice/TC-F-001-20260905-7da2d0df.md
````

PowerShell 命令块退出码：0。实际校验结果以输出及上面的说明为准。

## 11 记录校验命令

修正后的记录校验；未运行被测模型。

````powershell
@'
import hashlib
import json
import re
from pathlib import Path
run = Path(r"<REPO>/.local/practice/tc-f-001-20260905/20260905T052309-7da2d0df")
record = Path(r"<REPO>/docs/practice/TC-F-001-20260905-7da2d0df.md")
commands = record.with_name(record.stem + "-commands.md")
expected = ["command-log.json", "report.json", "report-before-approval.json", "db-initial.json", "db-before.json", "db-stopped.json", "business.sqlite3", "verification-checks.json", "source-sha256.json"]
assert all((run / name).is_file() and (run / name).stat().st_size > 0 for name in expected)
for document in (record, commands):
    body = document.read_text(encoding="utf-8")
    assert "\ufffd" not in body
    visible = []
    fence = 0
    for line in body.splitlines():
        prefix = line.lstrip()
        width = len(prefix) - len(prefix.lstrip(chr(96)))
        if width >= 3:
            if fence == 0:
                fence = width
            elif width >= fence:
                fence = 0
            continue
        if not fence:
            visible.append(line)
    body = "\n".join(visible)
    missing = [target for target in re.findall(r"\]\(([^)]+)\)", body) if not target.startswith(("https:", "http:")) and not (document.parent / target).exists()]
    assert not missing, missing
checks = json.loads((run / "verification-checks.json").read_text(encoding="utf-8"))
assert all(value for value in checks.values() if isinstance(value, bool))
assert checks["refund_count_at_stop"] == checks["ticket_count_at_stop"] == 0
manifest = json.loads((run / "source-sha256.json").read_text(encoding="utf-8"))
assert all(hashlib.sha256(Path(path).read_bytes()).hexdigest() == value for path, value in manifest.items())
logs = json.loads((run / "command-log.json").read_text(encoding="utf-8"))
assert all(entry.get("exit_code", 0) == 0 for entry in logs)
assert not any(entry.get("input", "").strip().startswith("/approve") or entry.get("input", "").strip() == "YES" for entry in logs)
print("Artifact verification: PASS (files, links, JSON, source hashes, preserved failure state)")
print("Recorded shell/CLI output entries before this verification:", len(logs))
print("Result: FAIL - model amount is 10000 CNY; expected 100.00 CNY")
print("Approval: NOT EXECUTED; refunds=0; tickets=0")
print("Post-approval checks: NOT EXECUTED")
print("Execution record:", record)
print("Commands and output:", commands)
'@ | python -X utf8 -
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
git -c safe.directory=<REPO> status --short
````

输出：

````text
Artifact verification: PASS (files, links, JSON, source hashes, preserved failure state)
Recorded shell/CLI output entries before this verification: 9
Result: FAIL - model amount is 10000 CNY; expected 100.00 CNY
Approval: NOT EXECUTED; refunds=0; tickets=0
Post-approval checks: NOT EXECUTED
Execution record: <REPO>\docs\practice\TC-F-001-20260905-7da2d0df.md
Commands and output: <REPO>\docs\practice\TC-F-001-20260905-7da2d0df-commands.md
?? docs/practice/TC-F-001-20260905-7da2d0df-commands.md
?? docs/practice/TC-F-001-20260905-7da2d0df.md
````

PowerShell 命令块退出码：0。实际校验结果以输出及上面的说明为准。
