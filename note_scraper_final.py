#!/usr/bin/env python3
"""
Note Scraper Final - 完全版
Note記事を取得してCSVに出力
完成データの品質で本文フォーマットを実装
"""

import asyncio
import argparse
import time
from src import NoteScraper


def parse_arguments():
    """コマンドライン引数を解析"""
    parser = argparse.ArgumentParser(description='Note記事スクレイピングツール')
    parser.add_argument('profile_url', help='プロフィールURL (例: https://note.com/ihayato)')
    parser.add_argument('--login', action='store_true', help='手動ログインモード')
    parser.add_argument('--no-headless', action='store_true', help='ブラウザを表示する')
    parser.add_argument('--limit', type=int, help='取得記事数の上限')
    
    return parser.parse_args()


async def main():
    """メイン関数"""
    args = parse_arguments()
    
    # headlessモードの設定（--no-headlessが指定されたらFalse）
    headless = not args.no_headless
    
    scraper = NoteScraper(headless=headless)
    result = await scraper.run(args.profile_url, limit=args.limit, manual_login=args.login)
    
    if result['success']:
        print(f"\n🎉 実行完了!")
        print(f"📁 ファイル: {result['filename']}")
        print(f"📊 記事数: {result['article_count']}")
        print(f"💾 サイズ: {result['file_size_mb']} MB")
    else:
        print(f"\n❌ 実行失敗: {result['error']}")


if __name__ == "__main__":
    asyncio.run(main())