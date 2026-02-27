#!/bin/bash

# ExitPlanMode の前に plan-viewer HTML が生成済みかチェック
# 未生成ならブロック (exit 2) して HTML 生成を促す

PLAN_DIR="${PLAN_VIEWER_DIR:-$HOME/plan-viewer}"
INDEX="$PLAN_DIR/index.html"

if [ -f "$INDEX" ]; then
  case "$(uname)" in
    Darwin) FILE_MOD=$(stat -f %m "$INDEX") ;;
    *)      FILE_MOD=$(stat -c %Y "$INDEX") ;;
  esac
  NOW=$(date +%s)
  DIFF=$((NOW - FILE_MOD))
  # 直近120秒以内に更新されていれば今回のplanに対応済みと判断
  if [ "$DIFF" -lt 120 ]; then
    exit 0
  fi
fi

cat >&2 << 'EOF'
⚠️ plan-viewer HTML が未生成です。
ExitPlanMode の前に、planの内容を非エンジニア向けHTMLに変換して保存してください。

手順:
1. planを非エンジニアにも分かる平易な日本語HTMLに変換（専門用語は括弧で解説）
2. 日付付きファイル名で保存（例: 2026-02-24_認証設計.html）
3. index.html の一覧を更新（新しいエントリを先頭に追加）
4. モバイルファーストのデザイン（スマホで読む前提）

plan-viewer スキルの SKILL.md に従ってください。
完了後、再度 ExitPlanMode を呼んでください。
EOF
exit 2
