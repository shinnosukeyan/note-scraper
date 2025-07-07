# Note Scraper 復旧プロジェクト - 作業記録

## 現在の状況（2025-07-06 深夜）

### 🚨 重要な問題と解決策

#### 1. 取得できている記事数の問題
- **現状**: 18記事しか取得できていない（イケハヤさんは600記事以上ある）
- **原因**: 「もっとみる」ボタンの自動クリックが機能していない
- **ボタンの正しい表記**: 「もっとみる」（ひらがな）

#### 2. タイトルが取得できない問題
- **現状**: CSVファイルでタイトル列が空欄
- **原因**: ページタイトルからの抽出は成功しているが、一部の記事で失敗
- **解決済み**: note_scraper_quick.pyでは正常に取得できている

#### 3. ブラウザが途中で閉じる問題
- **原因**: タイムアウト設定、予測変換クリック時の不具合
- **対策**: 手動操作時の注意事項を明確化

### 📌 次のスレッドでやるべきこと

#### 最も確実な方法（推奨）
1. ブラウザを開く（note_scraper_manual_prep.py使用）
2. 手動でログイン
3. **手動で「もっとみる」を全部クリック**（600記事まで展開）
4. setup_done.txtファイルを作成して通知
5. 自動でスクレイピング開始

#### 使用コマンド
```bash
cd /Users/yusukeohata/Desktop/development/note-scraper
source venv/bin/activate
python note_scraper_manual_prep.py https://note.com/ihayato

# 手動作業完了後、新しいターミナルで：
touch /Users/yusukeohata/Desktop/development/note-scraper/setup_done.txt
```

### 作成済みスクリプトの概要
1. **note_scraper_stable.py** - 基本の安定版
2. **note_scraper_quick.py** - タイトル取得OK、3記事後にエラー
3. **note_scraper_manual_prep.py** - 手動準備版（推奨）
4. **note_scraper_auto.py** - 自動「もっとみる」版（動作不安定）
5. **note_scraper_simple.py** - シンプル版（18記事のみ）

### 完了したこと
1. ✅ note-scraperフォルダの調査完了
2. ✅ 基本版note_scraper.pyを作成
3. ✅ 高機能版note_scraper_advanced.pyを作成  
4. ✅ 安定版note_scraper_stable.pyを作成（最新版）
5. ✅ デバッグツールdebug_scraper.pyを作成
6. ✅ setup.shスクリプト作成
7. ✅ 正しいイケハヤアカウントを特定 (https://note.com/ihayato)
8. ✅ 記事タブ(/all)への移動機能を追加
9. ✅ 無限スクロール対応を実装
10. ✅ 18記事の取得に成功

### 現在の問題点
1. ✅ CSVの列順序を修正済み（A列=番号、B列=公開日、C列=タイトル...）
2. ✅ 1記事しか取得できない問題を解決（18記事取得成功）
3. ✅ ログイン時のタブキー問題を修正済み
4. 🔄 より多くの記事を取得する可能性があるが、現在18記事は正常に取得できている

### 次回やること
1. ✅ デバッグツールでイケハヤさんのページを調査（完了）
2. ✅ 記事取得数の問題を解決（18記事取得成功）
3. ✅ 本格的なスクレイピング実行（正常動作確認済み）
4. ⏳ YouTube一覧フォルダの復旧（未着手）

## ファイル構成
```
/Users/yusukeohata/Desktop/development/note-scraper/
├── note_scraper.py              # 基本版
├── note_scraper_advanced.py     # 高機能版
├── note_scraper_stable.py       # 安定版（メイン）
├── debug_scraper.py             # デバッグ用
├── setup.sh                     # セットアップスクリプト
├── requirements.txt             # 依存関係
├── README.md                    # 基本説明
├── README_advanced.md           # 高機能版説明
└── venv/                        # Python仮想環境
```

## 使用コマンド

### セットアップ
```bash
cd /Users/yusukeohata/Desktop/development/note-scraper
./setup.sh
```

### デバッグ実行
```bash
source venv/bin/activate
python debug_scraper.py https://note.com/ikedahayato
```

### 本格実行
```bash
python note_scraper_stable.py https://note.com/ihayato --login --no-headless
```

## 期待する成果物
- CSVファイル: 番号,公開日,タイトル,本文,価格,購入状況
- イケハヤさんの全Note記事（構造保持）
- 古い順に通し番号付き

## 技術メモ
- Playwright + BeautifulSoup4 + pandas
- 手動ログイン対応（タブキー使用禁止）
- 記事構造保持（改行・太字・リンク・画像情報）
- サーバー負荷軽減（1.5秒間隔）

## ⚠️ 次のスレッドへの申し送り事項

### 絶対に守ること
1. **指示は具体的に** - 「ターミナルアプリを開く」など明確に
2. **タイムアウトは長めに設定** - 手動作業があるため最低30分以上
3. **「もっとみる」はひらがな** - 「もっと見る」ではない
4. **ブラウザが消える問題** - 予測変換をクリックすると閉じることがある

### 現在の成果
- 18記事の取得には成功（タイトル付きも可能）
- 600記事全体の取得には手動「もっとみる」クリックが必要
- note_scraper_manual_prep.pyが最も確実

### ユーザーの状況
- 技術的な知識はあるが、曖昧な指示にイライラする
- 手動作業は問題ないが、事前に明確な説明が必要
- 時間の無駄を嫌う（同じ作業の繰り返しなど）