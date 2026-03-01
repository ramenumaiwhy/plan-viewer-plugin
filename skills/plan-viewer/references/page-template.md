# 個別ページ HTML テンプレート

## デザインリファレンス（Zenn ダークテーマ準拠）

catnose氏の設計思想（読みやすさ・気持ちよさ・青を基調とした落ち着き）を反映。

### カラーパレット（公式 zenn-content-css 準拠）
| CSS変数 | 値 | 用途 |
|---------|-----|------|
| `--c-bg-base` | `#0d223a` | ページ背景 |
| `--c-bg-dim` | `#0b2c53` | ハイライト背景 |
| `--c-bg-card` | `#0f2744` | カード背景 |
| `--c-bg-code` | `#2e445c` | インラインコード背景 |
| `--c-text-main` | `#c8d6e5` | 本文テキスト |
| `--c-text-heading` | `#dee4ed` | 見出しテキスト |
| `--c-text-subtle` | `#acbcc7` | 補助テキスト |
| `--c-text-link` | `#3ea8ff` | リンク |
| `--c-border` | `#2e445c` | 通常ボーダー |
| `--c-border-emphasis` | `#344c69` | 強調ボーダー |
| `--c-blue-500` | `#3ea8ff` | アクセントカラー |
| `--c-blue-600` | `#0f83fd` | アクセント（ホバー） |
| `--c-success` | `#34d399` | 成功・After |
| `--c-warning` | `#e5a21a` | 警告 |
| `--c-error` | `#c63939` | エラー・Before |

### 角丸（Zenn variables.scss 準拠）
`4px`（インラインコード）→ `7px`（カード・ボタン）→ `10px`（コンテナ）→ `14px`（大カード）

### 見出しサイズ
h1: 1.7em / h2: 1.5em / h3: 1.3em / h4: 1.1em（すべて `border-bottom: 1px solid var(--c-border)` は h1, h2 のみ）

Sources: [zenn-content-css](https://github.com/zenn-dev/zenn-editor/blob/main/packages/zenn-content-css/src/index.scss) / [variables.scss](https://github.com/zenn-dev/zenn-editor/blob/main/packages/zenn-content-css/src/_variables.scss) / [ダークモード](https://zenn.dev/team_zenn/articles/zenn-darkmode-system)

---

```html
<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{{タイトル}}</title>
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
  .date {
    color: #acbcc7;
    font-size: 0.8rem;
    margin-bottom: 32px;
  }
  h2 {
    color: #dee4ed;
    font-size: 1.25rem;
    margin: 2.3em 0 1rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid #2e445c;
  }
  h3 {
    color: #dee4ed;
    font-size: 1.1rem;
    margin: 2em 0 0.5em;
  }
  p { margin-bottom: 1.2em; }
  .highlight {
    background: #0b2c53;
    border-left: 3px solid #3ea8ff;
    padding: 16px 20px;
    border-radius: 7px;
    margin-bottom: 1.5em;
    font-size: 1.05rem;
  }
  .card {
    background: #0f2744;
    border: 1px solid #2e445c;
    border-radius: 10px;
    padding: 20px;
    margin-bottom: 16px;
  }
  .step-num {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    background: #3ea8ff;
    color: #0d223a;
    width: 28px;
    height: 28px;
    border-radius: 50%;
    font-weight: bold;
    font-size: 0.85rem;
    margin-right: 10px;
    flex-shrink: 0;
  }
  .step-title {
    font-weight: bold;
    color: #dee4ed;
  }
  .step-desc {
    color: #acbcc7;
    font-size: 0.9rem;
    margin-top: 8px;
    padding-left: 38px;
  }
  ul, ol {
    margin: 1.2em 0;
    padding-left: 1.8em;
    line-height: 1.7;
  }
  li { margin: 0.4rem 0; }
  li::marker { color: #acbcc7; }
  table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.9rem;
    margin: 1.2em 0;
  }
  th, td {
    padding: 0.6rem 0.5rem;
    border: 1px solid #2e445c;
    text-align: left;
  }
  th {
    background: #0b2c53;
    color: #dee4ed;
    font-weight: 700;
  }
  td { background: #0d223a; }
  code {
    background: #2e445c;
    padding: 0.2em 0.4em;
    border-radius: 4px;
    font-size: 0.85em;
    font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
  }
  .note {
    background: #0f2744;
    border: 1px solid #2e445c;
    border-radius: 10px;
    padding: 20px;
    font-size: 0.9rem;
    color: #acbcc7;
  }
  .note p { margin-bottom: 0.8em; }
  .note p:last-child { margin-bottom: 0; }
  .before-after {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
    margin-bottom: 1.5em;
  }
  .ba-card {
    background: #0f2744;
    border: 1px solid #2e445c;
    border-radius: 7px;
    padding: 16px;
  }
  .ba-card h3 {
    font-size: 0.85rem;
    margin: 0 0 10px;
    border: none;
    padding: 0;
  }
  .ba-card.before h3 { color: #c63939; }
  .ba-card.after h3 { color: #34d399; }
  .ba-card ul {
    list-style: none;
    padding: 0;
    margin: 0;
    font-size: 0.82rem;
  }
  .ba-card ul li { margin-bottom: 4px; }
  .ba-card.before ul li::before { content: "✕ "; color: #c63939; }
  .ba-card.after ul li::before { content: "✓ "; color: #34d399; }
  /* --- Diff Box（変更の Before/After 表示） --- */
  .diff-box {
    background: #0f2744;
    border: 1px solid #2e445c;
    border-radius: 10px;
    padding: 20px;
    margin-bottom: 1.5em;
    font-size: 0.9rem;
    line-height: 1.8;
  }
  .diff-before-label, .diff-after-label {
    font-weight: bold;
    font-size: 0.8rem;
    margin-bottom: 8px;
  }
  .diff-before-label { color: #c63939; }
  .diff-after-label { color: #34d399; margin-top: 16px; }
  .diff-before-text {
    background: rgba(198, 57, 57, 0.1);
    border-left: 3px solid #c63939;
    padding: 10px 14px;
    border-radius: 4px;
    color: #e8a0a0;
    text-decoration: line-through;
  }
  .diff-after-text {
    background: rgba(52, 211, 153, 0.1);
    border-left: 3px solid #34d399;
    padding: 10px 14px;
    border-radius: 4px;
    color: #a0e8c8;
    font-weight: bold;
  }
  /* --- FAB（右下固定ボタン群） --- */
  .fab-group {
    position: fixed; bottom: 24px; right: 24px; z-index: 100;
    display: flex; flex-direction: column; align-items: center; gap: 12px;
  }
  .fab-btn {
    width: 44px; height: 44px;
    background: rgba(15,39,68,0.8); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
    border: 1px solid rgba(62,168,255,0.12); border-radius: 14px;
    display: flex; align-items: center; justify-content: center;
    cursor: pointer; box-shadow: 0 4px 20px rgba(0,0,0,0.35);
    -webkit-tap-highlight-color: transparent;
    transition: transform 0.15s ease, background 0.15s ease; padding: 0;
  }
  .fab-btn:active { transform: scale(0.9); background: rgba(11,44,83,0.95); }
  .fab-btn svg { width: 20px; height: 20px; color: rgba(62,168,255,0.7); transition: transform 0.5s cubic-bezier(0.4,0,0.2,1), color 0.15s; }
  .fab-btn:active svg { color: #3ea8ff; }
  .fab-btn.is-spinning svg { transform: rotate(360deg); }
  .fab-btn.is-active { background: rgba(62,168,255,0.25); border-color: rgba(62,168,255,0.4); }
  .fab-btn.is-active svg { color: #3ea8ff; }
  /* --- アノテーション --- */
  .ann-mode-banner {
    position: fixed; top: 0; left: 0; right: 0; z-index: 200;
    background: rgba(62,168,255,0.15); backdrop-filter: blur(8px); -webkit-backdrop-filter: blur(8px);
    border-bottom: 1px solid rgba(62,168,255,0.3);
    color: #3ea8ff; text-align: center; padding: 8px; font-size: 0.8rem; font-weight: bold;
    transform: translateY(-100%); transition: transform 0.2s ease;
  }
  .ann-mode-banner.is-visible { transform: translateY(0); }
  mark[data-ann] {
    background: rgba(62,168,255,0.2); color: #dee4ed;
    border-bottom: 2px solid #3ea8ff; cursor: pointer;
    border-radius: 2px; padding: 0 2px;
  }
  /* --- アノテーション: ボトムシート（モバイル）/ ポップオーバー（PC）--- */
  @keyframes annPopIn {
    from { opacity: 0; transform: scale(0.95) translateY(4px); }
    to { opacity: 1; transform: scale(1) translateY(0); }
  }
  @keyframes annSlideUp {
    from { transform: translateY(100%); }
    to { transform: translateY(0); }
  }
  .ann-overlay {
    display: none; position: fixed; inset: 0; z-index: 240;
    background: rgba(0,0,0,0.5); -webkit-tap-highlight-color: transparent;
  }
  .ann-overlay.is-visible { display: block; }
  .ann-popover {
    display: none; position: fixed; z-index: 250;
    background: #0f2744; border-radius: 16px 16px 0 0;
    padding: 12px 20px calc(20px + env(safe-area-inset-bottom, 0px));
    width: 100%; left: 0; bottom: 0;
    box-shadow: 0 -4px 32px rgba(0,0,0,0.5);
    border-top: 1px solid #344c69;
  }
  .ann-popover.is-visible {
    display: block;
    animation: annSlideUp 0.25s cubic-bezier(0.22, 1, 0.36, 1) forwards;
  }
  .ann-popover-grip {
    width: 36px; height: 4px; border-radius: 2px;
    background: #4a6580; margin: 0 auto 12px;
  }
  .ann-popover-selected {
    font-size: 0.9rem; color: #3ea8ff; margin-bottom: 12px;
    padding: 10px 14px; background: rgba(62,168,255,0.08);
    border-radius: 8px; line-height: 1.5;
    max-height: 72px; overflow-y: auto; word-break: break-all;
  }
  .ann-popover textarea {
    width: 100%; min-height: 56px; background: #0b2c53; color: #c8d6e5;
    border: 1px solid #2e445c; border-radius: 8px; padding: 12px 14px;
    font-family: inherit; font-size: 1rem; line-height: 1.6;
    resize: none; outline: none;
  }
  .ann-popover textarea:focus { border-color: #3ea8ff; }
  .ann-popover-actions {
    display: flex; gap: 10px; margin-top: 12px;
  }
  .ann-popover-actions button {
    flex: 1; padding: 12px 16px; border-radius: 10px; font-size: 0.95rem;
    cursor: pointer; border: none; font-family: inherit;
    min-height: 44px;
  }
  .ann-btn-cancel { background: #2e445c; color: #acbcc7; }
  .ann-btn-send { background: #3ea8ff; color: #0d223a; font-weight: bold; }
  .ann-btn-send:disabled { opacity: 0.4; }
  .ann-toast {
    position: fixed; bottom: 90px; left: 50%; transform: translateX(-50%);
    background: #34d399; color: #0d223a; padding: 10px 24px; border-radius: 20px;
    font-size: 0.9rem; font-weight: bold; z-index: 300;
    opacity: 0; transition: opacity 0.3s; pointer-events: none;
  }
  .ann-toast.is-visible { opacity: 1; }
  /* --- PC向けレスポンシブ --- */
  @media (min-width: 768px) {
    .container { max-width: 820px; padding: 40px 48px 80px; }
    h1 { font-size: 1.8rem; }
    h2 { font-size: 1.4rem; }
    h3 { font-size: 1.2rem; }
    .highlight { padding: 20px 28px; }
    .card { padding: 24px 28px; }
    .note { padding: 24px 28px; }
    table { font-size: 0.9rem; }
    th, td { padding: 0.7rem 0.8rem; }
    .before-after { gap: 20px; }
    .ba-card { padding: 20px; }
    .ann-overlay { display: none !important; }
    .ann-popover {
      width: min(440px, calc(100vw - 80px)); border-radius: 10px;
      padding: 16px; bottom: auto; left: auto;
      border: 1px solid #344c69; border-top: none;
      box-shadow: 0 8px 32px rgba(0,0,0,0.5);
    }
    .ann-popover.is-visible {
      animation: annPopIn 0.2s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
    }
    .ann-popover-grip { display: none; }
    .ann-popover-actions button { flex: none; padding: 8px 20px; min-height: 36px; }
    .fab-group { bottom: 32px; right: 32px; }
    .fab-btn { width: 48px; height: 48px; }
  }
  @media (hover: hover) {
    .fab-btn:hover { background: rgba(11,44,83,0.95); }
    .fab-btn:hover svg { color: #3ea8ff; }
    .ann-btn-cancel:hover { background: #344c69; }
    .ann-btn-send:hover { background: #0f83fd; }
  }
</style>
</head>
<body>
<div class="container">
  <a class="back" href="index.html">← 一覧に戻る</a>
  <h1>{{タイトル}}</h1>
  <div class="date">{{YYYY年M月D日 HH:MM 更新}}</div>

  <h2>一言でいうと</h2>
  <div class="highlight">{{30文字以内で本質}}</div>

  <h2>なぜこれが必要なのか</h2>
  <p>{{課題・動機＋技術的背景の補足}}</p>

  <h2>何をしたのか</h2>
  <!-- Before/After, ステップ, カードなどを使って説明 -->
  <!-- 変更を伴う plan では diff box を使う:
  <div class="diff-box">
    <div class="diff-before-label">BEFORE</div>
    <div class="diff-before-text">削除される内容をここに</div>
    <div class="diff-after-label">AFTER</div>
    <div class="diff-after-text">追加・変更される内容をここに</div>
  </div>
  -->

  <h2>ステップ / 詳細</h2>
  <!-- 具体的な手順や内容 -->

  <h2>ポイント</h2>
  <div class="note">
    <p>{{補足情報}}</p>
  </div>
</div>
<!-- ⚠️ 以下は省略禁止 — SKILL.md「必須コンポーネント」参照 -->
<!-- アノテーション: モードバナー -->
<div class="ann-mode-banner" id="annBanner">📝 質問モード — テキストを選択してね</div>
<!-- アノテーション: オーバーレイ（モバイル用） -->
<div class="ann-overlay" id="annOverlay"></div>
<!-- アノテーション: ポップオーバー / ボトムシート -->
<div class="ann-popover" id="annPopover">
  <div class="ann-popover-grip"></div>
  <div class="ann-popover-selected" id="annSelected"></div>
  <textarea id="annComment" placeholder="ここに質問を書いてね"></textarea>
  <div class="ann-popover-actions">
    <button class="ann-btn-cancel" id="annCancel">キャンセル</button>
    <button class="ann-btn-send" id="annSend">送信</button>
  </div>
</div>
<!-- アノテーション: トースト -->
<div class="ann-toast" id="annToast">✓ 質問を送信しました</div>
<!-- FABボタン群 -->
<div class="fab-group">
  <button class="fab-btn" id="annToggle" aria-label="質問モード"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg></button>
  <button class="fab-btn" id="reloadBtn" aria-label="更新"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 2v6h-6"/><path d="M3 12a9 9 0 0 1 15-6.7L21 8"/><path d="M3 22v-6h6"/><path d="M21 12a9 9 0 0 1-15 6.7L3 16"/></svg></button>
</div>
<script>
(function(){
  var annMode = false;
  var currentRange = null;
  var debounceTimer = null;
  var isMouseDown = false;
  var toggle = document.getElementById('annToggle');
  var banner = document.getElementById('annBanner');
  var popover = document.getElementById('annPopover');
  var selEl = document.getElementById('annSelected');
  var comment = document.getElementById('annComment');
  var sendBtn = document.getElementById('annSend');
  var cancelBtn = document.getElementById('annCancel');
  var toast = document.getElementById('annToast');
  var overlay = document.getElementById('annOverlay');
  var reloadBtn = document.getElementById('reloadBtn');
  var isMobile = function(){ return window.innerWidth < 768; };

  reloadBtn.addEventListener('click', function(){
    reloadBtn.classList.add('is-spinning');
    setTimeout(function(){ location.href = location.pathname + '?t=' + Date.now(); }, 500);
  });

  toggle.addEventListener('click', function(){
    annMode = !annMode;
    toggle.classList.toggle('is-active', annMode);
    banner.classList.toggle('is-visible', annMode);
    if (!annMode) hidePopover();
  });

  document.addEventListener('mousedown', function(){ isMouseDown = true; });
  document.addEventListener('mouseup', function(){
    isMouseDown = false;
    if (annMode) { clearTimeout(debounceTimer); debounceTimer = setTimeout(handleSelection, 50); }
  });
  document.addEventListener('touchstart', function(){ isMouseDown = true; }, {passive: true});
  document.addEventListener('touchend', function(){
    isMouseDown = false;
    if (annMode) { clearTimeout(debounceTimer); debounceTimer = setTimeout(handleSelection, 400); }
  }, {passive: true});

  document.addEventListener('selectionchange', function(){
    if (!annMode || isMouseDown) return;
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(handleSelection, isMobile() ? 600 : 200);
  });

  function handleSelection(){
    var sel = window.getSelection();
    if (!sel || sel.isCollapsed || !sel.toString().trim()) return;
    currentRange = sel.getRangeAt(0).cloneRange();
    selEl.textContent = sel.toString().trim();
    comment.value = '';
    showPopover(currentRange);
  }

  function showPopover(range){
    if (isMobile()) {
      popover.style.top = '';
      popover.style.left = '';
      popover.style.width = '';
      overlay.classList.add('is-visible');
      popover.classList.add('is-visible');
      setTimeout(function(){ comment.focus(); }, 200);
    } else {
      var rect = range.getBoundingClientRect();
      var left = rect.left + (rect.width / 2);
      var pw = Math.min(440, window.innerWidth - 80);
      left = Math.max(20, Math.min(left - pw / 2, window.innerWidth - pw - 20));
      var top;
      if (rect.top > 236) {
        top = rect.top - 228;
      } else {
        top = rect.bottom + 8;
      }
      popover.style.top = top + 'px';
      popover.style.left = left + 'px';
      popover.style.width = pw + 'px';
      popover.classList.add('is-visible');
      setTimeout(function(){ comment.focus(); }, 100);
    }
  }

  function hidePopover(){
    popover.classList.remove('is-visible');
    overlay.classList.remove('is-visible');
    currentRange = null;
    comment.value = '';
  }

  cancelBtn.addEventListener('click', function(){
    hidePopover();
    window.getSelection().removeAllRanges();
  });

  sendBtn.addEventListener('click', function(){
    var text = selEl.textContent;
    var q = comment.value.trim();
    if (!text) return;

    var data = {
      page: location.pathname.split('/').pop(),
      selectedText: text,
      comment: q || '(質問テキストなし — この箇所がわからない)',
      timestamp: new Date().toISOString()
    };

    if (currentRange) {
      try {
        var mark = document.createElement('mark');
        mark.setAttribute('data-ann', data.timestamp);
        currentRange.surroundContents(mark);
      } catch(e) {
        try {
          var mark2 = document.createElement('mark');
          mark2.setAttribute('data-ann', data.timestamp);
          mark2.appendChild(currentRange.extractContents());
          currentRange.insertNode(mark2);
        } catch(e2){}
      }
    }

    window.getSelection().removeAllRanges();
    hidePopover();

    fetch('/api/questions', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(data)
    }).then(function(){ showToast(); })
      .catch(function(){ showToast('送信失敗…'); });
  });

  function showToast(msg){
    toast.textContent = msg || '✓ 質問を送信しました';
    toast.classList.add('is-visible');
    setTimeout(function(){ toast.classList.remove('is-visible'); }, 2000);
  }

  overlay.addEventListener('click', function(){ hidePopover(); });
  document.addEventListener('mousedown', function(e){
    if (!popover.contains(e.target) && e.target !== toggle && e.target !== overlay && popover.classList.contains('is-visible')){
      hidePopover();
    }
  });
})();
</script>
</body>
</html>
```
