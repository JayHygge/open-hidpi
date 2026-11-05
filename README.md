# open-hidpi

### 免费开源的 Mac 外接屏 HiDPI 工具，让文字显示更清晰、缩放选择更多。

[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
![macOS](https://img.shields.io/badge/platform-macOS-black.svg)
![M1 Pro Preview](https://img.shields.io/badge/M1%20Pro-preview-orange.svg)

**[下载 MacHiDPI.zip](https://github.com/JayHygge/open-hidpi/releases/download/v0.1.0-preview/MacHiDPI.zip)** · [使用说明](MacHiDPI/使用说明.md) · [English](README.en.md) · [问题与适配](https://github.com/JayHygge/open-hidpi/issues/new/choose)

外接显示器上的文字发虚，系统又缺少合适的缩放档位？**open-hidpi 聚焦 Mac 外接屏的原生 HiDPI 与自定义分辨率，是面向这部分需求的免费开源 BetterDisplay 替代方案。** 它用 Swift 实现模式检测、配置生成、切换与恢复：不需要付费许可证，不需要关闭 SIP，也没有常驻进程或启动项。

**当前为 M1 Pro 预览版。** 启用、安装、重连和保存模式目前仅允许 Apple M1 Pro；其他设备可先阅读源码，结合自己的 AI 分析适配，也可以直接提 Issue。已有验证来自一台 MacBook Pro、两种显示器型号；[实测范围](#兼容性与实测范围)见下文。

## 为什么用 open-hidpi

| 你想解决的问题 | 项目提供的能力 |
| --- | --- |
| 不确定是否真的开启 HiDPI | 同时读取逻辑桌面与实际渲染尺寸，核验横纵是否为 2× |
| 系统缩放档位太少，字号与桌面空间难兼顾 | 按面板尺寸生成 11 档 HiDPI 候选；也可为现有普通分辨率生成对应档位 |
| 已有目标 HiDPI 模式，想直接使用 | 直接切换模式，无需安装覆盖文件或输入管理员密码 |
| 需要安装配置，也需要有路可退 | 备份型号覆盖文件、记录原模式，提供恢复入口；同型号多屏共用配置、逐屏处理 |
| 不希望为一个显示设置常驻运行软件 | 操作完成后退出，不安装后台服务或开机启动项 |
| 自己的设备不在已测范围 | 单文件 Swift 源码、构建脚本、离线回归测试，便于自己或 AI 阅读、修改和验证 |

“11 档”是生成的候选，不保证每台显示器都接受全部档位；最终以系统枚举和实际渲染核验为准。

## HiDPI 到底改变了什么

HiDPI 让 macOS 以更高像素密度绘制文字和界面，再缩放到显示器输出。在已测 Dell P3424WE 上，可以保持原生桌面空间并使用 2× 渲染：

```text
逻辑桌面          macOS 实际渲染       物理面板
3440 × 1440  →   6880 × 2880      →   3440 × 1440
```

也可以选择较小桌面，让文字和界面变大。以该屏为例，生成的候选档位包括 3440×1440、2752×1152、2408×1008、1720×720；完整表见[使用说明](MacHiDPI/使用说明.md)。

**2× 比较的是渲染尺寸与逻辑桌面尺寸，不是固定与面板原生分辨率比较。** HiDPI 不会增加面板物理像素，也不改变线缆带宽、刷新率上限或把普通屏幕变成 Retina 面板。清晰度和舒适度仍需在自己的屏幕上判断。

## 开始使用

1. [下载预览版 ZIP](https://github.com/JayHygge/open-hidpi/releases/download/v0.1.0-preview/MacHiDPI.zip)，解压并保留完整 `MacHiDPI` 文件夹。
2. 先读[使用说明](MacHiDPI/使用说明.md)，双击 **检查状态.command** 查看当前桌面和渲染尺寸。
3. 想尝试已有模式，双击 **直接开启HiDPI.command**，阅读提示后确认。成功时会核验当前是否为 2× HiDPI。
4. 需要整组缩放档位、或系统没有目标模式时，打开 MacBook 内屏，按说明使用 **安装并开启.command**；需要撤回时使用 **恢复原配置.command**。

显示模式切换可能短暂黑屏。安装需要管理员授权，会写入型号覆盖文件和系统显示开关；恢复针对本工具记录的配置，不是将所有系统偏好还原到出厂状态。使用前了解[修改范围与恢复方法](MacHiDPI/使用说明.md#恢复)。

### 命令行

以下命令在解压后的 `MacHiDPI` 文件夹内运行：

```sh
./MacHiDPI list       # 查看外屏、桌面与渲染尺寸
./MacHiDPI status     # 检查当前 HiDPI 状态
./MacHiDPI plan       # 只读查看配置计划
```

模式操作还包括 `enable`、`install`、`reconnect`、`persist`、`restore`。其中 `persist` 向系统请求保存当前 HiDPI 模式，不保证睡眠或重启后保持。多屏选择和 `--all-resolutions` 的用法见[完整命令说明](MacHiDPI/使用说明.md#命令行与源码)。

## 兼容性与实测范围

| 环境 | 已验证的结果 |
| --- | --- |
| M1 Pro MacBook Pro · macOS 27.2 · Dell P3424WE · 3440×1440 / 60 Hz | 直接开启已有 2× 模式、安装后识别全部 11 档、两个桌面档位各一次拔插保持 |
| 同一台 MacBook Pro · Duo 两块 MB14FCD · 各 1920×1200 / 60 Hz | 专用执行程序完成两屏各 10 档切换及原生桌面档位拔插保持；整合版通过构建、离线和只读检查 |
| 其他芯片、macOS 或显示器 | 未建立兼容性结论；欢迎带设备信息提 Issue 或贡献适配 |

**整合后的双屏版本尚未重做安装／恢复／切屏实机闭环。** 睡眠、重启保持、高刷新率、HDR／VRR 未验证；DisplayLink、Sidecar、虚拟屏不在当前范围。程序使用 macOS 私有显示接口，系统升级可能影响行为。最低编译目标 macOS 14.0 不等于所有后续系统均已验证。

精确的通过项与历史版本差异见[验证摘要](MacHiDPI/验证记录.md)，操作前提见[支持范围](MacHiDPI/使用说明.md#支持范围)。

## 让自己的 AI 帮你适配

一个人的设备覆盖不了所有组合。项目把实现、操作说明、验证边界和测试一起公开，让你无需从零向 AI 描述整个问题。

把仓库地址交给 AI，再复制这段任务说明：

```text
请阅读 open-hidpi 的 README、CONTRIBUTING.md、使用说明、验证记录、
docs/DEVELOPMENT.md 和 MacHiDPI/source/MacHiDPI.swift。

我的设备：芯片［填写］；macOS［填写］；显示器型号［填写］；
连接线／扩展坞［填写］；原生尺寸与刷新率［填写］；目标桌面尺寸［填写］。
问题与已尝试步骤：［填写］。

先比较设备差异，提出只读诊断和适配方案；不要直接切屏或修改系统。
不要只删除 M1 Pro 检查，也不要把编译成功视为兼容性验证。
修改前解释影响、恢复方法和测试步骤，等我确认。公开日志先脱敏。
```

**不会使用 AI 也可以求助。** [提交 Issue](https://github.com/JayHygge/open-hidpi/issues/new/choose)，提供设备、连接、目标桌面尺寸和错误片段；有修复、适配或设备验证，欢迎 [PR](CONTRIBUTING.md)。

## 常见问题

### 可以替代 BetterDisplay 吗？

如果你需要的是**外接屏 HiDPI、缩放档位与模式核验**，open-hidpi 提供一条免费开源、可自行修改的实现路径；当前直接使用范围仍是 M1 Pro。它不提供亮度／DDC 控制、HDR 增亮、虚拟屏或完整显示器管理套件。需要这些能力，可以了解 [BetterDisplay](https://github.com/waydabber/BetterDisplay)。两个项目没有隶属关系。

### 和 one-key-hidpi 有什么关系？

[one-key-hidpi](https://github.com/xzhih/one-key-hidpi) 是相关的 macOS HiDPI 项目。open-hidpi 采用 Swift、自行生成配置，运行不依赖其脚本或 BetterDisplay；不声称是两者的分支或官方后继。

### 为什么不直接支持所有 Apple Silicon Mac？

芯片、系统、连接方式和显示器都会影响模式可用性。项目选择保留已验证路径与可追溯边界，再通过源码适配和社区验证扩展。欢迎提交其他设备的证据，不以解除检查代替适配。

## 构建、贡献与许可

- **开发者**：[构建、离线检查、打包](docs/DEVELOPMENT.md) · [项目结构](docs/README.md)。
- **贡献者**：[Issue／PR 指南](CONTRIBUTING.md) · [诊断数据隐私](docs/PRIVACY.md)。
- **许可**：[MIT](LICENSE)，可免费使用、修改和分发；引用部分保留[第三方声明](THIRD_PARTY_NOTICES.md)。

由 [Jay](https://github.com/JayHygge) 从自己的 MacBook 外接屏需求出发整理。感谢 one-key-hidpi、BetterDisplay 和 displayplacer 的相关工作。如果项目帮到了你，欢迎 Star，或把设备验证结果带回社区，让下一位用户少走弯路。
