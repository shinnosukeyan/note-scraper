# Note Scraper - 復旧版

Note記事をスクレイピングするためのツールです。

## 機能

- Note記事のタイトルと本文を抽出
- 複数URLの一括処理
- CSV/JSON形式での出力
- ブラウザ自動化によるJavaScript対応

## セットアップ

1. 仮想環境を有効化
```bash
source venv/bin/activate
```

2. Playwrightのブラウザをインストール
```bash
playwright install chromium
```

## 使い方

### 単一URLのスクレイピング
```bash
python note_scraper.py https://note.com/example/n/article
```

### 複数URLのスクレイピング
```bash
python note_scraper.py url1 url2 url3
```

### URLリストファイルから読み込み
```bash
python note_scraper.py -f urls.txt
```

### オプション
- `-o, --output`: 出力ファイル名（デフォルト: scraped_notes）
- `--format`: 出力形式 (csv/json/both)
- `--no-headless`: ブラウザを表示モードで実行

## 出力ファイル

- `scraped_notes.csv`: スクレイピング結果（CSV形式）
- `scraped_notes.json`: スクレイピング結果（JSON形式）