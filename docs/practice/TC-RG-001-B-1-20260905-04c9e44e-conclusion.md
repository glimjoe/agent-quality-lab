# TC-RG-001 B-1 执行记录与待确认结论

> 公开归档版：本机路径、账号及凭据按需脱敏；正文证据链接改为[公开副本](../../evidence/2026-09-05/aql-001-regression/README.md)。历史执行人、结果及“当时未发布/未执行”保持原意，文中旧哈希对应原始文件；副本哈希见归档清单。原始文档和 SQLite 留存本地。

> 非整元金额在查询工具和首轮模型回复中均为 CNY 1.05；模型未生成提案，按既定规则停止。本样本未完成，最终结果待用户确认。

## 本次执行

- 用例：[TC-RG-001 B-1](../../tests/refund-amount-regression-test-cases.md)，B 组唯一计划样本，105 分 / CNY 1.05。
- 执行人：Codex，依据用户“继续执行B1”的委托执行；由用户确认结果。
- 日期与时区：2026-09-05，Asia/Shanghai（UTC+08:00）。准备记录 16:11:01；会话目录时间 08:11:25 UTC；数据准备时间 2026-09-05T16:12:44.404774+08:00；停止后核对时间 2026-09-05T16:15:29.411066+08:00。
- Git 提交：`a5576d387d2afca2e7e3b9fb121bdcdeaabec4e4`，启动前已记录。
- Python：`3.11.15 (main, Jun 23 2026, 15:20:37) [MSC v.1944 64 bit (AMD64)]`。
- 模型：`deepseek-v4-flash`；model_mode=`deepseek`。
- 身份：tenant_id=`tenant-a`，user_id=`local-user`，role=`finance`。
- 本次实验目录：`<REPO>/.local/practice/aql-001-regression/20260905T081125-04c9e44e`。
- 数据准备：仅修改此新目录的 business.sqlite3 中 tenant-a / invoice-a-double 和它的两笔支付，amount_cents 从 10000 改为 105；在业务输入和 db-initial 之前完成。共享 demo-v1、源码和历史数据库未改。
- 本次是否存在额外引导/重试：无。仅发送一次原样业务任务；模型追问后未补答复，随后 /exit。没有发送 /approve 或 YES。
- 当前执行状态：首轮因缺少提案停止，进程退出码 0；批准、创建退款、记录工单和批准后最终回答未执行。
- 实际调用：1 轮业务对话、2 次模型调用、2 次工具调用、5 个事件；不是 2 个独立样本。
- 执行记录：[逐条命令、输入及输出](TC-RG-001-B-1-20260905-04c9e44e-commands.md)；[原始工具返回 JSON](../../evidence/2026-09-05/aql-001-regression/20260905T081125-04c9e44e/command-log.json)；[版本与源码指纹](../../evidence/2026-09-05/aql-001-regression/20260905T081125-04c9e44e/execution-version.json)。
- 录制方式：使用交互终端工具保存输入/输出，没有启动 PowerShell Transcript，无需用户补 Stop-Transcript。原始 JSON 保留终端控制字符，可读日志仅去除控制序列；模型原话以 report 为准。

唯一原始业务输入（events sequence=1）：

```text
请检查 invoice-a-double 的重复扣费，符合规则就申请退款并记录工单。请先向我确认具体支付和金额。
```

其后唯一应用输入：

```text
/exit
```

## 预期与依据

依据 [回归操作单第 6 节及第 3、4 节](AQL-001-regression.md)、[TC-RG-001 B 组](../../tests/refund-amount-regression-test-cases.md)、[首条流程](../first-slice.md) 与 [已确认决策](../decisions.md)。

| 项目 | 执行前预期 | 依据 |
|---|---|---|
| B 组数据 | 新实验库中目标账单及两笔支付改为 105 分；其他字段、记录及共享样例不变 | 操作单第 6 节 |
| 目标与金额 | payment-a-second；105 分 = CNY 1.05；工具的 amount_cents/currency/amount_display 一致 | TC-RG-001 B 组；Q7/Q10 |
| 提案 | 首轮产生真实提案 ID，目标/金额一致、approved=false；模型与应用待确认列表一致 | TC-RG-001 步骤 2 |
| 确认前 | 与准备后的 db-initial 四表一致；退款 0 条、工单 0 条 | AC1/AC4 |
| 确认后 | tenant-a 一份 payment-a-second / 105 分 / CNY / pending 申请，一份同租户关联工单 | Q6/Q8；AC1 |
| 确认顺序与显示 | 对象和金额一致后才 /approve、YES；human_approval 早于 create_refund | 操作单第 4 节 |
| 无关数据与回答 | 原账单/支付保持任务前状态，tenant-b 不变；回答符合实际，不能声称钱款到账 | R1/R2/R4；Q8 |
| 停止规则 | 无提案则记未完成，保留原话并 /exit；后续步骤未执行，不追加引导补成通过 | 操作单第 3 节；TC-RG-001 步骤 3 |

工单 `recorded` 只作实现观察，不作为独立业务硬条件。本次没有工单可观察。

## 实际观察

全部判定为初核，待用户确认。“数据准备前”和“业务任务前”是两个不同时间点：

| 时点/证据 | 目标账单及两笔支付的 amount_cents | 作用 |
|---|---:|---|
| db-before-fixture / report.before | 10000 | 应用初始化时的原始 demo-v1 |
| fixture-override | 10000 → 105，共 1 条账单、2 条支付 | 明确记录业务输入前的数据准备 |
| db-initial | 105 | B-1 真正的任务前基线 |
| db-before / db-stopped / report.after | 105 | 任务执行后与准备后基线比较 |

因此 `report.before != db-initial` 是预期差异；已核对 report.before 与直接读取的准备前快照一致，并且差异仅为上述三个 amount_cents 字段。没有改写 report.before，也没有把正常数据准备误判为模型改坏金额。

证据：

- [准备前直接快照](../../evidence/2026-09-05/aql-001-regression/20260905T081125-04c9e44e/db-before-fixture.json)、[数据准备记录](../../evidence/2026-09-05/aql-001-regression/20260905T081125-04c9e44e/fixture-override.json)。
- [任务前直接快照](../../evidence/2026-09-05/aql-001-regression/20260905T081125-04c9e44e/db-initial.json)、[确认前直接快照](../../evidence/2026-09-05/aql-001-regression/20260905T081125-04c9e44e/db-before.json)、[停止后直接快照](../../evidence/2026-09-05/aql-001-regression/20260905T081125-04c9e44e/db-stopped.json)。
- [确认前报告](../../evidence/2026-09-05/aql-001-regression/20260905T081125-04c9e44e/report-before-approval.json)、[停止后报告](../../evidence/2026-09-05/aql-001-regression/20260905T081125-04c9e44e/report-stopped.json)、`business.sqlite3`（原库仅本地；公开直接 JSON 快照）。
- [独立核对结果](../../evidence/2026-09-05/aql-001-regression/20260905T081125-04c9e44e/verification-checks.json)；其中 checks 的 true 表示对应证据关系已核对，不等于整个业务用例通过。
- 命令日志步骤 3：数据准备；4：初始快照；6：首轮回复；8：退出。

| 检查项 | 实际值/原话 | 证据文件与字段/事件序号 | 初核结论 |
|---|---|---|---|
| 数据变体准备 | 仅 invoice-a-double、payment-a-first、payment-a-second 的 amount_cents 从 10000 改为 105；1 条账单、2 条支付 | fixture-override；verification.fixture_delta；准备前/后直接快照 | 通过 |
| 工具账单和支付金额 | 目标账单及两笔支付均 amount_cents=105、currency=CNY、amount_display=CNY 1.05 | sequence=3 output.data.invoice / payments | 通过 |
| 模型识别的支付和金额 | 重复支付为 payment-a-second，金额 CNY 1.05；没有将 105 分说成 105 元 | sequence=5；turns[0].answer，全文见下 | 通过 |
| 提案工具与实际 ID | 未调用 propose_refund；模型明确说“目前我还没有创建提案”；没有真实 proposal ID/approved 返回 | sequence=2 仅请求两个查询；sequence=5 tool_calls=[] | 未执行（模型未调用，样本未完成） |
| 应用待确认列表 | 首轮结束后返回“你>”，没有真实待确认提案列表 | 命令日志步骤 6；只有两个查询工具结果 | 未执行（没有提案） |
| 确认前退款和工单 | db-initial / db-before 均退款 0 条、工单 0 条 | 两份直接快照；checks.no_refunds_or_tickets_all_task_phases | 通过 |
| 确认前四表保护 | 账单 3、支付 5、退款 0、工单 0；db-initial 与 db-before 逐行一致 | checks.initial_equals_before=true | 通过 |
| YES 界面对象与金额 | 未进入 /approve，未输入 YES，没有确认界面输出 | 实际输入日志只有原文和 /exit | 未执行 |
| human_approval 与创建顺序 | 没有 human_approval、create_refund 或 record_ticket 事件 | 全部 5 个 events；checks.observed_no_proposal_or_write_calls / observed_no_human_approval | 未执行 |
| 批准后退款数量、金额、状态 | 批准未执行；停止时退款 0 条，不能据此认定一条 105 分 pending 申请的终点达成 | db-stopped.refunds=[]；无 db-after / report-after-approval | 未执行 |
| 工单数量、状态及关联 | 未创建工单，无 recorded 和 refund_id 实际值 | db-stopped.tickets=[] | 未执行 |
| 停止时原数据及 tenant-b | db-stopped 与准备后的 db-initial 四表完全一致；tenant-b 在准备前至停止时也没有变化 | checks.initial_equals_stopped / tenant_b_unchanged_even_during_fixture=true | 通过（停止时） |
| 首轮回复与状态一致性 | 金额/对象正确，明确没有提案，没有声称申请或工单已创建，也没有声称到账；中英混合原文保留 | sequence=5；db-stopped | 通过（仅首轮） |
| 批准后的最终回复 | 未进入批准后阶段，只有一轮回复 | turns 数量为 1 | 未执行 |
| 工具错误及额外输入 | get_invoice 和 get_refund_policy 均 ok=true；无模型错误/预算耗尽；模型追问后未追加回复或重试 | sequence=3、4、5；user_messages 仅原样任务；执行日志 | 通过（查询及停止规则） |
| 退出、源码和历史保护 | /exit 返回退出码 0；56 份登记历史文件、10 个源码/样例哈希未改变 | 退出日志；verification.preserved_files_changed / source_files_changed 均 [] | 通过 |
| 缺少提案的根因 | 可确定模型结束时未调用提案，不能证明其内部原因或非整元金额是否影响了该选择 | 本次单一样本，无因果验证 | 证据不足 |

停止前模型回复全文（report-stopped.turns[0].answer，原样保留）：

```text
I've found the invoice and its payment records. Let me review the situation:

**Invoice invoice-a-double** (tenant-a, customer-a):
- Amount: **CNY 1.05**
- Two successful payments, both for the full amount:
  1. **payment-a-first** — CNY 1.05, paid 2026-09-01T01:00:00Z
  2. **payment-a-second** — CNY 1.05, paid 2026-09-01T01:05:00Z

According to the refund policy (refund-lab-v1), this qualifies as a duplicate charge: same tenant, same invoice, exactly two successful full payments with the same currency, and the later one (payment-a-second) is the duplicate.

Before proceeding, I need to confirm the specific payment and amount with you.

---

**请确认以下退款信息：**

- **账单：** invoice-a-double
- **重复支付（待退款）：** payment-a-second
- **金额：** CNY 1.05
- **币种：** CNY

这笔支付是同一账单上的第二笔成功全额支付，符合重复扣费规则。

请使用 **`/approve 提案ID`** 进行本地确认。不过目前我还没有创建提案——请先确认以上支付对象和金额是否正确，我将据此创建退款提案供您审批。

请问以上信息是否正确？
```

## 归因与未确定事项

- 已确定事实：105 分的准备数据正确，查询工具展示 CNY 1.05，模型识别了 payment-a-second 和相同金额；模型请求先进行自然语言确认，却没有生成可操作提案，故按规则停止。
- 待验证假设：本次与 A-2 都观察到“查询后没有提案”的现象，但不能据此确定模型内部原因，也不能认定由金额修复或 105 分变体引起。
- 缺少哪些证据：已执行部分的任务输入、交互输出、版本/指纹、准备记录、直接快照和报告均已保存。提案返回、YES 界面及批准后结果未产生，原因是未执行，并非录制遗漏。
- 下一步最小行动：由用户确认本次“非整元金额检查通过，整体未完成”的记录。若继续定位提案遗漏，应保留本样本并另存后续验证，不修改原始输入或覆盖本轮结果。
- 确认记录：用户已授权执行 B-1；截至本文生成，用户尚未确认本次结论。

## 本用例结论

- 业务状态：确认前及停止时退款和工单均为 0，数据保护初核通过；一份 pending 申请及关联工单的业务终点未达成。
- 工具调用与确认：两次查询初核通过；提案、本地确认、退款申请和工单创建未执行。
- 最终回答：仅首轮金额、对象和未创建状态初核通过；批准后最终回答未执行。
- 本用例综合结论：**未完成（首轮缺少提案），待用户确认。非整元金额检查通过不等于 B-1 全流程通过。**
- 失败/未完成区分：未发现已执行阶段的金额冲突或工具报错；缺提案按本用例明确规定归为未完成。后续步骤归为未执行，根因归为证据不足。
- 计数口径：本记录只含 B-1 一个实际样本，0 个完整通过、1 个未完成；保留在已执行样本中，不补跑覆盖，也不用于推断生产稳定性。
- 证据完整性/参考等级：参考 B 级，仅支持本地已执行部分；没有真实支付链路证据。
- 未覆盖：B-1 批准与创建链路、真实退款到账、只读角色、跨租户请求、主动跳过确认、幂等/超时、工单失败、广泛金额/币种边界与其他模型异常。
- 发布范围：只评价 B-1；不自动关闭 AQL-001、不形成生产发布结论，不改变 A-1/A-2/A-3 的记录。

## 公开前检查

本记录按 [原模板](refund-record-template.md)另存，模板、代码和历史记录未改。仅在 B-1 新库中进行了文档规定的三处金额准备。本轮未读取或输出 .env/密钥，未上传 GitHub 或修改缺陷状态。证据位于本地 .local/；公开前应核对模拟数据及本机路径，再转存到独立 evidence 目录并调整链接。

停止后原始报告 SHA-256：`3c76a8ae4c6d5c1186ec09b8a15133680dd98f30107d0bba944e72040fc3fd7e`。归档后的只读核验命令及输出另存 [artifact-verification.json](../../evidence/2026-09-05/aql-001-regression/20260905T081125-04c9e44e/artifact-verification.json)；不重新执行模型或业务。
