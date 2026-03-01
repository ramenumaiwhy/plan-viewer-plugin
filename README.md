# plan-viewer

Claude Code の plan mode で生成した計画を、非エンジニア向け HTML に変換してスマホで読めるようにするプラグイン。

## インストール

```bash
claude --plugin-dir /path/to/plan-viewer-plugin
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

# スマホ（同じ WiFi）からアクセスする場合:
python3 scripts/server.py --port 8765 --host 0.0.0.0
```

デフォルトは localhost のみ。スマホからアクセスするには `--host 0.0.0.0` が必要（PIN 認証はデフォルトで有効）。ディレクトリが存在しない場合は自動作成される。

## 設定

| 環境変数 | デフォルト | 説明 |
|----------|-----------|------|
| `PLAN_VIEWER_DIR` | `~/plan-viewer/` | HTML の出力先ディレクトリ |

## デザイン

Zenn（catnose氏設計）のダークテーマにインスパイアされたデザイン。

## ライセンス

MIT
