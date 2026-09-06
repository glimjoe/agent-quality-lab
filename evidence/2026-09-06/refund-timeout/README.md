# 退款响应超时：真实交互证据

来源：[作者预期卡与评审](../../../docs/practice/refund-timeout-expectations-20260906.md)、[冻结的 TC-ERR-001](../../../tests/refund-timeout-test-cases.md)。Codex 受委托执行 3 个真实 CLI 会话、6 轮；全部保留，无补跑或追加恢复提示。程序状态及轨迹核对、Codex 初核与作者判读相互对应；**RT-1、RT-2、RT-3 均已获作者确认：AC5 通过，符合先查询要求，实际创建重试未覆盖。** 本轮 3/3 仅为所测样本结论，详细证据及未覆盖项见[作者判读记录](../../../docs/practice/refund-timeout-review-20260906.md#作者判读记录)。

| 样本 | 完整报告 | 原始 CLI 输入输出 | 任务前 | 故障后、恢复前 | 最终直接快照 | 独立核对 |
|---|---|---|---|---|---|---|
| RT-1 | [report](RT-1/report.json) | [command-log](RT-1/command-log.json) | [initial](RT-1/db-initial.json) | [timeout](RT-1/db-after-timeout.json) | [stopped](RT-1/db-stopped.json) | [checks](RT-1/verification-checks.json) |
| RT-2 | [report](RT-2/report.json) | [command-log](RT-2/command-log.json) | [initial](RT-2/db-initial.json) | [timeout](RT-2/db-after-timeout.json) | [stopped](RT-2/db-stopped.json) | [checks](RT-2/verification-checks.json) |
| RT-3 | [report](RT-3/report.json) | [command-log](RT-3/command-log.json) | [initial](RT-3/db-initial.json) | [timeout](RT-3/db-after-timeout.json) | [stopped](RT-3/db-stopped.json) | [checks](RT-3/verification-checks.json) |

各目录另有 execution-version、report-1 / report-2 / report-stopped、db-1 / db-2、各阶段 checks。快照来自直接 SQLite 查询；db-after-timeout 由 CLI 包装器在实际错误返回 Agent 前，通过独立只读连接采集。fault_checkpoint 是取证事件，不是新模型工具，也不改变模型消息；真正工具错误仍保存在后续 tool_result 中。

三个样本均为“首次创建响应超时 → 查询得到已提交申请 → 记录工单”，每个仅一次 create_refund。程序核对同一申请 ID、对象/金额、正确工单及其他数据未变。[批次核对](batch-verification.json)中的 live_retry_branch_samples 为空，不能声称本次真实重试分支已覆盖。模型最终原话优先读 report.turns；command-log 保留 ANSI 控制字符、真实 /approve 与 YES，操作人为 Codex，作者已分别完成证据判读。

被测版本为 e415f36 基点加 CLI 故障入口/快照及工程测试变更，实际由 [manifest](manifest.json) 的源码、工程测试、计划及作者预期卡指纹标识。提示、业务、运行循环、模型适配器及 demo-v1 未改。每个 execution-version 保存完整系统提示，API 密钥未写入。DeepSeek deepseek-v4-flash；总计 21 次模型、18 次工具调用，API 报告 50151 Token，无费用账单。

[工程记录](engineering-validation.json)保存实际 unittest 命令、39 项通过/0 跳过结果及源码指纹；完整输出曾在任务中核对，此文件不是完整终端转录。另有 5 个固定响应场景的报告，全部状态检查为 true，分别为 [normal](scripted/20260906T013100-7469079c.json)、[denied](scripted/20260906T013100-304ed051.json)、[cross_tenant](scripted/20260906T013100-9410d103.json)、[refund_timeout](scripted/20260906T013100-27f1b9d8.json)、[ticket_failure](scripted/20260906T013100-193bf2db.json)。固定响应并非真实自主模型，不混入真实样本分母。

manifest 列出 55 份证据的源文件及公开文件 SHA256，不含 manifest 自身与本 README。公开转换为凭据按需脱敏、本机路径/账号/主机/SID 占位、UTF-8/LF、物理行尾空格处理及末尾单个换行。本批次未检出凭据，原始字节和 SQLite 留存本地，嵌入哈希不重写；原有 318 个本地证据文件保持不变。公开路径中的 `<REPO>` 是占位符，不能直接执行。

[collect.py](tooling/collect.py)、[verify.py](tooling/verify.py)为当次取证脚本存档，原位置 `<REPO>/.local/refund-timeout-work/`，依赖冻结计划、原始目录、case-index 与历史哈希文件，不能直接在归档目录执行。它们不调用模型、不批准、不写业务数据，输出拒绝覆盖。语义备注来自 Codex 阅读评审，不冒充自动语义判定器。RT-1 及后续 RT-2、RT-3 的作者确认分别归档。原始证据及 manifest 不改写，JSON 中 project_author_confirmation=pending 保留为取证时状态，当前确认以作者判读记录为准。
