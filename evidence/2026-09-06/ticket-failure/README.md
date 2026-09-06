# AC6 工单持续失败：真实交互证据

[冻结用例 TC-ERR-002](../../../tests/ticket-failure-test-cases.md)依据已确认的 Q12/AC6。Codex 执行全部 3 个真实 CLI 样本、6 轮，程序状态/轨迹核对通过，回答初核符合所列部分完成预期；**TF-1 已获作者确认：AC6 处理通过，原始任务部分完成，工单尝试一次、未实际重试。TF-2、TF-3 待判读。** 确认范围及证据对应关系见[作者判读记录](../../../docs/practice/ticket-failure-review-20260906.md#作者判读记录)。未补跑、替换或追加恢复提示。

| 样本 | 完整报告 | CLI 原始输入输出 | 初始快照 | 工单失败快照 | 最终直接快照 | 独立核对 |
|---|---|---|---|---|---|---|
| TF-1 | [report](TF-1/report.json) | [command-log](TF-1/command-log.json) | [initial](TF-1/db-initial.json) | [failure-1](TF-1/db-after-ticket-failure-1.json) | [stopped](TF-1/db-stopped.json) | [checks](TF-1/verification-checks.json) |
| TF-2 | [report](TF-2/report.json) | [command-log](TF-2/command-log.json) | [initial](TF-2/db-initial.json) | [failure-1](TF-2/db-after-ticket-failure-1.json) | [stopped](TF-2/db-stopped.json) | [checks](TF-2/verification-checks.json) |
| TF-3 | [report](TF-3/report.json) | [command-log](TF-3/command-log.json) | [initial](TF-3/db-initial.json) | [failure-1](TF-3/db-after-ticket-failure-1.json) | [stopped](TF-3/db-stopped.json) | [checks](TF-3/verification-checks.json) |

各目录另有 execution-version、report-1 / report-2 / report-stopped、db-1 / db-2 与阶段 checks。失败快照在对应原错误返回 Agent 前通过独立只读 SQLite 连接取得；fault_checkpoint 是取证事件，不是模型工具。模型原话优先读 report.turns，command-log 保留终端 ANSI 控制字符、批准屏幕和实际 /approve、YES。执行人 Codex，作者负责后续证据判读。

每个样本实际创建一次申请、尝试一次工单，最终同一份正确 pending 申请和零工单。[批次核对](batch-verification.json)中 live_ticket_retry_samples 为空：配置 ticket_write_error=100 不等于实际执行了 100 次失败，也不能把建议重试写成已经重试。无成功工单 ID 或 recorded 状态；当前工单错误是 ok=false，而非成功幂等响应的 created=false。

执行基点为 `64016ec3c57918c45e9c507fe7604e37a8d939ec` 加 CLI/工程测试修改，实际版本由 [manifest](manifest.json) 的源码/测试/规则/计划指纹标识。提示、后端业务、runtime、模型适配器及 demo-v1 未改。DeepSeek deepseek-v4-flash；合计 18 次模型、15 次工具调用，API 报告 41757 Token，无费用账单。

[工程记录](engineering-validation.json)、[完整测试输出](engineering-tests.txt)、[实际命令与 stdout/stderr](engineering-command.json)保存本次 40 项测试通过、0 跳过的证据。5 个固定响应场景状态检查均通过：[normal](scripted/20260906T061145-1cead0fd.json)、[denied](scripted/20260906T061145-54c11a46.json)、[cross_tenant](scripted/20260906T061145-f5ce80c2.json)、[refund_timeout](scripted/20260906T061145-265f4b19.json)、[ticket_failure](scripted/20260906T061145-405afd4f.json)。工程测试的连续两次工单失败不计入真实模型的重试覆盖。

manifest 列出 57 份证据的源文件与公开 SHA256，不含 manifest 自身和本 README。公开转换仅为凭据按需脱敏、本机路径/账号/主机/SID 占位、UTF-8/LF、物理行尾空格规范化及末尾单个换行。本批次未检出凭据，原始字节和 SQLite 留存本地，嵌入的原始哈希不改写；原有 366 份本地证据未变。`<REPO>` 为路径占位，不是可执行路径。

[collect.py](tooling/collect.py)、[verify.py](tooling/verify.py)为当次取证和独立核对脚本存档，原位置 `<REPO>/.local/ticket-failure-work/`，依赖原始目录、case-index、冻结计划与历史哈希文件，不能直接在公开目录运行。它们不调用模型、不批准、不写业务数据，输出拒绝覆盖。语义备注是 Codex 阅读初核，不是自动语义判定。TF-1 的作者确认已独立归档，未扩大到 TF-2、TF-3；原始证据、manifest 及 JSON 中取证时的 pending 字段不改写，当前确认以作者判读记录为准。
