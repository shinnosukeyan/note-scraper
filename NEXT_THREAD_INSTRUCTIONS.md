# 次スレッド用：完全版Note Scraper制作指示書

## 🎯 **完成形**
- **ファイル名**: `note_scraper_final.py`
- **機能**: イケハヤさんのNote記事を全て取得（600記事以上）
- **出力**: `ihayato_final_YYYYMMDD_HHMM.csv`
- **形式**: 番号,公開日,タイトル,本文,価格,購入状況

## 📋 **やりたいこと（シンプル版）**
1. ブラウザを開く
2. 手動でログイン
3. 手動で「もっとみる」全部クリック
4. 完了通知
5. 自動で全記事スクレイピング
6. CSV保存

## 🏗️ **設計図**

### **構成**
```
NoteScraperFinal クラス
├── 初期化 (タイムアウト無し設定)
├── 手動準備フェーズ
│   ├── ブラウザ起動
│   ├── ログイン待機
│   └── 記事展開待機
├── 自動実行フェーズ
│   ├── 記事リンク収集
│   ├── 各記事スクレイピング
│   └── CSV保存
└── エラーハンドリング
```

### **重要な設計方針**
- **タイムアウト完全無効化** (`timeout=0`)
- **手動作業を邪魔しない**
- **シンプルな進捗表示**
- **確実な保存機能**
- **エラー時の継続処理**

## 🔧 **実装手順**

### **ステップ1: 基本クラス作成**
```python
class NoteScraperFinal:
    def __init__(self):
        self.headless = False
        self.browser = None
        self.page = None
        self.articles = []
```

### **ステップ2: 初期化メソッド**
```python
async def initialize(self):
    # Playwrightブラウザ起動
    # タイムアウト無効化設定
    # context.set_default_timeout(0)
    # page.set_default_timeout(0)
```

### **ステップ3: 手動準備メソッド**
```python
async def manual_setup(self, profile_url):
    # 1. プロフィールページ→記事一覧に移動
    # 2. ログイン指示表示
    # 3. 「もっとみる」クリック指示表示
    # 4. 完了通知待機 (input() 使用)
```

### **ステップ4: 記事収集メソッド**
```python
async def collect_articles(self):
    # 1. 現在ページから記事リンク抽出
    # 2. 重複除去
    # 3. リスト作成
```

### **ステップ5: スクレイピングメソッド**
```python
async def scrape_article(self, url):
    # 1. ページ移動 (timeout=0)
    # 2. タイトル取得 (page.title()から)
    # 3. 本文取得 (BeautifulSoupで)
    # 4. 日付・価格取得
    # 5. 1.5秒待機
```

### **ステップ6: CSV保存メソッド**
```python
async def save_csv(self, filename):
    # pandas DataFrame作成
    # CSV出力 (utf-8-sig)
    # 保存完了通知
```

## 📝 **完全なコード仕様**

### **必須要素**
- `#!/usr/bin/env python3`
- `import asyncio, pandas, BeautifulSoup, playwright`
- `async def main()` 関数
- `if __name__ == "__main__": asyncio.run(main())`

### **エラーハンドリング**
- try-except for each method
- 失敗時の継続処理
- 進捗表示の維持

### **ユーザー指示**
- 明確な手順表示
- 完了通知の方法
- 進捗状況の表示

## 🚀 **実行手順**

### **制作手順**
1. `note_scraper_final.py` を作成
2. 上記設計図通りに実装
3. エラーチェック
4. 実行テスト

### **使用手順**
```bash
cd /Users/yusukeohata/Desktop/development/note-scraper
source venv/bin/activate
python note_scraper_final.py
```

### **ユーザー作業**
1. ブラウザでログイン
2. 「もっとみる」全部クリック
3. Enterキー押下
4. 完了まで待機

## ⚠️ **重要な注意事項**

### **絶対に守ること**
- タイムアウト設定は `timeout=0` のみ
- 手動作業中はブラウザを閉じない
- エラー時も処理を継続
- 進捗を明確に表示

### **避けるべきこと**
- 複雑な自動「もっとみる」クリック
- 短いタイムアウト設定
- 複数ブラウザの同時起動
- 不明確な指示

## 🎯 **成功基準**
- **記事数**: 400記事以上取得
- **タイトル**: 90%以上取得成功
- **本文**: 95%以上取得成功
- **エラー**: 処理継続可能

## 📊 **期待する出力**
```
ihayato_final_20250707_HHMM.csv
番号,公開日,タイトル,本文,価格,購入状況,URL
1,2025-06-27T09:28:41.000+09:00,記事タイトル,記事本文...,有料,購入済み,https://note.com/ihayato/n/xxxxx
```

## 🎨 **完成データの品質仕様**

### **本文フォーマット（重要）**
参考ファイル: `/Users/yusukeohata/Desktop/youtube-chanel/URLなし/07.イケハヤ2(note).csv`

#### **必須フォーマット**
- **改行**: 「→」で表現
- **太字**: `**テキスト**`で表現
- **区切り線**: `====`で表現
- **画像**: `![画像](URL)`＋`*キャプション*`で表現
- **埋め込みコンテンツ**: `[埋め込みコンテンツ: [**タイトル***説明文**ドメイン名*](URL)[URL](URL)](URL)`

#### **具体例**
```
イケハヤです。
→
今日も山奥でコツコツ草刈りをしています。
→
**タイトルにもある通りなんですが、昨日1日で、ブログ記事を50万文字ほど書いた（生成した）んです。**
→
![画像](https://assets.st-note.com/img/1750207955-gGwutiUlyC3XoDTJbpFBE829.png?width=1200)
*朝からゴリゴリ書いてます*
→
[埋め込みコンテンツ: [**Vibe Codingサロン - AIと走る、コーディング未経験からのスタート***コーディング未経験でも、AIと一緒に夢のWebサイト・ゲーム・アプリを作ろう！900人以上が参加するコミュニティで「ナイス**vibecoding.salon*](http://vibecoding.salon/)[http://vibecoding.salon/](http://vibecoding.salon/)](http://vibecoding.salon/)
```

### **データ品質要求**
- **記事数**: 600記事（実証済み）
- **期間**: 2017年8月〜2025年6月（8年間）
- **構造**: 完全なマークダウン準拠
- **一貫性**: 全記事同じ書式で統一

---

**この指示書に従って `note_scraper_final.py` を作成してください。**
**制作から実行まで、この1つのファイルで完結させてください。**