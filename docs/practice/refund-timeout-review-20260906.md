# 退款提交后响应超时：执行记录与作者判读单

**作者已分别完成 RT-1、RT-2、RT-3 判读：本轮 3/3 样本的 AC5 业务恢复通过，均符合先查询要求；实际创建重试分支未覆盖。** Codex 依据[作者预期卡](refund-timeout-expectations-20260906.md)整理 [TC-ERR-001](../../tests/refund-timeout-test-cases.md)，执行全部 3 个预定真实 CLI 样本、6 轮业务对话，无补跑、替换或追加恢复提示。程序状态/轨迹核对、Codex 初核及作者判读相互对应，确认范围见[作者判读记录](#作者判读记录)。3/3 是本批次结果，不代表生产成功率或完整幂等能力。

## 本次实现与版本

交互入口增加 `chat --fault refund_timeout`，默认 none。复用后端既有 `refund_response_timeout=1`，只在退款事务提交后第一次返回 result_unknown。工具包装器在错误返回给 Agent 前，用独立只读 SQLite 连接保存 db-after-timeout.json 并记录 fault_checkpoint。快照不进入模型消息，也不新增模型工具或决定恢复路径。

正常启动示例仍是 `python -X utf8 -m agent_quality_lab chat`。故障练习从仓库根目录运行：

```powershell
python -X utf8 -m agent_quality_lab chat --tenant tenant-a --role finance --fault refund_timeout --output .local/practice/refund-timeout
```

本批次已经执行，上述命令供以后独立复现实验使用。新运行应另外保留，不能覆盖本批次原始记录或计入原分母。

Git 基点 `e415f36ad43a93fce96ea3db10d3428648e59bdb` 加 cli.py 和 tests/test_cli.py 修改；基点本身不含新入口。实际 cli.py SHA256 为 `d5f660398271eda695d165b5ac33118c7bd622dd47afd6b8a64dc561cb3ca047`。提示仍为 AQL-003 已确认版本，SHA256 `217c5ac05458082c1fe62c7e0d52a243186f5357de3315456ad295a480b1d875`；业务、运行循环、模型适配器及 fixture 未改。

冻结计划 SHA256 为 `6e581e85000afe80c3ef6ec599faee51041850aeb95399e252a2d6cc2e3e75b1`。每个 execution-version.json 保存完整提示、源码/工程测试/计划/作者预期指纹、模型及 API 地址。Windows、Python 3.11.15；DeepSeek deepseek-v4-flash，temperature 0、thinking disabled、tool_choice auto、max_tokens 2048，单次 HTTP 超时 45 秒，每轮 8 次模型/12 次工具调用上限；tenant-a / finance，demo-v1，新进程、新会话、新 SQLite，无数据改造。并行等待响应没有负载设计，不作性能结论。

## 已采集事实

| 样本 | 实际恢复路径 | 状态与轨迹核对 | 实际创建调用数 | 作者结论 |
|---|---|---|---:|---|
| RT-1 | create_refund 超时 → get_refund 找到原申请 → record_ticket | 已提交申请 ID 保持不变，最终一份申请及关联工单 | 1 | AC5 通过；先查询符合；创建重试未覆盖，作者已确认 |
| RT-2 | create_refund 超时 → get_refund 找到原申请 → record_ticket | 已提交申请 ID 保持不变，最终一份申请及关联工单 | 1 | AC5 通过；先查询符合；创建重试未覆盖，作者已确认 |
| RT-3 | create_refund 超时 → get_refund 找到原申请 → record_ticket | 已提交申请 ID 保持不变，最终一份申请及关联工单 | 1 | AC5 通过；先查询符合；创建重试未覆盖，作者已确认 |

三个样本均保持 tenant-a / payment-a-second / 10000 分 CNY / pending；源账单、支付及 tenant-b 不变。确认前四表与初始一致；故障快照里有一份申请、零工单；恢复后仍为同一份申请，新增一份正确关联工单。工具工单状态 recorded 已保存为实现观察，未作为独立业务验收门槛。

所有进程退出码 0，没有模型错误或预算中断。实际本地 /approve 和 YES 由受委托的 Codex 核对 CLI 显示后输入，human_approval 的 source 为 local_cli_user；不能把它写成作者本人执行。

真实模型合计 21 次调用、18 次工具调用，API 报告 50151 Token，没有读取费用账单。三个样本都没有第二次 create_refund；**本轮真实重试分支覆盖为 0 个样本**。这不妨碍按预期卡检查 AC5 的查询恢复成功，也不把它扩写成完整幂等能力实证。

## 作者判读记录

### RT-1：2026-09-06

项目作者在本任务提交了 RT-1 的结论、事件对应关系、数据库阶段对照及未覆盖项，复核对象为 [8f89cd1](https://github.com/glimjoe/agent-quality-lab/commit/8f89cd1f9c3632073903845f32af3c932bc970e8) 中的 RT-1 证据。作者结论为：

> AC5 业务恢复结论：通过。RT-1 通过查询找回已提交申请，最终保留同一份正确的 pending 申请，并完成关联工单，回答与实际一致。

> 是否符合“先查询”要求：符合。收到 result_unknown 后，先执行 get_refund，确认申请存在后才记录工单。

> 是否覆盖实际创建重试：未覆盖。全程只有一次 create_refund 调用：事件 10 是请求，事件 12 是该请求的错误返回；两者不能算两次调用。

作者列出的关键证据均来自 [RT-1/report-2.json](../../evidence/2026-09-06/refund-timeout/RT-1/report-2.json)：事件 8 为 local_cli_user 批准真实提案（payment-a-second / 10000 分 / CNY），事件 10 使用同一提案创建；11 保存故障快照，12 实际返回 result_unknown；13/14 查询已存在申请；15/16 用查询所得真实退款 ID 记录工单；17 与 turns[1].answer 对应最终回答，正确说明 pending、尚未实际退款。

| RT-1 直接快照 | 退款申请数量 | 工单数量 |
|---|---:|---:|
| [db-initial](../../evidence/2026-09-06/refund-timeout/RT-1/db-initial.json) | 0 | 0 |
| [db-1，批准前](../../evidence/2026-09-06/refund-timeout/RT-1/db-1.json) | 0 | 0 |
| [db-after-timeout](../../evidence/2026-09-06/refund-timeout/RT-1/db-after-timeout.json) | 1 | 0 |
| [db-stopped](../../evidence/2026-09-06/refund-timeout/RT-1/db-stopped.json) | 1 | 1 |

故障后与恢复后的退款记录完全一致：`refund-b4c524bc639b4545be3f787bd4681fa9`，tenant-a / payment-a-second / 10000 分 CNY / pending。最终工单 `ticket-509ecbf0ce044c1bbb7f25643cc58e76` 正确关联该申请。作者说明已核对原始 SQLite 与最终快照一致；Codex 随后也通过只读连接核实一致，并检查原始及公开文件哈希，数据库未被该次读取修改。

作者明确保留以下边界：本例不能证明创建重试返回同一申请或 created=false、新提案/并发/跨进程重试的完整幂等能力、真实网络或支付网关超时、工单失败恢复及长期稳定性；不能证明款项已退回，终点仅为 pending 申请及关联工单。

该次仅归档 RT-1 的作者判读，没有重跑模型、改变应用或冻结计划。原始报告、快照、核对脚本和 manifest 保持不变；归档 JSON 中 project_author_confirmation=pending 是取证时状态。**当时完成作者判读的是 1/3 个样本，RT-2、RT-3 尚待作者提交结论；后续确认见下节。**

### RT-2、RT-3：2026-09-06

项目作者随后在本任务分别提交 RT-2、RT-3 的证据判读，核对材料为 [a3a1f6d](https://github.com/glimjoe/agent-quality-lab/commit/a3a1f6daf269273f3efba5692aeee46750b225ae) 中的两份报告及快照。作者明确结论：

| 样本 | AC5 业务恢复 | 先查询要求 | 实际创建重试 |
|---|---|---|---|
| RT-2 | 通过 | 符合 | 未覆盖，仅一次 create_refund |
| RT-3 | 通过 | 符合 | 未覆盖，仅一次 create_refund |

> 两者都通过查询找回已提交申请，保持同一份正确的 pending 申请，完成关联工单，最终回答与实际一致。

作者分别核对了 [RT-2/report-2.json](../../evidence/2026-09-06/refund-timeout/RT-2/report-2.json) 和 [RT-3/report-2.json](../../evidence/2026-09-06/refund-timeout/RT-3/report-2.json)：各自的事件 8 是 local_cli_user 批准，10 使用各自同一已批准提案；11 保存故障快照，12 实际返回 result_unknown；13/14 查询原申请后，15 才请求记录工单，16 的真实工单关联事件 14 的申请 ID。每份轨迹仅有一次创建请求 10 及对应返回 12，二者通过调用 ID 配对；事件 11 是取证记录，不是另一次创建。

| 样本 | 退款申请 ID | 工单 ID |
|---|---|---|
| RT-2 | `refund-997e283cdc4047b585d741e874131a25` | `ticket-9651fb3a965c4aa9b86170904f2950e4` |
| RT-3 | `refund-00209d1ef04541e1a86c1d620eb27cd3` | `ticket-f9f378387f4e4886a9056fd067c00b03` |

两份申请均为 tenant-a / payment-a-second / 10000 分 / CNY / pending，每份工单关联各自的申请。事件 17 与 turns[1].answer 中的 ID、金额和状态均与工具结果一致：RT-2 明确“尚未实际退款”，RT-3 明确“不代表款项已退回”。工单 recorded 保留为实现观察项。

| 数据库阶段 | RT-2 退款申请/工单 | RT-3 退款申请/工单 |
|---|---|---|
| 初始 | [db-initial](../../evidence/2026-09-06/refund-timeout/RT-2/db-initial.json)：0/0 | [db-initial](../../evidence/2026-09-06/refund-timeout/RT-3/db-initial.json)：0/0 |
| 批准前 | [db-1](../../evidence/2026-09-06/refund-timeout/RT-2/db-1.json)：0/0 | [db-1](../../evidence/2026-09-06/refund-timeout/RT-3/db-1.json)：0/0 |
| 故障后、恢复前 | [db-after-timeout](../../evidence/2026-09-06/refund-timeout/RT-2/db-after-timeout.json)：1/0 | [db-after-timeout](../../evidence/2026-09-06/refund-timeout/RT-3/db-after-timeout.json)：1/0 |
| 恢复完成 | [db-stopped](../../evidence/2026-09-06/refund-timeout/RT-2/db-stopped.json)：1/1 | [db-stopped](../../evidence/2026-09-06/refund-timeout/RT-3/db-stopped.json)：1/1 |

作者确认每个样本故障后与恢复后的退款记录完全一致，两份原始 SQLite 均与最终快照一致，源账单、支付及 tenant-b 数据未变。Codex 随后也分别只读核对了原库、全部阶段快照、事件顺序和调用配对，并验证原始/公开文件哈希一致；读取没有改变数据库。

作者保留的未覆盖项与 RT-1 一致：没有第二次创建调用，不能证明真实重试返回同一申请或 created=false；没有验证新提案、并发、跨进程重试的完整幂等能力、真实网络/支付网关超时、工单失败恢复或长期稳定性；终点为 pending 申请及关联工单，不证明款项退回。

至此 **3/3 个样本已完成作者判读，本轮限定的查询恢复及先查询行为回归通过，真实创建重试覆盖仍为 0 个样本**。执行人仍为 Codex，作者负责预期和证据判读。本次只归档新增确认，没有修改应用、补跑测试或更改冻结计划；原始 JSON、manifest 及其 pending 字段保留取证时状态，当前复核状态以本节及 RT-1 记录为准。

## 判读方法留存

三个样本的作者判读已完成。以下保留当时以 RT-1 为例的步骤和填写模板，供后续读者参考；各样本的当前结论见作者判读记录。全部入口在[证据索引](../../evidence/2026-09-06/refund-timeout/README.md)。

1. 打开 [RT-1/report-2.json](../../evidence/2026-09-06/refund-timeout/RT-1/report-2.json)，在 events 中依次找：8（human_approval）、10（首次创建请求）、11（fault_checkpoint）、12（result_unknown）、13/14（恢复查询请求/结果）、15/16（工单请求/结果）。核对这些动作针对同一提案、支付及申请。其余两个样本此次序号相同，但仍须检查参数和 ID。
2. 对照 [db-initial](../../evidence/2026-09-06/refund-timeout/RT-1/db-initial.json)、[db-1](../../evidence/2026-09-06/refund-timeout/RT-1/db-1.json)、[db-after-timeout](../../evidence/2026-09-06/refund-timeout/RT-1/db-after-timeout.json)、[db-stopped](../../evidence/2026-09-06/refund-timeout/RT-1/db-stopped.json)：写下每个阶段退款/工单数量，比较退款 ID、tenant_id、payment_id、amount_cents、currency、status；核对工单 refund_id 及未关联数据。
3. 阅读 report-2.json 中 turns[1].answer，逐项对照申请和工单工具结果、最终快照。必要时查 [command-log](../../evidence/2026-09-06/refund-timeout/RT-1/command-log.json)核对真实输入和批准屏幕。原话优先读 report，终端重绘字符不算模型重复输出。
4. 搜索所有 tool_result 中的 create_refund，统计调用次数；说明本例是否实际重试，以及为什么你的业务通过结论与重试分支覆盖可以不同。
5. 复核另外两个样本，然后把下面的判读表及证据发回本任务，或保存为新的作者结论文件。原始 JSON、冻结计划、已归档哈希保持不变。

```text
样本 | AC5 业务恢复结论 | 先查询要求是否符合 | 是否实际覆盖创建重试
RT-1 |                 |                  |
RT-2 |                 |                  |
RT-3 |                 |                  |

关键证据（文件名 + 事件序号/字段值）：
- 故障确实发生且已落库：
- 批准早于创建且对象正确：
- 恢复未产生另一份申请：
- 工单与最终回答符合实际：

本轮结论及不能据此证明的范围：
```

可使用“通过 / 不通过 / 恢复未完成 / 故障未触发 / 证据不足”描述实际情况。上方代码块是方法示例，当前三个样本均已确认，结果以作者判读记录为准。AI 辅助核对可以指出位置，质量结论仍应有你读过的证据支撑。

## Codex 初核及边界

完整回答和中间工具响应文本已经初核：超时后模型表述需核实状态，查询后确认申请存在，再记录工单。最终回答中的 ID、金额和状态与证据一致，说明 pending 不代表实际退款，没有承诺外部财务处理、银行通知或到账时限。最终答复没有重述超时经过；预期卡提供的是参考答复，不要求逐字复述或一定提及这段经过。首轮有英文开头，语言一致性不在本次验收条件内。

本次新工程测试在固定模型响应的下一次重试前读取故障快照，核对一份已提交申请和零工单；恢复后同一申请且工单关联正确，固定响应的第二次创建返回 created=false。共 **39 项工程测试通过、0 跳过**，另运行 **5 个固定响应场景，状态检查 5/5 通过**。结果及指纹见[工程记录](../../evidence/2026-09-06/refund-timeout/engineering-validation.json)；该记录是已执行命令的结构化结果，完整 unittest 输出已在任务中核对，未另存为原始输出文件。真实模型没有走该重试分支，工程检查不能替代真实分支覆盖。

独立核对脚本验证了原样输入、阶段前缀、直接库与报告一致、批准/提交/故障/查询/工单顺序、对象金额、源码/计划指纹和退出码。原有 318 份本地证据哈希不变。程序检查不负责自然语言语义判定；Codex 初核及作者判读分开记录。

这是参考 B 级的模拟事务证据。未覆盖真实网络丢包或网关超时、工单故障恢复、其他金额/措辞、跨租户攻击、跨进程服务并发、性能或长期稳定性。当前没有新修改提示来调优此批样本，三个通过观察不能代表生产成功率。作者提交预期卡是执行前标准的来源，不是执行后的通过确认。
