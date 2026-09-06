# 故障解除后补记工单：真实交互证据

[冻结用例 TC-ST-002](../../../tests/ticket-recovery-test-cases.md)的 3 个真实 CLI 样本、9 轮业务对话已全部执行保留。每个样本工单首次失败，解除本地故障后对同一退款申请重试成功：申请/工单从 1/0 到 1/1，退款完整记录不变。**程序状态/轨迹检查和 Codex 回答初核通过；作者已确认 TR-1 恢复通过，进度 1/3，TR-2、TR-3 尚待判读。** 确认范围见[作者判读记录](../../../docs/practice/ticket-recovery-review-20260906.md#作者判读记录)。未补跑、替换或临时追加提示。

| 样本 | 完整报告 | 实际 CLI 输入输出 | 失败时快照 | 解除报告/快照 | 最终直接快照 | 独立核对 |
|---|---|---|---|---|---|---|
| TR-1 | [report](TR-1/report.json) | [command-log](TR-1/command-log.json) | [failure-1](TR-1/db-after-ticket-failure-1.json) | [report](TR-1/report-cleared.json) / [db](TR-1/db-cleared.json) | [stopped](TR-1/db-stopped.json) | [checks](TR-1/verification-checks.json) |
| TR-2 | [report](TR-2/report.json) | [command-log](TR-2/command-log.json) | [failure-1](TR-2/db-after-ticket-failure-1.json) | [report](TR-2/report-cleared.json) / [db](TR-2/db-cleared.json) | [stopped](TR-2/db-stopped.json) | [checks](TR-2/verification-checks.json) |
| TR-3 | [report](TR-3/report.json) | [command-log](TR-3/command-log.json) | [failure-1](TR-3/db-after-ticket-failure-1.json) | [report](TR-3/report-cleared.json) / [db](TR-3/db-cleared.json) | [stopped](TR-3/db-stopped.json) | [checks](TR-3/verification-checks.json) |

各目录另有 execution-version、db-initial、report-1/2/3/stopped、db-1/2/3 及阶段 checks。失败时与阶段数据库快照来自独立只读 SQLite 查询，不复制 report.after；故障解除时只有一条 fault_control 新事件、没有新业务轮次或数据库变化。模型原话优先读 report.turns，command-log 保留 ANSI 控制字符、实际提案、批准屏幕、YES 及控制命令。实际执行人为受委托的 Codex，作者负责证据判读。

每个样本创建调用为 1、工单尝试为 2、工单实际重试为 1；第一次返回 ticket_write_error，第二次成功并落库。故障剩余次数为 100 → 99 → 0；初始 faults 字段始终保留 100，当前剩余值见 remaining_faults。配置次数、失败取证事件和本地控制事件均不计为工具调用。[批次核对](batch-verification.json)列出三个实际重试及成功样本、事件序号、调用次数和指纹。

执行基点为 `9da66d1f0274b7a0767d1b671bbfe398df32c27f` 加 CLI 本地故障控制/报告落盘及工程回归，实际版本见 [manifest](manifest.json)。后端业务、提示、runtime、模型适配器及 demo-v1 不变。DeepSeek deepseek-v4-flash；合计 25 次模型、19 次工具调用，API 报告 64064 Token，没有读取费用账单。申请仍为 pending，本地模拟成功不代表款项退回或真实工单服务恢复。

[工程结果](engineering-validation.json)、[完整测试输出](engineering-tests.txt)、[命令与 stdout/stderr](engineering-command.json)保存 **42 项测试通过、0 跳过** 的证据。5 个固定响应场景状态检查通过：[normal](scripted/20260906T083916-0b847645.json)、[denied](scripted/20260906T083917-e4501e66.json)、[cross_tenant](scripted/20260906T083917-22423251.json)、[refund_timeout](scripted/20260906T083917-a2be61ea.json)、[ticket_failure](scripted/20260906T083917-fa37bffb.json)。固定模型的工程测试不代替真实模型和回答评审。

manifest 列出 **75 份证据**的源文件与公开 SHA256，不含 manifest 自身和本 README。转换限于凭据按需脱敏、本机路径/账号/主机/SID 占位、UTF-8/LF、物理行尾空格规范化及末尾单个换行；本批未检出凭据。原始字节和 SQLite 留存本地，嵌入的原始哈希不改写；原有 414 份本地证据未变。`<REPO>` 是路径占位，不是可执行路径。

[collect.py](tooling/collect.py)、[verify.py](tooling/verify.py)为当次取证和核对脚本存档，原位置 `<REPO>/.local/ticket-recovery-work/`，依赖原始目录、case-index、冻结计划与历史哈希文件，不能直接在公开目录运行。它们不调用模型、不批准、不写业务数据，输出拒绝覆盖。语义备注来自 Codex 阅读初核，不是自动语义分类器。TR-1 的作者确认已单独归档；原始报告、manifest 及取证时的 pending 保留，当前确认以作者判读记录为准。

本轮只覆盖同一模拟会话中一次真实失败后解除并补记成功。未覆盖已成功工单的重复补记、并发幂等、连续多次真实失败后的恢复、跨会话恢复、真实工单服务/网络、其他输入/金额、性能和长期稳定性。
