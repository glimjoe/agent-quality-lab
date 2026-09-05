# TC-F-001：批准前金额错误的公开证据

执行版本：`3af890009e53824b8975d367ef86fa09fbc019fa`。真实模型：`deepseek-v4-flash`。运行标识：`20260905T052309-7da2d0df`。

**本次失败**：模型将 10000 分写成 10000 CNY；正确金额为 100.00 CNY。批准后的步骤未执行。退款和工单均为零，四张表在已执行区间内未变化。参见[结论](../../../docs/practice/TC-F-001-20260905-7da2d0df-conclusion.md)、[执行记录](../../../docs/practice/TC-F-001-20260905-7da2d0df.md)和[命令附录](../../../docs/practice/TC-F-001-20260905-7da2d0df-commands.md)。

## 文件与复核

- [report-before-approval.json](report-before-approval.json) 与 [report.json](report.json)：模型原话、工具调用、参数、返回与状态；两份报告内容一致。
- [db-initial.json](db-initial.json)、[db-before.json](db-before.json)、[db-stopped.json](db-stopped.json)：任务前、首轮完成、退出后的直接数据库快照。停止快照不是批准后证据。
- [verification-checks.json](verification-checks.json)：本次零写入、快照与事件核对，不能解释为用例综合通过。
- [command-log.json](command-log.json)：11 条实际命令、输入或读取输出的记录。第一条是已标注的转录，其余来自工具返回。
- [artifact-operations.json](artifact-operations.json)：文档整理命令及失败记录；整理过程未重新运行模型。
- [source-sha256.json](source-sha256.json)：执行时的源码与需求文件指纹，保留历史值，不表示修复后的版本。
- [manifest.json](manifest.json)：每份 JSON 的本地原始 SHA-256 和公开副本 SHA-256；两者差异用于说明脱敏变换。

## 公开处理

用户授权去除敏感信息后公开。检查了本地配置中已知凭据、常见 API/PAT Token、Bearer 值、私钥和带凭据 URL，以及当时可达 Git 历史的 61 个文件对象。未发现真实密钥。扫描中两个误报已人工确认：`example.invalid` 的负向测试 URL、环境变量 `GIT_CONFIG_KEY_*` 中的配置项名称；它们不属于真实凭据。

公开副本将本机仓库路径替换为 `<REPO>`、用户目录替换为 `<USER_HOME>`；文档正文证据链接改到本目录。命令占位符需换成本机路径，代码围栏内原执行时的相对链接仅作为历史输出保留。原始文件仍在本地；SQLite 二进制库不上传，公开的是三份四表 JSON 快照。

这些处理不修改业务 ID、金额、模型错误原话、调用次序、失败信息或未执行状态。运行目录名、模拟租户及支付标识用于证据关联，保留原值。历史记录中的“尚未发布”描述的是整理当时；本目录及文档中的公开版说明记录本次归档，不重写旧执行事实。

公开证据仅支持本地模拟场景下这一次失败，参考 B 级；不代表真实支付链路、完整退款流程或稳定性通过。
