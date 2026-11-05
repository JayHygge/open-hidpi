# 项目结构 / Project layout

公开仓库保留使用工具、理解实现及参与贡献所需的文件。

| 路径 | 用途 |
| --- | --- |
| `README.md`、`README.en.md` | 中英文项目入口与 AI 适配任务说明 |
| `MacHiDPI/source/MacHiDPI.swift` | 唯一维护的 Swift 源码 |
| `MacHiDPI/MacHiDPI`、`*.command` | 程序与五个双击入口 |
| `MacHiDPI/使用说明.md` | 操作、修改范围与恢复方法 |
| `MacHiDPI/验证记录.md` | 已验证设备、结果与未测范围摘要 |
| `MacHiDPI/build.json`、`SHA256SUMS` | 构建关联与工具包文件校验 |
| `scripts/` | 构建、打包与隐私检查 |
| `tests/` | 贡献者可重复运行的离线回归测试；不修改显示设置 |
| `docs/DEVELOPMENT.md` | 开发与打包步骤 |
| `docs/PRIVACY.md` | 诊断数据与公开文件的隐私边界 |
| `CONTRIBUTING.md`、`.github/` | 贡献指南、Issue 表单和 PR 模板 |
| `LICENSE`、`THIRD_PARTY_NOTICES.md` | 项目许可与第三方声明；工具包内保留同名副本 |
| `release/` | 可下载 ZIP 与项目文件校验 |

五个双击入口依赖同目录二进制；源码不是运行依赖。工具包作为完整文件夹分发。生成与检查步骤以 [开发说明](DEVELOPMENT.md) 为准。

可重复运行的测试用于帮助他人及其 AI 验证源码修改；它们不包含个人测试输出。本机系统审计、逐次操作日志、交接档案、旧文档和研究原始材料不进入公开仓库或 ZIP。

The repository includes the tool, source, operating instructions, a concise validation summary, reproducible offline tests, build/package scripts, and contribution materials. Personal run logs, unrelated system audits, handoff notes, archived documents, and raw research materials are excluded. See [Development](DEVELOPMENT.md) for commands and [Privacy](PRIVACY.md) before sharing diagnostics.
