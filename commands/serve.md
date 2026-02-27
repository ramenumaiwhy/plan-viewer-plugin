---
name: serve
description: plan-viewer の HTTP サーバーを起動する
---
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/server.py" --port 8765 --host 0.0.0.0 --dir "${PLAN_VIEWER_DIR:-$HOME/plan-viewer}" を実行してください。ポート・ホスト・ディレクトリはオプションで変更可能です（--host のデフォルトは 127.0.0.1、外部アクセスには 0.0.0.0 を指定）。
