#!/bin/bash
set -uo pipefail
asset_dir="$(cd -- "$(dirname -- "$0")" && pwd)"
"$asset_dir/MacHiDPI" enable
result=$?
if [[ "$result" == 0 ]]; then
  echo "HiDPI 已开启。"
else
  echo "若提示找不到唯一目标模式，可阅读使用说明，再运行安装并开启.command。"
fi
read -r -p "按回车关闭窗口。" ignored
exit "$result"
