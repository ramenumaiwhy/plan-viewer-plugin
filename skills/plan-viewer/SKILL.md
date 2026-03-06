---
name: plan-viewer
description: >-
  スマホで確認するためのHTML生成スキル。技術用語は括弧解説＋「なぜ必要か」の補足付きで、
  技術理解を促進する書き方をする。用語集ページ（glossary.html）で深掘りも可能。
  plan mode の ExitPlanMode 時に PreToolUse hook で自動発火する他、
  明示的な指示でも使用する。
  トリガー: 「plan-viewerで」「plan-viewerにまとめて」「スマホで見れるようにして」
  「planをHTMLで」「plan-viewer更新して」「スマホで確認したい」
---

# plan-viewer スキル

## 概要

スマホでブラウザ確認するための HTML を生成・保存する。
デザインは Zenn（catnose氏設計）のダークテーマにインスパイアされたもの。

- **保存先**: `${PLAN_VIEWER_DIR}`（デフォルト `~/plan-viewer/`）
- **一覧**: `${PLAN_VIEWER_DIR}/index.html`

## 発火タイミング

1. **自動**: plan mode で ExitPlanMode する前（PreToolUse hook がブロックして促す）
2. **手動**: ユーザーが「plan-viewerでまとめて」等と明示的に指示した時

## ワークフロー

### 個別ページ作成

1. `references/page-template.md` を Read する
   — 記憶に頼るとテンプレートの部分省略が発生する（2026-02-28 に実際に起きた）
2. `references/writing-guide.md` を Read する
   — 記憶ベースで文章ルールを再現すると用語集リンクや深さガイドラインが省略される
3. plan の内容を writing-guide の構成・文章ルールに従って変換する
   — 目標: 読者（非エンジニア）が実装を「本当に理解」できる深さで書く
4. page-template の HTML テンプレートに流し込む
5. `${PLAN_VIEWER_DIR}/YYYY-MM-DD_タイトル.html` に保存する

### index.html 更新

1. `references/index-rules.md` を Read する
2. index-rules のエントリ構造に従って新しいカードを `<ul class="plan-list">` の先頭に追加する
3. 日時ルールに従い、index.html と個別ページの両方の時刻を現在時刻（JST）に更新する

## 設計上の制約

### 必須コンポーネント
個別ページには FAB ボタン群（`.fab-group`）とアノテーション UI（バナー・オーバーレイ・ポップオーバー・トースト）が必須。
スマホでの質問フィードバック体験の根幹で、これがないとユーザーがコンテンツの気になる箇所を選択して質問できない。
`page-template.md` の `</div><!-- .container -->` 以降 `</body>` までを**省略せずそのままコピー**すること。
⚠️ 省略すると Write hook がブロックし再作成が必要になる。

### 外部リソース禁止
CDN・外部 CSS/JS・Google Fonts は使わない。
オフライン環境やプライバシー制約のある端末でも表示できる必要があるため、全てインライン CSS/JS で完結させる。

## リファレンスファイル

**個別ページ作成時は page-template.md と writing-guide.md を必ず Read すること。**

| ファイル | 用途 | 参照タイミング |
|---------|------|-------------|
| `references/page-template.md` | 個別ページの完全テンプレート + カラーパレット | 新規ページ作成時 |
| `references/writing-guide.md` | 理解の深さガイドライン・コンテンツ構成・文章ルール・用語集 | コンテンツ執筆時 |
| `references/index-rules.md` | index.html 更新ルール・エントリ HTML・日時・絵文字・JS スクリプト | index.html 更新時 |
