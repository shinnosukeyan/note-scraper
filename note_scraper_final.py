#!/usr/bin/env python3
"""
Note Scraper Final - 完全版
イケハヤさんのNote記事を600記事以上取得
完成データの品質で本文フォーマットを実装
"""

import asyncio
from src import NoteScraper


async def main():
    """メイン関数"""
    profile_url = "https://note.com/ihayato"
    
    scraper = NoteScraper(headless=False)
    result = await scraper.run(profile_url)
    
    if result['success']:
        print(f"\n🎉 実行完了!")
        print(f"📁 ファイル: {result['filename']}")
        print(f"📊 記事数: {result['article_count']}")
        print(f"💾 サイズ: {result['file_size_mb']} MB")
    else:
        print(f"\n❌ 実行失敗: {result['error']}")


if __name__ == "__main__":
    asyncio.run(main())