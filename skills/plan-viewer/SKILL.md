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

## HTML生成ルール

### ファイル命名
- 個別ページ: `YYYY-MM-DD_タイトル.html`（日本語OK）
- 一覧ページ: `index.html`（新しいエントリを先頭に追加）

### index.html 更新ルール
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

**絵文字の選び方**（Zennの記事アイコンと同じ運用）:
- 設計・plan: 📋 📐 🗺️ / 構築・実装: 🏗️ ⚙️ 🔧 / デザイン: 🎨 ✨ 💎
- 調査・分析: 🔍 📊 🧪 / 修正・改善: 🔄 🛠️ ✅ / インフラ: 🌐 🖥️ ☁️

**相対時刻 + 自動ソートスクリプト**（`</body>` 直前に必ず維持）:
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
      return (bT&&bT.title||'').localeCompare(aT&&aT.title||'');
    });
    items.forEach(function(item){ list.appendChild(item); });
  }
})();
</script>
```

### 日時ルール
- すべての日時は **JST（日本標準時, UTC+9）** で表示する
- 時刻は必ず含める（日付のみは不可）— **時刻が無い場合、一覧で最下部に表示される**（自動ソートの仕様）
- コンテンツを新規作成・更新した場合、**以下の両方の時刻を必ず更新**すること:
  1. **index.html**: 該当エントリの `card-meta` 内 `<span>` の日時
  2. **個別ページ**: `.date` 要素の日時
- 既存エントリを更新した場合、該当エントリの時刻も現在時刻（JST）に更新すること
- 表示形式:
  - index.html: `YYYY-MM-DD HH:MM`（例: `2026-02-28 14:30`）— JSが「◯分前」「◯時間前」「◯日前」に自動変換する
  - 個別ページ: `YYYY年M月D日 HH:MM 更新`（例: `2026年2月28日 14:30 更新`）

### コンテンツ構成
```
一言でいうと（30文字以内で本質）
なぜこれが必要なのか（課題・動機）
何をしたのか / 何をするのか（具体的な内容）
ステップ / 進捗（手順や状態）
ポイント・補足（知っておくと良いこと）
```

### 文章ルール
- 専門用語は初出時に括弧で簡潔に解説し、用語集ページへリンクする
  - 例: `<a href="glossary.html#api">API</a>（プログラム同士が会話する窓口）`
- 括弧解説の後に**「なぜ必要か」を1文で補足**する
  - 例: 「API（プログラム同士が会話する窓口）を追加する。これがないとフロントエンドからデータを取得できない」
- 比喩から実際の概念への橋渡しをする
  - ✕ 比喩で終わり: 「hookは自動ドアのセンサーみたいなもの」
  - ○ 橋渡し: 「hookは自動ドアのセンサーみたいなもの。コードの特定の処理が実行される直前・直後に、別の処理を差し込める仕組み」
- **ファイル名・関数名**が出てきた場合、その役割を括弧で解説する
  - ○ 「`auth.ts`（ログイン認証を担当するファイル）の `validateToken`（トークンが正しいか検証する関数）を修正する」
  - ✕ 「`auth.ts` の `validateToken` を修正する」（何のファイル・関数か不明）
- **操作文**（「〇〇を△△する」）には、その操作の目的を添える
  - ○ 「dependency array（変更を監視する対象リスト）に `userId` を追加する。これにより、ユーザーが切り替わったときに画面が正しく更新される」
  - ✕ 「dependency arrayに `userId` を追加する」（なぜ追加するのか不明）
- 実装の説明は**概念レベル**に留める（コードスニペットは入れない）
  - ○ 「新しいAPIエンドポイント（受付窓口）を追加する」
  - ✕ 「`app.get('/api/users', ...)` を追加する」
- 「何がどう変わったか」を Before/After で示す
- 変更を伴う plan では **diff box** で Before/After を視覚的に示す
  - 赤背景 + 取り消し線 = 削除される部分
  - 緑背景 + 太字 = 追加・変更される部分
  - CSS クラス: `.diff-box`, `.diff-before-label/text`, `.diff-after-label/text`
  - 詳細は `references/page-template.md` の diff セクション参照

### 用語集（glossary.html）
- ファイル: `${PLAN_VIEWER_DIR}/glossary.html` — 新しい用語は `<dl>` の**アルファベット順**に追加、各用語に `id` 属性をつける（`glossary.html#api` 等）
- 用語エントリの構造: **ひとことで**（20文字以内）→ **もう少し詳しく**（2-3文）→ **このプロジェクトでは**（該当する場合のみ）
- HTMLテンプレートは不要 — 既存の `~/plan-viewer/glossary.html` 自体が生きたテンプレートとして機能する

### 必須コンポーネント（省略禁止 — 省略した場合 hook でブロックされる）
個別ページには以下を**必ず**含めること。`references/page-template.md` の該当部分をそのまま使う:
1. **FABボタン群**（`.fab-group`）— リロードボタン + アノテーションボタン
2. **アノテーションUI**（バナー・オーバーレイ・ポップオーバー・トースト）
3. **JavaScript**（アノテーション操作 + リロード処理）

テンプレートの `</div><!-- .container -->` 以降 `</body>` までの HTML・JS は**一切省略せずそのままコピー**すること。
**⚠️ FABボタン群とアノテーションUIを省略すると、Write hook でブロックされて再作成が必要になる。**

### 外部リソース禁止
- CDN、外部CSS、外部JS、Google Fonts は一切使わない
- 全てインラインCSS/JSで完結させる

## リファレンスファイル

**個別ページ作成時は `page-template.md` を必ず Read すること**（部分省略の原因になるため記憶に頼らない）。

| ファイル | 用途 | 参照タイミング |
|---------|------|-------------|
| `references/page-template.md` | 個別ページの完全テンプレート + カラーパレット | 新規ページ作成時 |
