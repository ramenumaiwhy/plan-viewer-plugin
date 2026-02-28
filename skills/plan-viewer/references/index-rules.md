# index.html 更新ルール

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

## 日時の注意
- 時刻は **JST（日本標準時）** で記載する
- 既存エントリを更新した場合、該当エントリの時刻も現在時刻（JST）に更新すること
- `<span>` のテキストは `YYYY-MM-DD HH:MM` の形式で書く（JSが相対時刻に変換する）

## 相対時刻スクリプト（必須）
index.html の `</body>` 直前に以下のスクリプトを維持すること。
リロードの都度、`card-meta` 内の日時を「◯分前」「◯時間前」「◯日前」に変換する。
元の日時は `title` 属性に保持され、ホバー/長押しで確認可能。

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
})();
</script>
```

## 絵文字の選び方
内容に合った絵文字を1つ選ぶ（Zennの記事アイコンと同じ運用）:
- 設計・plan: 📋 📐 🗺️
- 構築・実装: 🏗️ ⚙️ 🔧
- デザイン: 🎨 ✨ 💎
- 調査・分析: 🔍 📊 🧪
- 修正・改善: 🔄 🛠️ ✅
- インフラ: 🌐 🖥️ ☁️
