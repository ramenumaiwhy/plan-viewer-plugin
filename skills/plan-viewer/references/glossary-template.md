# 用語集ページ（glossary.html）

技術用語の詳しい解説を集約するページ。個別ページから用語リンクで飛べる。

## 運用ルール
- ファイル: `${PLAN_VIEWER_DIR}/glossary.html`（デフォルト `~/plan-viewer/glossary.html`）
- 新しい用語が出たら `<dl>` の**アルファベット順の適切な位置**に追加
- 各用語には `id` 属性をつける（リンク先: `glossary.html#api` 等）
- 用語が既に存在する場合は追加しない

## 用語エントリの書き方
```
用語名（英語表記）
├─ ひとことで: 20文字以内の端的な説明
├─ もう少し詳しく: 2-3文で仕組みや役割を説明
└─ このプロジェクトでは: その用語がこのプロジェクトでどう使われているか（該当する場合のみ）
```

## glossary.html テンプレート

```html
<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>用語集</title>
<link rel="icon" href="icon.png">
<link rel="icon" type="image/png" sizes="32x32" href="favicon-32.png">
<link rel="apple-touch-icon" sizes="180x180" href="apple-touch-icon.png">
<link rel="manifest" href="manifest.json">
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Hiragino Sans',
                 'Hiragino Kaku Gothic ProN', 'Noto Sans JP', sans-serif;
    -webkit-font-smoothing: antialiased;
    background: #0d223a;
    color: #c8d6e5;
    line-height: 1.9;
    letter-spacing: 0.02em;
  }
  .container {
    max-width: 640px;
    margin: 0 auto;
    padding: 24px 20px 60px;
  }
  a { color: #3ea8ff; text-decoration: none; }
  a:hover { text-decoration: underline; }
  .back {
    color: #acbcc7;
    font-size: 0.85rem;
    display: inline-block;
    margin-bottom: 20px;
  }
  h1 {
    color: #dee4ed;
    font-size: 1.5rem;
    line-height: 1.5;
    margin-bottom: 8px;
  }
  .subtitle {
    color: #acbcc7;
    font-size: 0.85rem;
    margin-bottom: 32px;
  }
  dl { margin: 0; }
  dt {
    color: #dee4ed;
    font-size: 1.1rem;
    font-weight: bold;
    margin-top: 2em;
    padding-top: 1em;
    border-top: 1px solid #2e445c;
    scroll-margin-top: 20px;
  }
  dt:first-of-type { border-top: none; margin-top: 0; padding-top: 0; }
  .term-en {
    color: #acbcc7;
    font-size: 0.85rem;
    font-weight: normal;
    margin-left: 8px;
  }
  dd { margin: 0.5em 0 0 0; }
  .dd-label {
    display: inline-block;
    background: #0b2c53;
    color: #3ea8ff;
    font-size: 0.75rem;
    font-weight: bold;
    padding: 2px 8px;
    border-radius: 4px;
    margin-bottom: 4px;
  }
  .dd-content {
    font-size: 0.9rem;
    color: #acbcc7;
    margin-bottom: 0.8em;
  }
  .dd-project {
    background: #0f2744;
    border: 1px solid #2e445c;
    border-radius: 7px;
    padding: 12px 16px;
    font-size: 0.85rem;
    color: #acbcc7;
    margin-bottom: 0.5em;
  }
</style>
</head>
<body>
<div class="container">
  <a class="back" href="index.html">← 一覧に戻る</a>
  <h1>📖 用語集</h1>
  <div class="subtitle">plan-viewerに登場する技術用語の解説</div>

  <dl>
    <!-- 用語エントリ例 -->
    <dt id="api">API <span class="term-en">Application Programming Interface</span></dt>
    <dd>
      <div class="dd-label">ひとことで</div>
      <div class="dd-content">プログラム同士が会話するための窓口</div>
      <div class="dd-label">もう少し詳しく</div>
      <div class="dd-content">あるプログラムが別のプログラムの機能を使いたいとき、直接中身を触るのではなく、決められた形式でリクエストを送る仕組み。レストランの「メニュー」のようなもので、メニューに載っている注文だけができる。</div>
    </dd>

    <dt id="hook">hook <span class="term-en">フック</span></dt>
    <dd>
      <div class="dd-label">ひとことで</div>
      <div class="dd-content">特定タイミングで自動実行される仕組み</div>
      <div class="dd-label">もう少し詳しく</div>
      <div class="dd-content">コードのある処理が実行される直前・直後に、別の処理を差し込めるポイント。自動ドアのセンサーのように、「人が近づいた」というイベントを検知して「ドアを開ける」処理を起動する。</div>
      <div class="dd-label">このプロジェクトでは</div>
      <div class="dd-project">Claude Codeの PreToolUse hook で、ExitPlanMode実行前にplan-viewerのHTML生成を促している。</div>
    </dd>
  </dl>
</div>
</body>
</html>
```
