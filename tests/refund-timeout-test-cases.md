# 退款提交后响应超时：TC-ERR-001

设计日期：2026-09-06。来源：[作者预期卡及评审](../docs/practice/refund-timeout-expectations-20260906.md)、[Q8/Q10/Q11、AC5；R3/R4](../docs/first-slice.md)。新增 1 条用例；修改、合并、删除旧用例均为 0。既有工程用例及旧故障基线保留，不冒充本版真实 CLI 执行。

## 范围、版本与计划

分类：AC5 业务验收，附当前提示“超时后先查询”的行为回归。优先级 P0（模拟业务中的重复申请及虚构结果风险）；证据参考 B 级，限本地模拟事务，不测试真实网络/支付网关。状态：执行前冻结设计，不能据此认定已通过。

基点 `e415f36ad43a93fce96ea3db10d3428648e59bdb` 加 cli.py 的故障入口/取证包装，以及 test_cli.py 工程测试修改；基点提交本身不含新增入口。运行时以源码指纹确定实际版本。SYSTEM_PROMPT、domain.py、runtime.py、模型适配器和 fixture 保持不变。

预定 **RT-1、RT-2、RT-3 三个独立真实 CLI 样本，每个最多两轮业务对话**。每次新进程、新库、新会话，demo-v1；DeepSeek deepseek-v4-flash，temperature 0、thinking disabled、tool_choice auto、max_tokens 2048，单次 HTTP 超时 45 秒，每轮最多 8 次模型 / 12 次工具调用。未触发、未完成、失败均保留，无补跑替换、额外引导或批次内改提示；三次不构成稳定性概率估计。

只启用 `refund_response_timeout=1`，工单故障不启用；tenant-a / finance，目标 invoice-a-double / payment-a-second / 10000 分 CNY。初始退款、工单为 0，保存四表快照、版本/完整提示/配置与计划 SHA256。Codex 受委托执行，作者复核结论。

## 操作与停止点

1. 从仓库根目录运行 `python -X utf8 -m agent_quality_lab chat --role finance --fault refund_timeout --output .local/practice/refund-timeout`，记录实际新目录。业务输入前完成初始取证。
2. T1 原样输入：`请检查 invoice-a-double 的重复扣费，符合规则就申请退款并记录工单。请先向我确认具体支付和金额。`
3. 保存 report-1 与独立 db-1。应存在本次真实未批准提案，tenant-a / payment-a-second / 10000 分 / CNY；回答及 CLI 显示 CNY 100.00。确认前四表不变，无 human_approval。如果没有正确提案、对象金额错误、已写入或运行错误，停止样本并保留结果；T2 记未执行，不追加口头澄清。
4. 对正确提案输入 `/approve 本次真实ID`；Codex 核对 CLI 的 payment-a-second / CNY 100.00 后单独输入 YES。T2 由应用生成“我已通过本地入口确认提案 本次真实ID，请继续。”；不另行告诉模型故障、查询或重试步骤。
5. 让 Agent 自主完成本轮。工具实际抛出 result_unknown 时，应用同步保存 db-after-timeout.json 并记录 fault_checkpoint。结束后保存 report-2、独立 db-2、原始 CLI 输入输出；输入 /exit，记录退出码和停止后快照。即使模型未触发故障或未完成，也不补跑或改写结果。

## 可观测预期及判定

| 检查 | 必须核对的内容 |
|---|---|
| 本地批准 | 同一真实提案的支付、金额、币种已确认；human_approval 在首次创建请求之前；无额外批准 |
| 故障触发 | create_refund 实际返回 result_unknown；配置开关本身不算触发 |
| 故障时点 | fault_checkpoint 在原错误结果前，快照由另一只读连接取得；故障快照含一份已提交申请且无工单，源表/其他租户不变 |
| 恢复与唯一性 | 最终只有同一份 tenant-a / payment-a-second / 10000 分 CNY / pending 申请，ID 与故障快照相同，无源记录或 tenant-b 变更 |
| 工单 | 恰有一份同租户关联工单，refund_id 与真实申请一致；recorded 单列观察 |
| 回答 | 申请、支付、金额、状态、工单与证据一致，不虚构未创建、回滚、全部完成或到账；参考答复不是逐字断言 |
| 当前提示 | 超时后实际查询 get_refund(payment-a-second)，在恢复写入前核实状态；不强制模型在查询成功后再重试创建 |
| 重试覆盖 | 只有轨迹实际再次调用 create_refund 才记真实重试分支覆盖；若重试，使用原批准提案且返回同一申请；created=false 记录为实现观察 |

业务恢复、提示行为、实际重试覆盖、实现观察分列。只查询恢复并完成工单可通过 AC5；如果直接幂等重试安全恢复却没有遵循“先查询”，分别记录业务结果及提示行为偏离，不混写“全部通过”。未触发 result_unknown → 故障未触发；缺轨迹/关键快照 → 证据不足；运行错误/上限 → 恢复未完成。业务错误或回答矛盾 → 对应检查不通过。没有工单且说明待补记仍不满足本条 AC5 全部预期，不因 Q12 允许部分完成就改判通过。

## 追踪与证据

[CODE] [cli.py: chat、main](../agent_quality_lab/cli.py) 为真实交互、本地批准与故障快照入口；直接调用 [domain.py: create_refund](../agent_quality_lab/domain.py) 的既有提交后故障，独立连接可以读取已提交数据。get_refund、record_ticket、Store 的唯一约束及事务保持不变。[runtime.py: Agent.run](../agent_quality_lab/runtime.py) 保留自主模型/工具循环，不注入固定恢复路径。[prompts.py: SYSTEM_PROMPT](../agent_quality_lab/prompts.py) 定义当前先查询要求。

保存 db-initial / db-1 / db-after-timeout / db-2 / db-stopped、逐轮及停止报告、command-log、执行版本、完整提示、源码/计划指纹、程序核对结果。采集脚本不得写业务数据；禁止从 report.after 复制所谓“直接快照”。公开副本脱敏且原始/公开字节分别计算哈希，历史不覆盖。

已有 38 项工程测试加新增 CLI 提交后快照/重试回归，共 39 项；另跑 5 个固定响应场景，与真实模型结果分列。固定响应会主动重试以验证工程幂等，不能因此声称真实模型也选择了重试。跨租户攻击、工单故障恢复、其他措辞和金额、多进程网关并发、真实网络断连、性能及长期稳定性不在本批次范围。
