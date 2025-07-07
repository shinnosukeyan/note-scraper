#!/bin/bash
# Note Scraper セットアップスクリプト

echo "Note Scraper セットアップを開始します..."

# 古いvenvを削除
if [ -d "venv" ]; then
    echo "既存のvenv環境を削除します..."
    rm -rf venv
fi

# 新しい仮想環境を作成
echo "新しい仮想環境を作成します..."
python3 -m venv venv

# 仮想環境を有効化
echo "仮想環境を有効化します..."
source venv/bin/activate

# 必要なパッケージをインストール
echo "必要なパッケージをインストールします..."
pip install --upgrade pip
pip install -r requirements.txt

# Playwrightのブラウザをインストール
echo "Playwrightブラウザをインストールします..."
playwright install chromium

echo "セットアップが完了しました！"
echo ""
echo "使い方:"
echo "1. 仮想環境を有効化: source venv/bin/activate"
echo "2. 基本版: python note_scraper.py <URL>"
echo "3. 高機能版: python note_scraper_advanced.py <著者URL> --login --no-headless"
echo ""
echo "高機能版の例:"
echo "python note_scraper_advanced.py https://note.com/ikedahayato --login --no-headless"