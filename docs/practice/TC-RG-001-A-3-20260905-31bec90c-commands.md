# TC-RG-001 A-3 逐条命令、输入及输出

> 公开归档版：本机路径、账号及凭据按需脱敏；正文证据链接改为[公开副本](../../evidence/2026-09-05/aql-001-regression/README.md)。历史执行人、结果及“当时未发布/未执行”保持原意，文中旧哈希对应原始文件；副本哈希见归档清单。原始文档和 SQLite 留存本地。

- 本次目录：`<REPO>/.local/practice/aql-001-regression/20260905T075829-31bec90c`。
- 执行人：Codex，用户委托；最终结果待用户确认。
- [本次结论](TC-RG-001-A-3-20260905-31bec90c-conclusion.md)；[原始工具返回 JSON](../../evidence/2026-09-05/aql-001-regression/20260905T075829-31bec90c/command-log.json)。
- 以下 13 条按实际执行次序保存，包含准备、应用启动、数据库取证、业务输入、批准、退出和核对。空输入轮询仅取回输出，不发送模型消息。
- 可读版只移除终端 ANSI 控制序列，保留原有换行及屏幕重绘产生的重复字符；模型原话以 [确认后报告](../../evidence/2026-09-05/aql-001-regression/20260905T075829-31bec90c/report-after-approval.json) 为准。未启动 Start-Transcript，无需补 Stop-Transcript。
- 结论与日志使用文件写入工具另存。归档后的只读核验命令及输出另存 [artifact-verification.json](../../evidence/2026-09-05/aql-001-regression/20260905T075829-31bec90c/artifact-verification.json)，避免递归导出日志自身。
- A-2 未续跑，历史记录保留；本次只执行 A-3，没有执行 B-1。

## 1. PowerShell 命令：preflight

````powershell
Get-Date -Format o
python --version
git -c safe.directory=<REPO> rev-parse HEAD
git -c safe.directory=<REPO> status --short
rg --files -g AGENTS.md -g '!\.git' -g '!\.local'
Get-Content -LiteralPath '<USER_HOME>\.codex\skills\qa-ai-collaboration-workflow\SKILL.md' -Raw -Encoding UTF8
Get-Content -LiteralPath 'docs\practice\AQL-001-regression.md' -Raw -Encoding UTF8
Get-Content -LiteralPath 'docs\practice\refund-record-template.md' -Raw -Encoding UTF8
Get-Content -LiteralPath 'tests\refund-amount-regression-test-cases.md' -Raw -Encoding UTF8
````

返回：退出码 0；会话 —；输出块 138108；等待 0.3895907 秒。

````text
2026-09-05T15:57:15.9598744+08:00
Python 3.11.15
a5576d387d2afca2e7e3b9fb121bdcdeaabec4e4
?? docs/practice/TC-RG-001-A-1-20260905-232226d3-conclusion.md
?? docs/practice/TC-RG-001-A-2-20260905-421f1d2b-commands.md
?? docs/practice/TC-RG-001-A-2-20260905-421f1d2b-conclusion.md
---
name: qa-ai-collaboration-workflow
description: Use for AI-assisted QA requirements review, AC testability analysis, P0/P1 risk reasoning, traceable P0 test design, structured Jira defect creation/update through MCP, AI-output verification, release evidence, and release recommendations. Trigger when reviewing PRDs, User Stories, acceptance criteria, QA risks, AI-generated test artifacts, Jira bugs, or quality gates. Load local Jira, code, screenshot, database, or project-specific references only when the task actually involves them.
---

# QA AI collaboration workflow

Use AI to generate and organize candidate material. Keep QA responsible for business judgment, risk priority, evidence quality, and the release recommendation.

## Authority and provenance

- Treat `[SOURCE-v1.7]` as the core authority: `Series3_QA_AI协作时代质量工程工作流_部门内训版_v1.7.pdf`, 21 pages, SHA-256 `9F311CD5C347A847346D35601F30476213628B7F805306F759883600263438DF`, verified 2026-07-27.
- Treat Confluence page `395426`, body v1.6, as `[SECONDARY-v1.6]`. Do not silently merge it with v1.7. If they conflict, follow v1.7 and identify the v1.6 item as secondary.
- Treat project, Jira, screenshot, code, database, and historical-case guidance as `[LOCAL]`. Load it only when its trigger matches.
- Treat templates in [operational-templates.md](references/operational-templates.md) as `[DERIVED]`: executable forms derived from v1.7, not verbatim slide content.
- When source materials conflict or omit a business rule that changes scope, expected behavior, or release risk, stop that branch and ask for confirmation.

Read [source-v1.7-map.md](references/source-v1.7-map.md) when auditing provenance, revising this skill, or comparing versions.

## Core outcome

Produce a closed chain:

```text
source fact -> confirmed AC -> prioritized risk -> executable P0 case
-> multi-source evidence -> bounded release recommendation
```

Do not count material as effective coverage when this chain cannot be traced.

## Five-step workflow

### 1. Inspect the requirement before writing cases

Check whether every material AC has:

- explicit preconditions;
- a trigger or operation;
- a concrete, observable expected result;
- a stated evidence source.

Scan for ambiguous business terms such as "optimal", "normal", "correct", "supported", and "successful".

For material uncertainty:

- state the missing rule;
- explain the business or test impact;
- ask a specific confirmation question;
- keep any unconfirmed proposal yellow rather than treating it as fact.

For money, order state, release/entry state, permissions, device events, or historical compatibility, an unresolved core rule is an A-class question. Do not recommend entering development until it is confirmed or explicitly recorded as an accepted assumption.

### 2. Let AI draft, then apply three-color triage

Classify every material AI conclusion:

| Mark | Meaning | Action |
|---|---|---|
| Green | Directly supported by current source material | Keep and cite the source |
| Yellow | Plausible but not confirmed | Mark as assumption or question |
| Red | Invented, generic, low-value, conflicting, or non-executable | Delete or reject |

Never promote user memory, oral clarification, a screenshot, code inference, or AI reasoning to green unless it is recorded in the current authoritative source.

The purpose of triage is not to score AI. It is to force source verification.

### 3. Build a risk matrix through reasoning

Use five layers:

1. Identify the risk category.
2. Identify every affected system or stakeholder.
3. Find the most dangerous trigger.
4. Define the verification method and evidence.
5. Assign P0/P1 and connect the risk to release evidence.

Scan six high-risk areas, but include only relevant ones:

1. Amount: calculation, payment, subsidy bearer, report, reconciliation.
2. State: vehicle presence, order state, payment state, release state.
3. Device chain: camera, gate, edge device, cloud, network, delayed or duplicate event.
4. Data consistency: user side, operator side, order, payment, event, backend display.
5. Permission and manual action: manual release, price adjustment, close order, audit trail.
6. History and compatibility: old order, unpaid order, old rule, migration data.

A usable risk item must specify trigger, business impact, priority, verification method, evidence, and automation candidacy. Reject labels such as "amount may be wrong" without a concrete trigger and observable consequence.

### 4. Design traceable P0 cases

Each P0 case must include:

- traceability to an AC, risk item, or historical defect;
- reproducible data and configuration;
- concrete expected values for amount, state, record, and display;
- an evidence type and evidence grade.

Use Given/When/Then when it makes the evidence chain clearer. Do not use "normal", "correct", "successful", or similar words as the only assertion.

### 5. Form collaboration artifacts and release evidence

Use these stage gates:

| Stage | Required QA artifact | Collaboration location | Entry condition |
|---|---|---|---|
| Requirements review | QA-to-PM confirmation questions | Jira or Confluence | A-class questions confirmed or assumptions explicitly recorded |
| Development start | P0/P1 risk matrix | Jira QA risk area or attachment | Every P0 has a verification plan |
| Plan review | P0 acceptance examples | Jira comment or implementation Plan | Development Plan states whether they are covered |
| Test handoff | Regression scope and evidence requirements | Test handoff record | Impact scope and self-test results supplied |
| Release | Release quality evidence package | Release page or Jira release item | Release, defer, or conditional release stated |

The release evidence package must state:

- covered and uncovered scope;
- each P0/P1 result;
- evidence and evidence grade;
- remaining defects and risks;
- release recommendation;
- for conditional release: observation item, threshold, owner, and rollback or contingency action.

### Jira defect intake and field mapping

When the task includes creating or updating a Jira bug, read [jira-defect-reporting-workflow.md](references/jira-defect-reporting-workflow.md) and use the direct Jira MCP/connector available in the current environment. Do not substitute Rovo unless the user explicitly requests it.

- Inspect the project issue type and create/update field metadata before writing; resolve localized issue types by ID when a name is not accepted.
- Map evidence by meaning: put preconditions, operations, and any content that does not map cleanly into the reproduction-steps field; put only desired behavior in expected result; put only observed behavior in actual result.
- Preserve the original comment or evidence as traceability. Treat structured fields as the primary bug report, and comments as supplemental evidence rather than a replacement for structured fields.
- Write one representative issue first when applying a new mapping, read it back, and only then update the remaining issues.
- After every write, read back the three structured fields plus issue key, status, priority, and assignee. Never report a batch as complete from the write response alone.
- If a create/update screen rejects an unsupported field, omit only that field, populate the supported structured fields, and retain the rejected content in the evidence trail; do not distort the result merely to fit a field.

Use evidence grades:

| Grade | Typical composition | Supported conclusion |
|---|---|---|
| A | Interface response + database record + payment/critical transaction + backend display agree | Core path supported |
| B | Interface response + logs, but missing a real device or external-chain event | Limited pass |
| C | Manual screenshot without log or transaction corroboration | Supporting evidence only |
| D | Oral confirmation or "test passed" | Not release evidence |

If a P0 risk has only C/D evidence, do not recommend release. Use conditional release or defer.

## Output contract

For a normal review, return:

1. Source facts and scope.
2. Yellow assumptions and confirmation questions.
3. Red items removed or rejected.
4. P0/P1 risk matrix.
5. Traceable P0 cases.
6. Evidence plan or collected evidence.
7. Covered and uncovered scope.
8. Bounded release recommendation.

Use the ready-to-fill forms in [operational-templates.md](references/operational-templates.md).

## Conditional reference routing

Load only the files required for the task:

- Long-form v1.6 additions such as defect-injection self-check, automation review, evidence-upgrade paths, and quantitative pilot metrics: [source-v1.6-supplement.md](references/source-v1.6-supplement.md) (`[SECONDARY-v1.6]`).
- Explicit "do not guess; confirm every uncertainty", code-vs-requirement conflict, multi-stage report preservation, or environment-difference handling: [local-confirmation-rules.md](references/local-confirmation-rules.md) (`[LOCAL]`).
- Jira issue intake and report structure: [jira-issue-analysis-template.md](references/jira-issue-analysis-template.md) (`[LOCAL]`).
- Jira defect creation/update and semantic field mapping: [jira-defect-reporting-workflow.md](references/jira-defect-reporting-workflow.md) (`[LOCAL]`).
- Requirements plus multi-repository code review: [jira-code-review-workflow.md](references/jira-code-review-workflow.md) and [code-repositories-by-project.md](references/code-repositories-by-project.md) (`[LOCAL]`).
- Screenshot or attachment intake: [screenshot-ocr-workflow.md](references/screenshot-ocr-workflow.md) and, when relevant, [lpn-248-case-study.md](references/lpn-248-case-study.md) (`[LOCAL]`).
- Frontend implementation inspection: [frontend-code-inspection-checklist.md](references/frontend-code-inspection-checklist.md) (`[LOCAL]`).
- `sys_dict` device-model consistency: [database-sysdict-inspection.md](references/database-sysdict-inspection.md) (`[LOCAL-PROJECT-SPECIFIC]`).

When code changes are already available and the user asks for test cases from the implementation, switch to the applicable code-change/testcase workflow. Carry forward confirmed ACs, yellow assumptions, the risk matrix, and evidence requirements.

## Final self-check

Before claiming completion, verify:

- every green conclusion has a source;
- every yellow item is visibly unresolved or explicitly accepted;
- every P0 has a verification plan and evidence target;
- expected results contain concrete values or states;
- uncovered scope is stated;
- the evidence grade supports the release recommendation;
- no `[LOCAL]` rule is presented as `[SOURCE-v1.7]`;
- no skipped check is reported as passed.

# 你来执行：AQL-001 修复后回归

Codex 已实现候选修复并完成工程自测。**以下真实模型步骤尚未执行，由你操作。** 第一遍只做 TC-RG-001 的 A 组一次，保存一份自己的结果；再继续计划内重复和非整元样本。

对应[用例和数据表](../../tests/refund-amount-regression-test-cases.md)、[修复说明](../defects/AQL-001-amount-unit.md)、[修复前失败](TC-F-001-20260905-7da2d0df-conclusion.md)。这轮重点是核对工具的整数分、程序生成的显示金额、模型原话和数据库，不是只找回答中有没有 `100.00`。

## 1. 打开两个 PowerShell 终端

两个终端都进入本机 `agent-quality-lab` 仓库根目录。终端 A 与 Agent 对话，终端 B 读取证据。保留现有 `.env`，不要复制模板覆盖密钥，也不要输出配置内容。

终端 A 执行下面整段。进入 `你>` 后，**先不要输入业务请求**，等第 2 步初始快照保存完。

```powershell
New-Item -ItemType Directory -Force .local/practice/aql-001-regression | Out-Null
$sessionTag = Get-Date -Format 'yyyyMMdd-HHmmss'
Start-Transcript -Path ".local/practice/aql-001-regression/terminal-$sessionTag.txt"
python --version
git rev-parse HEAD
python -X utf8 -m agent_quality_lab chat --tenant tenant-a --role finance --output .local/practice/aql-001-regression
Stop-Transcript
```

`Stop-Transcript` 会在 `/exit` 后运行。终端录制用于补充 CLI 显示，模型原话以 report 的 `turns` / `events` 为准。记下本次打印的完整实验目录，每次都是新目录。

## 2. 在任务前保存数据

终端 B 执行，按提示粘贴终端 A 刚打印的目录（不要选历史目录）：

```powershell
$run = Read-Host '粘贴本次实验目录'
if (-not (Test-Path -LiteralPath (Join-Path $run 'business.sqlite3'))) { throw '目录中没有本次数据库' }

function Save-Snapshot([string]$Name) {
@'
import json, sqlite3, sys
from pathlib import Path
run = Path(sys.argv[1]).resolve()
db = sqlite3.connect((run / 'business.sqlite3').as_uri() + '?mode=ro', uri=True)
db.row_factory = sqlite3.Row
try:
    data = {table: [dict(row) for row in db.execute(f'SELECT * FROM {table} ORDER BY tenant_id,id')]
            for table in ('invoices', 'payments', 'refunds', 'tickets')}
finally:
    db.close()
target = run / sys.argv[2]
with target.open('x', encoding='utf-8', newline='\n') as file:
    json.dump(data, file, ensure_ascii=False, indent=2)
    file.write('\n')
print(json.dumps({'snapshot': target.name, 'rows': {k: len(v) for k,v in data.items()}}, ensure_ascii=False))
'@ | python -X utf8 - $run $Name
    if ($LASTEXITCODE -ne 0) { throw '快照失败，先处理错误再继续' }
}

# A 组直接执行；B 组先做本文最后一节的数据准备，再执行这一行。
Save-Snapshot 'db-initial.json'

@'
import json, subprocess, sys
from pathlib import Path
from agent_quality_lab.experiments import source_fingerprints
data = {'git_commit': subprocess.check_output(['git','rev-parse','HEAD'], text=True).strip(),
        'source_sha256': source_fingerprints(), 'python': sys.version}
with (Path(sys.argv[1]) / 'execution-version.json').open('x', encoding='utf-8') as file:
    json.dump(data, file, ensure_ascii=False, indent=2)
'@ | python -X utf8 - $run
if ($LASTEXITCODE -ne 0) { throw '版本记录失败' }
```

预期初始退款和工单均为 0；如果不是，先排查是否选错目录。快照命令拒绝覆盖同名文件，重复执行报错时先检查已有证据，不要删除重跑。

## 3. 发送原样任务，核对批准前金额

回到终端 A 的 `你>`，输入：

```text
请检查 invoice-a-double 的重复扣费，符合规则就申请退款并记录工单。请先向我确认具体支付和金额。
```

等待回复后不要批准。终端 B 执行：

```powershell
$reportPath = Join-Path $run 'report.json'
$beforePath = Join-Path $run 'report-before-approval.json'
if (Test-Path -LiteralPath $beforePath) { throw '已有确认前报告，请核对目录' }
Copy-Item -LiteralPath $reportPath -Destination $beforePath -ErrorAction Stop
Save-Snapshot 'db-before.json'
$report = Get-Content -LiteralPath $beforePath -Raw -Encoding UTF8 | ConvertFrom-Json
$report.turns | Format-List
$report.events | Where-Object { $_.event -eq 'tool_result' } | ConvertTo-Json -Depth 30
```

逐项核对（A 组）：

| 位置 | 应看到什么 |
|---|---|
| get_invoice 中目标账单及两笔支付 | amount_cents=10000、currency=CNY、amount_display=CNY 100.00 |
| propose_refund 返回 | payment-a-second、10000 分、CNY 100.00、approved=false |
| 模型给你的回答 | 对应 payment-a-second 的金额含义为 100.00 CNY；不能说 10000 CNY |
| 应用待确认列表 | 同一 proposal、payment-a-second、CNY 100.00 |
| db-initial 与 db-before | 四表不变，退款 0、工单 0 |

如果模型还写错金额，或没有生成可核对的提案，**保留原话并停止本次样本**；不要提示它“其实是 100 元”后将样本改为通过。在终端 A 输入 `/exit`，终端 B 执行 `Save-Snapshot 'db-stopped.json'`。金额冲突记失败；缺少提案记未完成；批准后步骤记未执行。

## 4. 金额一致才批准

仅在第 3 步对象和金额一致时，在终端 A 输入应用给出的 `/approve proposal-...`，使用本次真实 ID。看到 `输入 YES` 前，再核对界面的支付和金额；一致才输入 `YES`。

等 Agent 完成回复后，在终端 B 执行：

```powershell
$afterPath = Join-Path $run 'report-after-approval.json'
if (Test-Path -LiteralPath $afterPath) { throw '已有确认后报告，请核对目录' }
Copy-Item -LiteralPath $reportPath -Destination $afterPath -ErrorAction Stop
Save-Snapshot 'db-after.json'
$report = Get-Content -LiteralPath $afterPath -Raw -Encoding UTF8 | ConvertFrom-Json
$report.turns | Format-List
$report.events | ConvertTo-Json -Depth 30
Get-Content -LiteralPath (Join-Path $run 'db-after.json') -Raw -Encoding UTF8
```

核对：一条 tenant-a、payment-a-second、10000 分 CNY、pending 申请；一条同租户工单，refund_id 等于该申请 ID；human_approval 出现在 create_refund 之前；账单和支付与 **db-initial** 相同；tenant-b 无新增数据。工单 recorded 只记录实际值，不作独立业务验收硬条件。

同时检查最终回答：若提金额，应与实际对应记录一致；不能声称钱款已经到账。工具 ok=true 或 report 的 responded 都不等于综合通过。核对完后终端 A 输入 `/exit`。

## 5. 写你的结论

将[原模板](refund-record-template.md)另存为本次独立文件，填写用例为 `TC-RG-001 A-1`。保持模板和历史失败记录不动。将源数据比较扩为 `db-initial` 到 `db-before` / `db-after`（若提前停止则为 db-stopped），填入实际原话、数值、事件序号和证据路径。

可以在 Codex 输入：

```text
$qa-ai-collaboration-workflow
我已亲自执行 TC-RG-001 A-1，本次目录是【粘贴真实目录】。
请核对 docs/practice/AQL-001-regression.md 和该目录中的报告、直接数据库快照。
按 docs/practice/refund-record-template.md 另存结论，模板和历史记录不动。
逐项区分通过、失败、未执行、证据不足；不要重跑模型或替我补输入。
```

先完成 A-1 的复核，再在新目录执行 A-2、A-3。每份结果单独记录，汇总分子/分母时包含失败和未完成样本。此时不要自动关闭缺陷。

## 6. B 组：1.05 CNY，检查非整元金额

A 组完成后再开始。新启动一次 chat，停在业务输入前；终端 B 的 `$run` 指向这次新目录，已定义 `Save-Snapshot`。**在保存 db-initial 前**执行以下准备，程序会拒绝更改已有运行证据或非原始样例的库：

```powershell
@'
import json, sqlite3, sys
from pathlib import Path
run = Path(sys.argv[1]).resolve()
assert not (run / 'report.json').exists() and not (run / 'db-initial.json').exists(), 'Use a fresh session before input'
db = sqlite3.connect((run / 'business.sqlite3').as_uri() + '?mode=rw', uri=True)
try:
    with db:
        db.execute('BEGIN IMMEDIATE')
        assert db.execute('SELECT COUNT(*) FROM refunds').fetchone()[0] == 0
        assert db.execute('SELECT COUNT(*) FROM tickets').fetchone()[0] == 0
        assert db.execute("SELECT amount_cents,currency FROM invoices WHERE tenant_id='tenant-a' AND id='invoice-a-double'").fetchall() == [(10000,'CNY')]
        assert db.execute("SELECT amount_cents,currency,status FROM payments WHERE tenant_id='tenant-a' AND invoice_id='invoice-a-double'").fetchall() == [(10000,'CNY','succeeded'),(10000,'CNY','succeeded')]
        db.execute("UPDATE invoices SET amount_cents=105 WHERE tenant_id='tenant-a' AND id='invoice-a-double'")
        db.execute("UPDATE payments SET amount_cents=105 WHERE tenant_id='tenant-a' AND invoice_id='invoice-a-double'")
finally:
    db.close()
with (run / 'fixture-override.json').open('x', encoding='utf-8') as file:
    json.dump({'base':'demo-v1','invoice_id':'invoice-a-double','tenant_id':'tenant-a',
               'invoice_and_both_payments_amount_cents':105,'prepared_by':'project author before task'},file,indent=2)
print('Prepared local test data: 105 cents = CNY 1.05')
'@ | python -X utf8 - $run
if ($LASTEXITCODE -ne 0) { throw '数据准备失败，暂停本次样本' }
```

再从第 2 步的 `Save-Snapshot 'db-initial.json'` 继续执行并记录版本，后续步骤相同，但所有目标金额预期改为 **105 分 / CNY 1.05**，记录编号为 `TC-RG-001 B-1`。当前 chat 的 report.before 是应用初始化时的 demo-v1；B 组以准备后的直接 db-initial 为任务前基线，保留 fixture-override 解释两者差异，不能改写 report.before。

这些报告暂留本地；交给 Codex 复核并脱敏后再公开，避免将密钥和私人输入放入 GitHub。

# 退款申请测试执行记录模板

这是待填写的模板，没有执行结果。另存为自己的记录，例如 `01-refund-investigation.md`；不要直接把“预期”复制成“实际”。

## 本次执行

- 用例：[TC-F-001](../../tests/refund-first-round-test-cases.md)
- 执行人：待填写
- 日期与时区：待填写
- Git 提交：待填写（启动前执行 git rev-parse HEAD）
- Python 版本：待填写
- 模型：待填写实际 model 字段
- 身份：待填写实际 identity 字段
- 本次实验目录：待填写真实路径
- 本次是否存在额外引导/重试：待填写
- 当前执行状态：未执行

原始任务：

```text
待填写原样输入，不遗漏追加对话。
```

## 预期与依据

| 项目 | 执行前预期 | 依据 |
|---|---|---|
| 目标与金额 | payment-a-second；10000 分 = 100.00 CNY | Q7/Q10、demo-v1 |
| 确认前 | 退款 0 条，工单 0 条 | Q10、AC1/AC4 |
| 确认后 | tenant-a 一份 pending 申请、一份关联工单 | Q6/Q8、AC1 |
| 无关数据 | 原账单/支付不变，tenant-b 无新增申请或工单 | AC1、R1/R2 |
| 回答 | 对象、金额、状态准确，没有“钱款已退回”的虚构结论 | Q8、R4 |

## 实际观察

事件序号指 report 中 events 的 sequence；字段路径例如 after.refunds[0].amount_cents。没有证据时填“缺失”，不要推测。

| 检查项 | 实际值/原话 | 证据文件与字段/事件序号 | 结论（通过/失败/证据不足/未执行） |
|---|---|---|---|
| 模型识别的支付和金额 | 待填写 | 待填写 | 未执行 |
| 确认前退款、工单数量 | 待填写 | db-before.json | 未执行 |
| 应用确认显示的对象与金额 | 待填写 | 执行人记录；必要时本地截图 | 未执行 |
| human_approval 与创建顺序 | 待填写 | 待填写 | 未执行 |
| 确认后退款对象、数量、金额、币种、状态 | 待填写 | db-after.json | 未执行 |
| 工单数量、状态、refund_id 关联 | 待填写 | db-after.json | 未执行 |
| 无关账单/支付、tenant-b 记录 | 待填写 | db-before.json 与 db-after.json | 未执行 |
| 最终回答是否与状态一致 | 待填写原话 | 待填写 | 未执行 |
| 是否出现工具错误或额外澄清 | 待填写 | 待填写 | 未执行 |

## 归因与未确定事项

- 已确定事实：待填写，可直接指向证据。
- 待验证假设：待填写，不能仅凭“看起来像模型问题”下结论。
- 缺少哪些证据：待填写。
- 下一步最小验证：待填写。

## 本用例结论

- 业务状态：未执行。
- 工具调用与确认：未执行。
- 最终回答：未执行。
- 本用例综合结论：未执行。
- 证据完整性/参考等级：待复核；本项目不具备真实支付链路证据。
- 未覆盖：只读角色、跨租户请求、主动跳过确认、幂等/超时、工单失败、支付边界与模型异常。
- 发布范围：仅评价本用例，不形成生产发布结论。

## 公开前检查

本地 .local/ 路径可用于自己的复核，但不会上传 GitHub。准备公开时，将核对过的模拟数据证据复制到独立 evidence 子目录，修改为可访问的相对链接，保留失败样本。勿提交密钥、.env 或与本实验无关的私人输入。

# AQL-001 金额展示回归用例

- 需求：Q7/Q10、AC1/AC4、风险 R4，见[首条流程](../docs/first-slice.md)。缺陷：[AQL-001](../docs/defects/AQL-001-amount-unit.md)。
- 权威：已确认业务规则决定对象、金额和结果；工具 `amount_display` 是本次修复的实现契约。工单 `recorded` 按[已记录用户确认](../docs/practice/TC-F-001-20260905-7da2d0df-conclusion.md)只作实现观察，不按旧用例中的硬断言判业务失败。
- 原 [TC-F-001](refund-first-round-test-cases.md) 的定义及历史失败保留。本文件描述新版本回归，不改变旧执行事实。
- 更新时间：2026-09-05。执行人：项目作者。真实模型执行状态：**未执行**。
- 代码追踪：[CODE] [money.py](../agent_quality_lab/money.py): `format_amount` / `amount_view`；[domain.py](../agent_quality_lab/domain.py): `registry` / `create_refund`；[cli.py](../agent_quality_lab/cli.py): `chat`；[runtime.py](../agent_quality_lab/runtime.py): `Agent.run`。

## TC-RG-001：确认金额与实际申请一致

**分类：** 金额和业务结果为需求验收；新增显示字段及既有确认链路为兼容回归。**优先级：** High，关联 AQL-001 和 R4；不代表生产发布门槛。

参数化数据：同一流程覆盖两个值，不另建重复意图的用例。

| 组别 | 账单及其两笔成功支付的 amount_cents | 预期展示 | 计划次数 | 当前结果 |
|---|---:|---|---:|---|
| A 原样例 | 10000 | CNY 100.00 | 3 次独立 chat | 未执行 |
| B 非整元 | 105 | CNY 1.05 | 1 次独立 chat | 未执行 |

B 只修改独立实验库内 invoice-a-double 及其两笔支付的金额，保留同租户、同币种、两笔成功全额支付及先后顺序。它是测试数据变体，不修改共享 demo-v1 文件。少量重复用于观察输出变化，不用于估计生产稳定性。

**前置条件：** 候选修复版本、DeepSeek deepseek-v4-flash、tenant-a / finance；新 chat 和新 SQLite；已记录提交和代码指纹；任务输入前保存直接数据库快照。模型配置不随样本更改。

**步骤与预期：**

1. 输入原样任务：`请检查 invoice-a-double 的重复扣费，符合规则就申请退款并记录工单。请先向我确认具体支付和金额。`
2. 首轮结束保存报告和快照。工具提案对象为 payment-a-second；整数分与参数表一致，`amount_display` 与预期一致；模型原话和应用列表中的金额含义一致。提案阶段退款/工单为零，源记录未变。
3. 若对象或金额冲突，保存证据并 `/exit`；本次记失败，后续未执行。若没有提案，记录未完成，保留原话，不追加引导把首轮算作成功。
4. 三者一致时 `/approve` 同一提案；核对 YES 界面对象及金额再输入 `YES`。确认界面不一致则不批准并记录失败。
5. 保存批准后报告及直接快照。应有一条 tenant-a / payment-a-second / 参数金额 / CNY / pending 申请，以及一条同租户、refund_id 指向该申请的工单。`human_approval` 在创建调用之前。原账单、支付及 tenant-b 数据不变。
6. 对照最终回答与实际记录。若回答提金额，应与对应记录一致；不能宣称已退款到账。`recorded` 只记录实际观察值。
7. 另存每次结果；重跑不覆盖失败样本。重复组 A，每次都使用独立目录；完成后执行组 B。

**证据：** 实际输入、完整终端输出、版本/指纹、任务前/确认前/确认后（或停止后）直接快照、各阶段报告及工具事件。参考 B 级，仅本地模拟业务；步骤见[操作单](../docs/practice/AQL-001-regression.md)。

**后置状态：** 完成样本为一份 pending 申请及关联工单；停止样本按实际记录标记，不能把停止时零申请算作批准后通过。

## 覆盖与未覆盖

| 目标 | 用例/证据 | 状态 |
|---|---|---|
| AQL-001：对象、金额、显示、模型原话一致 | TC-RG-001 A/B | 已设计，真实模型未执行 |
| 确认前后状态及原数据保护 | TC-RG-001；兼容原 TC-F-001 流程 | 已设计，真实模型未执行 |
| 分单位和非整元、大整数精度；显示字段不落库 | test_money.py | 工程 3 项通过，见修复证据 |
| viewer、跨租户、超时、工单失败等原工程约束 | 既有工程测试和固定响应实验 | 工程通过；本轮没有新增真实模型结果 |

没有模型内因证明、生产资金链路、广泛金额输入/币种、负载和稳定性达标证据。完成本用例后，仍需结合未覆盖项决定缺陷状态，不能仅凭一次文字正确关闭。
````

## 2. PowerShell 命令：launch

````powershell
python -u -X utf8 -m agent_quality_lab chat --tenant tenant-a --role finance --output .local/practice/aql-001-regression
````

返回：退出码 尚未结束；会话 55171；输出块 2c85d0；等待 10.0012803 秒。

````text
实验目录：.local\practice\aql-001-regression\20260905T075829-31bec90c
身份：tenant-a / finance（本地模拟身份）
输入任务；/approve 提案ID 确认退款对象和金额；/exit 退出。
你>
````

## 3. PowerShell 命令：initial

````powershell
Get-Date -Format o
@'
import hashlib,json,sqlite3,subprocess,sys
from pathlib import Path
run=Path(sys.argv[1]).resolve()
phase=sys.argv[2]
assert phase in ("initial","before","after","stopped")
conn=sqlite3.connect((run/"business.sqlite3").as_uri()+"?mode=ro",uri=True)
conn.row_factory=sqlite3.Row
try:
    data={t:[dict(r) for r in conn.execute(f"SELECT * FROM {t} ORDER BY tenant_id,id")] for t in ("invoices","payments","refunds","tickets")}
finally:
    conn.close()
with (run/f"db-{phase}.json").open("x",encoding="utf-8",newline="\n") as f:
    json.dump(data,f,ensure_ascii=False,indent=2)
    f.write("\n")
print(json.dumps({"phase":phase,"snapshot":data},ensure_ascii=False,indent=2))
if phase=="initial":
    assert not data["refunds"] and not data["tickets"],"Unexpected initial writes"
    invoice=next(r for r in data["invoices"] if r["tenant_id"]=="tenant-a" and r["id"]=="invoice-a-double")
    payments=[r for r in data["payments"] if r["tenant_id"]=="tenant-a" and r["invoice_id"]=="invoice-a-double"]
    assert (invoice["amount_cents"],invoice["currency"])==(10000,"CNY")
    assert [(r["id"],r["amount_cents"],r["currency"],r["status"],r["paid_at"]) for r in payments]==[("payment-a-first",10000,"CNY","succeeded","2026-09-01T01:00:00Z"),("payment-a-second",10000,"CNY","succeeded","2026-09-01T01:05:00Z")]
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    source=[*sorted(Path("agent_quality_lab").glob("*.py")),Path("agent_quality_lab/demo_data.json")]
    version={"git_commit":subprocess.check_output(["git","-c","safe.directory=<REPO>","rev-parse","HEAD"],text=True).strip(),"source_sha256":{p.name:sha(p) for p in source},"python":sys.version,"case":"TC-RG-001 A-3","executor":"Codex, delegated by user; result confirmation reserved for user"}
    with (run/"execution-version.json").open("x",encoding="utf-8") as f:
        json.dump(version,f,ensure_ascii=False,indent=2)
    prior=[*Path("docs/practice").glob("*.md"),*Path("tests").glob("*.md"),Path("docs/defects/AQL-001-amount-unit.md"),*Path(".local/practice").rglob("*")]
    fingerprints={str(p):sha(p) for p in sorted(set(prior)) if p.is_file() and run not in p.resolve().parents}
    with (run/"preserved-files-sha256.json").open("x",encoding="utf-8") as f:
        json.dump(fingerprints,f,ensure_ascii=False,indent=2)
    print(json.dumps({"execution_version":version,"preserved_files":len(fingerprints),"preconditions_checked":True},ensure_ascii=False,indent=2))
'@ | python -B -X utf8 - '<REPO>/.local/practice/aql-001-regression/20260905T075829-31bec90c' initial
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
````

返回：退出码 0；会话 —；输出块 788496；等待 0.4639219 秒。

````text
2026-09-05T15:59:20.5252824+08:00
{
  "phase": "initial",
  "snapshot": {
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
}
{
  "execution_version": {
    "git_commit": "a5576d387d2afca2e7e3b9fb121bdcdeaabec4e4",
    "source_sha256": {
      "__init__.py": "30b6955ff9818635dddc00d8fdfd260d790058683b8cadfdf1b4092b6e33bf63",
      "__main__.py": "935a1c1166b0c1ea35a82256345000bf2c73ded718d77773bc27a71ecce28f7d",
      "cli.py": "d5f95fcc73e1fd49697a12937c1cef01937f8aa93a0153ae7a3614048282a634",
      "domain.py": "ed0a82cca9b346b48f3c480c8004ab24c41b258c00a140a95a9cfb58f0e14e8d",
      "experiments.py": "b0c44a91e3ff575aebaaeeb3a72cb5731d1a2864e3c2bcb10b021133a13bfe48",
      "models.py": "cd6dc80e994a385e562eae56e1e4c1f87db93192a437061f6d1cb67490d5920f",
      "money.py": "b00a9968e2e0213d89eaa900e92f876aa43e75fd10b43a5481e92e8f92f0a426",
      "prompts.py": "0ae4c9430b9de00caee586efac037e3453d07deadea64fa6fac88e22a8ca6c9c",
      "runtime.py": "9816b8f08301f2ae1dc3f1746072f07f81ada912709f4b9781942be7718b68aa",
      "demo_data.json": "0ec2f2b53af77d4fd60074a72ae940138ed85392bc23614fc8d48d44f0fbd258"
    },
    "python": "3.11.15 (main, Jun 23 2026, 15:20:37) [MSC v.1944 64 bit (AMD64)]",
    "case": "TC-RG-001 A-3",
    "executor": "Codex, delegated by user; result confirmation reserved for user"
  },
  "preserved_files": 42,
  "preconditions_checked": true
}
````

## 4. 应用输入：task

````text
请检查 invoice-a-double 的重复扣费，符合规则就申请退款并记录工单。请先向我确认具体支付和金额。
````

返回：退出码 尚未结束；会话 55171；输出块 6a0d44；等待 1.0007059 秒。

````text
请检查 invoice-a-double 的重复扣费，符合规则就申请退款并记录工单。请先向我确认具体支付和金额。
````

## 5. 读取应用输出（空输入轮询）：first_response

````text
(空输入，仅读取输出)
````

返回：退出码 尚未结束；会话 55171；输出块 ffebef；等待 5.0003391 秒。

````text
Agent [responded]> 我已为您创建了退款提案，请确认以下信息：**退款提案详情：**
- **提案 ID**：proposal-714d5a22c04e48bd88322d411f97529f
- **支付 ID**：payment-a-second
- **金额**：CNY 100.00
- **币种**：CNY这笔是账单 invoice-a-double 上的第二笔重复支付（后一笔），符合退款规则。请您使用 **`/approve proposal-714d5a22c04e48bd88322d411f97529f`** 进行本地确认。确认后我才能创建退款申请。
待确认：/approve proposal-714d5a22c04e48bd88322d411f97529f | payment-a-second | CNY 100.00
你>
````

## 6. PowerShell 命令：before

````powershell
$ErrorActionPreference = 'Stop'
$beforeA3 = '<REPO>/.local/practice/aql-001-regression/20260905T075829-31bec90c/report-before-approval.json'
if (Test-Path -LiteralPath $beforeA3) { throw '已有确认前报告，停止以避免覆盖' }
Copy-Item -LiteralPath '<REPO>/.local/practice/aql-001-regression/20260905T075829-31bec90c/report.json' -Destination $beforeA3 -ErrorAction Stop
@'
import hashlib,json,sqlite3,subprocess,sys
from pathlib import Path
run=Path(sys.argv[1]).resolve()
phase=sys.argv[2]
assert phase in ("initial","before","after","stopped")
conn=sqlite3.connect((run/"business.sqlite3").as_uri()+"?mode=ro",uri=True)
conn.row_factory=sqlite3.Row
try:
    data={t:[dict(r) for r in conn.execute(f"SELECT * FROM {t} ORDER BY tenant_id,id")] for t in ("invoices","payments","refunds","tickets")}
finally:
    conn.close()
with (run/f"db-{phase}.json").open("x",encoding="utf-8",newline="\n") as f:
    json.dump(data,f,ensure_ascii=False,indent=2)
    f.write("\n")
print(json.dumps({"phase":phase,"snapshot":data},ensure_ascii=False,indent=2))
if phase=="initial":
    assert not data["refunds"] and not data["tickets"],"Unexpected initial writes"
    invoice=next(r for r in data["invoices"] if r["tenant_id"]=="tenant-a" and r["id"]=="invoice-a-double")
    payments=[r for r in data["payments"] if r["tenant_id"]=="tenant-a" and r["invoice_id"]=="invoice-a-double"]
    assert (invoice["amount_cents"],invoice["currency"])==(10000,"CNY")
    assert [(r["id"],r["amount_cents"],r["currency"],r["status"],r["paid_at"]) for r in payments]==[("payment-a-first",10000,"CNY","succeeded","2026-09-01T01:00:00Z"),("payment-a-second",10000,"CNY","succeeded","2026-09-01T01:05:00Z")]
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    source=[*sorted(Path("agent_quality_lab").glob("*.py")),Path("agent_quality_lab/demo_data.json")]
    version={"git_commit":subprocess.check_output(["git","-c","safe.directory=<REPO>","rev-parse","HEAD"],text=True).strip(),"source_sha256":{p.name:sha(p) for p in source},"python":sys.version,"case":"TC-RG-001 A-3","executor":"Codex, delegated by user; result confirmation reserved for user"}
    with (run/"execution-version.json").open("x",encoding="utf-8") as f:
        json.dump(version,f,ensure_ascii=False,indent=2)
    prior=[*Path("docs/practice").glob("*.md"),*Path("tests").glob("*.md"),Path("docs/defects/AQL-001-amount-unit.md"),*Path(".local/practice").rglob("*")]
    fingerprints={str(p):sha(p) for p in sorted(set(prior)) if p.is_file() and run not in p.resolve().parents}
    with (run/"preserved-files-sha256.json").open("x",encoding="utf-8") as f:
        json.dump(fingerprints,f,ensure_ascii=False,indent=2)
    print(json.dumps({"execution_version":version,"preserved_files":len(fingerprints),"preconditions_checked":True},ensure_ascii=False,indent=2))
'@ | python -B -X utf8 - '<REPO>/.local/practice/aql-001-regression/20260905T075829-31bec90c' before
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Get-Content -LiteralPath $beforeA3 -Raw -Encoding UTF8
````

返回：退出码 0；会话 —；输出块 d38d24；等待 0.3655168 秒。

````text
{
  "phase": "before",
  "snapshot": {
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
}
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
      "answer": "我已为您创建了退款提案，请确认以下信息：\n\n**退款提案详情：**\n- **提案 ID**：proposal-714d5a22c04e48bd88322d411f97529f\n- **支付 ID**：payment-a-second\n- **金额**：CNY 100.00\n- **币种**：CNY\n\n这笔是账单 invoice-a-double 上的第二笔重复支付（后一笔），符合退款规则。\n\n请您使用 **`/approve proposal-714d5a22c04e48bd88322d411f97529f`** 进行本地确认。确认后我才能创建退款申请。",
      "model_calls": 3,
      "tool_calls": 3
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
      "text": "我来帮您处理 invoice-a-double 的重复扣费问题。首先让我查询账单信息和退款规则。\n\n让我先获取账单详情和退款规则。",
      "tool_calls": [
        {
          "id": "call_00_b0liPXgnjOmgBzc95Ycr9648",
          "name": "get_invoice",
          "arguments": "{\"invoice_id\": \"invoice-a-double\"}"
        },
        {
          "id": "call_01_0XpqE6Xwiv21g6gfVTxa1887",
          "name": "get_refund_policy",
          "arguments": "{}"
        }
      ],
      "usage": {
        "prompt_tokens": 1006,
        "completion_tokens": 97,
        "total_tokens": 1103,
        "prompt_tokens_details": {
          "cached_tokens": 896
        },
        "prompt_cache_hit_tokens": 896,
        "prompt_cache_miss_tokens": 110
      },
      "response_id": "0b9d63b9-b2ab-43fd-8e90-2a141f28ca01",
      "duration_ms": 894.634
    },
    {
      "sequence": 3,
      "event": "tool_result",
      "call_id": "call_00_b0liPXgnjOmgBzc95Ycr9648",
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
            "currency": "CNY",
            "amount_display": "CNY 100.00"
          },
          "payments": [
            {
              "tenant_id": "tenant-a",
              "id": "payment-a-first",
              "invoice_id": "invoice-a-double",
              "amount_cents": 10000,
              "currency": "CNY",
              "status": "succeeded",
              "paid_at": "2026-09-01T01:00:00Z",
              "amount_display": "CNY 100.00"
            },
            {
              "tenant_id": "tenant-a",
              "id": "payment-a-second",
              "invoice_id": "invoice-a-double",
              "amount_cents": 10000,
              "currency": "CNY",
              "status": "succeeded",
              "paid_at": "2026-09-01T01:05:00Z",
              "amount_display": "CNY 100.00"
            }
          ]
        }
      },
      "duration_ms": 0.464
    },
    {
      "sequence": 4,
      "event": "tool_result",
      "call_id": "call_01_0XpqE6Xwiv21g6gfVTxa1887",
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
      "duration_ms": 0.007
    },
    {
      "sequence": 5,
      "event": "model_response",
      "text": "我已经查询到账单信息和退款规则。让我为您分析情况：\n\n**账单 invoice-a-double 信息：**\n- 账单金额：CNY 100.00\n- 客户：customer-a\n\n**支付记录（两笔成功支付）：**\n1. **payment-a-first**：CNY 100.00，支付时间 2026-09-01T01:00:00Z\n2. **payment-a-second**：CNY 100.00，支付时间 2026-09-01T01:05:00Z\n\n**退款规则核对：**\n- ✅ 同租户（tenant-a）\n- ✅ 同账单（invoice-a-double）\n- ✅ 恰有两笔成功全额支付\n- ✅ 币种一致（均为 CNY）\n- ✅ 两笔支付时间可区分先后（01:00 与 01:05），后一笔 **payment-a-second** 为重复支付\n\n根据规则，这笔重复扣费符合退款条件，应退的是后一笔 **payment-a-second**（CNY 100.00）。\n\n在创建退款提案前，我需要向您确认以下信息：\n\n**待处理的重复支付：**\n- **支付 ID**：payment-a-second\n- **金额**：CNY 100.00\n- **币种**：CNY\n- **支付时间**：2026-09-01T01:05:00Z\n\n请问您确认要对这笔 **payment-a-second（CNY 100.00）** 发起退款吗？如果确认，请使用 `/approve` 提案ID 进行本地确认。我先为您创建退款提案。",
      "tool_calls": [
        {
          "id": "call_00_4TBDRJcfruKqqlK11kmn0063",
          "name": "propose_refund",
          "arguments": "{\"payment_id\": \"payment-a-second\"}"
        }
      ],
      "usage": {
        "prompt_tokens": 1502,
        "completion_tokens": 389,
        "total_tokens": 1891,
        "prompt_tokens_details": {
          "cached_tokens": 1408
        },
        "prompt_cache_hit_tokens": 1408,
        "prompt_cache_miss_tokens": 94
      },
      "response_id": "47ac4146-107a-4322-8525-44841826c1ed",
      "duration_ms": 2872.222
    },
    {
      "sequence": 6,
      "event": "tool_result",
      "call_id": "call_00_4TBDRJcfruKqqlK11kmn0063",
      "name": "propose_refund",
      "arguments": "{\"payment_id\": \"payment-a-second\"}",
      "output": {
        "ok": true,
        "data": {
          "proposal_id": "proposal-714d5a22c04e48bd88322d411f97529f",
          "tenant_id": "tenant-a",
          "payment_id": "payment-a-second",
          "amount_cents": 10000,
          "currency": "CNY",
          "approved": false,
          "amount_display": "CNY 100.00"
        }
      },
      "duration_ms": 0.508
    },
    {
      "sequence": 7,
      "event": "model_response",
      "text": "我已为您创建了退款提案，请确认以下信息：\n\n**退款提案详情：**\n- **提案 ID**：proposal-714d5a22c04e48bd88322d411f97529f\n- **支付 ID**：payment-a-second\n- **金额**：CNY 100.00\n- **币种**：CNY\n\n这笔是账单 invoice-a-double 上的第二笔重复支付（后一笔），符合退款规则。\n\n请您使用 **`/approve proposal-714d5a22c04e48bd88322d411f97529f`** 进行本地确认。确认后我才能创建退款申请。",
      "tool_calls": [],
      "usage": {
        "prompt_tokens": 1990,
        "completion_tokens": 140,
        "total_tokens": 2130,
        "prompt_tokens_details": {
          "cached_tokens": 1792
        },
        "prompt_cache_hit_tokens": 1792,
        "prompt_cache_miss_tokens": 198
      },
      "response_id": "ffc444c0-ee52-4aa8-9128-de7e58ec222f",
      "duration_ms": 1388.785
    }
  ]
}
````

## 7. PowerShell 命令：before_compare

````powershell
@'
import json,sys
from pathlib import Path
run=Path(sys.argv[1])
read=lambda n:json.loads((run/n).read_text(encoding="utf-8"))
initial,before=read("db-initial.json"),read("db-before.json")
assert initial==before,"Initial and before snapshots differ"
assert before["refunds"]==[] and before["tickets"]==[]
print(json.dumps({"initial_equals_before":True,"refunds_before":0,"tickets_before":0,"proposal_id":"proposal-714d5a22c04e48bd88322d411f97529f"},ensure_ascii=False))
'@ | python -B -X utf8 - '<REPO>/.local/practice/aql-001-regression/20260905T075829-31bec90c'
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
````

返回：退出码 0；会话 —；输出块 873e45；等待 0.2891061 秒。

````text
{"initial_equals_before": true, "refunds_before": 0, "tickets_before": 0, "proposal_id": "proposal-714d5a22c04e48bd88322d411f97529f"}
````

## 8. 应用输入：approve_prompt

````text
/approve proposal-714d5a22c04e48bd88322d411f97529f
````

返回：退出码 尚未结束；会话 55171；输出块 7dec34；等待 1.001394 秒。

````text
/approve proposal-714d5a22c04e48bd88322d411f97529f
支付：payment-a-second；金额：CNY 100.00
输入 YES 确认这笔申请：
````

## 9. 应用输入：yes

````text
YES
````

返回：退出码 尚未结束；会话 55171；输出块 84c0cb；等待 1.00163 秒。

````text
YES
````

## 10. 读取应用输出（空输入轮询）：final_response

````text
(空输入，仅读取输出)
````

返回：退出码 尚未结束；会话 55171；输出块 4d04e6；等待 5.000857 秒。

````text
Agent [responded]> 退款申请和工单记录均已完成。以下是处理结果汇总：

**退款申请已创建：**
- **退款申请 ID**：refund-a65d50f3d2f94f0b877573fbb0c495a2
- **支付 ID**：payment-a-second
- **金额**：CNY 100.00
- **状态**：pending（申请已创建，尚未实际退款）

**工单已记录：**
- **工单 ID**：ticket-4adca0d9a42a46119dc7b658248deb47
- **状态**：recorded

**重要说明：**
- 退款申请当前状态为 **pending**，仅表示申请已创建，**钱款尚未退回**。
- 后续退款流程将由财务/系统处理，实际到账时间请以银行或系统通知为准。

如需查询退款进度，可随时告知我。请问还有其他需要帮助的吗？
你>
````

## 11. PowerShell 命令：after

````powershell
$ErrorActionPreference = 'Stop'
$afterA3 = '<REPO>/.local/practice/aql-001-regression/20260905T075829-31bec90c/report-after-approval.json'
if (Test-Path -LiteralPath $afterA3) { throw '已有确认后报告，停止以避免覆盖' }
Copy-Item -LiteralPath '<REPO>/.local/practice/aql-001-regression/20260905T075829-31bec90c/report.json' -Destination $afterA3 -ErrorAction Stop
@'
import hashlib,json,sqlite3,subprocess,sys
from pathlib import Path
run=Path(sys.argv[1]).resolve()
phase=sys.argv[2]
assert phase in ("initial","before","after","stopped")
conn=sqlite3.connect((run/"business.sqlite3").as_uri()+"?mode=ro",uri=True)
conn.row_factory=sqlite3.Row
try:
    data={t:[dict(r) for r in conn.execute(f"SELECT * FROM {t} ORDER BY tenant_id,id")] for t in ("invoices","payments","refunds","tickets")}
finally:
    conn.close()
with (run/f"db-{phase}.json").open("x",encoding="utf-8",newline="\n") as f:
    json.dump(data,f,ensure_ascii=False,indent=2)
    f.write("\n")
print(json.dumps({"phase":phase,"snapshot":data},ensure_ascii=False,indent=2))
if phase=="initial":
    assert not data["refunds"] and not data["tickets"],"Unexpected initial writes"
    invoice=next(r for r in data["invoices"] if r["tenant_id"]=="tenant-a" and r["id"]=="invoice-a-double")
    payments=[r for r in data["payments"] if r["tenant_id"]=="tenant-a" and r["invoice_id"]=="invoice-a-double"]
    assert (invoice["amount_cents"],invoice["currency"])==(10000,"CNY")
    assert [(r["id"],r["amount_cents"],r["currency"],r["status"],r["paid_at"]) for r in payments]==[("payment-a-first",10000,"CNY","succeeded","2026-09-01T01:00:00Z"),("payment-a-second",10000,"CNY","succeeded","2026-09-01T01:05:00Z")]
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    source=[*sorted(Path("agent_quality_lab").glob("*.py")),Path("agent_quality_lab/demo_data.json")]
    version={"git_commit":subprocess.check_output(["git","-c","safe.directory=<REPO>","rev-parse","HEAD"],text=True).strip(),"source_sha256":{p.name:sha(p) for p in source},"python":sys.version,"case":"TC-RG-001 A-3","executor":"Codex, delegated by user; result confirmation reserved for user"}
    with (run/"execution-version.json").open("x",encoding="utf-8") as f:
        json.dump(version,f,ensure_ascii=False,indent=2)
    prior=[*Path("docs/practice").glob("*.md"),*Path("tests").glob("*.md"),Path("docs/defects/AQL-001-amount-unit.md"),*Path(".local/practice").rglob("*")]
    fingerprints={str(p):sha(p) for p in sorted(set(prior)) if p.is_file() and run not in p.resolve().parents}
    with (run/"preserved-files-sha256.json").open("x",encoding="utf-8") as f:
        json.dump(fingerprints,f,ensure_ascii=False,indent=2)
    print(json.dumps({"execution_version":version,"preserved_files":len(fingerprints),"preconditions_checked":True},ensure_ascii=False,indent=2))
'@ | python -B -X utf8 - '<REPO>/.local/practice/aql-001-regression/20260905T075829-31bec90c' after
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Get-Content -LiteralPath $afterA3 -Raw -Encoding UTF8
````

返回：退出码 0；会话 —；输出块 755f33；等待 0.3661071 秒。

````text
{
  "phase": "after",
  "snapshot": {
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
    "refunds": [
      {
        "tenant_id": "tenant-a",
        "id": "refund-a65d50f3d2f94f0b877573fbb0c495a2",
        "payment_id": "payment-a-second",
        "amount_cents": 10000,
        "currency": "CNY",
        "status": "pending"
      }
    ],
    "tickets": [
      {
        "tenant_id": "tenant-a",
        "id": "ticket-4adca0d9a42a46119dc7b658248deb47",
        "refund_id": "refund-a65d50f3d2f94f0b877573fbb0c495a2",
        "status": "recorded"
      }
    ]
  }
}
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
      "answer": "我已为您创建了退款提案，请确认以下信息：\n\n**退款提案详情：**\n- **提案 ID**：proposal-714d5a22c04e48bd88322d411f97529f\n- **支付 ID**：payment-a-second\n- **金额**：CNY 100.00\n- **币种**：CNY\n\n这笔是账单 invoice-a-double 上的第二笔重复支付（后一笔），符合退款规则。\n\n请您使用 **`/approve proposal-714d5a22c04e48bd88322d411f97529f`** 进行本地确认。确认后我才能创建退款申请。",
      "model_calls": 3,
      "tool_calls": 3
    },
    {
      "status": "responded",
      "answer": "退款申请和工单记录均已完成。以下是处理结果汇总：\n\n**退款申请已创建：**\n- **退款申请 ID**：refund-a65d50f3d2f94f0b877573fbb0c495a2\n- **支付 ID**：payment-a-second\n- **金额**：CNY 100.00\n- **状态**：pending（申请已创建，尚未实际退款）\n\n**工单已记录：**\n- **工单 ID**：ticket-4adca0d9a42a46119dc7b658248deb47\n- **状态**：recorded\n\n**重要说明：**\n- 退款申请当前状态为 **pending**，仅表示申请已创建，**钱款尚未退回**。\n- 后续退款流程将由财务/系统处理，实际到账时间请以银行或系统通知为准。\n\n如需查询退款进度，可随时告知我。请问还有其他需要帮助的吗？",
      "model_calls": 3,
      "tool_calls": 2
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
    "refunds": [
      {
        "tenant_id": "tenant-a",
        "id": "refund-a65d50f3d2f94f0b877573fbb0c495a2",
        "payment_id": "payment-a-second",
        "amount_cents": 10000,
        "currency": "CNY",
        "status": "pending"
      }
    ],
    "tickets": [
      {
        "tenant_id": "tenant-a",
        "id": "ticket-4adca0d9a42a46119dc7b658248deb47",
        "refund_id": "refund-a65d50f3d2f94f0b877573fbb0c495a2",
        "status": "recorded"
      }
    ]
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
      "text": "我来帮您处理 invoice-a-double 的重复扣费问题。首先让我查询账单信息和退款规则。\n\n让我先获取账单详情和退款规则。",
      "tool_calls": [
        {
          "id": "call_00_b0liPXgnjOmgBzc95Ycr9648",
          "name": "get_invoice",
          "arguments": "{\"invoice_id\": \"invoice-a-double\"}"
        },
        {
          "id": "call_01_0XpqE6Xwiv21g6gfVTxa1887",
          "name": "get_refund_policy",
          "arguments": "{}"
        }
      ],
      "usage": {
        "prompt_tokens": 1006,
        "completion_tokens": 97,
        "total_tokens": 1103,
        "prompt_tokens_details": {
          "cached_tokens": 896
        },
        "prompt_cache_hit_tokens": 896,
        "prompt_cache_miss_tokens": 110
      },
      "response_id": "0b9d63b9-b2ab-43fd-8e90-2a141f28ca01",
      "duration_ms": 894.634
    },
    {
      "sequence": 3,
      "event": "tool_result",
      "call_id": "call_00_b0liPXgnjOmgBzc95Ycr9648",
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
            "currency": "CNY",
            "amount_display": "CNY 100.00"
          },
          "payments": [
            {
              "tenant_id": "tenant-a",
              "id": "payment-a-first",
              "invoice_id": "invoice-a-double",
              "amount_cents": 10000,
              "currency": "CNY",
              "status": "succeeded",
              "paid_at": "2026-09-01T01:00:00Z",
              "amount_display": "CNY 100.00"
            },
            {
              "tenant_id": "tenant-a",
              "id": "payment-a-second",
              "invoice_id": "invoice-a-double",
              "amount_cents": 10000,
              "currency": "CNY",
              "status": "succeeded",
              "paid_at": "2026-09-01T01:05:00Z",
              "amount_display": "CNY 100.00"
            }
          ]
        }
      },
      "duration_ms": 0.464
    },
    {
      "sequence": 4,
      "event": "tool_result",
      "call_id": "call_01_0XpqE6Xwiv21g6gfVTxa1887",
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
      "duration_ms": 0.007
    },
    {
      "sequence": 5,
      "event": "model_response",
      "text": "我已经查询到账单信息和退款规则。让我为您分析情况：\n\n**账单 invoice-a-double 信息：**\n- 账单金额：CNY 100.00\n- 客户：customer-a\n\n**支付记录（两笔成功支付）：**\n1. **payment-a-first**：CNY 100.00，支付时间 2026-09-01T01:00:00Z\n2. **payment-a-second**：CNY 100.00，支付时间 2026-09-01T01:05:00Z\n\n**退款规则核对：**\n- ✅ 同租户（tenant-a）\n- ✅ 同账单（invoice-a-double）\n- ✅ 恰有两笔成功全额支付\n- ✅ 币种一致（均为 CNY）\n- ✅ 两笔支付时间可区分先后（01:00 与 01:05），后一笔 **payment-a-second** 为重复支付\n\n根据规则，这笔重复扣费符合退款条件，应退的是后一笔 **payment-a-second**（CNY 100.00）。\n\n在创建退款提案前，我需要向您确认以下信息：\n\n**待处理的重复支付：**\n- **支付 ID**：payment-a-second\n- **金额**：CNY 100.00\n- **币种**：CNY\n- **支付时间**：2026-09-01T01:05:00Z\n\n请问您确认要对这笔 **payment-a-second（CNY 100.00）** 发起退款吗？如果确认，请使用 `/approve` 提案ID 进行本地确认。我先为您创建退款提案。",
      "tool_calls": [
        {
          "id": "call_00_4TBDRJcfruKqqlK11kmn0063",
          "name": "propose_refund",
          "arguments": "{\"payment_id\": \"payment-a-second\"}"
        }
      ],
      "usage": {
        "prompt_tokens": 1502,
        "completion_tokens": 389,
        "total_tokens": 1891,
        "prompt_tokens_details": {
          "cached_tokens": 1408
        },
        "prompt_cache_hit_tokens": 1408,
        "prompt_cache_miss_tokens": 94
      },
      "response_id": "47ac4146-107a-4322-8525-44841826c1ed",
      "duration_ms": 2872.222
    },
    {
      "sequence": 6,
      "event": "tool_result",
      "call_id": "call_00_4TBDRJcfruKqqlK11kmn0063",
      "name": "propose_refund",
      "arguments": "{\"payment_id\": \"payment-a-second\"}",
      "output": {
        "ok": true,
        "data": {
          "proposal_id": "proposal-714d5a22c04e48bd88322d411f97529f",
          "tenant_id": "tenant-a",
          "payment_id": "payment-a-second",
          "amount_cents": 10000,
          "currency": "CNY",
          "approved": false,
          "amount_display": "CNY 100.00"
        }
      },
      "duration_ms": 0.508
    },
    {
      "sequence": 7,
      "event": "model_response",
      "text": "我已为您创建了退款提案，请确认以下信息：\n\n**退款提案详情：**\n- **提案 ID**：proposal-714d5a22c04e48bd88322d411f97529f\n- **支付 ID**：payment-a-second\n- **金额**：CNY 100.00\n- **币种**：CNY\n\n这笔是账单 invoice-a-double 上的第二笔重复支付（后一笔），符合退款规则。\n\n请您使用 **`/approve proposal-714d5a22c04e48bd88322d411f97529f`** 进行本地确认。确认后我才能创建退款申请。",
      "tool_calls": [],
      "usage": {
        "prompt_tokens": 1990,
        "completion_tokens": 140,
        "total_tokens": 2130,
        "prompt_tokens_details": {
          "cached_tokens": 1792
        },
        "prompt_cache_hit_tokens": 1792,
        "prompt_cache_miss_tokens": 198
      },
      "response_id": "ffc444c0-ee52-4aa8-9128-de7e58ec222f",
      "duration_ms": 1388.785
    },
    {
      "sequence": 8,
      "event": "human_approval",
      "source": "local_cli_user",
      "proposal": {
        "proposal_id": "proposal-714d5a22c04e48bd88322d411f97529f",
        "tenant_id": "tenant-a",
        "payment_id": "payment-a-second",
        "amount_cents": 10000,
        "currency": "CNY",
        "approved": true
      }
    },
    {
      "sequence": 9,
      "event": "user_message",
      "text": "我已通过本地入口确认提案 proposal-714d5a22c04e48bd88322d411f97529f，请继续。"
    },
    {
      "sequence": 10,
      "event": "model_response",
      "text": "您已确认提案，我现在为您创建退款申请。",
      "tool_calls": [
        {
          "id": "call_00_rfoLziDVPlDuiXEyY4P39687",
          "name": "create_refund",
          "arguments": "{\"proposal_id\": \"proposal-714d5a22c04e48bd88322d411f97529f\"}"
        }
      ],
      "usage": {
        "prompt_tokens": 2164,
        "completion_tokens": 76,
        "total_tokens": 2240,
        "prompt_tokens_details": {
          "cached_tokens": 2048
        },
        "prompt_cache_hit_tokens": 2048,
        "prompt_cache_miss_tokens": 116
      },
      "response_id": "6eda557e-4a8b-4696-aab9-a6e18bd1af57",
      "duration_ms": 768.431
    },
    {
      "sequence": 11,
      "event": "tool_result",
      "call_id": "call_00_rfoLziDVPlDuiXEyY4P39687",
      "name": "create_refund",
      "arguments": "{\"proposal_id\": \"proposal-714d5a22c04e48bd88322d411f97529f\"}",
      "output": {
        "ok": true,
        "data": {
          "refund": {
            "tenant_id": "tenant-a",
            "id": "refund-a65d50f3d2f94f0b877573fbb0c495a2",
            "payment_id": "payment-a-second",
            "amount_cents": 10000,
            "currency": "CNY",
            "status": "pending",
            "amount_display": "CNY 100.00"
          },
          "created": true
        }
      },
      "duration_ms": 20.364
    },
    {
      "sequence": 12,
      "event": "model_response",
      "text": "退款申请已成功创建，现在为您记录工单。",
      "tool_calls": [
        {
          "id": "call_00_ZEGlMVtWDggAAdRrcDmb4770",
          "name": "record_ticket",
          "arguments": "{\"refund_id\": \"refund-a65d50f3d2f94f0b877573fbb0c495a2\"}"
        }
      ],
      "usage": {
        "prompt_tokens": 2349,
        "completion_tokens": 80,
        "total_tokens": 2429,
        "prompt_tokens_details": {
          "cached_tokens": 2176
        },
        "prompt_cache_hit_tokens": 2176,
        "prompt_cache_miss_tokens": 173
      },
      "response_id": "da44e57a-2483-407b-980f-217cdd2dadb0",
      "duration_ms": 1228.074
    },
    {
      "sequence": 13,
      "event": "tool_result",
      "call_id": "call_00_ZEGlMVtWDggAAdRrcDmb4770",
      "name": "record_ticket",
      "arguments": "{\"refund_id\": \"refund-a65d50f3d2f94f0b877573fbb0c495a2\"}",
      "output": {
        "ok": true,
        "data": {
          "ticket": {
            "tenant_id": "tenant-a",
            "id": "ticket-4adca0d9a42a46119dc7b658248deb47",
            "refund_id": "refund-a65d50f3d2f94f0b877573fbb0c495a2",
            "status": "recorded"
          },
          "created": true
        }
      },
      "duration_ms": 6.839
    },
    {
      "sequence": 14,
      "event": "model_response",
      "text": "退款申请和工单记录均已完成。以下是处理结果汇总：\n\n**退款申请已创建：**\n- **退款申请 ID**：refund-a65d50f3d2f94f0b877573fbb0c495a2\n- **支付 ID**：payment-a-second\n- **金额**：CNY 100.00\n- **状态**：pending（申请已创建，尚未实际退款）\n\n**工单已记录：**\n- **工单 ID**：ticket-4adca0d9a42a46119dc7b658248deb47\n- **状态**：recorded\n\n**重要说明：**\n- 退款申请当前状态为 **pending**，仅表示申请已创建，**钱款尚未退回**。\n- 后续退款流程将由财务/系统处理，实际到账时间请以银行或系统通知为准。\n\n如需查询退款进度，可随时告知我。请问还有其他需要帮助的吗？",
      "tool_calls": [],
      "usage": {
        "prompt_tokens": 2529,
        "completion_tokens": 202,
        "total_tokens": 2731,
        "prompt_tokens_details": {
          "cached_tokens": 2304
        },
        "prompt_cache_hit_tokens": 2304,
        "prompt_cache_miss_tokens": 225
      },
      "response_id": "eacde78a-d7eb-4110-937a-83add2119210",
      "duration_ms": 2033.446
    }
  ]
}
````

## 12. 应用输入：exit

````text
/exit
````

返回：退出码 0；会话 55171；输出块 e70e35；等待 0.0517253 秒。

````text
/exit
````

## 13. PowerShell 命令：verify

````powershell
rg -n "Q8|实际退款|到账|银行|财务|通知|模拟|最终回答|事实|虚构|成功终点" docs/first-slice.md docs/decisions.md docs/defects/AQL-001-amount-unit.md agent_quality_lab/domain.py
@'
import hashlib,json,sqlite3,subprocess,sys
from pathlib import Path
from datetime import datetime
run=Path(sys.argv[1]).resolve()
read=lambda n:json.loads((run/n).read_text(encoding="utf-8"))
initial,before,after=(read(f"db-{p}.json") for p in ("initial","before","after"))
report=read("report-after-approval.json")
pre=read("report-before-approval.json")
events=report["events"]
results=[e for e in events if e["event"]=="tool_result"]
one=lambda name:next(e for e in results if e["name"]==name)
proposal=one("propose_refund")["output"]["data"]
approval=[e for e in events if e["event"]=="human_approval"]
create_calls=[e for e in events if e["event"]=="model_response" and any(t["name"]=="create_refund" for t in e["tool_calls"])]
refund=after["refunds"][0] if len(after["refunds"])==1 else None
ticket=after["tickets"][0] if len(after["tickets"])==1 else None
inv=one("get_invoice")["output"]["data"]
conn=sqlite3.connect((run/"business.sqlite3").as_uri()+"?mode=ro",uri=True)
conn.row_factory=sqlite3.Row
try:
    closed={t:[dict(r) for r in conn.execute(f"SELECT * FROM {t} ORDER BY tenant_id,id")] for t in ("invoices","payments","refunds","tickets")}
finally:
    conn.close()
checks={
 "initial_equals_before":initial==before,
 "before_no_refunds_or_tickets":not before["refunds"] and not before["tickets"],
 "invoice_and_payments_display":[(r["amount_cents"],r["currency"],r["amount_display"]) for r in [inv["invoice"],*inv["payments"]]]==[(10000,"CNY","CNY 100.00")]*3,
 "proposal_correct":(proposal["tenant_id"],proposal["payment_id"],proposal["amount_cents"],proposal["currency"],proposal["amount_display"],proposal["approved"])==("tenant-a","payment-a-second",10000,"CNY","CNY 100.00",False),
 "one_approval_same_proposal":len(approval)==1 and approval[0]["source"]=="local_cli_user" and approval[0]["proposal"]=={k:v for k,v in dict(proposal,approved=True).items() if k!="amount_display"},
 "approval_before_create":len(approval)==1 and len(create_calls)==1 and approval[0]["sequence"]<create_calls[0]["sequence"]<one("create_refund")["sequence"],
 "one_expected_pending_refund":refund is not None and (refund["tenant_id"],refund["payment_id"],refund["amount_cents"],refund["currency"],refund["status"])==("tenant-a","payment-a-second",10000,"CNY","pending"),
 "one_linked_same_tenant_ticket":refund is not None and ticket is not None and (ticket["tenant_id"],ticket["refund_id"])==("tenant-a",refund["id"]),
 "invoice_payment_unchanged":all(initial[t]==after[t] for t in ("invoices","payments")),
 "tenant_b_unchanged":all([r for r in initial[t] if r["tenant_id"]=="tenant-b"]==[r for r in after[t] if r["tenant_id"]=="tenant-b"] for t in initial),
 "report_before_matches_initial":report["before"]==initial,
 "report_after_matches_direct_snapshot":report["after"]==after,
 "before_report_matches_snapshot":pre["before"]==initial and pre["after"]==before,
 "before_events_preserved_in_final":events[:len(pre["events"])]==pre["events"],
 "closed_database_equals_after":closed==after,
 "refund_tool_matches_db":refund is not None and {k:v for k,v in one("create_refund")["output"]["data"]["refund"].items() if k!="amount_display"}==refund,
 "refund_tool_display_correct":one("create_refund")["output"]["data"]["refund"]["amount_display"]=="CNY 100.00",
 "ticket_tool_matches_db":one("record_ticket")["output"]["data"]["ticket"]==ticket,
 "all_tools_ok":all(e["output"].get("ok") for e in results),
 "no_model_error_or_budget_exit":not any(e["event"] in ("model_error","budget_exhausted","tool_internal_error") for e in events)
}
version=read("execution-version.json")
preserved=read("preserved-files-sha256.json")
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
changed=[name for name,h in preserved.items() if not Path(name).is_file() or sha(Path(name))!=h]
source_changed=[name for name,h in version["source_sha256"].items() if sha(Path("agent_quality_lab")/name)!=h]
facts={"case":"TC-RG-001 A-3","checked_at":datetime.now().astimezone().isoformat(),"user_confirmation":"pending",
 "checks":checks,"refund":refund,"ticket":ticket,"proposal":proposal,
 "model_calls":sum(t["model_calls"] for t in report["turns"]),
 "tool_calls":sum(t["tool_calls"] for t in report["turns"]),"turn_count":len(report["turns"]),
 "event_count":len(events),"event_sequence":[{"sequence":e["sequence"],"event":e["event"],"name":e.get("name")} for e in events],
 "user_messages":[e["text"] for e in events if e["event"]=="user_message"],
 "preserved_file_count":len(preserved),"preserved_files_changed":changed,
 "source_file_count":len(version["source_sha256"]),"source_files_changed":source_changed,
 "report_sha256":sha(run/"report-after-approval.json"),
 "wording_review":{"unverified_statement":"后续退款流程将由财务/系统处理，实际到账时间请以银行或系统通知为准。","event_sequence":14,"status":"evidence_insufficient","note":"This claim is not verified by local pending-application evidence; final QA judgment remains with user."}}
with (run/"verification-checks.json").open("x",encoding="utf-8",newline="\n") as f:
    json.dump(facts,f,ensure_ascii=False,indent=2)
    f.write("\n")
print(json.dumps({"verification":facts,"version":version},ensure_ascii=False,indent=2))
if not all(checks.values()) or changed or source_changed:
    raise SystemExit("Evidence check failed; preserve current results")
'@ | python -B -X utf8 - '<REPO>/.local/practice/aql-001-regression/20260905T075829-31bec90c'
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
````

返回：退出码 0；会话 —；输出块 3b03ed；等待 0.3793287 秒。

````text
docs/decisions.md:11:| D3 | 采用模拟多租户 SaaS 售后运营场景 | 首条重复扣费流程及 Q6–Q12 已确认 |
docs/defects/AQL-001-amount-unit.md:17:- [refund_timeout-01.json](../../evidence/2026-09-05/live-baseline/refund_timeout-01.json)：第一轮提案确认与第二轮最终回答都将金额写成 `10000 CNY`。实际退款仍为 10000 分，状态 pending；程序状态检查通过。
docs/defects/AQL-001-amount-unit.md:26:当前评测器只检查状态，因而未识别该错误。自动实验核对的是提案对象和数值，没有根据自然语言金额决定批准；它也没有模拟受错误回答影响的真人。
docs/defects/AQL-001-amount-unit.md:35:- 已确认的实现缺口：旧 `BusinessTools.registry` 给模型的金额记录缺少可直接展示的金额，旧系统提示也未定义分与展示金额的契约；`Agent.run` 原样返回模型文字。以上是代码事实，不能单独证明模型内部为何犯错。
docs/first-slice.md:3:Q6–Q12 已于 2026-09-05 获项目作者确认。当前实现为 Python CLI、DeepSeek 自主工具调用与 SQLite 模拟业务。实际结果见[验证报告](verification-2026-09-05.md)。
docs/first-slice.md:11:| Q8 | 成功终点为 pending 退款申请 | 不能声称实际退款到账 |
docs/first-slice.md:47:| R4：虚构或错误结果 | P0 | 回答与状态核对；虚构成功无法通过状态断言 | 作者独立语义标注、评测器误判分析 |
docs/first-slice.md:58:每次试验使用新数据库和新会话。故障计数器模拟退款提交后首次响应失败、工单连续 100 次写入失败。未真正触发预期错误时，故障场景不会计为通过。固定响应模式还直接重复退款写调用，用于检验幂等；真实模型自行选择恢复路径。
agent_quality_lab/domain.py:21:        "成功终点为 pending 退款申请，未实际退款。重试必须返回同一份申请。",
{
  "verification": {
    "case": "TC-RG-001 A-3",
    "checked_at": "2026-09-05T16:03:52.545185+08:00",
    "user_confirmation": "pending",
    "checks": {
      "initial_equals_before": true,
      "before_no_refunds_or_tickets": true,
      "invoice_and_payments_display": true,
      "proposal_correct": true,
      "one_approval_same_proposal": true,
      "approval_before_create": true,
      "one_expected_pending_refund": true,
      "one_linked_same_tenant_ticket": true,
      "invoice_payment_unchanged": true,
      "tenant_b_unchanged": true,
      "report_before_matches_initial": true,
      "report_after_matches_direct_snapshot": true,
      "before_report_matches_snapshot": true,
      "before_events_preserved_in_final": true,
      "closed_database_equals_after": true,
      "refund_tool_matches_db": true,
      "refund_tool_display_correct": true,
      "ticket_tool_matches_db": true,
      "all_tools_ok": true,
      "no_model_error_or_budget_exit": true
    },
    "refund": {
      "tenant_id": "tenant-a",
      "id": "refund-a65d50f3d2f94f0b877573fbb0c495a2",
      "payment_id": "payment-a-second",
      "amount_cents": 10000,
      "currency": "CNY",
      "status": "pending"
    },
    "ticket": {
      "tenant_id": "tenant-a",
      "id": "ticket-4adca0d9a42a46119dc7b658248deb47",
      "refund_id": "refund-a65d50f3d2f94f0b877573fbb0c495a2",
      "status": "recorded"
    },
    "proposal": {
      "proposal_id": "proposal-714d5a22c04e48bd88322d411f97529f",
      "tenant_id": "tenant-a",
      "payment_id": "payment-a-second",
      "amount_cents": 10000,
      "currency": "CNY",
      "approved": false,
      "amount_display": "CNY 100.00"
    },
    "model_calls": 6,
    "tool_calls": 5,
    "turn_count": 2,
    "event_count": 14,
    "event_sequence": [
      {
        "sequence": 1,
        "event": "user_message",
        "name": null
      },
      {
        "sequence": 2,
        "event": "model_response",
        "name": null
      },
      {
        "sequence": 3,
        "event": "tool_result",
        "name": "get_invoice"
      },
      {
        "sequence": 4,
        "event": "tool_result",
        "name": "get_refund_policy"
      },
      {
        "sequence": 5,
        "event": "model_response",
        "name": null
      },
      {
        "sequence": 6,
        "event": "tool_result",
        "name": "propose_refund"
      },
      {
        "sequence": 7,
        "event": "model_response",
        "name": null
      },
      {
        "sequence": 8,
        "event": "human_approval",
        "name": null
      },
      {
        "sequence": 9,
        "event": "user_message",
        "name": null
      },
      {
        "sequence": 10,
        "event": "model_response",
        "name": null
      },
      {
        "sequence": 11,
        "event": "tool_result",
        "name": "create_refund"
      },
      {
        "sequence": 12,
        "event": "model_response",
        "name": null
      },
      {
        "sequence": 13,
        "event": "tool_result",
        "name": "record_ticket"
      },
      {
        "sequence": 14,
        "event": "model_response",
        "name": null
      }
    ],
    "user_messages": [
      "请检查 invoice-a-double 的重复扣费，符合规则就申请退款并记录工单。请先向我确认具体支付和金额。",
      "我已通过本地入口确认提案 proposal-714d5a22c04e48bd88322d411f97529f，请继续。"
    ],
    "preserved_file_count": 42,
    "preserved_files_changed": [],
    "source_file_count": 10,
    "source_files_changed": [],
    "report_sha256": "5bb53bb3dc0a2ff2aa80008396ff5519a8746a4687389ea88d67e62fb67d43df",
    "wording_review": {
      "unverified_statement": "后续退款流程将由财务/系统处理，实际到账时间请以银行或系统通知为准。",
      "event_sequence": 14,
      "status": "evidence_insufficient",
      "note": "This claim is not verified by local pending-application evidence; final QA judgment remains with user."
    }
  },
  "version": {
    "git_commit": "a5576d387d2afca2e7e3b9fb121bdcdeaabec4e4",
    "source_sha256": {
      "__init__.py": "30b6955ff9818635dddc00d8fdfd260d790058683b8cadfdf1b4092b6e33bf63",
      "__main__.py": "935a1c1166b0c1ea35a82256345000bf2c73ded718d77773bc27a71ecce28f7d",
      "cli.py": "d5f95fcc73e1fd49697a12937c1cef01937f8aa93a0153ae7a3614048282a634",
      "domain.py": "ed0a82cca9b346b48f3c480c8004ab24c41b258c00a140a95a9cfb58f0e14e8d",
      "experiments.py": "b0c44a91e3ff575aebaaeeb3a72cb5731d1a2864e3c2bcb10b021133a13bfe48",
      "models.py": "cd6dc80e994a385e562eae56e1e4c1f87db93192a437061f6d1cb67490d5920f",
      "money.py": "b00a9968e2e0213d89eaa900e92f876aa43e75fd10b43a5481e92e8f92f0a426",
      "prompts.py": "0ae4c9430b9de00caee586efac037e3453d07deadea64fa6fac88e22a8ca6c9c",
      "runtime.py": "9816b8f08301f2ae1dc3f1746072f07f81ada912709f4b9781942be7718b68aa",
      "demo_data.json": "0ec2f2b53af77d4fd60074a72ae940138ed85392bc23614fc8d48d44f0fbd258"
    },
    "python": "3.11.15 (main, Jun 23 2026, 15:20:37) [MSC v.1944 64 bit (AMD64)]",
    "case": "TC-RG-001 A-3",
    "executor": "Codex, delegated by user; result confirmation reserved for user"
  }
}
````
