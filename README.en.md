# open-hidpi

### Free, open-source HiDPI scaling for Mac external monitors. Sharper text. More scaling choices.

[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
![macOS](https://img.shields.io/badge/platform-macOS-black.svg)
![M1 Pro Preview](https://img.shields.io/badge/M1%20Pro-preview-orange.svg)

**[Download MacHiDPI.zip](https://github.com/JayHygge/open-hidpi/releases/download/v0.1.0-preview/MacHiDPI.zip)** · [Usage guide](MacHiDPI/使用说明.md) · [中文](README.md) · [Get help](https://github.com/JayHygge/open-hidpi/issues/new/choose)

Blurry text on an external monitor? Missing the scaling option that makes your Mac comfortable to use? **open-hidpi is a free, open-source BetterDisplay alternative focused on native HiDPI and custom display resolutions.** Written in Swift, it inspects modes, generates scaling configurations, switches resolutions, and restores managed configuration. No paid license, SIP changes, resident process, or startup item required.

**Currently an M1 Pro preview.** Enabling, installing, reconnecting, and saving modes are restricted to Apple M1 Pro. For other hardware, use the source as a starting point with your own AI, or open an issue for help. Existing evidence covers one MacBook Pro and two monitor models; see [Compatibility](#compatibility-and-hardware-evidence).

## What you get

| Your problem | What open-hidpi provides |
| --- | --- |
| You cannot tell whether HiDPI is really active | Checks logical desktop and actual rendering dimensions for 2× scaling on both axes |
| macOS offers too few useful scaling options | Generates 11 HiDPI desktop presets from panel dimensions, or presets based on existing standard resolutions |
| A suitable HiDPI mode already exists | Switches to it without installing override files or requesting an administrator password |
| You want a recovery path before installing configuration | Backs up existing model overrides, records original modes, and provides restoration; same-model screens share configuration and are handled individually |
| You only need an occasional display adjustment | Exits when the operation finishes; no background service or login item |
| Your setup has not been tested | A single Swift source file, build scripts, and repeatable offline tests to inspect and adapt yourself or with AI |

The 11 presets are candidates, not a promise that every display accepts every size. The system's mode list and actual rendering checks determine what is available.

## How HiDPI works

macOS draws text and interface elements at a higher rendering resolution, then scales the image to the display output. On the tested Dell P3424WE, the tool can retain native desktop space while using 2× rendering:

```text
Logical desktop       macOS rendering       Physical panel
3440 × 1440       →    6880 × 2880        →   3440 × 1440
```

Choose a smaller logical desktop for larger text and controls. Generated options for that panel include 3440×1440, 2752×1152, 2408×1008, and 1720×720; see the [full preset table](MacHiDPI/使用说明.md).

**2× describes rendering pixels relative to logical desktop dimensions, not a fixed multiple of the panel's native resolution.** HiDPI does not add physical pixels, turn a panel into a Retina display, or increase cable bandwidth or maximum refresh rate. Judge the result on your own screen.

## Get started

1. [Download the preview ZIP](https://github.com/JayHygge/open-hidpi/releases/download/v0.1.0-preview/MacHiDPI.zip), extract it, and keep the entire `MacHiDPI` folder together.
2. Read the [usage guide](MacHiDPI/使用说明.md). Open **检查状态.command** to inspect desktop and rendering dimensions.
3. To try an existing mode, open **直接开启HiDPI.command** and confirm the displayed instructions. The tool checks whether 2× HiDPI is active afterward.
4. For additional presets or a missing mode, keep the MacBook's built-in screen open and follow **安装并开启.command** in the guide. Use **恢复原配置.command** to restore managed configuration.

Mode changes may briefly blank the external display. Installation requires administrator approval and writes a model override and a system display setting. Restoration uses recorded configuration; it does not reset every system preference. Review the [recovery instructions](MacHiDPI/使用说明.md#恢复) first. **Runtime prompts and the detailed operating guide are currently in Chinese.**

### Command line

Run these commands inside the extracted `MacHiDPI` folder:

```sh
./MacHiDPI list       # External displays, desktop and rendering dimensions
./MacHiDPI status     # Current HiDPI state
./MacHiDPI plan       # Read-only configuration preview
```

Mode operations also include `enable`, `install`, `reconnect`, `persist`, and `restore`. `persist` asks macOS to save the current HiDPI mode; it does not guarantee sleep or reboot persistence. See the [command reference](MacHiDPI/使用说明.md#命令行与源码) for display selection and `--all-resolutions`.

## Compatibility and hardware evidence

| Setup | What has been verified |
| --- | --- |
| M1 Pro MacBook Pro · macOS 27.2 · Dell P3424WE · 3440×1440 at 60 Hz | Direct activation of an existing 2× mode, recognition of all 11 installed presets, and one hotplug check each at two desktop sizes |
| The same MacBook Pro · two MB14FCD panels in a Duo setup · 1920×1200 each at 60 Hz | A dedicated test executable switched both screens through 10 modes each and checked native-desktop hotplug retention; the integrated tool passed build, offline, and read-only checks |
| Other chips, macOS versions, or monitors | Compatibility has not been established; hardware reports and adaptation PRs are welcome |

**The integrated dual-display version has not completed a new hardware install/restore/switch cycle.** Sleep, reboot retention, high refresh rates, and HDR/VRR remain untested. DisplayLink, Sidecar, and virtual displays are outside the current scope. The tool uses private macOS display APIs, which may change with system updates. The macOS 14.0 build target is not a claim that all later versions have been tested.

Read the [validation summary](MacHiDPI/验证记录.md) for precise results and version differences, and the [supported-scope notes](MacHiDPI/使用说明.md#支持范围) before changing settings.

## Adapt it with your own AI

One developer cannot test every combination of Mac, cable, dock, and monitor. The source, operating instructions, validation boundaries, and tests are public so you and your AI have a concrete implementation to work from.

Give your AI the repository URL and this prompt:

```text
Read open-hidpi's README, CONTRIBUTING.md, usage guide, validation summary,
docs/DEVELOPMENT.md, and MacHiDPI/source/MacHiDPI.swift.

My setup: chip [...], macOS [...], monitor [...], cable/dock [...],
native resolution/refresh rate [...], desired desktop size [...].
Problem and steps already tried: [...].

Compare the hardware differences. Start with read-only diagnostics and an
adaptation plan; do not switch modes or change system settings.
Do not merely remove the M1 Pro check or treat a successful build as compatibility.
Before editing, explain the impact, recovery path, and tests, then wait for my
confirmation. Redact personal information from any logs intended for sharing.
```

**You do not need AI experience to get help.** [Open an issue](https://github.com/JayHygge/open-hidpi/issues/new/choose) with your setup, connection, desired desktop size, and relevant error. Fixes, adaptations, and hardware reports are welcome through [PRs](CONTRIBUTING.md).

## FAQ

### Can it replace BetterDisplay?

For **external-display HiDPI, scaling presets, and mode verification**, open-hidpi offers a free, inspectable implementation you can modify. The current direct-use target is M1 Pro. It does not provide brightness/DDC controls, HDR brightness boosts, virtual screens, or a full display-management suite. If you need those features, see [BetterDisplay](https://github.com/waydabber/BetterDisplay). The projects are unaffiliated.

### How does it relate to one-key-hidpi?

[one-key-hidpi](https://github.com/xzhih/one-key-hidpi) is related work on macOS HiDPI. open-hidpi is written in Swift, generates its own configuration, and does not require its scripts or BetterDisplay at runtime. No fork or official-successor relationship is claimed.

### Why not enable every Apple Silicon Mac?

Available modes depend on the chip, OS, connection, and display. The project keeps a tested path and explicit evidence boundaries while inviting further adaptation. A removed guard is not a hardware compatibility test.

## Build, contribute, and license

- **Developers:** [Build, test, and package](docs/DEVELOPMENT.md) · [Project layout](docs/README.md).
- **Contributors:** [Issue and PR guide](CONTRIBUTING.md) · [Diagnostic privacy](docs/PRIVACY.md).
- **License:** [MIT](LICENSE), free to use, modify, and distribute. Preserve applicable [third-party notices](THIRD_PARTY_NOTICES.md).

Created by [Jay](https://github.com/JayHygge) to solve a personal MacBook external-display problem. Thanks to one-key-hidpi, BetterDisplay, and displayplacer for their work in this area. If this helps you, give it a Star or contribute your hardware results so the next user has a better starting point.
