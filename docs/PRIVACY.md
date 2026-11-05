# 隐私与诊断数据 / Privacy and diagnostics

公开源码、文档、测试和 ZIP 不应包含个人绝对路径、非公开账号、真实凭据、设备序列号、UUID 或其他唯一标识。示例使用占位符，所需路径和用户信息从运行环境获取。作者的公开 GitHub 署名，以及芯片／显示器型号、厂商和产品 ID、分辨率等非唯一技术参数可以保留。

## 本机生成的数据

安装配置会在用户目录保存恢复记录、屏幕身份和可能存在的原覆盖文件备份。具体路径及影响见 [使用说明](../MacHiDPI/使用说明.md)。这些是使用者自己的本机资料，不属于项目发布内容。

提 Issue 或 PR 时，只提供与问题相关的脱敏片段。不要直接上传完整 `state.json`、恢复备份、原始系统报告、个人目录或凭据。分享芯片、macOS 版本、显示器型号、连接方式、桌面／渲染尺寸和错误信息通常足够开始讨论。

## 发布与检查

打包和只读发布校验执行 `scripts/privacy.py`。命中规则会停止，报告只显示脱敏位置与类别，不回显匹配值；规则不能保证发现所有秘密。命令见 [开发说明](DEVELOPMENT.md)。

检查范围是当前 Git 跟踪文件、未被忽略的新增普通文件和发布 ZIP 的解压内容；不覆盖被忽略的本机资料，也不会扫描或清除旧 Git 历史。推送前检查文件列表和将被推送的历史，不能把当前文件检查通过当成历史已清理。

## English

Do not include private account details, personal paths, credentials, serial numbers, UUIDs, or other unique identifiers in source, documents, tests, or release archives. Public author attribution and non-unique hardware details are intentional.

The tool generates local recovery state and backups that may contain display identifiers. Do not attach raw state files, backups, or system reports to issues or PRs. Share only relevant, redacted excerpts.

Packaging checks current project files and archive contents against configured privacy patterns. This is not a guarantee that all secrets are absent, and it does not inspect or erase old Git history. Review both the file list and the history before publishing.
