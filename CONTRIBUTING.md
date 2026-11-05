# 参与 open-hidpi / Contributing

这个项目公开有限设备上的实现，欢迎大家共同扩展验证范围。无需先会使用 AI，也无需提交代码才能参与。

## 求助、反馈或设备验证

通过仓库的 Issue 模板提交：芯片、macOS 版本、显示器型号、连接方式／扩展坞、原生尺寸和刷新率、目标桌面尺寸，以及现象、操作步骤、预期和实际结果。说明是否曾使用其他显示配置工具。

日志只附与问题相关的脱敏片段。不要上传完整 `state.json`、原始系统报告或恢复备份；它们可能包含身份字段。公开范围以 [隐私说明](docs/PRIVACY.md) 为准。

当前二进制仅允许 M1 Pro。其他芯片可以先提“设备适配／求助”Issue，交流只读诊断和适配方案；不要为了运行而自行删掉检查后直接安装。

## 使用 AI 协助

[README](README.md) 提供可复制的任务说明。让 AI 先读项目、比较设备差异，再提出只读诊断。AI 的解释或改动建议不构成兼容性证明；提交时注明哪些结论来自实测，哪些只是推断。

## 提交 PR

1. 说明具体问题、改动、适用设备及已知限制；避免夹带无关重构。
2. 按 [开发说明](docs/DEVELOPMENT.md) 完成与改动相关的离线检查。文档变更无需重编译；Swift 变更需要构建和相应检查。
3. 新设备适配先解释与现有 M1 Pro 路径的差异，包括私有 API、目标渲染尺寸及恢复方式。单纯解除芯片限制不能作为适配完成。
4. 硬件验证需设备所有者明确同意。记录测试的提交、设备／系统／连接、原状态、步骤、实际桌面与渲染尺寸、刷新率、恢复结果和未测项目。切换、安装、恢复、拔插、睡眠、重启各自单独报告，不能互相代替。
5. 公开日志前脱敏。没有实机条件的改进仍可提 PR，明确标注“未实机验证”。

提交贡献表示你有权提供相关内容，并同意以本项目 MIT 许可证分发自己的贡献；保留引用或复用部分的原有署名与许可证。

## English

Open an issue with your chip, macOS version, monitor model, connection/dock, native resolution and refresh rate, desired desktop size, steps, and actual result. AI use is optional. Share only redacted, relevant diagnostics; do not upload raw system reports, state files, or recovery backups.

For a PR, explain the problem, scope, device differences, checks performed, and remaining uncertainty. Follow the [development guide](docs/DEVELOPMENT.md). A successful build or removal of the M1 Pro guard does not establish compatibility. Hardware changes need the device owner's consent. Report mode switching, installation, restoration, hotplug, sleep, and reboot separately, including the tested commit and rendering dimensions. Untested changes are welcome when clearly labeled.

You must have the right to submit your contribution and agree to distribute your own contribution under MIT, while preserving applicable third-party notices.
