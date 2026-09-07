# 同一提案再次提交退款：真实交互证据

[TC-ST-003 冻结用例](../../../tests/refund-retry-test-cases.md)的三个新真实会话、九轮业务对话已完成并全部保留。**作者已分别完成 3/3 样本判读：数据安全检查均通过，实际退款创建重试覆盖仍为 0/3，本条重试验收不能判通过。** 三者追加再次提交均未执行；Q11 不禁止同一已批准提案的幂等重提。作者已确认 FR-3 构成[规则解释缺陷 AQL-004](../../../docs/defects/AQL-004-refund-retry-guidance.md)，未修复；FR-2 的规则解释正确，不归入该缺陷。当前确认见[作者判读记录](../../../docs/practice/refund-retry-review-20260906.md#作者判读记录)。

| 样本 | 完整报告 | 实际 CLI 输入输出 | 正常完成、再次请求前 | 再次请求后 | 最终直接快照 | 独立核对 |
|---|---|---|---|---|---|---|
| FR-1 | [report](FR-1/report.json) | [command-log](FR-1/command-log.json) | [db-2](FR-1/db-2.json) | [db-3](FR-1/db-3.json) | [stopped](FR-1/db-stopped.json) | [checks](FR-1/verification-checks.json) |
| FR-2 | [report](FR-2/report.json) | [command-log](FR-2/command-log.json) | [db-2](FR-2/db-2.json) | [db-3](FR-2/db-3.json) | [stopped](FR-2/db-stopped.json) | [checks](FR-2/verification-checks.json) |
| FR-3 | [report](FR-3/report.json) | [command-log](FR-3/command-log.json) | [db-2](FR-3/db-2.json) | [db-3](FR-3/db-3.json) | [stopped](FR-3/db-stopped.json) | [checks](FR-3/verification-checks.json) |

各目录另有 execution-version、db-initial、db-1、逐轮 report-1/2/3、report-stopped 及阶段 checks。直接快照来自独立只读 SQLite 查询，不复制 report.after；退出后再次核对原库及文件哈希。原始模型文字优先读 report.turns，command-log 保留 ANSI 控制字符、实际批准屏幕、原提案及所有输入。实际执行人是受委托的 Codex，作者负责判读。

每个样本事件 8 为本地批准，10/11 为唯一创建调用，12/13 为唯一工单调用，14 为正常完成回答；15 是再次提交请求，16/17 为 get_refund 查询，18 为最终回答。数据库从初始/批准前 0/0 到正常完成后 1/1；再次请求前后四表完全一致。全部 tool_result 成功，不代表再次提交执行过；事件 17 是查询结果，不能解释为创建重试返回 created=false。

[批次核对](batch-verification.json)将 state_safe_samples 与 actual_create_retry_samples 分列，后者为空。retry_returns_original_refund=null 表示没有实际重试结果可评。阶段 checks 中依赖存在重试的布尔合取为 false，也不能误读为“实际重试返回了错误申请”。语义备注由 Codex 阅读初核产生，不是自动语义分类器。

执行提交 `f8c87e9023c89e95c32889d289590278f6d69559`，无代码、提示、测试或数据修改，无故障注入。DeepSeek deepseek-v4-flash；本批 24 次模型、18 次工具调用，API 报告 60898 Token，没有读取费用账单。三份完整模型配置、源码/测试/规则/计划指纹见各目录 execution-version 及 [manifest](manifest.json)。

[engineering-baseline](engineering-baseline.json)记录与已执行版本 db02e4f 的应用和测试无差异，沿用[上轮 42 项工程测试](../ticket-recovery/engineering-validation.json)及 5 个固定响应场景；**本轮新工程测试运行数、新固定响应场景运行数均为 0**，不计入本批真实模型结果。

manifest 列出 **56 份证据**的原始/公开 SHA256，不包含 manifest 自身及本 README。公开转换为凭据按需脱敏、本机路径/账号/主机/SID 占位、UTF-8/LF、物理行尾空格规范化及末尾单个换行；本批未检出凭据。原始字节与 SQLite 留存本地，嵌入的原始哈希不改写，原有 **480 份本地运行文件未变**。

[collect.py](tooling/collect.py) 和 [verify.py](tooling/verify.py)是当次取证与核对脚本存档，原位置 `<REPO>/.local/refund-retry-work/`，依赖原始目录、case-index、冻结计划、工程基线及历史哈希文件，不能直接在公开目录运行。它们不调用模型、不批准、不写业务数据，输出拒绝覆盖。FR-1 及后续 FR-2、FR-3、AQL-004 的作者判读均已单独归档；原始 JSON、manifest 及取证时的 pending、候选标记保留，当前确认以作者判读记录和缺陷记录为准。

本轮参考 B 级，未覆盖实际退款创建重试、超时后的创建重试、新提案/跨会话重试、工单重复调用、并发与跨进程幂等、真实服务、其他输入/金额、性能和长期稳定性。无补跑、替换、追加引导或同批修复，不能把数据安全结果当作重试能力通过。
