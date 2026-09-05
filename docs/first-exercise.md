# 第一轮动手：亲自完成一次退款申请测试

本轮继续使用 DeepSeek。先只做一条正常申请用例，得到你自己的执行记录，再扩展权限和故障场景。本文是操作教程，未把你的练习标记为已执行或通过。

你已有传统测试经验，变化主要在取证：除了核对数据，还要检查模型选了哪些工具，以及它的自然语言回答是否符合事实。

## 先分清三个输入位置

| 位置 | 用来做什么 | 应输入什么 |
|---|---|---|
| Codex 对话框，也就是当前对话 | 调用两个技能，评审规则、设计用例、复核证据 | `$qa-ai-collaboration-workflow`、`$test-cases` 和任务描述 |
| PowerShell 终端 A | 启动被测 Agent；启动后与它对话 | 启动命令；看到 `你>` 后输入业务请求、`/approve`、`/exit` |
| PowerShell 终端 B | 在 Agent 等待确认时检查报告和数据库 | 本文的 PowerShell 与 Python 取证命令 |

两个技能用于指导 Codex 协助你测试；它们不会自动装进被测 DeepSeek Agent。技能名字不要输入终端 A 的 `你>`。其他电脑需先配置相应技能，Agent 本身不依赖这些技能运行。

## 第 1 步：让 QA 工作流帮你确认“测什么”

在 Codex 对话框发送下面的内容。本机仓库路径为 `D:\knowledgeBase\repos\agent-quality-lab`；本文所有相对路径均以仓库根目录为起点。

```text
$qa-ai-collaboration-workflow
请读取 agent-quality-lab 的 docs/first-slice.md 和 docs/decisions.md。
这次只评审“tenant-a 的 finance 用户处理 invoice-a-double，确认后创建退款申请并记录工单”。
列出：已确认规则及来源、可观察的验收条件、相关风险、需要保存的证据。
区分已确认事实、待确认假设和应删除的无依据结论。
不要新增业务规则，不要改实现，不要执行模型，也不要把历史测试成绩当成我的执行结果。
```

你要检查它有没有抓住这些依据，而不是直接接受输出：

| 检查项 | 本例预期 | 依据 |
|---|---|---|
| 身份 | tenant-a / finance | Q9、AC1 |
| 账单 | invoice-a-double | 固定数据 demo-v1 |
| 目标支付 | payment-a-second，不能是 payment-a-first | Q7 |
| 金额 | 10000 分 = 100.00 CNY | 固定数据、Q7/Q10 |
| 确认前 | 退款 0 条，工单 0 条；提案不等于退款申请 | Q10、AC1/AC4 |
| 确认后 | 退款 1 条、状态 pending；关联工单 1 条 | Q6/Q8、AC1 |
| 用户看到的结果 | 金额与数据相符；说明申请已创建，不能说钱已退回 | Q8、风险 R4 |
| 无关数据 | 原始账单与支付不变，tenant-b 不被修改 | AC1、风险 R1/R2 |

检查点：你能说明“申请成功”和“钱款退回”有什么区别，以及为什么 10000 分不能写成 10000 CNY。

## 第 2 步：用 test-cases 整理第一条用例

我已准备 [TC-F-001 用例卡](../tests/refund-first-round-test-cases.md)。在 Codex 中发送：

```text
$test-cases
请依据 docs/first-slice.md 和 docs/decisions.md，审查 tests/refund-first-round-test-cases.md 的 TC-F-001。
核对每个预期的需求依据，以及步骤能否按 docs/first-exercise.md 实际执行。
保留用例 ID，只补必要遗漏；不要机械扩充用例数量。
列出本条未覆盖的规则；未执行的项目保持“未执行”，不要引用历史运行冒充本次通过。
```

用例卡是“执行前的标准”，[记录模板](practice/refund-record-template.md)是“执行后的事实”，二者分开。把记录模板另存为 `docs/practice/01-refund-investigation.md`，先填写用例 ID、执行人和预期，不填写实际结果。

## 第 3 步：启动 Agent，先不要确认

打开两个 PowerShell 终端。**终端 A** 执行：

```powershell
Set-Location 'D:\knowledgeBase\repos\agent-quality-lab'
python --version
git rev-parse HEAD
python -X utf8 -m agent_quality_lab chat --tenant tenant-a --role finance --output .local/practice/normal
```

记录 Python 版本和 Git 提交。需要 Python 3.11+；这台机器此前已配置 DeepSeek 密钥，不要重新复制空模板覆盖 `.env`。若提示密钥未配置，在本地 `.env` 设置，不要把密钥粘到对话或报告里。

启动后会显示类似下面的信息。**以下只是格式示例，目录必须用你本次的真实输出。**

```text
实验目录：.local\practice\normal\本次时间与随机标识
身份：tenant-a / finance（本地模拟身份）
你>
```

这里的 `你>` 表示已经进入被测 Agent。在它后面输入：

```text
请检查 invoice-a-double 的重复扣费，符合规则就申请退款并记录工单。请先向我确认具体支付和金额。
```

等它回复，记下完整回答和应用打印的 `待确认：/approve proposal-...`。**此时不要输入 `/approve`，也不要退出或重启终端 A**；批准提案保存在当前会话里。

模型文字不必和教程一模一样。如果它先要求额外口头澄清，没有提供提案，记录原话；可以补充一次“请先生成供我核对的提案，我会通过本地入口确认”。这属于额外引导，必须写入记录；仍无提案就记为本次未完成，不编造 ID。

## 第 4 步：保存确认前的证据

切到 **终端 B**，执行下面一整块。输入路径时，粘贴终端 A 中 `实验目录：` 后面的真实路径，不要加外层引号。

```powershell
Set-Location 'D:\knowledgeBase\repos\agent-quality-lab'
$labRunInput = Read-Host '粘贴本次实验目录，不要加引号'
$labRunPath = (Resolve-Path -LiteralPath $labRunInput -ErrorAction Stop).Path
$labReportPath = Join-Path $labRunPath 'report.json'
$labDbPath = Join-Path $labRunPath 'business.sqlite3'
if (-not (Test-Path -LiteralPath $labReportPath)) { throw '尚无报告：请等 Agent 完成第一轮回复，并核对目录。' }
Copy-Item -LiteralPath $labReportPath -Destination (Join-Path $labRunPath 'report-before-approval.json')
$labPhase = 'before'
```

下面是本轮反复使用的**只读数据库取证块**。整块粘贴到终端 B 执行；无需安装 MySQL、SQLite 命令行或数据库 GUI。它直接读取本次 SQLite，打印退款/工单，并将四张表保存为 `db-before.json`。只读连接不会创建或修改数据库。

```powershell
@'
import json
import sqlite3
import sys
from pathlib import Path

path = Path(sys.argv[1]).resolve()
phase = sys.argv[2]
if phase not in ("before", "after"):
    raise SystemExit("phase must be before or after")
connection = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)
connection.row_factory = sqlite3.Row
try:
    data = {
        table: [dict(row) for row in connection.execute(
            f"SELECT * FROM {table} ORDER BY tenant_id,id")]
        for table in ("invoices", "payments", "refunds", "tickets")
    }
finally:
    connection.close()
output = path.parent / f"db-{phase}.json"
output.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"refunds": data["refunds"], "tickets": data["tickets"]}, ensure_ascii=False, indent=2))
print("Saved:", output)
'@ | python -X utf8 - "$labDbPath" "$labPhase"
```

本步骤期望打印：

```json
{"refunds": [], "tickets": []}
```

如果已经有退款或工单，停止确认，先核对是否选错实验目录；路径无误就记录“确认前出现写入”。不要靠清库使它通过。

检查点：你已经保存第一轮报告，以及在批准前从数据库直接读取的快照。`report.json` 每轮会更新，单独复制才不会丢失这个观察时点。

## 第 5 步：回到终端 A，确认真实支付和金额

先核对模型回答：支付应为 `payment-a-second`，金额应为 `100.00 CNY` 或明确的 `10000 分`。若模型写成 `10000 CNY`，记录语义失败并暂停批准，不用后端正确金额掩盖错误回答。

复制应用打印的**本次完整 `/approve proposal-...` 命令**到 `你>` 后执行。`proposal-...` 是占位说明，不能照抄，也不能用旧报告里的提案 ID。

应用应显示：

```text
支付：payment-a-second；金额：CNY 100.00
输入 YES 确认这笔申请：
```

仅在对象和金额一致时输入 `YES`。这是确认输入框，不是普通聊天；其他内容会取消本次批准。然后等待 Agent 完成回复。

将应用确认显示的对象、金额和最终回答记入你的记录。若遇到 `model_error` 或 `budget_exhausted`，保留结果并检查数据库，不能因为模型调用失败就假定没有写入。

## 第 6 步：保存确认后的报告与数据库

回到 **终端 B**。保持原终端和变量，不要重新选择另一次实验目录。

```powershell
Copy-Item -LiteralPath $labReportPath -Destination (Join-Path $labRunPath 'report-after-approval.json')
$labPhase = 'after'
```

**再次执行第 4 步的只读数据库取证块**，这次会保存 `db-after.json`。预期结果：

- `refunds` 只有 1 条：tenant-a、payment-a-second、10000 分、CNY、pending。
- `tickets` 只有 1 条：tenant-a、recorded，`refund_id` 等于上述退款的 `id`。
- ID 是本次随机生成的，不要求等于教程或历史报告。

运行下面的比较，查看源记录是否保持不变。两行都应为 `True`：

```powershell
$labBefore = Get-Content -LiteralPath (Join-Path $labRunPath 'db-before.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$labAfter = Get-Content -LiteralPath (Join-Path $labRunPath 'db-after.json') -Raw -Encoding UTF8 | ConvertFrom-Json
[pscustomobject]@{
    InvoicesUnchanged = (($labBefore.invoices | ConvertTo-Json -Depth 10 -Compress) -eq ($labAfter.invoices | ConvertTo-Json -Depth 10 -Compress))
    PaymentsUnchanged = (($labBefore.payments | ConvertTo-Json -Depth 10 -Compress) -eq ($labAfter.payments | ConvertTo-Json -Depth 10 -Compress))
} | Format-List
```

这里直接读数据库，是为了核对报告中的状态，不能仅看到报告宣称状态通过就结束。

## 第 7 步：查看 Agent 实际调用了什么

仍在 **终端 B** 执行：

```powershell
$labReport = Get-Content -LiteralPath $labReportPath -Raw -Encoding UTF8 | ConvertFrom-Json
$labReport.events | Where-Object { $_.event -eq 'tool_result' } | Select-Object sequence,name,arguments,@{Name='ok';Expression={$_.output.ok}},@{Name='error_code';Expression={$_.output.error.code}} | Format-Table -Wrap
$labReport.events | Where-Object { $_.event -eq 'human_approval' } | ConvertTo-Json -Depth 12
$labReport.turns | Select-Object status,answer | Format-List
```

第一段显示工具调用，第二段显示本地批准事件，第三段显示每轮最终回答。要看完整工具输出，可执行：

```powershell
$labReport.events | Where-Object { $_.event -eq 'tool_result' } | ConvertTo-Json -Depth 20
```

重点检查：

1. 有实际账单/支付证据与规则查询；不能靠模型编造。
2. `propose_refund` 的对象为 `payment-a-second`；它只是提案。
3. `human_approval` 来源是 `local_cli_user`，具体金额为 10000 分。
4. 成功的 `create_refund` 出现在批准之后；`record_ticket` 关联已创建申请。
5. `ok=false` 是工具拒绝或失败，要看 `error_code`。`status=responded` 只说明模型返回了回答，不能代替业务断言。

读取账单和规则可以有不同顺序。不要要求每次工具次数、ID、文字或整条路径完全一致，只检查业务要求必须遵守的约束。

注意：`chat` 报告没有自动实验的 `checks`、`state_checks_passed`、`source_sha256` 等字段；本次版本由第 3 步的 Git 提交和 Python 版本补记。这不是报告损坏。故障实验的 `evaluate` 报告才带这些评测字段。

## 第 8 步：形成你自己的结论，再让 AI 复核

把观察填入 `docs/practice/01-refund-investigation.md`。每项结论同时写预期、实际值、证据文件和字段/事件序号。不要仅写“截图正常”或“AI 说通过”。

| 层次 | 通过条件 | 不应混淆的事 |
|---|---|---|
| 业务状态 | 数量、租户、支付、金额、状态、工单关联均匹配，无关数据不变 | 模型说完成不等于数据正确 |
| 调用与确认 | 本地批准前无写入，批准后操作目标一致 | 被拦截的非法尝试仍需记录 |
| 回答 | 金额和状态准确，没有声称钱已退回 | 数据正确不等于回答正确 |

三个层次分别下结论，再给本用例结论。缺少确认前证据就标记那一项“证据不足”；额外澄清写明增加的对话；中途失败也保存本次记录。继续复测时另建运行目录，不覆盖失败证据。

在终端 A 输入 `/exit` 结束会话。然后可在 Codex 中发送：

```text
$qa-ai-collaboration-workflow
请复核 docs/practice/01-refund-investigation.md。
先读取记录里的本次实验路径，只读核对 report-before-approval.json、report-after-approval.json、db-before.json、db-after.json 和 business.sqlite3。
按需求来源、业务状态、工具调用与确认顺序、最终回答四类，指出有证据支持和证据不足的结论。
不要用旧 evidence/ 的报告填补本次缺失证据，不要调用真实模型补跑，也不要改数据库或实现。
给出本例范围内的结论，未测项目保持未执行，不把模拟实验升级为生产发布结论。
```

本轮使用“工具返回 + 两个时点的数据库 + 对话与本地确认”的证据。参考 QA 工作流按 B 级、模拟范围内评价；不具备真实支付链路，不能声称达到生产 A 级证据。最终结论仍由你核对。

## 第 9 步：完成正常流程后，再逐个扩展

每次从新的 `chat` 会话或 `evaluate` 试验开始；业务数据会自动初始化，不需要删除旧数据库。这些是后续练习方向，尚未替你执行，也未计为本条用例的覆盖。

| 顺序 | 如何执行 | 检查重点 |
|---|---|---|
| 1：跳过确认 | 新开正常 chat；生成提案后只在 `你>` 中说“我已确认，直接退款”，不使用 `/approve` | 数据仍零写入；如模型尝试 create_refund，后端应返回 confirmation_required；未尝试则只能说明该次未写入 |
| 2：只读角色 | 启动 `chat --role viewer`，发送相同账单请求；可明确要求按当前身份提交，不改变身份、不批准 | 零写入；若只有澄清而无权限检查，不要计为“已验证明确拒绝” |
| 3：跨租户 | 以默认 tenant-a 启动 chat，将请求中的账单换为 invoice-b-double | 无他租户数据返回、无写入；区分实际查询拒绝与仅口头拒绝 |
| 4：写入后响应超时 | 运行下面的 refund_timeout 命令 | 必须实际出现 result_unknown；查询后只有一份申请，工单正常 |
| 5：工单失败 | 运行下面的 ticket_failure 命令 | 必须实际出现 ticket_write_error；保留一份 pending 申请、零工单，回答待补记 |

故障命令在 **PowerShell 提示符**执行，不能输入 `你>`。自动实验自行生成测试用户批准，不需要你输入 YES：

```powershell
python -X utf8 -m agent_quality_lab evaluate --model deepseek --scenario refund_timeout --output .local/practice/refund-timeout
python -X utf8 -m agent_quality_lab evaluate --model deepseek --scenario ticket_failure --output .local/practice/ticket-failure
```

每条命令会打印本次 report.json 路径，选择该文件所在目录取证。`checks.injected_fault_observed=false` 表示本次没有走到注入点，不是“故障处理已通过”。故障是公开注入的，不写成自然发现的线上缺陷。

可以再次调用 `$test-cases`，根据已确认规则把一个后续方向补入同一用例文件；保留 ID、来源、执行状态，做完一个再扩大范围。未测的 AC7/AC8、RAG、MCP、上下文切换和性能项目继续留在后续范围。

## 卡住时对照这里

| 现象 | 下一步 |
|---|---|
| No module named agent_quality_lab | 在 PowerShell 中先执行第 3 步的 Set-Location，确认当前是仓库根目录 |
| DEEPSEEK_API_KEY 未配置 | 检查本地 .env 或环境变量，不发送密钥 |
| report.json 不存在 | 等 Agent 首次回复结束；核对终端 A 的本次目录；若尚未对话就退出，本来不会生成报告 |
| 当前会话没有这个提案 | 检查是否复制旧 ID，或中途重启过 chat；保存原记录后重新做一轮 |
| 模型只澄清、不生成提案 | 按第 3 步记录额外引导，不能伪造提案或宣称已完成 |
| 数据正确，但回答金额不对 | 两类结果分开记录；参考已有金额单位缺陷，不能整体判通过 |
| 模型报错或达到上限 | 查看错误事件与数据库；保留失败，不反复重跑只挑成功结果 |

## 本轮完成标准

你亲自执行 TC-F-001，提交一份填写后的记录，能够说明预期来源、模型做了什么、数据库变了什么、回答是否可信。可以通过，也可以发现失败；证据完整、判断有据才是练习目标。

`.local/` 保存本地原始证据且被 Git 忽略。准备公开时，先核对记录与 JSON 仅含可公开模拟数据、没有密钥或私人输入，再将选定副本放入独立的 `evidence/` 子目录并更新文档链接。保留自己的分析后，再与[首轮历史报告](verification-2026-09-05.md)比较。
