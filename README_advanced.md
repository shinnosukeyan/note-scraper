# Note Scraper Advanced - 高機能版

著者のNote記事を一括でスクレイピングし、構造を保持したまま保存するツールです。

## 主な機能

1. **著者の全記事を自動収集**
   - 著者ページから全記事リストを取得
   - 古い順に通し番号付けて保存

2. **記事構造の完全保持**
   - 改行・段落を維持
   - 太字（**テキスト**）の保持
   - 画像の情報（[画像: 説明] + URL）
   - リンクの保持（[テキスト](URL)）
   - 引用の保持（> 引用文）

3. **ログイン対応**
   - 手動ログインモードで有料記事にも対応
   - ログイン状態を維持してスクレイピング

## 使い方

### 1. セットアップ
```bash
cd /Users/yusukeohata/Desktop/development/note-scraper
./setup.sh
```

### 2. 基本的な使用方法

#### 公開記事のみ取得
```bash
source venv/bin/activate
python note_scraper_advanced.py https://note.com/ikedahayato
```

#### ログインして全記事取得（推奨）
```bash
python note_scraper_advanced.py https://note.com/ikedahayato --login --no-headless
```

1. ブラウザが開きます
2. 手動でNoteにログイン
3. ログイン完了後、ターミナルでEnterキー
4. 自動的に全記事の収集開始

### 3. 出力ファイル

デフォルトでは `著者名_notes.csv` として保存されます。

#### CSV形式
- 番号：古い順の通し番号
- 公開日：記事の公開日時
- タイトル：記事タイトル
- 本文：構造を保持した本文
- 価格：N/A or 有料
- 購入状況：購入済み or 無料 or 未購入

### 4. オプション

- `--no-headless`：ブラウザを表示（デバッグ用）
- `--login`：手動ログインモード
- `-o, --output`：出力ファイル名指定

## 実行例

イケハヤさんの全記事を取得：
```bash
python note_scraper_advanced.py https://note.com/ikedahayato --login --no-headless -o イケハヤ_note
```

## 注意事項

- 大量の記事がある場合、時間がかかります
- サーバー負荷軽減のため、記事間で1秒の待機時間があります
- ログインが必要な記事は `--login` オプションを使用してください