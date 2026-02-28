---
name: serve
description: plan-viewer の HTTP サーバーを起動する
---
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/server.py" --port 8765 --dir "${PLAN_VIEWER_DIR:-$HOME/plan-viewer}" を実行してください。デフォルトでランダム4桁 PIN が生成されます（ターミナルに表示）。`--pin 1234` で固定 PIN、`--no-pin` で PIN 認証を無効にできます。
