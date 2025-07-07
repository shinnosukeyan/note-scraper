#!/usr/bin/env python3
"""
Note Scraper Simple - シンプル版
ログイン後、Claude Codeで「ログイン完了」と入力するだけ
"""

import asyncio
import sys
import os
from datetime import datetime
from typing import List, Dict, Optional
import pandas as pd
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, Page, Browser
import argparse
import json
import re
import time
from urllib.parse import urljoin, urlparse


class NoteScraperSimple:
    """シンプル版Noteスクレイパー"""
    
    def __init__(self, headless: bool = False):
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.base_url = "https://note.com"
        
    async def initialize(self):
        """ブラウザを初期化"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=self.headless,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        context = await self.browser.new_context(
            viewport={'width': 1280, 'height': 720}
        )
        self.page = await context.new_page()
        
    async def close(self):
        """ブラウザを閉じる"""
        if self.browser:
            await self.browser.close()
            
    async def wait_for_simple_login(self, author_url: str):
        """シンプルログイン待機"""
        print("\n" + "="*60)
        print("🔐 シンプルログインモード")
        print("="*60)
        print("1. ブラウザでログインしてください")
        print("2. Claude Codeで「ログイン完了」と入力してください")
        print("="*60)
        
        # 記事一覧ページに移動
        article_list_url = author_url.rstrip('/') + '/all'
        
        try:
            await self.page.goto(article_list_url, wait_until="domcontentloaded")
            await self.page.wait_for_timeout(3000)
            print(f"✅ ページを開きました: {article_list_url}")
        except Exception as e:
            print(f"❌ エラー: {e}")
            
        # ファイル待機
        login_file = os.path.join(os.getcwd(), "simple_login.txt")
        print(f"📁 待機中... simple_login.txt の作成を待っています")
        
        while True:
            if os.path.exists(login_file):
                break
            time.sleep(1)
            print(".", end="", flush=True)
            
        os.remove(login_file)
        print("\n✅ ログイン完了！")
        
    async def auto_load_all_articles(self):
        """「もっとみる」を自動クリック"""
        print("🔄 全記事を読み込み中...")
        
        for attempt in range(100):
            try:
                # 「もっとみる」ボタンを探す
                more_selectors = [
                    'button:has-text("もっとみる")',
                    'button:has-text("もっと見る")',
                    '[data-testid="load-more"]'
                ]
                
                button_found = False
                for selector in more_selectors:
                    try:
                        button = await self.page.query_selector(selector)
                        if button:
                            await button.scroll_into_view_if_needed()
                            await self.page.wait_for_timeout(500)
                            await button.click()
                            print(f"  🔄 {attempt + 1}回目クリック")
                            button_found = True
                            await self.page.wait_for_timeout(2000)
                            break
                    except:
                        continue
                
                if not button_found:
                    # スクロールしてみる
                    await self.page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                    await self.page.wait_for_timeout(2000)
                    
                    # 記事数チェック
                    links = await self.page.query_selector_all('a[href*="/n/"]')
                    print(f"  記事数: {len(links)}")
                    
                    if attempt > 5:  # 5回試してだめなら終了
                        break
                        
            except Exception as e:
                print(f"  エラー: {e}")
                break
                
        print("✅ 記事読み込み完了")
        
    async def collect_articles(self) -> List[Dict]:
        """記事を収集"""
        print("📝 記事を収集中...")
        
        articles = []
        all_links = await self.page.query_selector_all('a[href*="/n/"]')
        
        for link in all_links:
            try:
                href = await link.get_attribute('href')
                if href and '/n/' in href and re.match(r'.*/n/[a-zA-Z0-9_-]+', href):
                    full_url = urljoin(self.base_url, href)
                    full_url = full_url.split('?')[0].split('#')[0]
                    
                    if '/info/n/' not in full_url and not any(a['url'] == full_url for a in articles):
                        articles.append({'url': full_url})
            except:
                continue
                
        print(f"✅ {len(articles)} 記事を収集")
        return articles
        
    async def scrape_article(self, url: str, index: int, total: int) -> Dict:
        """記事内容を取得"""
        print(f"📄 {index}/{total}: {url}")
        
        try:
            await self.page.goto(url, wait_until="domcontentloaded")
            await self.page.wait_for_timeout(1000)
            
            content = await self.page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            data = {
                'url': url,
                'タイトル': '',
                '本文': '',
                '公開日': '',
                '価格': 'N/A',
                '購入状況': '購入済み or 無料'
            }
            
            # タイトル
            page_title = await self.page.title()
            if page_title and '｜note' in page_title:
                data['タイトル'] = page_title.split('｜note')[0].strip()
            
            # 公開日
            time_elem = soup.select_one('time')
            if time_elem:
                data['公開日'] = time_elem.get('datetime', '')
                
            # 本文
            paragraphs = soup.find_all('p')
            data['本文'] = '\n'.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
            
            # 有料チェック
            if '有料' in content or '続きをみるには' in content:
                data['価格'] = '有料'
                
            print(f"✅ '{data['タイトル'][:20]}...'")
            return data
            
        except Exception as e:
            return {
                'url': url,
                'タイトル': f'エラー',
                '本文': f'エラー: {str(e)}',
                '公開日': '',
                '価格': 'N/A',
                '購入状況': 'エラー'
            }
            
    async def run(self, author_url: str):
        """実行"""
        await self.initialize()
        
        try:
            await self.wait_for_simple_login(author_url)
            await self.auto_load_all_articles()
            
            articles = await self.collect_articles()
            if not articles:
                print("❌ 記事が見つかりません")
                return
                
            print(f"\n🚀 {len(articles)} 記事をスクレイピング開始")
            
            results = []
            for i, article in enumerate(articles, 1):
                result = await self.scrape_article(article['url'], i, len(articles))
                results.append(result)
                
                if i % 10 == 0:
                    print(f"💾 {i} 記事完了")
                    
                await asyncio.sleep(1)
                
            # CSV保存
            df = pd.DataFrame(results)
            df.insert(0, '番号', range(1, len(df) + 1))
            
            columns = ['番号', '公開日', 'タイトル', '本文', '価格', '購入状況']
            df = df[columns]
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            filename = f"ihayato_simple_{timestamp}.csv"
            
            df.to_csv(filename, index=False, encoding='utf-8-sig')
            
            file_size = os.path.getsize(filename) / 1024
            print(f"\n🎉 完了! {len(results)} 記事を {filename} に保存")
            print(f"📁 サイズ: {file_size:.1f} KB")
            
        finally:
            await self.close()


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('url', help='著者URL')
    parser.add_argument('--headless', action='store_true')
    
    args = parser.parse_args()
    
    print("🚀 Note Scraper Simple 開始")
    
    scraper = NoteScraperSimple(headless=args.headless)
    await scraper.run(args.url)


if __name__ == "__main__":
    asyncio.run(main())