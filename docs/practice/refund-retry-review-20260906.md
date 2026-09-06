# 同一提案再次提交退款：执行记录与作者判读单

**三个样本的数据安全检查均通过，但实际退款创建重试覆盖为 0/3，本条重试验收不能判通过。** FR-1、FR-2、FR-3 在正常完成申请和工单后，面对再次提交原已批准提案的请求，均只调用 get_refund 查询并结束，没有第二次 create_refund。FR-3 另有一条与 Q11 不一致的规则解释，已记录[候选缺陷 AQL-004](../defects/AQL-004-refund-retry-guidance.md)，待作者判读。全部三个会话、九轮原始结果保留，未追加引导或替换样本。

依据：[已确认 Q8/Q10/Q11、AC1、R3](../first-slice.md)及本任务接受的下一步。[冻结用例 TC-ST-003](../../tests/refund-retry-test-cases.md)在首次模型调用前形成：新增一条用例，旧用例未改。Codex 受委托设计、执行与取证，作者负责判读，当前作者确认 **0/3**。本轮没有修改应用、提示、工具描述或工程测试。

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
| FR-1 | 正确申请和关联工单均完成 | get_refund | 1/0 | 1 | 原完整记录 1/1，不变 | 未覆盖 |
| FR-2 | 正确申请和关联工单均完成 | get_refund | 1/0 | 1 | 原完整记录 1/1，不变 | 未覆盖 |
| FR-3 | 正确申请和关联工单均完成 | get_refund | 1/0 | 1 | 原完整记录 1/1，不变 | 未覆盖；另有回答问题 |

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

## 回答初核及候选缺陷

Codex 已阅读三份完整对话及全部中间模型响应。T1 提案和金额正确，T2 准确报告申请及工单，明确 pending 未实际退款。T3 均正确展示原申请 ID、金额及 pending，没有声称已经实际重试或已到账；但对再次提交的解释有差别：

- FR-1 明确“因此，我不会重复提交”，并说明原申请和工单已存在。记录为未执行追加请求；仅凭其拒绝不判后端幂等失败。
- FR-2 说“再次提交同一笔退款申请会返回同一份申请……不会产生新的申请”，该规则解释有 Q11 依据；其实际仍只查询，不能据这句话补算一次重试。
- FR-3 说“重复提交同一笔支付会产生重复的退款申请，不符合规则。”这把同一提案的幂等重提说成会重复落库，与 Q11 不一致。候选 AQL-004 为回答规则解释问题，优先级建议 P2，尚待作者确认，未修复。实际数据库没有重复申请。

没有把所有“只查询”样本合并成三次同一缺陷：**0/3 重试覆盖**与 **1/3 出现上述明确错误解释**分别统计。FR-1/FR-2 的拒绝及措辞仍交作者独立判读；不能将同一批三次记录推算为模型普遍行为或生产发生率。中英文混用原样保留，没有新增语言门槛。

## 作者先判读 FR-1，再对照 FR-2、FR-3

1. 打开 [FR-1/report-2.json](../../evidence/2026-09-06/refund-retry/FR-1/report-2.json)，核对事件 8 的原提案批准、10/11 的唯一退款创建以及 12/13 的工单记录，确认再次请求前已是正确 1/1。
2. 打开 [FR-1/report-3.json](../../evidence/2026-09-06/refund-retry/FR-1/report-3.json)，阅读事件 15 的实际输入，核对事件 16/17 的工具名称和 call_id。这里是否真的出现第二次 create_refund？
3. 比较 db-2、db-3、db-stopped 四表，以及首次创建、最终查询返回的申请完整字段。分别判断“数据安全”和“重试是否实际执行”，不要只给一个通过。
4. 阅读事件 18／turns[2].answer，判断其是否准确描述实际动作和当前状态。结合 T2，区分原始业务任务已完成与追加再次提交请求未执行。
5. 按同样方法核对 [FR-2/report-3](../../evidence/2026-09-06/refund-retry/FR-2/report-3.json) 和 [FR-3/report-3](../../evidence/2026-09-06/refund-retry/FR-3/report-3.json)，重点比较两个样本对“再次提交是否产生新申请”的解释，并对候选 AQL-004 给出结论。

可按以下模板分别回复，每条结论附文件名、事件序号或字段值：

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

当前作者判读 0/3。后续确认单独归档，原始 JSON 和 manifest 中取证时的 pending 不改写。下一步先完成这批结果的判读；针对确认后的规则解释问题，再设计单独的改进与对照回归，原批次保留。

## 验证与边界

独立核对验证了原样输入、各阶段事件/轮次前缀、每个请求/结果配对、本地批准先于创建、原完整业务记录和无关数据保护、实际 T3 查询、源码/测试/规则/计划指纹及退出码；停止后用只读连接再次核对原始 SQLite，读取不改变数据库。证据一致性及数据安全检查通过，不代表重试验收通过。

阶段 checks 文件中 retry_used_original_proposal、all_retry_results_same_refund 为 false，是“存在重试且满足条件”的合取结果未成立；本批原因是根本没有重试。最终 verification-checks 使用 retry_coverage_result=not_exercised、retry_returns_original_refund=null 明确区分未观察与返回了错误申请，不把空调用集合判为通过。

本轮**工程测试和固定响应场景新执行均为 0**：应用及工程测试相较已执行版本 db02e4f 无差异，源码和测试指纹一致，沿用已保留的 42 项工程测试及 5 个固定响应场景结果。[工程基线核对](../../evidence/2026-09-06/refund-retry/engineering-baseline.json)链接其来源；这些不是本轮新执行，也不能代替真实创建重试覆盖。

本轮证据参考 B 级。原有 480 份本地运行文件哈希不变，新证据按[公开索引](../../evidence/2026-09-06/refund-retry/README.md)保留，源字节和公开字节分别计算 SHA256。未覆盖实际退款创建重试、超时后的创建重试、新提案/跨会话重试、工单重复调用、并发与跨进程幂等、真实服务、其他输入/金额、性能与长期稳定性。候选 AQL-004 待判读；本批不能作重试能力通过或生产发布结论。
