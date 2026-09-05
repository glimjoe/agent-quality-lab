# AQL-002 提示修复后的真实 CLI 证据

2026-09-05，执行人 Codex，受用户委托核对界面并输入 `/approve` 和 `YES`；本轮限定结论已获项目作者复核确认。[回归报告](../../../docs/practice/AQL-002-regression-20260905.md)与[执行前计划](../../../tests/proposal-flow-regression-test-cases.md)定义判定范围。

作者回复“已复核确认”的来源与范围见[确认记录](../../../docs/practice/AQL-002-regression-20260905.md#作者确认记录)。归档 JSON 的复核状态字段（如 user_confirmation、project_author_confirmation）中的 pending 反映文件生成时的状态，保留原始字节及哈希；当前复核状态以该记录为准。退款业务状态 pending 仍表示申请创建。

| 样本 | 金额/身份 | 阶段报告 | 直接最终快照 | 独立核对 | CLI 命令与输出 |
|---|---|---|---|---|---|
| C100-1 | CNY 100.00，finance | [report](C100-1/report.json) | [db](C100-1/db-stopped.json) | [checks](C100-1/verification-checks.json) | [log](C100-1/command-log.json) |
| C100-2 | CNY 100.00，finance | [report](C100-2/report.json) | [db](C100-2/db-stopped.json) | [checks](C100-2/verification-checks.json) | [log](C100-2/command-log.json) |
| C100-3 | CNY 100.00，finance | [report](C100-3/report.json) | [db](C100-3/db-stopped.json) | [checks](C100-3/verification-checks.json) | [log](C100-3/command-log.json) |
| C105-1 | CNY 1.05，finance | [report](C105-1/report.json) | [db](C105-1/db-stopped.json) | [checks](C105-1/verification-checks.json) | [log](C105-1/command-log.json) |
| C105-2 | CNY 1.05，finance | [report](C105-2/report.json) | [db](C105-2/db-stopped.json) | [checks](C105-2/verification-checks.json) | [log](C105-2/command-log.json) |
| C105-3 | CNY 1.05，finance | [report](C105-3/report.json) | [db](C105-3/db-stopped.json) | [checks](C105-3/verification-checks.json) | [log](C105-3/command-log.json) |
| D-viewer-1 | CNY 100.00，viewer | [report](D-viewer-1/report.json) | [db](D-viewer-1/db-stopped.json) | [checks](D-viewer-1/verification-checks.json) | [log](D-viewer-1/command-log.json) |
| N-single-1 | 单笔支付，finance | [report](N-single-1/report.json) | [db](N-single-1/db-stopped.json) | [checks](N-single-1/verification-checks.json) | [log](N-single-1/command-log.json) |

每份目录还包含执行版本、完整系统提示、准备前/任务前/批准前快照与报告。六个正常样本有批准后副本；两个边界样本没有批准步骤。所有样本最终退出码为 0，这只说明 CLI 正常退出，不能替代业务判定。工具返回、模型原话在 report.events / turns；command-log 保留实际输入输出及终端控制序列，阅读时优先核对这些结构化字段。

测试时 HEAD 为 `a5576d387d2afca2e7e3b9fb121bdcdeaabec4e4`，工作区已有 prompts.py 修改；**不能用这个提交号代表修复后的全部代码**。实际源码和完整提示见各 execution-version.json；新 prompts.py SHA256 为 `f9d2956a7104eb2c220118a6956a0c0e4decea8da400f59f6b33d3b37c2360a1`。其余包内源码和 fixture 与基线一致。[manifest](manifest.json)记录每个原始文件及公开副本的 SHA256，report 内的历史哈希没有重写。

[批次核对](batch-verification.json)和[样本目录映射](case-index.json)保留本地来源标识；`.local/...` 是来源位置，不是 GitHub 链接。[工程输出](engineering-tests.txt)为 38 项、零跳过；[5 份 scripted 报告](scripted/)仅验证固定响应链路，不计入真实模型样本。

[evidence_helper.py](tooling/evidence_helper.py)与[verify_batch.py](tooling/verify_batch.py)是当次使用的一次性取证脚本存档，不是新增应用接口。脚本原运行位置为 `<REPO>/.local/aql-002-work/`；它们依赖原始运行目录、case-index 和本地保存清单，拒绝覆盖既有证据。不要在本归档目录直接运行。复测正常业务用仓库 CLI 和[操作单](../../../docs/practice/AQL-001-regression.md)，每次新建目录。

公开副本仅作路径/账号等脱敏及 UTF-8/LF 规范化，数据库原件、原始日志和文档备份仍在本地。预定 8 个样本全部公开，没有择优删除或用重试替换。本批次仅覆盖模拟业务；D-viewer-1 仍有误导性的权限重试引导，详见报告，不能写为“8/8 综合通过”。
