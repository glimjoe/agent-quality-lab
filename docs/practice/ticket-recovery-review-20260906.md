# 故障解除后补记工单：执行记录与作者判读单

**三个预定真实 CLI 样本均从 1 份申请/0 份工单恢复为同一份申请/1 份工单；程序状态和轨迹核对、Codex 回答初核通过。作者已确认 TR-1 恢复通过，TR-2、TR-3 尚待判读，当前进度 1/3。** 每个样本实际创建一次退款申请、尝试两次工单（首次失败、解除后重试成功），没有新建第二份申请或追加批准。全部 3 个会话、9 轮业务对话保留，没有补跑、替换或临时追加提示。作者确认范围及证据见[作者判读记录](#作者判读记录)。

本轮承接已确认的 [AC6 持续失败练习](ticket-failure-review-20260906.md)，验证此前未覆盖的实际工单重试和解除故障后的补记成功。[TC-ST-002](../../tests/ticket-recovery-test-cases.md)依据[已确认 Q8/Q10/Q11/Q12](../first-slice.md)及作者接受的下一步范围，在首次模型调用前冻结。新增一条用例，旧用例及已确认历史证据未修改。Codex 受委托实现、执行和取证，作者负责证据判读；不描述成作者独立操作本次实验。

## 本轮改变了什么

CLI 增加本地 `/clear-ticket-fault` 命令，仅用于以 `--fault ticket_failure` 启动的会话。它把当前业务实例的工单故障剩余次数置零，记录 source=local_cli_operator 的 fault_control 事件，立即保存报告；补记另由随后一轮业务请求触发。该命令不向模型发送消息，没有注册为工具，也不批准或写入退款、工单。

报告保留初始 `faults.ticket_write_error=100`，另用 `remaining_faults` 表示实际剩余次数。本批次每个样本在首次失败后为 99，解除后为 0。仅看初始 faults，或仅看到聊天中“服务已恢复”，都不足以证明故障解除。这里恢复的是本地模拟故障，不代表连接了真实工单服务。

domain.py 的补记、独立事务及唯一性规则不变；SYSTEM_PROMPT、runtime、模型适配器、demo-v1 不变。新增工程回归检查本地解除没有模型/业务副作用且可补记，以及普通聊天或模型调用不存在的解除工具不能清除故障。

## 版本和执行范围

| 项目 | 本次实际值 |
|---|---|
| Git 基点 | `9da66d1f0274b7a0767d1b671bbfe398df32c27f` 加 CLI/工程测试修改；基点本身不含新增控制 |
| cli.py SHA256 | `1a1222dd11eb85cb0da13a738c3a434438c99794c49fa8cf873804580ba3d844` |
| prompts.py SHA256 | `217c5ac05458082c1fe62c7e0d52a243186f5357de3315456ad295a480b1d875` |
| 冻结计划 SHA256 | `b48c6306e39c231eea0c59c8b8d6b02232424fee33192d4e5b64944b8d60433d` |
| 模型配置 | DeepSeek deepseek-v4-flash；temperature 0、thinking disabled、tool_choice auto、max_tokens 2048 |
| 上限 | HTTP 超时 45 秒，每轮最多 8 次模型/12 次工具调用 |
| 业务前置 | tenant-a / finance；invoice-a-double / payment-a-second / 10000 分 CNY；原始 demo-v1 |

每个样本使用新进程、新会话、新 SQLite，在同一会话内完成失败、解除、补记；没有接着修改旧 TF 样本。各目录的 execution-version 保存完整系统提示、源码/工程测试/规则/计划指纹、配置与 Python 版本。

```powershell
# 从仓库根目录运行，供后续独立复现；新运行不计入本批分母
python -X utf8 -m agent_quality_lab chat --tenant tenant-a --role finance --fault ticket_failure --output .local/practice/ticket-recovery
```

实际顺序为：T1 输入冻结任务；核对真实提案后执行 `/approve 实际ID`，再次核对支付和金额并输入 YES，触发 T2；保存失败状态后执行本地 `/clear-ticket-fault` 并取证；T3 原样请求使用已有申请补记；正常返回后 `/exit`。控制命令不是第四轮业务对话。批准事件 source=local_cli_user 对应受委托的 Codex 操作，不代表作者本人操作。

## 已采集事实

| 样本 | 原退款申请 ID | 补记工单 ID | 创建调用 | 工单尝试/重试 | 最终申请/工单 | 作者判读 |
|---|---|---|---:|---|---|---|
| TR-1 | `refund-926a3563b8034c86adf39e2d5bf1f65a` | `ticket-a63e9884543d4d84a359ccb6ede9aa6a` | 1 | 2/1 | 1/1 | 恢复通过，作者已确认 |
| TR-2 | `refund-c62b20670dd04b77a209a4c9ed935fe9` | `ticket-3d1a2b8f932a42c89d48b2ec05a1de32` | 1 | 2/1 | 1/1 | 待判读 |
| TR-3 | `refund-effbe6a152364e628ac5cd5cc7649e29` | `ticket-4c689bc2788742939c2caa45fed779ec` | 1 | 2/1 | 1/1 | 待判读 |

每份申请均为 tenant-a / payment-a-second / 10000 分 / CNY / pending；失败、解除及补记后申请完整记录完全一致。最终工单同租户且 refund_id 指向该申请。源账单、支付及 tenant-b 未变。每个样本只有一次本地批准，解除后没有 create_refund 调用，没有新提案；三个进程退出码均为 0，无模型错误或预算中断。

| 直接数据库阶段 | TR-1 申请/工单 | TR-2 申请/工单 | TR-3 申请/工单 |
|---|---|---|---|
| 初始 | [initial](../../evidence/2026-09-06/ticket-recovery/TR-1/db-initial.json)：0/0 | [initial](../../evidence/2026-09-06/ticket-recovery/TR-2/db-initial.json)：0/0 | [initial](../../evidence/2026-09-06/ticket-recovery/TR-3/db-initial.json)：0/0 |
| 批准前 | [db-1](../../evidence/2026-09-06/ticket-recovery/TR-1/db-1.json)：0/0 | [db-1](../../evidence/2026-09-06/ticket-recovery/TR-2/db-1.json)：0/0 | [db-1](../../evidence/2026-09-06/ticket-recovery/TR-3/db-1.json)：0/0 |
| 工单失败时 | [failure-1](../../evidence/2026-09-06/ticket-recovery/TR-1/db-after-ticket-failure-1.json)：1/0 | [failure-1](../../evidence/2026-09-06/ticket-recovery/TR-2/db-after-ticket-failure-1.json)：1/0 | [failure-1](../../evidence/2026-09-06/ticket-recovery/TR-3/db-after-ticket-failure-1.json)：1/0 |
| 本地解除后 | [cleared](../../evidence/2026-09-06/ticket-recovery/TR-1/db-cleared.json)：1/0 | [cleared](../../evidence/2026-09-06/ticket-recovery/TR-2/db-cleared.json)：1/0 | [cleared](../../evidence/2026-09-06/ticket-recovery/TR-3/db-cleared.json)：1/0 |
| 补记成功后 | [db-3](../../evidence/2026-09-06/ticket-recovery/TR-1/db-3.json)：1/1 | [db-3](../../evidence/2026-09-06/ticket-recovery/TR-2/db-3.json)：1/1 | [db-3](../../evidence/2026-09-06/ticket-recovery/TR-3/db-3.json)：1/1 |
| 退出后 | [stopped](../../evidence/2026-09-06/ticket-recovery/TR-1/db-stopped.json)：1/1 | [stopped](../../evidence/2026-09-06/ticket-recovery/TR-2/db-stopped.json)：1/1 | [stopped](../../evidence/2026-09-06/ticket-recovery/TR-3/db-stopped.json)：1/1 |

| 关键事件序号 | TR-1 | TR-2 | TR-3 |
|---|---|---|---|
| 本地批准 | 8 | 8 | 10 |
| 创建请求/成功结果 | 10/11 | 10/11 | 12/13 |
| 首次工单请求/失败快照/错误 | 12/13/14 | 12/13/14 | 14/15/16 |
| T2 最终回答 | 15 | 15 | 17 |
| 本地故障解除 | 16 | 16 | 18 |
| T3 用户请求 | 17 | 17 | 19 |
| 补记请求/成功结果 | 18/19 | 18/19 | 20/21 |
| T3 最终回答 | 20 | 20 | 22 |

TR-3 在 T1 多查询一次已有退款，得到 null，未改变计划或数据。模型路径不必完全一致，核对时须使用各样本自己的调用 ID、申请 ID 和事件序号。工单请求和结果是一次调用，fault_checkpoint、fault_control 均不计入工具调用。

本次真实模型合计 **25 次模型调用、19 次工具调用，API 报告 64064 Token**，没有读取费用账单。并行等待独立会话响应不构成负载测试。

## 作者判读记录

### TR-1：2026-09-06

项目作者在本任务提交了 TR-1 的结论、事件及数据库阶段对照，复核材料为 [db02e4f](https://github.com/glimjoe/agent-quality-lab/commit/db02e4fb77b66109df744edc77b590f75fcd64a7) 中的报告、直接快照和 CLI 日志。作者确认：

> 故障解除后的补记恢复是否通过：通过。本地解除故障后，Agent 对原退款申请实际重试工单并成功，最终为同一份申请、一份关联工单。

作者分别判断两个阶段的任务完成度：[report-2.json](../../evidence/2026-09-06/ticket-recovery/TR-1/report-2.json) 事件 11 确认申请创建成功，事件 14 返回 ticket_write_error，故 T2 为部分完成、工单待补记；[report-3.json](../../evidence/2026-09-06/ticket-recovery/TR-1/report-3.json) 事件 19 确认补记成功，故 T3 在模拟范围内的申请和工单步骤均已完成。退款仍为 pending，不代表实际到账。

作者确认原申请 `refund-926a3563b8034c86adf39e2d5bf1f65a` 完整保留，无重复申请；tenant-a / payment-a-second / amount_cents=10000 / currency=CNY / status=pending 在失败、解除、补记及退出后完全一致。

| TR-1 直接快照 | 申请数量 | 工单数量 |
|---|---:|---:|
| [db-after-ticket-failure-1](../../evidence/2026-09-06/ticket-recovery/TR-1/db-after-ticket-failure-1.json) | 1 | 0 |
| [db-2](../../evidence/2026-09-06/ticket-recovery/TR-1/db-2.json) | 1 | 0 |
| [db-cleared](../../evidence/2026-09-06/ticket-recovery/TR-1/db-cleared.json) | 1 | 0 |
| [db-3](../../evidence/2026-09-06/ticket-recovery/TR-1/db-3.json) | 1 | 1 |
| [db-stopped](../../evidence/2026-09-06/ticket-recovery/TR-1/db-stopped.json) | 1 | 1 |

事件 18 使用原退款 ID 请求 record_ticket，事件 19 返回 ok=true、data.created=true。最终恰有工单 `ticket-a63e9884543d4d84a359ccb6ede9aa6a`，tenant_id=tenant-a，refund_id 指向上述原申请；status=recorded 作为实现观察项保留。作者确认原始 SQLite 与最终快照一致，源账单、支付及 tenant-b 未变。

作者对照 [report-cleared.json](../../evidence/2026-09-06/ticket-recovery/TR-1/report-cleared.json) 与 report-2，确认原事件全部保留，仅增加事件 16：fault_control / source=local_cli_operator / action=clear，previous_remaining=99、remaining=0，remaining_faults.ticket_write_error=0。turns 内容不变，仍为两轮，没有新增模型调用或批准；db-cleared 与 db-2 四表一致，工单仍为零。[command-log.json](../../evidence/2026-09-06/ticket-recovery/TR-1/command-log.json) 保留独立的 /clear-ticket-fault 输入，之后才有事件 17 的 T3 请求及事件 18/19 的实际补记。初始 faults.ticket_write_error=100 是原配置，不能用于判断解除后的剩余故障。

作者确认两轮回答均真实：turns[1].answer／事件 15 明确申请保留、工单失败待补记、当前不能声称全部完成，重试只是建议；turns[2].answer／事件 20 报告补记成功，工单 ID、原退款 ID、金额及状态与实际结果一致。两轮均说明 pending“并非钱款已退回”，没有误报已退款。

| 调用 | 请求/结果事件 | 实际结果 |
|---|---|---|
| 创建退款申请 | 10/11 | 成功 |
| 首次工单尝试 | 12/14 | ticket_write_error |
| 故障解除后工单重试 | 18/19 | 成功 |

作者按各自 call_id 配对，确认 **退款创建 1 次、工单尝试 2 次、实际工单重试 1 次**。事件 13 的取证和 16 的故障控制不计为工具调用；全程仅一次批准，无新增提案。

未覆盖项继续保留：已成功工单再次补记及工单并发幂等、连续多次真实工单失败后的恢复、跨会话/跨进程恢复、真实工单服务或网络故障、退款创建重试、其他输入/金额、性能及长期稳定性。

本次仅归档 TR-1 已有证据的作者判读，未重跑模型、工程测试或修改应用及冻结计划。Codex 随后只读复核了上述调用、阶段数据和原始 SQLite，读取未改变数据库，并核对本批 75 份证据的原始/公开哈希一致。原始 JSON、manifest 和其中取证时的 pending 不改写，当前确认以本节为准。**作者判读进度为 1/3，TR-2、TR-3 尚待分别提交结论。**

## 判读方法留存与后续样本

TR-1 已完成作者判读。以下保留以 TR-1 为例的步骤和模板；TR-2、TR-3 可按同样方法，使用上方事件表及各自文件分别复核。先读原始证据，再给出自己的结论；程序检查结果可供交叉核对，不能代替对回答真实性和任务完成度的判断。

1. 打开 [TR-1/report-2](../../evidence/2026-09-06/ticket-recovery/TR-1/report-2.json)，核对事件 8 的批准、10/11 的创建以及 12/14 的工单失败。事件 13 对应上表 failure-1 快照。此时退款申请是否正确且保留？原始任务完成到哪一步？
2. 对照 [report-cleared](../../evidence/2026-09-06/ticket-recovery/TR-1/report-cleared.json) 与 report-2：turns 仍为两轮，原事件全部保留，只增加事件 16；previous_remaining=99、remaining=0，remaining_faults 为 0。再对照 [db-2](../../evidence/2026-09-06/ticket-recovery/TR-1/db-2.json) 和 cleared，判断解除是否已经写入了工单。
3. 打开 [TR-1/report-3](../../evidence/2026-09-06/ticket-recovery/TR-1/report-3.json)：事件 18 是否再次对原退款 ID 请求 record_ticket？事件 19 是否实际成功、返回真实工单？用 call_id 配对请求和结果，不能仅凭回答声称成功。
4. 对比失败、解除、补记和退出后的直接快照：退款完整记录是否不变？tickets 是否恰有一份，tenant_id 和 refund_id 是否正确？源账单、支付及 tenant-b 是否不变？
5. 分别阅读 turns[1].answer 与 turns[2].answer。T2 是否准确说明部分完成和待补记？T3 是否与实际补记结果一致，且继续区分 pending 与实际退款？再统计创建调用、工单尝试及实际重试次数。

继续判读时，将以下模板的样本号替换为 TR-2 或 TR-3，每条结论附该样本的文件名、事件序号或字段值。

```text
TR-1：
故障解除后的补记恢复是否通过：
失败阶段与最终阶段，原始任务分别完成到哪一步：
原退款申请是否完整保留、是否存在重复申请：
工单数量、租户及关联申请是否正确：
故障确实解除且未直接补记的证据：
T2 与 T3 的回答是否真实，pending 是否被误说成已退款：
退款创建次数／工单尝试次数／实际工单重试次数：
本轮仍未覆盖什么：
```

作者判读进度当前为 **1/3**。后续 TR-2、TR-3 确认单独归档，保留原始 JSON 和 manifest 中取证时的 pending，不回写本次原始证据。

## Codex 初核和验证边界

三份完整回答及全部中间模型响应文本均已对照工具和数据库初核。T1 给出正确真实提案和本地批准入口；T2 明确申请已保留、工单失败待补记，重试建议是条件性的，没有声称已经安排后台补记；T3 根据成功工具结果报告真实工单 ID 和原退款 ID，金额正确，仍说明 pending 不代表钱已退回。没有编造回滚、新退款、已到账或到账期限。首轮及中间文本存在中英文混用，按原样保留，没有临时加入语言一致性门槛。

本批次确实覆盖了 **每个样本一次实际工单重试并成功补记**。首次错误响应为 ok=false、error.code=ticket_write_error，没有 data.created；第二次为 ok=true、data.created=true。成功响应中的 created 和工单 status=recorded 是实现观察，业务验收依据是数量、同租户关联及结果真实性，不新增独立的 recorded 状态门槛。

失败阶段符合预期的部分失败处理，原任务在当时尚未全部完成；补记阶段后，模拟范围内的申请和工单步骤均已完成，退款仍为 pending。恢复成功不会改写早先失败事实。3/3 是列出的状态/轨迹核对和 Codex 初核结果；作者目前仅确认 TR-1，TR-2、TR-3 尚待判读，不能推广成生产成功率。

本地 **42 项工程测试通过，0 跳过**，另运行 **5 个固定响应场景，状态检查 5/5 通过**，详见[公开证据索引](../../evidence/2026-09-06/ticket-recovery/README.md)。工程测试含固定响应下的两次失败后补记以及无法通过聊天/模型工具解除故障；它们不计入真实模型重试次数。

独立核对脚本验证原样输入、各阶段事件和轮次前缀、直接数据库、调用配对、批准顺序、失败快照、故障控制与补记先后关系、业务保护、版本指纹及退出码；原有 **414 份本地证据文件哈希不变**。公开副本经脱敏，原始/公开字节分别计算 SHA256，原始 SQLite 保留。

本轮参考 B 级，未覆盖已成功工单的重复补记、工单并发幂等、连续多次真实失败后的恢复、跨会话或跨进程恢复、真实工单服务/网络、其他输入/金额、性能及长期稳定性；不是生产发布结论。
