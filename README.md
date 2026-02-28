# plan-viewer

Claude Code の plan mode で生成した計画を、非エンジニア向け HTML に変換してスマホで読めるようにするプラグイン。

## インストール

```bash
# 単一セッション
claude --plugin-dir /path/to/plan-viewer-plugin

# 初回セットアップ（出力ディレクトリにアセットをコピー）
# Claude Code 内で:
/plan-viewer:setup
```

## 使い方

1. Claude Code で plan mode に入る
2. 計画を確定する前に、プラグインが自動で HTML 生成を促す（PreToolUse hook）
3. 生成された HTML はデフォルトで `~/plan-viewer/` に保存される

### HTTP サーバー

スマホからアクセスするために HTTP サーバーを起動:

```bash
# Claude Code 内で:
/plan-viewer:serve

# または直接:
python3 /path/to/plan-viewer-plugin/scripts/server.py --port 8765
```

ポートやディレクトリは `--port` / `--dir` オプションで変更可能。tailscale 等でネットワークを構成し、スマホからアクセスする。

## 設定

| 環境変数 | デフォルト | 説明 |
|----------|-----------|------|
| `PLAN_VIEWER_DIR` | `~/plan-viewer/` | HTML の出力先ディレクトリ |

## デザイン

Zenn（catnose氏設計）のダークテーマにインスパイアされたデザイン。アイコンは `assets/` に同梱されており、差し替え可能。

## ライセンス

MIT
