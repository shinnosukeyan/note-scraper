#!/usr/bin/env python3
"""
Note Scraper - 基本的なスクレイピング機能を提供
復旧版 - 最小限の機能実装
"""

import asyncio
import sys
from datetime import datetime
from typing import List, Dict, Optional
import pandas as pd
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, Page, Browser
import argparse
import json


class NoteScraper:
    """Noteプラットフォームからコンテンツをスクレイピング"""
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        
    async def initialize(self):
        """ブラウザを初期化"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=self.headless)
        self.page = await self.browser.new_page()
        
    async def close(self):
        """ブラウザを閉じる"""
        if self.browser:
            await self.browser.close()
            
    async def scrape_article(self, url: str) -> Dict:
        """記事をスクレイピング"""
        if not self.page:
            await self.initialize()
            
        try:
            await self.page.goto(url, wait_until="networkidle")
            await self.page.wait_for_timeout(2000)  # コンテンツ読み込み待機
            
            # ページのHTMLを取得
            content = await self.page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            # 基本的な情報を抽出
            data = {
                'url': url,
                'scraped_at': datetime.now().isoformat(),
                'title': '',
                'author': '',
                'content': '',
                'likes': 0
            }
            
            # タイトルの抽出
            title_elem = soup.find('h1')
            if title_elem:
                data['title'] = title_elem.get_text(strip=True)
                
            # 本文の抽出
            article_elem = soup.find('article')
            if article_elem:
                data['content'] = article_elem.get_text(strip=True)
            else:
                # articleタグがない場合は本文と思われる部分を探す
                main_elem = soup.find('main') or soup.find('div', class_='content')
                if main_elem:
                    data['content'] = main_elem.get_text(strip=True)
                    
            return data
            
        except Exception as e:
            print(f"Error scraping {url}: {str(e)}")
            return {'url': url, 'error': str(e)}
            
    async def scrape_multiple(self, urls: List[str]) -> List[Dict]:
        """複数のURLをスクレイピング"""
        results = []
        for i, url in enumerate(urls, 1):
            print(f"Scraping {i}/{len(urls)}: {url}")
            result = await self.scrape_article(url)
            results.append(result)
            await asyncio.sleep(1)  # サーバー負荷軽減のため待機
        return results


def save_to_csv(data: List[Dict], filename: str = "scraped_notes.csv"):
    """結果をCSVファイルに保存"""
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False, encoding='utf-8-sig')
    print(f"Saved {len(data)} items to {filename}")


def save_to_json(data: List[Dict], filename: str = "scraped_notes.json"):
    """結果をJSONファイルに保存"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(data)} items to {filename}")


async def main():
    parser = argparse.ArgumentParser(description="Note記事スクレイパー")
    parser.add_argument("urls", nargs="*", help="スクレイピングするURL")
    parser.add_argument("-f", "--file", help="URLリストファイル")
    parser.add_argument("-o", "--output", default="scraped_notes", help="出力ファイル名（拡張子なし）")
    parser.add_argument("--format", choices=["csv", "json", "both"], default="csv", help="出力形式")
    parser.add_argument("--no-headless", action="store_true", help="ブラウザを表示")
    
    args = parser.parse_args()
    
    # URLリストの準備
    urls = args.urls
    if args.file:
        with open(args.file, 'r') as f:
            file_urls = [line.strip() for line in f if line.strip()]
            urls.extend(file_urls)
            
    if not urls:
        print("Error: URLが指定されていません")
        sys.exit(1)
        
    # スクレイピング実行
    scraper = NoteScraper(headless=not args.no_headless)
    try:
        results = await scraper.scrape_multiple(urls)
        
        # 結果を保存
        if args.format in ["csv", "both"]:
            save_to_csv(results, f"{args.output}.csv")
        if args.format in ["json", "both"]:
            save_to_json(results, f"{args.output}.json")
            
    finally:
        await scraper.close()


if __name__ == "__main__":
    asyncio.run(main())