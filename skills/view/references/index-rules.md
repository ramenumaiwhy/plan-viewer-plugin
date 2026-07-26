# index-rules: index.html 更新ルール

## ファイル命名

- 個別ページ: `YYYY-MM-DD_タイトル.html`（日本語OK）
- 一覧ページ: `index.html`

## index.html エントリ HTML 構造

新しいエントリを `<ul class="plan-list">` の先頭に追加（Zenn風カード形式）:

```html
<li>
  <a href="YYYY-MM-DD_タイトル.html">
    <div class="emoji-box">{{絵文字}}</div>
    <div class="card-body">
      <span class="card-title">{{タイトル}}</span>
      <div class="card-meta">
        <span>YYYY-MM-DD HH:MM</span>
      </div>
    </div>
  </a>
</li>
```

## 絵文字の選び方（Zenn の記事アイコンと同じ運用）

- 設計・plan: 📋 📐 🗺️
- 構築・実装: 🏗️ ⚙️ 🔧
- デザイン: 🎨 ✨ 💎
- 調査・分析: 🔍 📊 🧪
- 修正・改善: 🔄 🛠️ ✅
- インフラ: 🌐 🖥️ ☁️

## 相対時刻 + 自動ソート JS スクリプト

index.html の `</body>` 直前に必ず維持する。このスクリプトがないと日時が生の `YYYY-MM-DD HH:MM` のまま表示され、「3分前」のような相対表示にならない。

```html
<script>
(function(){
  var spans = document.querySelectorAll('.card-meta > span:first-child');
  for(var i=0;i<spans.length;i++){
    var raw = spans[i].textContent.trim();
    var m = raw.match(/^(\d{4}-\d{2}-\d{2})(?:\s+(\d{2}:\d{2}))?$/);
    if(!m) continue;
    var dt = new Date(m[1]+'T'+(m[2]||'00:00')+':00+09:00');
    if(isNaN(dt)) continue;
    var diff = Date.now() - dt.getTime();
    var mins = Math.floor(diff/60000);
    var hours = Math.floor(diff/3600000);
    var days = Math.floor(diff/86400000);
    var t;
    if(mins<1) t='たった今';
    else if(mins<60) t=mins+'分前';
    else if(hours<24) t=hours+'時間前';
    else if(days<30) t=days+'日前';
    else{ var mo=Math.floor(days/30); t=mo<12?mo+'ヶ月前':Math.floor(days/365)+'年前'; }
    spans[i].title=raw;
    spans[i].textContent=t;
  }
  var list = document.querySelector('.plan-list');
  if(list){
    var items = Array.from(list.querySelectorAll('li'));
    items.sort(function(a, b){
      var aT = a.querySelector('.card-meta > span:first-child');
      var bT = b.querySelector('.card-meta > span:first-child');
      var bVal = bT&&bT.title||'', aVal = aT&&aT.title||'';
      return bVal > aVal ? 1 : bVal < aVal ? -1 : 0;
    });
    items.forEach(function(item){ list.appendChild(item); });
  }
})();
</script>
```

## 日時ルール

- すべて JST（UTC+9）
- 時刻は必須 — 時刻がないと自動ソートで最下部に表示される（ソートスクリプトが `00:00` にフォールバックするため）
- 新規作成・更新時は index.html と個別ページの**両方**の時刻を更新
- 既存エントリ更新時も時刻を現在時刻（JST）に更新
- index.html: `YYYY-MM-DD HH:MM`（例: `2026-02-28 14:30`）→ JS が「◯分前」「◯時間前」に自動変換
- 個別ページ: `YYYY年M月D日 HH:MM 更新`（例: `2026年2月28日 14:30 更新`）
