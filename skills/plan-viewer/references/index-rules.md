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

## 絵文字の選び方
内容に合った絵文字を1つ選ぶ（Zennの記事アイコンと同じ運用）:
- 設計・plan: 📋 📐 🗺️
- 構築・実装: 🏗️ ⚙️ 🔧
- デザイン: 🎨 ✨ 💎
- 調査・分析: 🔍 📊 🧪
- 修正・改善: 🔄 🛠️ ✅
- インフラ: 🌐 🖥️ ☁️
