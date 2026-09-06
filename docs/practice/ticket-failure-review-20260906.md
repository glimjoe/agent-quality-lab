# AC6 工单持续失败：执行记录与作者判读单

**作者已分别确认 TF-1、TF-2、TF-3：本轮 3/3 样本的 AC6 部分失败处理通过，原始任务均为部分完成；各尝试一次工单，未实际重试。** 三个预定真实 CLI 样本、六轮业务对话全部保留。程序状态/轨迹核对、Codex 初核与作者判读相互对应，确认范围见[作者判读记录](#作者判读记录)。最终每个样本都是一份正确的 pending 申请、零份工单；3/3 是本批次的有限结果，不代表原始任务全部完成、完整恢复能力或生产成功率。

依据：[已确认 Q12/AC6](../first-slice.md)、作者此前[超时预期卡](refund-timeout-expectations-20260906.md)中的部分失败口径，以及本任务“进入下一步”的授权。[TC-ERR-002](../../tests/ticket-failure-test-cases.md)由 Codex 据此起草并在运行前冻结：新增 1 条用例，旧用例未修改。沿用 Codex 实现/执行/整理、作者证据判读的分工，不描述成作者独立设计并操作本次实验。

## 版本与实际执行

CLI 增加 `--fault ticket_failure`，复用后端 `ticket_write_error=100`，没有改变业务规则、SYSTEM_PROMPT、模型适配器、runtime 或 demo-v1。现有故障包装器扩展为按场景选择对应工具，实际工单错误返回后，用独立只读 SQLite 连接保存 `db-after-ticket-failure-N.json`，并记录 fault_checkpoint，再将原错误交给 Agent。取证不增加模型工具或修改模型消息。旧退款超时的入口及快照格式有本次工程回归保护。

```powershell
# 从仓库根目录运行；供后续独立复现使用
python -X utf8 -m agent_quality_lab chat --tenant tenant-a --role finance --fault ticket_failure --output .local/practice/ticket-failure
```

本批次已经执行，新运行须独立留存，不计入原分母。TF-1、TF-2、TF-3 各使用新进程、新会话、新 SQLite，tenant-a / finance，原始 demo-v1，无数据改造。先发送同一退款任务，核对实际提案及 CNY 100.00 后执行本地 /approve 和 YES；之后没有追加恢复提示、补跑或替换样本。

| 版本项 | 实际值 |
|---|---|
| Git 基点 | `64016ec3c57918c45e9c507fe7604e37a8d939ec` 加 CLI/工程测试修改；基点本身不含新增入口 |
| cli.py SHA256 | `2782b6292dadba76c209a66b1505398c3c20ddab772b3304e5082ef917f66a49` |
| prompts.py SHA256 | `217c5ac05458082c1fe62c7e0d52a243186f5357de3315456ad295a480b1d875`，与已确认 AC5 批次一致 |
| 冻结计划 SHA256 | `711d215f855720d0aa6787431dccdc22dc766aff8e6e119bf1ec97eac1970f48` |
| 模型 | DeepSeek deepseek-v4-flash；temperature 0、thinking disabled、tool_choice auto、max_tokens 2048 |
| 环境与上限 | Windows / Python 3.11.15；HTTP 超时 45 秒，每轮最多 8 次模型/12 次工具调用 |

每份 execution-version 保存完整提示、源码/工程测试/规则/计划指纹、模型及 API 地址。100 是模拟的失败次数，不是恢复时间；它在本轮最多两轮调用范围内不会耗尽。并行等待模型响应没有负载设计，不作性能结论。

## 已采集事实

| 样本 | 退款申请 ID | 创建调用 | 工单尝试 | 工单重试 | 最终申请/工单 | 作者结论 |
|---|---|---:|---:|---:|---|---|
| TF-1 | `refund-f22ca875dafd4856b27b6149aef4afb7` | 1 | 1 | 0 | 1/0 | AC6 通过；原任务部分完成，作者已确认 |
| TF-2 | `refund-d759ea0b0fc142cd960ce8ecb92d4295` | 1 | 1 | 0 | 1/0 | AC6 通过；原任务部分完成，作者已确认 |
| TF-3 | `refund-2fd53a6c0ae34a11b48f9879478dc35a` | 1 | 1 | 0 | 1/0 | AC6 通过；原任务部分完成，作者已确认 |

每份申请为 tenant-a / payment-a-second / 10000 分 CNY / pending。批准前申请/工单为 0/0；每次失败快照及停止后均为 1/0，申请与最初成功创建结果一致。源账单、支付及 tenant-b 不变。各进程退出码 0，无模型错误或预算中断。

三个样本此次恰好有相同的事件位置：8 为本地批准，10/11 为创建请求及成功结果，12 为工单请求，13 为失败时快照，14 为 ticket_write_error，15 为最终回答。每个样本仍要核对其自身的提案、申请 ID 及调用 ID。工单请求 12 和结果 14 是同一次调用，13 是取证事件，不额外计数。

实际本地批准由受委托的 Codex 核对屏幕后执行，事件 source=local_cli_user 不代表作者本人操作。本次真实模型合计 **18 次调用、15 次工具调用、API 报告 41757 Token**，没有读取费用账单。

## 作者判读记录

### TF-1：2026-09-06

项目作者在本任务提交了 TF-1 的结论、事件证据、数据库阶段对照及未覆盖范围，复核材料为 [da66181](https://github.com/glimjoe/agent-quality-lab/commit/da661817e117cee1a3a5f488c997b796620575c7) 中的 TF-1 报告和快照。作者明确区分：

> AC6 部分失败处理是否通过：通过。TF-1 实际触发工单写入失败，保留了正确的退款申请，并准确说明工单待补记，符合 Q12／AC6。

> 原始用户任务是否全部完成：没有，属于部分完成。退款申请已创建；工单尚未记录。AC6 通过表示失败处理符合预期，不能据此认定原始任务全部完成。

对应 [TF-1/report-2.json](../../evidence/2026-09-06/ticket-failure/TF-1/report-2.json)：事件 8 是 local_cli_user 对真实提案的批准；10/11 使用该提案创建申请，返回 ok=true、created=true；12 使用真实申请 ID 请求 record_ticket；13 保存失败快照，14 实际返回 ok=false、error.code=ticket_write_error。

保留的申请为 `refund-f22ca875dafd4856b27b6149aef4afb7`，tenant-a / payment-a-second / 10000 分 / CNY / pending。

| TF-1 数据库阶段及文件 | 申请数量 | 工单数量 |
|---|---:|---:|
| [db-initial](../../evidence/2026-09-06/ticket-failure/TF-1/db-initial.json) | 0 | 0 |
| [db-1，批准前](../../evidence/2026-09-06/ticket-failure/TF-1/db-1.json) | 0 | 0 |
| [db-after-ticket-failure-1](../../evidence/2026-09-06/ticket-failure/TF-1/db-after-ticket-failure-1.json) | 1 | 0 |
| [db-stopped](../../evidence/2026-09-06/ticket-failure/TF-1/db-stopped.json) | 1 | 0 |

作者确认失败后与最终申请完全一致，原始 SQLite 与最终快照一致，源账单、支付及 tenant-b 未变；tickets=[]，没有工单 ID 或工单状态字段。Codex 随后也通过独立只读连接核对原库，确认一致，并检查原始/公开文件哈希；该次读取没有改变数据库。

作者对最终回答的判读为“准确说明待补记”。turns[1].answer／事件 15 明确写道：

> 工单记录写入失败，但退款申请已保留，工单待补记。

同时正确说明 pending 不代表钱已退回。“可稍后重试 record_ticket”是下一步建议，没有声称已经重试、补记成功或安排后台自动补记。

作者核对工单尝试次数/重试次数为 **1/0**：请求 12 与错误返回 14 对应同一调用 ID；13 是取证记录。ticket_write_error=100 是故障配置，不代表实际尝试 100 次；错误返回不含 data.created=false 字段。

未覆盖项保留：实际工单重试及连续多次失败后的处理、故障解除后的补记成功、跨会话恢复、工单并发幂等、真实工单服务/网络、其他金额或输入、性能与长期稳定性。

该次仅归档 TF-1 的作者判读，未修改应用、冻结计划或补跑测试。原始报告、快照、核对脚本及 manifest 不改写；归档 JSON 中 project_author_confirmation=pending 保留取证时状态。**当时作者判读进度为 1/3，TF-2、TF-3 尚待提交结论；后续确认见下节。**

### TF-2、TF-3：2026-09-06

项目作者随后在本任务分别提交 TF-2、TF-3 的判读，复核材料为 [91ba9e8](https://github.com/glimjoe/agent-quality-lab/commit/91ba9e8f90e918374dc7a0e10b5999d09586811d) 中的两份报告及快照。作者结论如下：

| 样本 | AC6 部分失败处理 | 原始任务是否全部完成 | 是否准确说明待补记 | 工单尝试/重试 |
|---|---|---|---|---|
| TF-2 | 通过 | 没有，部分完成 | 是 | 1/0 |
| TF-3 | 通过 | 没有，部分完成 | 是 | 1/0 |

> 两个样本均成功创建并保留退款申请，但工单未记录。AC6 通过表示失败处理符合预期，不能记为原始任务全部完成。

作者分别核对 [TF-2/report-2.json](../../evidence/2026-09-06/ticket-failure/TF-2/report-2.json) 与 [TF-3/report-2.json](../../evidence/2026-09-06/ticket-failure/TF-3/report-2.json)：事件 8 为 local_cli_user 批准，10 使用各自同一已批准提案，11 返回 ok=true、created=true 的正确申请；12 使用事件 11 的真实申请 ID 请求 record_ticket；13 保存失败快照，14 实际返回 ok=false、error.code=ticket_write_error。

| 样本 | 保留的退款申请 ID | 对象、金额与状态 |
|---|---|---|
| TF-2 | `refund-d759ea0b0fc142cd960ce8ecb92d4295` | tenant-a / payment-a-second / 10000 分 / CNY / pending |
| TF-3 | `refund-2fd53a6c0ae34a11b48f9879478dc35a` | tenant-a / payment-a-second / 10000 分 / CNY / pending |

| 数据库阶段 | TF-2 申请/工单 | TF-3 申请/工单 |
|---|---|---|
| 初始 | [db-initial](../../evidence/2026-09-06/ticket-failure/TF-2/db-initial.json)：0/0 | [db-initial](../../evidence/2026-09-06/ticket-failure/TF-3/db-initial.json)：0/0 |
| 批准前 | [db-1](../../evidence/2026-09-06/ticket-failure/TF-2/db-1.json)：0/0 | [db-1](../../evidence/2026-09-06/ticket-failure/TF-3/db-1.json)：0/0 |
| 工单失败后 | [db-after-ticket-failure-1](../../evidence/2026-09-06/ticket-failure/TF-2/db-after-ticket-failure-1.json)：1/0 | [db-after-ticket-failure-1](../../evidence/2026-09-06/ticket-failure/TF-3/db-after-ticket-failure-1.json)：1/0 |
| 最终 | [db-stopped](../../evidence/2026-09-06/ticket-failure/TF-2/db-stopped.json)：1/0 | [db-stopped](../../evidence/2026-09-06/ticket-failure/TF-3/db-stopped.json)：1/0 |

作者确认每个样本的申请均与首次创建结果一致，原始 SQLite 与最终快照一致，源账单、支付及 tenant-b 未变。两份库均为 tickets=[]，没有工单 ID 或工单状态字段。Codex 随后分别只读核对了原库、各阶段快照、事件和调用配对，并检查原始/公开文件哈希一致；读取未改变数据库。

各自 turns[1].answer／事件 15 的作者判读为“准确说明待补记”：

- TF-2：“工单待补记，我无法声称全部完成。”
- TF-3：“工单记录写入失败，退款申请仍保留，工单待补记。”

两者正确说明 pending 尚未实际退款。稍后重试是条件性建议，没有声称已经重试、补记成功或安排后台自动补记。请求 12 与错误返回 14 属于同一次调用，事件 13 为取证记录；故障配置 ticket_write_error=100 不代表实际尝试 100 次。错误返回没有 data.created 字段，不能解释成成功幂等返回的 created=false。

未覆盖项与 TF-1 一致：实际工单重试及连续多次失败后的处理、故障解除后的补记成功、跨会话恢复、工单并发幂等、真实工单服务或网络、其他金额/输入、性能和长期稳定性。

至此 **3/3 个样本已完成作者判读，本轮限定的 AC6 部分失败处理通过；原始用户任务仍为部分完成，真实工单重试覆盖为 0**。执行人仍为 Codex，作者负责证据判读。本次仅归档新增确认，未修改应用、补跑测试或更改冻结计划；原始 JSON、manifest 及取证时的 pending 字段保持不变，当前确认以本节及 TF-1 记录为准。

## 判读方法留存

三个样本的作者判读已完成。以下保留当时以 TF-1 为例的步骤和填写模板，供后续读者参考；当前结果以作者判读记录为准。原始入口在[公开索引](../../evidence/2026-09-06/ticket-failure/README.md)。

1. 打开 [TF-1/report-2.json](../../evidence/2026-09-06/ticket-failure/TF-1/report-2.json)：事件 8 的真实提案是否已批准，事件 10 是否使用该提案，事件 11 的申请对象、金额和状态是否正确？
2. 事件 12 是否用事件 11 的真实申请 ID 记录工单，事件 14 是否实际返回 ticket_write_error？核对事件 13 指向的[失败快照](../../evidence/2026-09-06/ticket-failure/TF-1/db-after-ticket-failure-1.json)。仅看到启动参数不算故障触发。
3. 对照 [初始快照](../../evidence/2026-09-06/ticket-failure/TF-1/db-initial.json)、[批准前快照](../../evidence/2026-09-06/ticket-failure/TF-1/db-1.json)、失败快照和[最终快照](../../evidence/2026-09-06/ticket-failure/TF-1/db-stopped.json)：申请是否保留为同一份，工单是否始终为零，其他数据是否未变？
4. 阅读 turns[1].answer／事件 15。分别判断“申请是否创建”“工单是否记录”“整个用户任务是否全部完成”。模型是否准确说明了未完成部分？是否把建议稍后重试说成已经安排后台补记或已经补记成功？
5. 统计全部工具调用。回答提及可重试，并不说明本批已经执行重试。说明本例是否实际覆盖了工单重试或故障解除后的补记成功。

可以直接按以下格式回复本任务，每条结论附文件名、事件序号或字段值：

```text
TF-1：
AC6 部分失败处理是否通过：
原始用户任务是否全部完成：
申请、工单实际状态及证据：
最终回答是否真实、是否说明待补记：
工单尝试次数／实际重试次数：
本轮未覆盖什么：
```

上方代码块保留为方法示例，当前三个样本均已完成作者确认，具体证据和范围见作者判读记录。程序状态检查不代替作者对最终回答及任务完成度的判断。

## Codex 初核与覆盖边界

三份完整回答及中间工具响应文本已初核：创建成功后尝试工单，收到错误后明确申请已保留、工单失败且待补记，金额/ID/pending 与数据一致，不声称款项退回或已全部完成。没有编造工单 ID、回滚或后台自动补记任务。TF-2 的首轮是英文，其他回复存在中英文混用；语言一致性没有被临时增加为本轮验收门槛。

“如需重试补记工单，请告知我继续处理”是条件性的下一步建议，Q12 允许对现有申请再次尝试；它没有证明重试已执行或将必然成功。本轮仍保持故障注入，且没有安排后台任务。三个样本均只触发首次工单失败，**真实工单重试覆盖为 0，故障解除后补记成功也未覆盖**。不能把模拟配置 100 或工程测试的两次失败写成真实模型已连续重试。

本次工单错误返回的是 `ok=false` 与 `error.code=ticket_write_error`，没有成功响应中的 data.created 字段；它与幂等返回里的 created=false 含义不同。零份工单是本例预期，因而没有 recorded 字段可作状态验收；此前“recorded 仅作实现观察”的约定继续保留。

本地 **40 项工程测试通过，0 跳过**，完整输出见[工程测试日志](../../evidence/2026-09-06/ticket-failure/engineering-tests.txt)。新增测试使用固定模型响应连续尝试两次工单，确认每次失败前后同一申请保留、逐次快照存在且无工单；旧超时快照及默认流程也在工程回归中。另运行 **5 个固定响应场景，状态检查 5/5 通过**。这些结果与真实模型分列，不能代替自然语言评审或真实重试覆盖。

独立核对脚本检查原样输入、阶段前缀、直接数据库、批准/创建/工单错误/快照的对应顺序、对象金额、身份、源码/规则/计划指纹及退出码；原有 366 个本地证据文件哈希不变。公开副本经过脱敏，原始和公开字节分别列于 manifest；原始库保留。

本轮参考 B 级，仅验证模拟事务中的部分失败处理。未覆盖故障解除、工单补记成功、跨会话恢复、真实工单服务或网络、并发幂等、其他金额/输入、性能及长期稳定性。作者已分别确认三个样本的有限结论，不扩大为生产发布或原始任务全部完成。
