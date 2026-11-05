# open-hidpi

**公开自己解决 Mac 外接屏 HiDPI 问题的实现，给你和你的 AI 一个可复现、可扩展的起点。**

[English](README.en.md) · [使用说明](MacHiDPI/使用说明.md) · [源码](MacHiDPI/source/MacHiDPI.swift) · [参与贡献](CONTRIBUTING.md)

我是 [Jay](https://github.com/JayHygge)。用 MacBook 外接显示器时，我觉得文字显示不够理想，开始研究 HiDPI，也接触到了 one-key-hidpi 和 BetterDisplay。后来，我把自己实际用到的配置生成、模式切换、状态核验和恢复流程做成了这个 Swift 小工具。

一个人的设备覆盖不了所有情况。这个项目的价值，是公开实现、验证过程和边界：你可以直接使用已支持的路径，也可以让自己的 AI 阅读代码，结合你的设备分析和适配。不使用 AI，也欢迎提 Issue；有改进，欢迎 PR。

## 目前能做什么

- 检查外屏当前桌面尺寸与实际渲染尺寸，确认是否为 2× HiDPI。
- 选择已存在的 HiDPI 模式，或生成并安装额外缩放档位。
- 提供软件重连、请求保存当前模式，以及配置备份和恢复。
- 支持同型号多屏的配置管理；无常驻进程、无启动项，无需关闭 SIP。

工具自行生成配置，运行不依赖 BetterDisplay 或 one-key-hidpi。HiDPI 不会增加面板物理像素；最终观感仍取决于面板和缩放比例。

## 先看支持边界

**当前程序仅允许 Apple M1 Pro。其他芯片会被拒绝，不能直接运行安装流程。**

现有验证来自一台 MacBook Pro（M1 Pro、macOS 27.2）及两种显示器型号：Dell P3424WE，以及 Duo 的两块 MB14FCD，均为 60 Hz。双屏实测用过专用执行程序；整合后的正式版通过构建和离线检查，尚未重做双屏安装／恢复实机闭环。

这是一份有限设备上的实现起点。其他芯片、系统、显示器、高刷新率、HDR／VRR、睡眠和重启保持均不能据此推定支持。DisplayLink、Sidecar、虚拟屏不在当前支持范围。完整事实见 [验证记录](MacHiDPI/验证记录.md)。

## 使用或适配

**符合当前支持范围：** 下载仓库内的 [MacHiDPI.zip](release/MacHiDPI.zip)，解压后保留完整目录，先读 [使用说明](MacHiDPI/使用说明.md)。先用“检查状态”，再按说明选择直接开启或安装配置。安装会修改型号覆盖文件和系统显示开关，需要确认及管理员授权。

**设备不同，想让 AI 协助：** 把仓库交给 AI，并使用下面的任务说明：

```text
请阅读这个仓库的 README、CONTRIBUTING.md、MacHiDPI/使用说明.md、
MacHiDPI/验证记录.md、docs/DEVELOPMENT.md，以及 Swift 源码。
我的设备信息：芯片［填写］；macOS 版本［填写］；显示器型号［填写］；
连接方式／扩展坞［填写］；原生尺寸和刷新率［填写］；目标桌面尺寸［填写］。
现象和已尝试步骤：［填写］。

先比较我的设备与已验证范围，解释可能原因和仍缺少的信息。
先提出只读诊断步骤，不执行显示切换、系统修改或管理员命令。
不要仅删除芯片检查来宣称支持，也不要把成功编译当成适配成功。
如需修改源码，请先解释方案、影响、恢复方式和验证方法，再等我确认。
用于反馈的日志须删除用户名、个人路径、序列号、UUID 和凭据。
```

**想求助或贡献：** 用 [Issue 模板](https://github.com/JayHygge/open-hidpi/issues/new/choose) 提交设备信息与现象；可读性改进、适配和验证记录也欢迎 PR。具体流程见 [贡献指南](CONTRIBUTING.md)。

## 开发与许可

[开发说明](docs/DEVELOPMENT.md) 包含构建、离线检查和打包步骤；[隐私说明](docs/PRIVACY.md) 说明公开文件与诊断数据的边界。项目结构见 [目录说明](docs/README.md)。

[MIT](LICENSE) · 实现参考与第三方声明见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。感谢 one-key-hidpi、BetterDisplay 和 displayplacer 的相关工作。本项目不代表这些项目，也不声称存在未经核实的分支关系。
