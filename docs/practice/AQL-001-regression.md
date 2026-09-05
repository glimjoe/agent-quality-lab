# 你来执行：AQL-001 修复后回归

这是一份可复用的手动操作单。原计划的 A1 已由作者执行，A2/A3/B1 后由 Codex 受委托执行，见[历史记录](../../evidence/2026-09-05/aql-001-regression/README.md)；提案提示修复后的新批次见[最新报告](AQL-002-regression-20260905.md)。重新练习时始终创建新目录，第一遍只做 TC-RG-001 的 A 组一次，再继续计划内重复和非整元样本。

对应[用例和数据表](../../tests/refund-amount-regression-test-cases.md)、[修复说明](../defects/AQL-001-amount-unit.md)、[修复前失败](TC-F-001-20260905-7da2d0df-conclusion.md)。这轮重点是核对工具的整数分、程序生成的显示金额、模型原话和数据库，不是只找回答中有没有 `100.00`。

## 1. 打开两个 PowerShell 终端

两个终端都进入本机 `agent-quality-lab` 仓库根目录。终端 A 与 Agent 对话，终端 B 读取证据。保留现有 `.env`，不要复制模板覆盖密钥，也不要输出配置内容。

终端 A 执行下面整段。进入 `你>` 后，**先不要输入业务请求**，等第 2 步初始快照保存完。

```powershell
New-Item -ItemType Directory -Force .local/practice/aql-001-regression | Out-Null
$sessionTag = Get-Date -Format 'yyyyMMdd-HHmmss'
Start-Transcript -Path ".local/practice/aql-001-regression/terminal-$sessionTag.txt"
python --version
$repoPath = (Get-Location).Path -replace '\\', '/'
git -c "safe.directory=$repoPath" rev-parse HEAD
if ($LASTEXITCODE -ne 0) { throw '版本读取失败，请先排查' }
python -X utf8 -m agent_quality_lab chat --tenant tenant-a --role finance --output .local/practice/aql-001-regression
Stop-Transcript
```

`Stop-Transcript` 会在 `/exit` 后运行。终端录制用于补充 CLI 显示，模型原话以 report 的 `turns` / `events` 为准。记下本次打印的完整实验目录，每次都是新目录。

这里的 Git 参数只信任本次命令正在使用的仓库目录，用于处理本人仓库由不同本地/沙箱账号拥有的情况；不设置全局通配信任。Git 报错虽不改变退款逻辑，但版本证据会缺失，应处理后再执行实验。

## 2. 在任务前保存数据

终端 B **先单独执行下面一行**，回车后粘贴终端 A 刚打印的本次目录，再回车完成输入。不要把后续脚本一起粘到 Read-Host 的输入提示里；两个终端的变量互不共享。

```powershell
$run = Read-Host '粘贴本次实验目录'
```

确认上面的输入已完成，再在终端 B 执行下面整段。A 组指 100.00 CNY 的数据组，B 组指 1.05 CNY 的数据组，**与终端 A/B 无关**。本节所有 PowerShell 命令都在终端 B 运行，终端 A 保持 `你>` 等待，无需中断。

```powershell
if ([string]::IsNullOrWhiteSpace($run)) { throw '本次目录为空；请先单独执行 Read-Host 并输入目录' }
$run = $run.Trim().Trim('"')
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

# 100.00 CNY 数据组直接执行；1.05 CNY 数据组先做本文最后一节的数据准备。
# 这条命令仍在终端 B 执行，终端 A 的 Agent 保持等待。
Save-Snapshot 'db-initial.json'

@'
import json, subprocess, sys
from pathlib import Path
from agent_quality_lab.experiments import source_fingerprints
data = {'git_commit': subprocess.check_output(['git','-c','safe.directory='+Path.cwd().as_posix(),'rev-parse','HEAD'], text=True).strip(),
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
