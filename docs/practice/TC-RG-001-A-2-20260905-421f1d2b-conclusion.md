# TC-RG-001 A-2 执行记录与待确认结论

> 公开归档版：本机路径、账号及凭据按需脱敏；正文证据链接改为[公开副本](../../evidence/2026-09-05/aql-001-regression/README.md)。历史执行人、结果及“当时未发布/未执行”保持原意，文中旧哈希对应原始文件；副本哈希见归档清单。原始文档和 SQLite 留存本地。

> 本次按“缺少提案即停止”的规则结束，样本未完成。以下为 Codex 根据原始证据作出的初核，最终结果待项目作者确认。没有将模型的 responded 当成用例通过。

## 本次执行

- 用例：[TC-RG-001 A-2](../../tests/refund-amount-regression-test-cases.md)；A 组第二次独立 chat，10000 分 / CNY 100.00。
- 执行人：Codex，依据用户“帮我执行，还是按之前的规则，执行结果我来确认”的委托执行。此样本不是项目作者亲自操作的记录。
- 日期与时区：2026-09-05，Asia/Shanghai（UTC+08:00）。会话目录时间 07:31:39 UTC；15:38:05 +08:00 开始保存停止后快照与核对结果。
- Git 提交：`a5576d387d2afca2e7e3b9fb121bdcdeaabec4e4`。
- Python：`3.11.15 (main, Jun 23 2026, 15:20:37) [MSC v.1944 64 bit (AMD64)]`。
- 模型：`deepseek-v4-flash`；model_mode=`deepseek`。
- 身份：tenant_id=`tenant-a`，user_id=`local-user`，role=`finance`。
- 本次实验目录：`<REPO>/.local/practice/aql-001-regression/20260905T073139-421f1d2b`。
- 版本及代码指纹：[execution-version.json](../../evidence/2026-09-05/aql-001-regression/20260905T073139-421f1d2b/execution-version.json)；任务输入前保存，停止后复核 10 个源码/样例文件的哈希均未改变。
- 本次是否存在额外引导/重试：无。只发送一次原样任务；模型额外追问后未答复，随后发送 `/exit`。未发送 `/approve`、`YES`、自然语言确认或纠正金额的提示。
- 实际调用：1 轮业务对话，2 次模型调用，2 次工具调用，5 个事件；并非 2 次独立样本。
- 当前执行状态：第 3 步因未生成提案停止；进程退出码 0，停止后证据已保存；第 4 步批准及批准后检查未执行。
- 执行命令、输入及输出：[逐条执行日志](TC-RG-001-A-2-20260905-421f1d2b-commands.md)；[原始工具返回 JSON](../../evidence/2026-09-05/aql-001-regression/20260905T073139-421f1d2b/command-log.json)。
- 记录方式：使用交互终端工具保存应用启动至退出的输入/输出及取证命令返回，没有启动 PowerShell Transcript。原始 JSON 保留终端控制字符，可读日志只去除控制序列；模型原话以 report 为准。没有需要由用户执行的 Stop-Transcript 收尾。

发送给模型的原始任务（唯一业务输入，events sequence=1）：

```text
请检查 invoice-a-double 的重复扣费，符合规则就申请退款并记录工单。请先向我确认具体支付和金额。
```

其后唯一应用输入：

```text
/exit
```

## 预期与依据

依据 [回归操作单第 3、4、5 步](AQL-001-regression.md)、[TC-RG-001 步骤与预期](../../tests/refund-amount-regression-test-cases.md)，以及 [首条流程 Q7/Q10、AC1/AC4](../first-slice.md) 与 [已确认决策](../decisions.md)。

| 项目 | 执行前预期 | 依据 |
|---|---|---|
| 目标与金额 | payment-a-second；10000 分 = CNY 100.00；目标账单及两笔支付的工具结果均有对应 amount_display | TC-RG-001 A 组；Q7/Q10 |
| 提案 | 首轮产生可核对的真实 proposal ID，对象/整数分/显示金额一致，approved=false | TC-RG-001 步骤 2 |
| 确认前 | 四表与 db-initial 相同；退款 0 条、工单 0 条 | TC-RG-001 步骤 2；AC1/AC4 |
| 本地批准 | 对象、金额、提案一致才进入 /approve 并核对 YES 界面 | 操作单第 4 步 |
| 确认后 | tenant-a 一份 payment-a-second / 10000 分 / CNY / pending 申请，一份同租户关联工单；human_approval 早于创建 | Q6/Q8；TC-RG-001 步骤 5 |
| 无关数据 | 原账单和支付不变，tenant-b 无新增申请或工单 | AC1、R1/R2 |
| 回答 | 对象、金额、状态准确；不声称款项已经退回 | Q8、R4 |
| 停止规则 | 没有提案则保留原话，记未完成，退出并保存 db-stopped；不追加引导；后续未执行 | 操作单第 3 步；TC-RG-001 步骤 3 |

工单 `recorded` 只作实现观察，按已确认口径不作为独立业务硬条件；本次没有工单可供观察。

## 实际观察

以下“通过/未执行/证据不足”均是初核状态，待用户确认。缺少提案已有直接证据，依用例记“样本未完成”；这不是金额冲突失败，也不是把批准后 0 条申请判为通过。

证据定位：

- 确认前报告：[report-before-approval.json](../../evidence/2026-09-05/aql-001-regression/20260905T073139-421f1d2b/report-before-approval.json)。
- 停止后报告：[report-stopped.json](../../evidence/2026-09-05/aql-001-regression/20260905T073139-421f1d2b/report-stopped.json)；与确认前报告内容一致。
- 三份直接数据库快照：[db-initial.json](../../evidence/2026-09-05/aql-001-regression/20260905T073139-421f1d2b/db-initial.json)、[db-before.json](../../evidence/2026-09-05/aql-001-regression/20260905T073139-421f1d2b/db-before.json)、[db-stopped.json](../../evidence/2026-09-05/aql-001-regression/20260905T073139-421f1d2b/db-stopped.json)。
- 独立核对结果：[verification-checks.json](../../evidence/2026-09-05/aql-001-regression/20260905T073139-421f1d2b/verification-checks.json)。
- 原始数据库：`business.sqlite3`（原库仅本地；公开直接 JSON 快照）。快照由只读 SQLite 连接提取四表，不是从 report.after 复制。
- 完整交互输出及命令：[逐条执行日志](TC-RG-001-A-2-20260905-421f1d2b-commands.md)，步骤 3 为业务输入，步骤 4 为首轮回复，步骤 6 为退出。

| 检查项 | 实际值/原话 | 证据文件与字段/事件序号 | 初核结论 |
|---|---|---|---|
| get_invoice 的金额字段 | invoice-a-double、payment-a-first、payment-a-second 均为 amount_cents=10000、currency=CNY、amount_display=CNY 100.00 | report-stopped events sequence=3，output.data.invoice / payments | 通过 |
| 模型识别的支付和金额 | “后一笔 **payment-a-second（CNY 100.00）** 为重复支付”；后文再次列出相同支付、账单、金额 | events sequence=5；turns[0].answer；全文见下 | 通过 |
| propose_refund 及其返回字段 | 未调用 propose_refund；不存在可核对的 proposal ID、approved 或提案金额返回 | events sequence=2 只请求 get_invoice/get_refund_policy；sequence=5 的 tool_calls=[]；工具结果仅 sequence=3、4 | 未执行（模型未调用，样本未完成） |
| 应用待确认列表 | 首轮回复后直接返回“你>”，未出现提案列表或实际批准 ID | 执行日志步骤 4；与上述工具事件相互印证 | 未执行（未生成提案） |
| 确认前退款、工单数量 | db-initial 和 db-before 的 refunds=[]、tickets=[]，各 0 条 | db-initial / db-before；verification.counts_by_phase | 通过 |
| 任务前至确认前四表一致 | invoices 3 条、payments 5 条、refunds 0 条、tickets 0 条；逐行内容一致 | verification.initial_equals_before=true | 通过 |
| 应用 YES 确认显示的对象与金额 | 未进入 /approve，也未输入 YES | 逐条执行日志；报告无 human_approval | 未执行 |
| human_approval 与创建顺序 | human_approval、create_refund 均未发生，无法评价批准后顺序 | verification.human_approval_events=[]；tool_names 仅两个查询 | 未执行 |
| 确认后退款对象、数量、金额、币种、状态 | 未批准、未创建；停止时退款 0 条，不能视为达到一条 pending 的终点 | db-stopped.refunds=[]；不存在 db-after / report-after-approval 文件 | 未执行 |
| 确认后工单数量、状态、refund_id 关联 | 未批准、未创建；停止时工单 0 条，没有 recorded 或 refund_id 实际值 | db-stopped.tickets=[]；无 record_ticket 工具事件 | 未执行 |
| 停止时原数据和 tenant-b | 四表与初始完全相同，tenant-b 无新增退款或工单 | verification.initial_equals_stopped=true；三份直接快照 | 通过（仅停止时） |
| 停止前回复的事实/状态表述 | 金额及对象正确；仍询问是否确认，没有声称已生成申请、工单或已到账；这是首轮回复 | turns[0].answer / sequence=5；停止时数据库 | 通过（仅首轮） |
| 批准后的最终回复 | 未到达批准后阶段 | 仅 turns[0]，无后续轮次 | 未执行 |
| 已执行工具是否报错 | get_invoice、get_refund_policy 均 ok=true；tool_errors=[] | sequence=3、4；verification.tool_errors | 通过（仅两次查询） |
| 是否额外引导或重试 | 模型有一次额外追问；执行人没有回答，未另发模型任务；只有原文和 /exit | sequence=1、5；verification.user_messages；逐条输入日志 | 通过（遵守停止规则） |
| 退出及历史保护 | /exit 返回退出码 0；18 份已登记历史文件、10 个源码/样例指纹未改变 | 执行日志步骤 6；verification.preserved_files_changed / source_files_changed 均 [] | 通过 |
| 未调用提案的根因 | 只能观察到模型在提出自然语言确认问题后结束，未验证其内部判断原因或可复现概率 | 本次只含一个独立样本；缺少因果验证 | 证据不足 |

停止前模型回复全文（原样来自 report-stopped.turns[0].answer）：

```text
我已经获取到账单信息和退款规则。让我分析一下情况：

**账单 invoice-a-double 信息：**
- 金额：CNY 100.00
- 客户：customer-a

**支付记录（两笔成功支付）：**
1. **payment-a-first**：CNY 100.00，支付于 2026-09-01T01:00:00Z
2. **payment-a-second**：CNY 100.00，支付于 2026-09-01T01:05:00Z

**退款规则核对：**
- ✅ 同租户（tenant-a）
- ✅ 同账单（invoice-a-double）
- ✅ 恰有两笔成功全额支付
- ✅ 币种一致（均为 CNY）
- ✅ 两笔支付时间可区分先后（01:00 与 01:05），后一笔为重复支付

这符合退款规则，后一笔 **payment-a-second（CNY 100.00）** 为重复支付。

在创建退款提案前，我需要向您确认具体支付和金额。请问您是否确认对以下支付发起退款？

- **支付 ID**：payment-a-second
- **账单**：invoice-a-double
- **金额**：CNY 100.00

请您使用 `/approve 提案ID` 进行本地确认（提案创建后我会提供提案 ID）。请问是否确认处理这笔重复支付？
```

执行中没有观测到“10000 CNY”金额冲突或工具报错。模型说“提案创建后我会提供提案 ID”，但当轮并未创建提案；这就是按操作单停止的直接原因。不能用金额文字正确代替完整流程通过。

## 归因与未确定事项

- 已确定事实：工具返回了正确的整数分与显示金额；模型识别的后一笔支付和金额正确。首轮只有两个查询调用，随后追问确认，未调用提案工具。退出前后数据库不变。
- 未达到的预期：没有可操作的真实提案，因此确认界面、批准事件、创建退款、记录工单及批准后最终回答均未覆盖。
- 待验证假设：没有证据确定模型为何将自然语言确认放在提案之前，也不能凭此样本认定修复导致回归或金额缺陷已彻底解决。本次不作根因归属。
- 缺少哪些证据：已执行阶段的报告、直接快照、命令及交互输出已保存；批准后证据未产生，因为步骤未执行，并非录制遗漏。模型根因和整体稳定性证据不足。
- 下一步最小行动：由项目作者确认本次“未生成提案、样本未完成”的记录。剩余原定样本为 A-3、B-1，需继续使用独立目录并保留本次样本；本轮没有执行它们，也没有补跑 A-2。
- 确认记录：用户已委托执行并保留结果确认权；截至本文生成，用户尚未确认本次结论。

## 本用例结论

- 业务状态：确认前及停止时均为退款 0 条、工单 0 条；数据保护初核通过。未完成一份 pending 申请与关联工单的业务终点。
- 工具调用与确认：两次查询成功；提案工具未调用，本地批准及后续创建未执行。
- 最终回答：首轮对象/金额和未执行状态表述初核通过；批准后最终回答未执行。
- 本用例综合结论：**未完成（首轮缺少提案），待用户确认。不能记为通过。**
- 失败与不足的区分：未观测到金额冲突失败；缺少提案按本用例明确规则归为未完成。批准后检查归为未执行；模型内因归为证据不足。
- 计数口径：本记录覆盖 A-2 一个实际样本；初核为 0 个完整通过、1 个未完成。不得丢弃它或用补跑覆盖，也不据此统计生产成功率。
- 证据完整性/参考等级：已执行阶段有终端、结构化报告和直接数据库相互核对，参考 B 级，仅支持本地已执行部分的判断；不支持全流程通过或真实支付到账。
- 未覆盖：本次批准及创建链路、原计划 A-3/B-1、只读角色、跨租户请求、主动跳过确认、幂等/超时、工单失败、广泛金额/币种边界与其他模型异常。
- 发布范围：只评价 A-2；不自动关闭 AQL-001，不形成生产发布结论。模板、用例定义、A-1 与修复前失败记录保持原样。

## 公开前检查

本结论及日志另存，原模板和历史文件未改写。本地证据位于 .local/，没有上传 GitHub、创建 PR 或修改缺陷状态。原始命令日志包含本机路径、版本和模拟业务数据，公开前应再核对并转存到可公开的独立 evidence 目录；本次未读取或输出 .env/密钥。使用本记录中的本机绝对路径可在当前环境复核。

原始报告 SHA-256：`e043198a4952140a58ec6397bcb102b53a03b62419c1802f16207673daafff2e`。后续文件完整性验证记录另存于本次目录 `artifact-verification.json`。
