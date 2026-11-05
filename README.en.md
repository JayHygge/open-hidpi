# open-hidpi

**A reproducible starting point for fixing external-display HiDPI on a Mac—with your own AI, or with help from the community.**

[中文](README.md) · [Swift source](MacHiDPI/source/MacHiDPI.swift) · [Contributing](CONTRIBUTING.md)

I'm [Jay](https://github.com/JayHygge). Text on my MacBook's external monitor didn't look right, so I started investigating HiDPI. This project shares the Swift tool, configuration generation, mode checks, recovery flow, and validation records that came out of that work.

I can't test every setup. The aim is to give you a concrete implementation to study and adapt. You can ask your own AI to read the repository and investigate your hardware, open an issue for help, or contribute a pull request.

## Current scope

**The executable currently accepts Apple M1 Pro only; other chips are explicitly rejected.** Validation comes from one M1 Pro MacBook Pro running macOS 27.2, a Dell P3424WE, and two MB14FCD panels in a Duo setup, all at 60 Hz. The integrated dual-display version passed build and offline checks; its full install/restore flow has not been retested on hardware. See the [validation record](MacHiDPI/验证记录.md).

The tool can inspect desktop and rendering dimensions, select an existing 2× mode, generate scaling overrides, reconnect displays, request persistence, and back up/restore managed configuration. It needs no resident process, startup item, or SIP changes. It does not increase the panel's physical pixel density. Installation needs administrator approval and changes display configuration.

Other chips, OS versions, monitors, HDR/VRR, high refresh rates, sleep, and reboot persistence need separate validation. DisplayLink, Sidecar, and virtual displays are outside the current scope. User-facing prompts and detailed operating instructions are currently in Chinese.

## Get started

For a supported setup, download [MacHiDPI.zip](release/MacHiDPI.zip), keep the extracted folder intact, and read the [usage guide](MacHiDPI/使用说明.md) before changing display settings.

For another setup, give your AI this repository and the following prompt:

```text
Read README.en.md, CONTRIBUTING.md, the usage and validation documents,
docs/DEVELOPMENT.md, and the Swift source.
My setup: chip [...], macOS [...], display [...], connection/dock [...],
native resolution/refresh rate [...], desired desktop size [...].
Problem and steps already tried: [...].

Compare my setup with what has actually been tested. Start with read-only
diagnostics; do not switch modes, change system settings, or run admin commands.
Do not simply remove the chip check or treat a successful build as compatibility.
Before modifying the source, explain the remaining uncertainty, impact, recovery
steps, and validation plan, then wait for my confirmation.
Remove personal paths, account names, serial numbers, UUIDs, and credentials
from any logs intended for sharing.
```

No AI experience required: [open an issue](https://github.com/JayHygge/open-hidpi/issues/new/choose). Contributions should include evidence and clearly separate what was tested from what remains unknown. See [Contributing](CONTRIBUTING.md) and the [development guide](docs/DEVELOPMENT.md).

MIT licensed. See [LICENSE](LICENSE) and [third-party notices](THIRD_PARTY_NOTICES.md). Thanks to one-key-hidpi, BetterDisplay, and displayplacer for their work in this area. This project is unaffiliated with them; no unverified fork relationship is claimed.
