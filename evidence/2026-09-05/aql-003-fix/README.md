# AQL-003 修复后真实 CLI 回归证据

Codex 受委托执行 5 个真实 DeepSeek CLI 会话、13 轮；前四个会话与旧调查作同输入对照，P-1 单独验证真实本地批准后的正常流程。[冻结计划](../../../tests/role-guidance-regression-test-cases.md)与[回归报告](../../../docs/practice/AQL-003-regression-20260905.md)定义范围。**Codex 初核原始权限重试引导未复现，所列业务检查通过；待项目作者确认。** 个别措辞、语言观察及未触发分支见报告。

被测版本为基点 `6434f37ad975c699e7c5f58a949b7ce72798d518` 加 prompts.py 修改。基点提交本身不含修复，实际版本由 [manifest.json](manifest.json) 与各 execution-version.json 的 source_sha256 识别；新提示 SHA256 为 `217c5ac05458082c1fe62c7e0d52a243186f5357de3315456ad295a480b1d875`。

| 样本 | 角色 / 业务轮数 | 完整报告 | 原始 CLI 输入输出 | 直接最终快照 | 独立核对 |
|---|---|---|---|---|---|
| V-1 | viewer / 3 | [report](V-1/report.json) | [command-log](V-1/command-log.json) | [db](V-1/db-stopped.json) | [checks](V-1/verification-checks.json) |
| V-2 | viewer / 3 | [report](V-2/report.json) | [command-log](V-2/command-log.json) | [db](V-2/db-stopped.json) | [checks](V-2/verification-checks.json) |
| V-3 | viewer / 3 | [report](V-3/report.json) | [command-log](V-3/command-log.json) | [db](V-3/db-stopped.json) | [checks](V-3/verification-checks.json) |
| F-1 | finance / 2，聊天确认 | [report](F-1/report.json) | [command-log](F-1/command-log.json) | [db](F-1/db-stopped.json) | [checks](F-1/verification-checks.json) |
| P-1 | finance / 2，真实本地批准 | [report](P-1/report.json) | [command-log](P-1/command-log.json) | [db](P-1/db-stopped.json) | [checks](P-1/verification-checks.json) |

各目录另有 db-initial、execution-version、report-N / db-N / checks-N，以及停止时副本。直接快照来自只读 SQLite 查询，不是复制 report.after。原始数据库仅本地留存。四个拒绝样本无批准及业务写入；P-1 只有一次正确批准、一份 pending 申请和同租户关联工单，其他数据不变。

report.turns 保存逐轮原话，events 保存真实工具参数、结果、批准顺序及 API usage。[command-log](P-1/command-log.json)保留启动、输入、等待、取证、退出及退出码；ANSI 屏幕重绘字符保留，阅读模型原话优先看 report，不能将终端重绘重复字符误判为模型输出错误。P-1 的 /approve 与 YES 是 Codex 按授权核对屏幕后执行；不是作者本人操作。

[batch-verification.json](batch-verification.json)与[case-index.json](case-index.json)提供汇总及原始会话映射。真模型总计 30 次调用、23 次工具调用、API 报告 69914 Token，无费用账单；固定响应实验另列。没有补跑或替换样本，原有 234 个本地证据文件未改动。旧批次及其作者确认见[历史证据](../aql-003-investigation/README.md)，不改写旧结果。

## 固定响应检查

[工程输出](engineering-tests.txt)：本次新提示上的 unittest 38 项通过，0 跳过。以下 5 个 evaluate 场景使用预先写好的模型响应，不调用真实 API，也不证明提示语义改善；各报告 state_checks_passed 为 true：

| 场景 | 报告 |
|---|---|
| normal | [report](scripted/20260905T122456-05875f14.json) |
| denied | [report](scripted/20260905T122457-bef19d3d.json) |
| cross_tenant | [report](scripted/20260905T122457-7f5cc2ac.json) |
| refund_timeout | [report](scripted/20260905T122457-bf3c4f84.json) |
| ticket_failure | [report](scripted/20260905T122457-55073d0a.json) |

## 公开转换与工具存档

[manifest.json](manifest.json)列出 89 份证据的源文件 SHA256 与公开副本 SHA256，manifest 自身和本 README 不计入这个数。公开转换仅为凭据按需脱敏、本机路径/账号占位、UTF-8/LF 与物理行尾空格规范化、文件末尾保留单个换行；本批次扫描没有检出凭据。业务字段及模型原话保持原意，嵌入的原始哈希不改写。`<REPO>` 等为本机路径占位，不能直接作为命令路径。

[collect.py](tooling/collect.py)和[verify.py](tooling/verify.py)是当次取证脚本存档，原位置为 `<REPO>/.local/aql-003-fix-work/`，依赖原始运行目录、冻结计划、case-index 及历史哈希文件。不能在公开目录直接执行。它们不调用模型、不批准、不写业务表；证据文件以拒绝覆盖方式创建。独立核对先检查全部样本，再保存结果。脚本里的 answer_review 为 Codex 阅读后记录的语义评审，不是自动语义测试；作者确认仍待完成。
