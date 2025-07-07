#!/usr/bin/env python3
"""
Note Scraperの動作テスト
"""

import sys
import os

# 必要なパッケージの確認
def check_packages():
    packages = {
        'bs4': 'beautifulsoup4',
        'playwright': 'playwright',
        'pandas': 'pandas',
        'numpy': 'numpy'
    }
    
    missing = []
    for module, package in packages.items():
        try:
            __import__(module)
            print(f"✓ {package} is installed")
        except ImportError:
            print(f"✗ {package} is NOT installed")
            missing.append(package)
    
    return missing

def main():
    print("Note Scraper 動作確認")
    print("=" * 50)
    
    # パッケージチェック
    print("\n1. パッケージの確認:")
    missing = check_packages()
    
    if missing:
        print(f"\n不足しているパッケージ: {', '.join(missing)}")
        print("\n以下のコマンドでインストールしてください:")
        print(f"pip install {' '.join(missing)}")
        return
    
    # Playwrightのブラウザ確認
    print("\n2. Playwrightブラウザの確認:")
    try:
        import subprocess
        result = subprocess.run(['playwright', 'install', '--help'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✓ Playwright CLIが利用可能です")
            print("\nブラウザをインストールするには:")
            print("playwright install chromium")
        else:
            print("✗ Playwright CLIが見つかりません")
    except:
        print("✗ Playwrightコマンドの実行に失敗しました")
    
    # スクレイパーのインポート確認
    print("\n3. Note Scraperのインポート確認:")
    try:
        from note_scraper import NoteScraper
        print("✓ Note Scraperを正常にインポートできました")
        print("\n使い方の例:")
        print("python note_scraper.py https://note.com/example/n/article")
    except Exception as e:
        print(f"✗ インポートエラー: {e}")

if __name__ == "__main__":
    main()