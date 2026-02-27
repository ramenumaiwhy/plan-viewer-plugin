---
name: serve
description: plan-viewer の HTTP サーバーを起動する
---
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/server.py --port 8765 --dir "${PLAN_VIEWER_DIR:-$HOME/plan-viewer}" を実行してください。ポートやディレクトリはオプションで変更可能です。
