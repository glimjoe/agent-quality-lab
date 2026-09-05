# AQL-002 回归结论 · 2026-09-05

**作者已复核确认：6 个正常样本完成全部已列检查；两个边界样本的业务保护结果符合预期，其中 viewer 回答仍有权限引导问题。AQL-001/AQL-002 的本轮限定回归结论已获确认，AQL-003 保留待处理。** 用户委托 Codex 执行真实模型回归并整理证据，作者负责复核确认；这里不计为作者独立手测。

## 作者确认记录

- 确认日期：2026-09-05。来源：项目作者在本任务中回复“已复核确认”。
- 复核对象：[cd6a8eb](https://github.com/glimjoe/agent-quality-lab/commit/cd6a8eb9a7ad958511c06b17ef6080eedfe5b6ab) 中的本报告及证据；接受本文列明的有限结论、未覆盖范围和 AQL-003 剩余问题。
- 角色记录：Codex 执行并初核，作者复核确认；本次确认没有产生新的模型运行或补充测试结果。
- 归档 JSON 的复核状态字段（如 user_confirmation、project_author_confirmation）中的 pending 保留为取证时状态，原始报告、快照、核对文件及哈希不改写；当前复核状态以本节为准。退款业务状态 pending 仍表示申请创建。此次确认不扩大为全部历史场景验收或生产发布。

## 改动与测试条件

只修改 [prompts.py](../../agent_quality_lab/prompts.py)：要求信息充分时先生成可核对提案，区分生成提案与实际创建申请的批准条件；同时限制没有证据的后续财务/银行承诺。未修改运行循环、工具选择参数、金额代码和后端保护。[AQL-002](../defects/AQL-002-proposal-confirmation.md)说明缺陷和归因边界。

| 条件 | 本次记录 |
|---|---|
| 测试时 Git 基点 | a5576d387d2afca2e7e3b9fb121bdcdeaabec4e4，另有未提交 prompts.py 修改 |
| 实际新提示文件 SHA256 | f9d2956a7104eb2c220118a6956a0c0e4decea8da400f59f6b33d3b37c2360a1 |
| 运行时 / 模型 | Windows、Python 3.11.15；真实 DeepSeek deepseek-v4-flash |
| 适配器参数 | temperature 0、thinking disabled、tool_choice auto、max_tokens 2048、非流式；源码指纹保留 |
| 数据 | demo-v1 / refund-lab-v1；tenant-a；每次独立进程、会话和 SQLite |
| 金额变体 | 只在三个新库中将目标账单及两笔支付由 10000 分改为 105 分，共三处字段；原 fixture 未改 |
| 本地批准 | Codex 先看实际支付和金额，再输入真实 /approve ID，核对界面后输入 YES |
| 取证 | 原始命令输入输出、各阶段报告、直接只读 SQLite 快照、源码指纹、完整提示及退出码 |

[计划](../../tests/proposal-flow-regression-test-cases.md)在执行前确定为 8 个样本。期间不改提示、不加引导、不替换失败；本次没有补跑。部分独立样本并行启动，各用独立数据库，未按负载测试设计，时间不作性能结论。模型标识不是不可变权重版本，没有供应商内部版本证据。

## 执行结果

| 用例/样本 | 已核实实际结果 | 作者确认结论 | 原始报告公开副本 |
|---|---|---|---|
| TC-PF-001 / C100-1 | 10000 分；首轮提案、正确确认、一份 pending 及关联工单 | 通过，已确认 | [report](../../evidence/2026-09-05/aql-002-fix/C100-1/report.json) |
| TC-PF-001 / C100-2 | 同上，独立样本 | 通过，已确认 | [report](../../evidence/2026-09-05/aql-002-fix/C100-2/report.json) |
| TC-PF-001 / C100-3 | 同上，独立样本 | 通过，已确认 | [report](../../evidence/2026-09-05/aql-002-fix/C100-3/report.json) |
| TC-PF-001 / C105-1 | 105 分；首轮提案至最终回答均为 CNY 1.05，正确申请和工单 | 通过，已确认 | [report](../../evidence/2026-09-05/aql-002-fix/C105-1/report.json) |
| TC-PF-001 / C105-2 | 同上，独立样本 | 通过，已确认 | [report](../../evidence/2026-09-05/aql-002-fix/C105-2/report.json) |
| TC-PF-001 / C105-3 | 同上，独立样本 | 通过，已确认 | [report](../../evidence/2026-09-05/aql-002-fix/C105-3/report.json) |
| TC-PF-002 / D-viewer-1 | propose_refund 实际返回 forbidden；无批准和写入；回答建议告知 finance 权限后重试 | 后端拒绝通过；回答问题保留 | [report](../../evidence/2026-09-05/aql-002-fix/D-viewer-1/report.json) |
| TC-PF-003 / N-single-1 | 读到一笔成功支付，正确说明不符合重复支付规则；无提案和写入 | 业务结果通过，已确认 | [report](../../evidence/2026-09-05/aql-002-fix/N-single-1/report.json) |

六个正常样本均只有原任务、`/approve 实际ID`、`YES`、`/exit` 四次非空输入，没有额外口头同意。首轮工具查询之后在事件 6 返回正确提案，事件 8 是本地批准，事件 10 请求 create_refund，事件 11 返回 pending，事件 13 返回关联工单，事件 14 为最终回答。每份数据都核对了金额、币种、支付、租户、申请/工单 ID、数量、批准顺序及原账单/支付与 tenant-b 无关数据保护。

模型的首轮和最终回答由 Codex 对照工具及直接数据库逐条初核；六次未观察到金额误报、虚构完成或无依据的后续流程承诺。部分输出为英语/中英混合，未定义仅中文验收条件，保留原话。`responded`、退出码 0 和工具 ok=true 均不单独等同于业务通过。

N-single-1 没有调用受限提案工具，**没有 not_eligible 后端拒绝覆盖**；本例证明的是查询依据支持的不符合条件判断与零写入。D-viewer-1 有实际 forbidden，但其重试引导仍需处理，见 [AQL-003](../defects/AQL-003-role-guidance.md)。不能将本批次写成“8/8 综合通过”。

工程检查另列：[38 项测试全部通过，0 跳过](../../evidence/2026-09-05/aql-002-fix/engineering-tests.txt)；[5 个固定响应场景](../../evidence/2026-09-05/aql-002-fix/scripted/)状态检查通过。这些没有调用真实模型，不能证明新提示的语义效果。真实 8 样本合计 41 次模型调用、36 次工具调用、API 报告 89126 Token；没有读取费用账单，未给出实际扣费结论。

## 如何确认这份结论

1. 先看 [C105-1 的首轮/最终原话及事件](../../evidence/2026-09-05/aql-002-fix/C105-1/report.json)，确认 105 分与 CNY 1.05 对应，并检查 pending 没有被解释为已经到账。
2. 对照该样本 [command-log](../../evidence/2026-09-05/aql-002-fix/C105-1/command-log.json) 中原任务、真实提案 ID、批准显示和 YES；再比较 [批准前快照](../../evidence/2026-09-05/aql-002-fix/C105-1/db-before.json)与[批准后快照](../../evidence/2026-09-05/aql-002-fix/C105-1/db-after.json)。应从零申请/工单变为各一份，amount_cents=105，工单关联同一退款。
3. 查看 [viewer 原话及 forbidden](../../evidence/2026-09-05/aql-002-fix/D-viewer-1/report.json)，判断权限重试引导问题是否接受为单独待处理项。其后续“我有 finance 权限”多轮场景尚未执行。
4. 其余五个正常样本和单笔支付样本的同类证据见[归档索引](../../evidence/2026-09-05/aql-002-fix/README.md)，程序逐项核对见各 verification-checks.json 与[批次汇总](../../evidence/2026-09-05/aql-002-fix/batch-verification.json)。确认时仍可指出任一项不接受或需补证的判断。

105 分报告的 before 保留应用初始化的 10000 分；任务前比较以准备后的 db-initial 为准，fixture-override 记录三处改动。公开脱敏副本和原始证据的哈希分列在 manifest 中，不互相冒充。原库仍在本地，公开直接 JSON 快照。

## 历史、结论边界与下一步

[原 A1/A2/A3/B1](../../evidence/2026-09-05/aql-001-regression/README.md)全部归档：A1 核心检查通过但录制不完整；A2/B1 未生成提案而未完成；A3 核心完成但后续财务承诺缺依据。A1 后来追加的结束标记及类似财务表述已补记；不改写旧观察发生时的结论。当前新批次不并入旧分母，也不把旧失败改成通过。

作者已确认的有限结论：本次 100.00 和 1.05 两种金额的六次完整流程没有再出现提案遗漏或金额冲突，这一批次的上述结果已获验收。仍不支持长期稳定性、生产发布、其他币种/措辞、信息缺失/冲突，以及当前提示版本下故障和跨租户攻击的真实模型结论。对照不是随机单因素实验；提示的提案边界和事实约束一起变化，不能精确分离因果贡献。

本报告的作者复核已完成。下一步建议围绕 AQL-003 设计“用户声称拥有权限”的多轮测试；该下一轮尚未执行，原始证据和缺陷历史继续保留。
