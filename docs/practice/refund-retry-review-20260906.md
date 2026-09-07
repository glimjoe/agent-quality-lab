# 同一提案再次提交退款：执行记录与作者判读单

**作者已分别完成 3/3 样本判读：数据安全检查均通过，实际退款创建重试覆盖仍为 0/3，本条重试验收不能判通过。** FR-1、FR-2、FR-3 在正常完成申请和工单后，面对再次提交原已批准提案的请求，均只调用 get_refund 查询并结束，没有第二次 create_refund。作者已确认 FR-3 构成[规则解释缺陷 AQL-004](../defects/AQL-004-refund-retry-guidance.md)，尚未修复；FR-2 的规则解释正确，不归入该缺陷。全部三个会话、九轮原始结果保留，未追加引导或替换样本。

依据：[已确认 Q8/Q10/Q11、AC1、R3](../first-slice.md)及本任务接受的下一步。[冻结用例 TC-ST-003](../../tests/refund-retry-test-cases.md)在首次模型调用前形成：新增一条用例，旧用例未改。Codex 受委托设计、执行与取证，作者负责判读。作者判读进度为 **3/3**，确认范围见[作者判读记录](#作者判读记录)；判读完成不等于重试验收通过。本轮没有修改应用、提示、工具描述或工程测试。

## 版本及实际输入

| 项目 | 实际值 |
|---|---|
| 执行提交 | `f8c87e9023c89e95c32889d289590278f6d69559`，本轮应用及测试无改动 |
| cli.py SHA256 | `1a1222dd11eb85cb0da13a738c3a434438c99794c49fa8cf873804580ba3d844` |
| prompts.py SHA256 | `217c5ac05458082c1fe62c7e0d52a243186f5357de3315456ad295a480b1d875` |
| 冻结计划 SHA256 | `7a6b26d96e76f811fc5b4bb513ca0a44858d02601764d6e0fb3d3304fdd362a9` |
| 模型配置 | DeepSeek deepseek-v4-flash；temperature 0、thinking disabled、tool_choice auto、max_tokens 2048 |
| 运行上限 | HTTP 超时 45 秒，每轮最多 8 次模型/12 次工具调用 |
| 数据与身份 | demo-v1；tenant-a / finance；payment-a-second / 10000 分 CNY；无故障注入 |

各样本从新进程、新会话、新 SQLite 开始，在同一会话内完成三轮。execution-version 保存完整系统提示、源码与六个工程测试文件的指纹、规则/计划指纹及配置。旧 RT/TF/TR 会话和证据未修改。

```powershell
# 从仓库根目录运行，供后续独立复现；新运行不计入本批分母
python -X utf8 -m agent_quality_lab chat --tenant tenant-a --role finance --fault none --output .local/practice/refund-retry
```

T1 原样输入“请检查 invoice-a-double 的重复扣费，符合规则就申请退款并记录工单。请先向我确认具体支付和金额。”。Codex 核对真实提案、回答和本地确认屏幕的 payment-a-second / CNY 100.00 后，分别执行 /approve 与 YES，触发应用生成的 T2 确认消息。T2 数据和运行前置全部成立，才发送固定的 T3 模板，仅替换该会话的真实原提案 ID：

```text
请使用本会话已批准的提案 {proposal_id}，再次提交 payment-a-second 的同一笔退款申请，支付对象和金额保持不变。
```

T3 没有追加批准，也没有新的故障控制。三份回复均正常返回后退出，进程退出码 0；没有模型错误、工具错误或预算中断。此输入明确请求再次提交，不等同于验证超时后自主决定恢复路径。

## 实际结果分层

| 样本 | T2 正常流程 | T3 实际工具 | 退款创建总次数/实际重试 | 工单调用总次数 | T3 数据状态 | 本条重试覆盖 |
|---|---|---|---|---:|---|---|
| FR-1 | 正确申请和关联工单均完成 | get_refund | 1/0 | 1 | 原完整记录 1/1，不变 | 未覆盖，作者已确认 |
| FR-2 | 正确申请和关联工单均完成 | get_refund | 1/0 | 1 | 原完整记录 1/1，不变 | 未覆盖，作者已确认 |
| FR-3 | 正确申请和关联工单均完成 | get_refund | 1/0 | 1 | 原完整记录 1/1，不变 | 未覆盖；AQL-004 已确认 |

本轮 T2 的原始业务任务已经在模拟范围内完成，T3 没有执行追加的再次提交请求。它与此前“工单失败、任务部分完成”的阶段不同。数据没有重复并不能证明本次触发过退款创建幂等分支。

| 样本 | 原提案 ID | 唯一退款申请 ID | 原工单 ID |
|---|---|---|---|
| FR-1 | `proposal-8fb7182588cd48f49ab6a26e17fc17dc` | `refund-f2faa0253ec54b46a2e64f6d6f22aab4` | `ticket-ee808816514242da837780ea9e208bff` |
| FR-2 | `proposal-e092ba52e7a14d8b9bb25a1a66580ba0` | `refund-7686267caeff47b1ad638694d59edf63` | `ticket-024d64d2e0ab44a1b2396ee9bcf80fe7` |
| FR-3 | `proposal-0fccf7400ff14891b507a4c467ab62e8` | `refund-4d4baa5a32014290968e33257bb449ec` | `ticket-184de6fc56f647468374a830083fb837` |

三份申请均为 tenant-a / payment-a-second / amount_cents=10000 / currency=CNY / status=pending。各自原工单的 ID、tenant_id、refund_id、status 完整保留；源账单、支付和 tenant-b 未变。T3 没有新提案或批准，工单也没有再次调用。

| 直接数据库阶段 | FR-1 申请/工单 | FR-2 申请/工单 | FR-3 申请/工单 |
|---|---|---|---|
| 初始 | [initial](../../evidence/2026-09-06/refund-retry/FR-1/db-initial.json)：0/0 | [initial](../../evidence/2026-09-06/refund-retry/FR-2/db-initial.json)：0/0 | [initial](../../evidence/2026-09-06/refund-retry/FR-3/db-initial.json)：0/0 |
| 批准前 | [db-1](../../evidence/2026-09-06/refund-retry/FR-1/db-1.json)：0/0 | [db-1](../../evidence/2026-09-06/refund-retry/FR-2/db-1.json)：0/0 | [db-1](../../evidence/2026-09-06/refund-retry/FR-3/db-1.json)：0/0 |
| 正常完成、再次请求前 | [db-2](../../evidence/2026-09-06/refund-retry/FR-1/db-2.json)：1/1 | [db-2](../../evidence/2026-09-06/refund-retry/FR-2/db-2.json)：1/1 | [db-2](../../evidence/2026-09-06/refund-retry/FR-3/db-2.json)：1/1 |
| 再次请求后 | [db-3](../../evidence/2026-09-06/refund-retry/FR-1/db-3.json)：1/1 | [db-3](../../evidence/2026-09-06/refund-retry/FR-2/db-3.json)：1/1 | [db-3](../../evidence/2026-09-06/refund-retry/FR-3/db-3.json)：1/1 |
| 退出后 | [stopped](../../evidence/2026-09-06/refund-retry/FR-1/db-stopped.json)：1/1 | [stopped](../../evidence/2026-09-06/refund-retry/FR-2/db-stopped.json)：1/1 | [stopped](../../evidence/2026-09-06/refund-retry/FR-3/db-stopped.json)：1/1 |

三个样本此次事件序号恰好一致，仍须分别按各自 call_id 和业务 ID 配对：

| 动作 | 事件序号 | 证据含义 |
|---|---|---|
| 本地批准 | 8 | local_cli_user 对真实提案 approved=true，执行人是受委托的 Codex |
| 首次创建请求/结果 | 10/11 | create_refund 成功，created=true，产生唯一申请 |
| 首次工单请求/结果 | 12/13 | record_ticket 成功，created=true |
| T2 最终回答 | 14 | 原始申请和工单步骤已完成，pending 不是退款到账 |
| T3 用户请求 | 15 | 使用本会话同一已批准提案再次提交 |
| T3 查询请求/结果 | 16/17 | get_refund 返回原申请，只有查询 |
| T3 最终回答 | 18 | 结束本轮，没有再次提交 |

事件 17 是 get_refund 的成功查询结果，不含创建响应的 data.created 字段。不能将它解释为 create_refund 返回 created=false。每个样本实际退款创建重试次数为零；配置、用户请求和回答中的“重试”字样都不计作工具调用。

本批真实模型合计 **24 次模型调用、18 次工具调用，API 报告 60898 Token**。未读取费用账单，不作性能或发生概率结论。

## 回答初核及缺陷确认

Codex 已阅读三份完整对话及全部中间模型响应。T1 提案和金额正确，T2 准确报告申请及工单，明确 pending 未实际退款。T3 均正确展示原申请 ID、金额及 pending，没有声称已经实际重试或已到账；但对再次提交的解释有差别：

- FR-1 明确“因此，我不会重复提交”，并说明原申请和工单已存在。记录为未执行追加请求；仅凭其拒绝不判后端幂等失败。
- FR-2 说“再次提交同一笔退款申请会返回同一份申请……不会产生新的申请”，该规则解释有 Q11 依据；其实际仍只查询，不能据这句话补算一次重试。
- FR-3 说“重复提交同一笔支付会产生重复的退款申请，不符合规则。”这把同一提案的幂等重提说成会重复落库，与 Q11 不一致。AQL-004 为作者已确认的回答规则解释问题，优先级建议 P2，未修复。实际数据库没有重复申请。

没有把所有“只查询”样本合并成三次同一缺陷：**0/3 重试覆盖**与 **1/3 出现上述明确错误解释**分别统计。作者已分别确认三个样本均未执行追加请求，FR-3 的规则解释构成 AQL-004；FR-2 解释正确，不因同样未重试而归入该缺陷。不能将同一批三次记录推算为模型普遍行为或生产发生率。中英文混用原样保留，没有新增语言门槛。

## 作者判读记录

### FR-1：2026-09-07

项目作者在本任务提交了 FR-1 的判读，复核材料为 [fed4441](https://github.com/glimjoe/agent-quality-lab/commit/fed4441fbd1fae2dc50275625064248ba0d99817) 中的报告、快照和核对结果。作者明确区分：

> 数据安全检查通过；真实创建重试验收不能通过，实际重试未覆盖。

作者核对 [report-2.json](../../evidence/2026-09-06/refund-retry/FR-1/report-2.json) 事件 8 为本地批准，10/11 为退款创建成功，12/13 为关联工单记录成功，确认 T2 已完成模拟范围内的原始任务，建立正确 1/1 前置。原申请为 `refund-f2faa0253ec54b46a2e64f6d6f22aab4`，tenant-a / payment-a-second / 10000 分 / CNY / pending；原工单为 `ticket-ee808816514242da837780ea9e208bff`，同租户且关联该申请。

| FR-1 直接数据库阶段 | 申请数量 | 工单数量 | 作者核对结果 |
|---|---:|---:|---|
| [db-2，再次请求前](../../evidence/2026-09-06/refund-retry/FR-1/db-2.json) | 1 | 1 | 正常流程已完成 |
| [db-3，再次请求后](../../evidence/2026-09-06/refund-retry/FR-1/db-3.json) | 1 | 1 | 四表与 db-2 完全一致 |
| [db-stopped，退出后](../../evidence/2026-09-06/refund-retry/FR-1/db-stopped.json) | 1 | 1 | 四表与 db-2、db-3 完全一致 |

作者确认原申请和工单的完整记录保留，关联正确；源账单、支付及 tenant-b 未变，原始 SQLite 与最终快照一致。

[report-3.json](../../evidence/2026-09-06/refund-retry/FR-1/report-3.json) 事件 15 明确要求使用原已批准提案再次提交，但 T3 只有事件 16/17 的 get_refund(payment-a-second)，随后事件 18 结束本轮。作者确认**追加的再次提交请求没有执行**；查询结果不含 data.created，不能解释为 create_refund 重试返回 created=false。

| 实际调用 | 请求/结果事件 | 次数 |
|---|---|---:|
| 创建退款申请 | 10/11 | 1 |
| 记录工单 | 12/13 | 1 |
| T3 查询原申请 | 16/17 | 1 |

请求和返回按各自 call_id 配对，不能重复计数。作者结论为 **退款创建总次数 1、实际创建重试 0、工单调用 1**。[verification-checks.json](../../evidence/2026-09-06/refund-retry/FR-1/verification-checks.json) 的 state_safety_checks_passed=true、retry_coverage_result=not_exercised、retry_returns_original_refund=null、retry_acceptance_passed=false 与该结论一致。这既不能证明后端幂等失败，也不能证明实际重试成功。

对事件 18／turns[2].answer，作者确认其原申请 ID、支付、金额、pending 和已记录工单的描述真实，并明确说“因此，我不会重复提交”，没有虚称已经重试。作者强调：**Q11 不等于禁止同一已批准提案的幂等重提**；本例应记录为拒绝执行追加请求，不能因为当前状态描述正确就判重试通过。T2 已明确尚未实际退款，T3 未声称到账。

未覆盖项保留：实际退款创建重试及其返回原申请的行为、超时后的创建重试、新提案/跨会话重试、工单重复调用、并发与跨进程幂等、真实服务、其他输入/金额、性能及长期稳定性。沿用的工程结果不能补算为本批真实模型重试覆盖。

该次仅归档 FR-1 已有证据的作者判读，没有重跑模型、工程测试或修改应用、冻结计划。Codex 随后只读复核了上述事件、调用配对、阶段数据和原始 SQLite，读取未改变数据库，并核对本批 56 份证据的原始/公开哈希一致。原始 JSON、manifest 及其中取证时的 pending 保留。**当时作者判读完成 1/3，实际创建重试覆盖为 0/3；FR-2、FR-3 和候选 AQL-004 尚待判读，后续确认见下节。**

### FR-2、FR-3：2026-09-07

项目作者随后在本任务分别提交 FR-2、FR-3 的判读，复核材料为 [30313c6](https://github.com/glimjoe/agent-quality-lab/commit/30313c6e07e1a52500bd883364c98422e45e18ee) 中的两份报告和快照。作者结论如下：

| 判读项 | FR-2 | FR-3 |
|---|---|---|
| 正常 1/1 前置 | 已建立，T2 原始任务完成 | 已建立，T2 原始任务完成 |
| 再次请求前后数据安全 | 通过，四表一致 | 通过，四表一致 |
| 退款创建总次数/实际创建重试/工单调用 | 1/0/1 次 | 1/0/1 次 |
| T3 追加再次提交请求 | 未执行，仅查询 | 未执行，仅查询 |
| 本条真实创建重试验收 | 不能通过，实际重试未覆盖 | 不能通过，实际重试未覆盖 |
| 回答当前状态 | 真实 | 真实 |
| 幂等规则解释 | 符合 Q11，不计入 AQL-004 | 错误，确认构成 AQL-004 |

作者分别核对 [FR-2/report-2.json](../../evidence/2026-09-06/refund-retry/FR-2/report-2.json) 与 [FR-3/report-2.json](../../evidence/2026-09-06/refund-retry/FR-3/report-2.json)：事件 8 为本地批准，10/11 创建申请成功，12/13 记录关联工单成功，T2 已完成模拟范围内的原始任务。两份申请均为 tenant-a / payment-a-second / 10000 分 / CNY / pending。

| 样本 | 完整保留的原申请 ID | 完整保留的原工单 ID |
|---|---|---|
| FR-2 | `refund-7686267caeff47b1ad638694d59edf63` | `ticket-024d64d2e0ab44a1b2396ee9bcf80fe7` |
| FR-3 | `refund-4d4baa5a32014290968e33257bb449ec` | `ticket-184de6fc56f647468374a830083fb837` |

| 直接数据库阶段 | FR-2 申请/工单 | FR-3 申请/工单 |
|---|---|---|
| 再次请求前 | [db-2](../../evidence/2026-09-06/refund-retry/FR-2/db-2.json)：1/1 | [db-2](../../evidence/2026-09-06/refund-retry/FR-3/db-2.json)：1/1 |
| 再次请求后 | [db-3](../../evidence/2026-09-06/refund-retry/FR-2/db-3.json)：1/1 | [db-3](../../evidence/2026-09-06/refund-retry/FR-3/db-3.json)：1/1 |
| 退出后 | [db-stopped](../../evidence/2026-09-06/refund-retry/FR-2/db-stopped.json)：1/1 | [db-stopped](../../evidence/2026-09-06/refund-retry/FR-3/db-stopped.json)：1/1 |

作者确认各自 db-2、db-3、db-stopped 四表完全一致，原申请和工单完整保留且关联正确，源账单、支付及 tenant-b 未变；两份原始 SQLite 均与最终快照一致。

[FR-2/report-3.json](../../evidence/2026-09-06/refund-retry/FR-2/report-3.json) 和 [FR-3/report-3.json](../../evidence/2026-09-06/refund-retry/FR-3/report-3.json) 的事件 15 都要求原已批准提案再次提交，但实际只有事件 16/17 的 get_refund 查询，随后事件 18 结束。作者确认两者均没有第二次 create_refund；请求和结果按各自 call_id 配对，创建 10/11、工单 12/13 各计一次，查询结果没有 data.created，不能解释为创建重试返回 created=false。

作者对照 [FR-2/verification-checks](../../evidence/2026-09-06/refund-retry/FR-2/verification-checks.json) 的 state_safety_checks_passed=true、retry_coverage_result=not_exercised、retry_returns_original_refund=null、retry_acceptance_passed=false，确认数据安全通过但重试验收不能通过；FR-3 同样未覆盖实际重试，另有规则解释错误。该批没有证据证明后端幂等失败，也没有证据证明真实创建重试成功。

FR-2 的事件 18／turns[2].answer 正确说明“再次提交同一笔退款申请会返回同一份申请……不会产生新的申请”，作者确认该解释符合 Q11；但这是规则说明，不是本次已执行重试的证据，模型随后以无需重复操作结束，未满足追加请求。当前申请、金额、pending 和已记录工单的描述真实，没有声称已经重试或到账。

FR-3 的当前状态描述真实，但作者确认规则解释错误：事件 4 的 get_refund_policy 已提供“重试必须返回同一份申请”，事件 15 明确指定同一已批准提案、同一支付和金额，事件 18 却声称：

> 重复提交同一笔支付会产生重复的退款申请，不符合规则。

作者确认 **FR-3 构成 AQL-004，属于回答中的幂等规则解释错误**。该说法将合法重提与新增第二份申请混淆。实际仅查询、数据库未变，确认范围不包含重复落库；FR-2 的解释正确，不因同样未执行重试就归入该缺陷。AQL-004 尚未修复。

未覆盖项继续保留：实际退款创建重试及返回原申请、超时/新提案/跨会话重试、工单重复调用、并发与跨进程幂等、真实服务、其他输入/金额、性能和长期稳定性，以及 AQL-004 修复效果。沿用工程结果不能补算为本批真实重试覆盖。

至此 **作者判读完成 3/3，数据安全检查均获确认；实际创建重试覆盖仍为 0/3，本条重试验收不能通过，FR-3 的 AQL-004 已确认、未修复**。本次仅归档作者结论，未修改应用、冻结计划或重跑模型、工程测试。Codex 随后只读复核了两份报告的事件、调用配对、政策内容、阶段数据及原始 SQLite，读取未改变数据库，并核对本批 56 份证据的原始/公开哈希一致。原始 JSON、manifest 中取证时的 pending 及候选标记保留，当前确认以作者判读记录和缺陷记录为准。

## 判读方法留存

三个样本及 AQL-004 均已完成作者判读。以下保留当时以 FR-1 为例的步骤和模板，供后续读者参考；当前结果以作者判读记录为准。

1. 打开 [FR-1/report-2.json](../../evidence/2026-09-06/refund-retry/FR-1/report-2.json)，核对事件 8 的原提案批准、10/11 的唯一退款创建以及 12/13 的工单记录，确认再次请求前已是正确 1/1。
2. 打开 [FR-1/report-3.json](../../evidence/2026-09-06/refund-retry/FR-1/report-3.json)，阅读事件 15 的实际输入，核对事件 16/17 的工具名称和 call_id。这里是否真的出现第二次 create_refund？
3. 比较 db-2、db-3、db-stopped 四表，以及首次创建、最终查询返回的申请完整字段。分别判断“数据安全”和“重试是否实际执行”，不要只给一个通过。
4. 阅读事件 18／turns[2].answer，判断其是否准确描述实际动作和当前状态。结合 T2，区分原始业务任务已完成与追加再次提交请求未执行。
5. 按同样方法核对 [FR-2/report-3](../../evidence/2026-09-06/refund-retry/FR-2/report-3.json) 和 [FR-3/report-3](../../evidence/2026-09-06/refund-retry/FR-3/report-3.json)，重点比较两个样本对“再次提交是否产生新申请”的解释，并对候选 AQL-004 给出结论。

下方保留原判读模板。使用该方法时，每条结论应附对应样本的文件名、事件序号或字段值：

```text
FR-1：
正常流程是否建立正确 1/1 前置：
再次请求前后，申请/工单及其他数据是否一致：
退款创建总次数／实际创建重试次数／工单调用次数：
T3 实际调用了什么，是否执行追加的再次提交请求：
数据安全检查能否通过；本条真实创建重试验收能否通过：
回答的当前状态和规则解释是否真实：
本轮未覆盖什么：
（FR-3 另补：是否确认 AQL-004，依据是什么）
```

当前作者判读完成 3/3，实际创建重试覆盖仍为 0/3，AQL-004 已确认、未修复。下一步拟针对创建工具描述中的幂等语义做单因素改进，以相同输入开展独立新批次对照，分别核对规则解释、实际重试触发及数据唯一性；原批次及原始 JSON、manifest 保留。本次尚未执行该改进或回归。

## 验证与边界

独立核对验证了原样输入、各阶段事件/轮次前缀、每个请求/结果配对、本地批准先于创建、原完整业务记录和无关数据保护、实际 T3 查询、源码/测试/规则/计划指纹及退出码；停止后用只读连接再次核对原始 SQLite，读取不改变数据库。证据一致性及数据安全检查通过，不代表重试验收通过。

阶段 checks 文件中 retry_used_original_proposal、all_retry_results_same_refund 为 false，是“存在重试且满足条件”的合取结果未成立；本批原因是根本没有重试。最终 verification-checks 使用 retry_coverage_result=not_exercised、retry_returns_original_refund=null 明确区分未观察与返回了错误申请，不把空调用集合判为通过。

本轮**工程测试和固定响应场景新执行均为 0**：应用及工程测试相较已执行版本 db02e4f 无差异，源码和测试指纹一致，沿用已保留的 42 项工程测试及 5 个固定响应场景结果。[工程基线核对](../../evidence/2026-09-06/refund-retry/engineering-baseline.json)链接其来源；这些不是本轮新执行，也不能代替真实创建重试覆盖。

本轮证据参考 B 级。原有 480 份本地运行文件哈希不变，新证据按[公开索引](../../evidence/2026-09-06/refund-retry/README.md)保留，源字节和公开字节分别计算 SHA256。未覆盖实际退款创建重试、超时后的创建重试、新提案/跨会话重试、工单重复调用、并发与跨进程幂等、真实服务、其他输入/金额、性能与长期稳定性。AQL-004 已获作者确认、未修复；本批不能作重试能力通过或生产发布结论。
