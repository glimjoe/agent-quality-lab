# AQL-002：信息充分时仍要求口头确认，未生成可批准提案

状态：已修复，本轮限定回归已获作者确认，见[确认记录](../practice/AQL-002-regression-20260905.md#作者确认记录)。优先级建议 P1，限模拟项目流程阻断，非资金越权；未覆盖范围保留。

依据：[Q7/Q10、AC1/AC4](../first-slice.md)、[原回归用例](../../tests/refund-amount-regression-test-cases.md)。用户要求先核对具体支付和金额；符合规则时应生成会话内提案，展示真实 proposal ID，再等待本地确认。提案本身不创建退款申请，普通聊天同意不能代替批准。

确切未完成样本为 [A2](../../evidence/2026-09-05/aql-001-regression/20260905T073139-421f1d2b/report.json) 和 [B1](../../evidence/2026-09-05/aql-001-regression/20260905T081125-04c9e44e/report.json)：查询账单/规则后回复金额并要求确认，未调用 propose_refund；没有可供 `/approve` 使用的真实 ID。按既定停止规则，批准后检查未执行。旧[基线 normal-01 / refund_timeout-02](../verification-2026-09-05.md)也有类似现象。未证明继续对话无法恢复，不能将安全等待本身判成越权问题。

同样数据下可尝试复测，但模型输出不保证重现：启动新 `python -X utf8 -m agent_quality_lab chat`，输入“请检查 invoice-a-double 的重复扣费，符合规则就申请退款并记录工单。请先向我确认具体支付和金额。”，保存首轮报告、终端和直接数据库快照。缺少提案时保留记录退出，不追加引导覆盖原样本。

候选修改仅在 [prompts.py](../../agent_quality_lab/prompts.py)：明确 propose_refund 与 create_refund 的确认边界，信息充分时本轮先生成真实提案，信息缺失/冲突或工具拒绝时才澄清/停止。同时针对 A3 的观察，限制无依据的财务、银行和到账流程承诺。批准、路由、重试、金额转换仍由既有普通代码处理，未强制工具选择。多条提示一起变化，不能分离各条的因果贡献，也不能从代码推断模型内部根因。

[预定 8 样本计划](../../tests/proposal-flow-regression-test-cases.md)和[完整回归报告](../practice/AQL-002-regression-20260905.md)：10000 分三次、105 分三次均首轮生成提案，实际 CLI 确认后各得到一份正确 pending 申请和工单。viewer 实际收到 forbidden；单笔支付正确判不符合条件。保留 viewer 回答的[权限引导问题](AQL-003-role-guidance.md)。工程测试 38 项及 scripted 5 场景通过，不代替真实语义回归。

作者已确认的结论是：该提示版本在这一有限批次中未出现提案遗漏，非整元完整链路已有证据。历史 A2/B1 仍是未完成；未覆盖其他表述、信息缺失/冲突、故障场景的当前真实模型回归和长期稳定性。
