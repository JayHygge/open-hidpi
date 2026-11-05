# 开发说明

所有命令从项目根目录运行。需要 macOS、Xcode Command Line Tools、Python 3 和 Git；不安装其他依赖。下面的编译、离线检查和打包命令不会修改系统显示设置。

## 修改与检查

Swift 源码位置见 [目录说明](README.md)。仅修改文档时无需重新编译。修改 Swift 源码后，先编译并运行三项离线检查：

```sh
python3 scripts/build.py
python3 tests/check-presets.py
python3 tests/check-persistence.py
python3 tests/check-groups.py
python3 scripts/build.py --check
```

第一项检查覆盖 11 档默认配置及 Duo 10 档编码；第二项使用模拟显示接口检查永久保存；第三项检查同型号身份匹配、旧记录解码、双屏快照、多型号共享开关恢复和现有普通分辨率筛选。它们不能代替真实安装、恢复、拔插、睡眠或重启测试。编译目标不等于已验证的支持范围，完整支持边界见 [使用说明](../MacHiDPI/使用说明.md)。

构建脚本先在临时目录编译并验证签名完整性，成功后才更新程序及 `MacHiDPI/build.json`，不会运行程序。构建记录绑定源码、二进制哈希和编译目标；源码或程序改变后，旧记录会使打包失败，须重新构建。`--check` 仅读取现有构建记录，不编译。该记录用于发现漏编译，不代替功能实测。

## 打包

在源码、程序和文档准备好后运行：

```sh
python3 tests/check-packaging.py
python3 tests/check-privacy.py
python3 scripts/privacy.py
python3 scripts/package.py
python3 scripts/package.py --check
git diff --check
```

打包检查使用临时 Git 仓库验证打包和失败检查，不运行 MacHiDPI。打包脚本先检查公开文件隐私规则，再核验构建记录、必需文件及程序和入口的执行权限；通过后重建随包校验清单、`release/MacHiDPI.zip` 和项目校验清单，不编译或运行 MacHiDPI。隐私处理与历史边界以 [隐私说明](PRIVACY.md) 为准。

ZIP 只包含 [打包脚本](../scripts/package.py) 中 `BUNDLE_INPUTS` 指定的文件及随包校验清单；目录里的临时文件、备份和其他额外文件不会进入 ZIP。新增正式发布文件时，必须显式更新该清单。项目校验覆盖 Git 已跟踪及尚未忽略的新增普通文件，不包含它自身、`.DS_Store`、`private/` 或其他忽略文件。运行前先检查新增文件；脚本不暂存、提交或上传文件。

根目录 `LICENSE` 和 `THIRD_PARTY_NOTICES.md` 为许可声明的维护源。修改后将它们分别复制到 `MacHiDPI/` 的同名文件；打包和只读校验会拒绝内容不一致的副本。ZIP 必须携带这两份声明。

`--check` 检查公开文件和 ZIP 的隐私规则、构建关联、发布文件完整性、两份清单及 ZIP 内容和执行权限，不改写文件。若仅文档变化，重新打包即可；若源码或二进制变化，先重新构建，再打包检查。

也可从项目根目录单独检查项目清单：

```sh
shasum -a 256 -c release/SHA256SUMS.project
```

Git 提交记录用于保存进度，项目校验文件用于核验内容；二者都不构成显示效果或系统干净状态的证明。

## 实现参考

配置生成保留 8 字节普通条目和两倍渲染的 8/16 字节编码。本机 11 档去重后为 32 条数据，条目数与桌面档位数不同；不再与 BetterDisplay 旧版 152 条集合相同，安装不读取其文件。用户档位和使用范围见使用说明，具体实测事实见随包验证记录。

模式选择枚举底层模式，要求尺寸、2× 密度和刷新率唯一匹配。公开 `CGDisplayCopyAllDisplayModes` 可能漏掉目标，不能只据公开列表缺失判断不支持。

`--all-resolutions` 仅用于 plan/install/export，选择当前公开普通模式中宽度大于 1024、宽高不超过面板的尺寸，去重并生成对应 2× 编码；不替代默认 11 档。Duo 的 10 档生成 30 条数据。

同型号 install/restore 共用一个覆盖文件，逐屏重连；各屏快照记录 ID、系统 UUID 和原模式。优先唯一 UUID 匹配，UUID 重复时只接受仍在且 UUID 相符的原 ID，身份不确定时停止。模式操作 enable/persist/reconnect 仍只针对选中的屏幕。

恢复记录新增可选 originalScreens，保留旧 originalMode 解码。旧记录尚受管理且没有双屏快照时，拒绝多屏安装/恢复；先单屏恢复到 managed=false，确认文件哈希已回到 originalHash 后，重装会采集本轮各屏模式，保留型号文件的首次备份。多个受管理型号继承相同 originalFlag（缺失表示原键不存在），只在最后一个恢复时还原全局开关。已恢复记录再次安装时更新共享开关基准；所有基准仅接受缺失、0、1。其他型号 managed 缺失或基准冲突时停止。

软件重连使用 `CGSConfigureDisplayEnabled`；模式选择使用 `CGSConfigureDisplayMode`；随后用公开 CoreGraphics 接口核验桌面与实际渲染尺寸。模式描述布局参考 [displayplacer Header.h](https://github.com/jakehilborn/displayplacer/blob/master/src/Header.h)。
