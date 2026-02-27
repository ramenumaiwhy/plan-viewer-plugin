#!/bin/bash
# plan-viewer セットアップ: 出力ディレクトリ作成 + アセットコピー
set -euo pipefail

PLUGIN_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEST="${PLAN_VIEWER_DIR:-$HOME/plan-viewer}"

case "$DEST" in
  "$HOME"/*) ;;
  *) echo "Error: PLAN_VIEWER_DIR must be under \$HOME ($DEST)" >&2; exit 1 ;;
esac

mkdir -p "$DEST"

copied=0
skipped=0
for f in "$PLUGIN_ROOT"/assets/*; do
  name="$(basename "$f")"
  if [ -f "$DEST/$name" ]; then
    skipped=$((skipped + 1))
  else
    cp "$f" "$DEST/$name"
    copied=$((copied + 1))
  fi
done

echo "✅ plan-viewer セットアップ完了: $DEST"
echo "   コピー: ${copied}件, スキップ（既存）: ${skipped}件"
[ "$copied" -eq 0 ] && [ "$skipped" -gt 0 ] && echo "   ℹ️ 全アセットが既に存在するため、新規コピーはありません"
