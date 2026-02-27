# Zenn ダークテーマ CSS

以下の CSS をベースとする。catnose氏の設計思想（読みやすさ・気持ちよさ・青を基調とした落ち着き）を反映。

## カラーパレット（公式 zenn-content-css 準拠）
```css
:root {
  /* 背景 */
  --c-bg-base: #0d223a;
  --c-bg-dim: #0b2c53;
  --c-bg-card: #0f2744;
  --c-bg-code: #2e445c;
  --c-bg-code-block: #1a2638;

  /* テキスト */
  --c-text-main: #c8d6e5;
  --c-text-heading: #dee4ed;
  --c-text-subtle: #acbcc7;
  --c-text-link: #3ea8ff;

  /* ボーダー */
  --c-border: #2e445c;
  --c-border-emphasis: #344c69;

  /* アクセント */
  --c-blue-500: #3ea8ff;
  --c-blue-600: #0f83fd;

  /* セマンティック */
  --c-success: #34d399;
  --c-warning: #e5a21a;
  --c-error: #c63939;
}
```

## タイポグラフィ
```css
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Hiragino Sans',
               'Hiragino Kaku Gothic ProN', 'Noto Sans JP', sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  line-height: 1.9;
  letter-spacing: 0.02em;
  font-size: 16px;
}
```

## 角丸（Zenn variables.scss 準拠）
```
4px   ... インラインコード、小さい要素
7px   ... カード、ボタン
10px  ... コンテナ
14px  ... 大きなカード
```

## 見出し
```
h1: 1.7em, border-bottom: 1px solid var(--c-border)
h2: 1.5em, border-bottom: 1px solid var(--c-border)
h3: 1.3em
h4: 1.1em
```

Sources:
- カラーパレット: https://github.com/zenn-dev/zenn-editor/blob/main/packages/zenn-content-css/src/index.scss
- 角丸・ブレークポイント: https://github.com/zenn-dev/zenn-editor/blob/main/packages/zenn-content-css/src/_variables.scss
- 見出し・コンテンツ: https://github.com/zenn-dev/zenn-editor/blob/main/packages/zenn-content-css/src/_content.scss
- ダークモード実装: https://zenn.dev/team_zenn/articles/zenn-darkmode-system
- catnose氏の設計思想: https://levtech.jp/media/article/interview/detail_283/
