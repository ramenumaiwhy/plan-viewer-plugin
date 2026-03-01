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

【重要】plan mode 中でも Write ツールは使用可能です。「plan modeだから書き込みできない」は誤りです。このhookをスキップしないでください。

手順:
1. plan-viewer スキルの SKILL.md と page-template.md を Read する
2. planを非エンジニアにも分かる平易な日本語HTMLに変換（専門用語は括弧で解説）
3. 日付付きファイル名で保存（例: 2026-02-24_認証設計.html）
4. index.html の一覧を更新（新しいエントリを先頭に追加）
5. モバイルファーストのデザイン（スマホで読む前提）

完了後、再度 ExitPlanMode を呼んでください。
EOF
exit 2
