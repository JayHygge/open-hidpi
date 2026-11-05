#!/bin/bash
set -uo pipefail
asset_dir="$(cd -- "$(dirname -- "$0")" && pwd)"
"$asset_dir/MacHiDPI" reconnect
result=$?
if [[ "$result" == 0 ]]; then echo "完成。"; else echo "未完成，请保留上方错误信息。"; fi
read -r -p "按回车关闭窗口。" ignored
exit "$result"
