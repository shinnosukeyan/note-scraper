#!/usr/bin/env python3
"""
Note Scraper Quick - ログイン済み状態でクイックスクレイピング
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


class NoteScraperQuick:
    """クイック版Noteスクレイパー - ログイン済み前提"""
    
    def __init__(self, headless: bool = False):
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.base_url = "https://note.com"
        
    async def initialize(self):
        """ブラウザを初期化"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=self.headless)
        context = await self.browser.new_context(
            viewport={'width': 1280, 'height': 720},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        )
        self.page = await context.new_page()
        
    async def close(self):
        """ブラウザを閉じる"""
        if self.browser:
            await self.browser.close()
            
    async def load_all_articles(self):
        """すべての記事を読み込むまで「もっと見る」をクリック"""
        max_attempts = 100  # 最大100回まで
        previous_article_count = 0
        
        for attempt in range(max_attempts):
            # 現在の記事数をカウント
            current_links = await self.page.query_selector_all('a[href*="/n/"]')
            current_count = len([link for link in current_links 
                               if await self.is_article_link(link)])
            
            print(f"  記事数: {current_count} (試行 {attempt + 1})")
            
            # 記事数が増えなくなったら終了
            if current_count == previous_article_count and attempt > 0:
                print(f"  ✅ 全記事読み込み完了: {current_count}記事")
                break
                
            previous_article_count = current_count
            
            # 「もっと見る」ボタンを探してクリック
            more_button_selectors = [
                'button:has-text("もっと見る")',
                'button:has-text("さらに読み込む")',
                '[data-testid="load-more"]',
                '.load-more',
                'button[aria-label="もっと見る"]',
                'a:has-text("もっと見る")'
            ]
            
            button_found = False
            for selector in more_button_selectors:
                try:
                    button = await self.page.query_selector(selector)
                    if button:
                        # ボタンが見える位置までスクロール
                        await button.scroll_into_view_if_needed()
                        await self.page.wait_for_timeout(500)
                        
                        # ボタンをクリック
                        await button.click()
                        print(f"  🔄 「もっと見る」をクリック")
                        button_found = True
                        
                        # 読み込み待機
                        await self.page.wait_for_timeout(2000)
                        break
                        
                except Exception as e:
                    continue
            
            if not button_found:
                # ボタンが見つからない場合はスクロールで試行
                await self.page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                await self.page.wait_for_timeout(2000)
                
                # それでも記事が増えない場合は終了
                new_links = await self.page.query_selector_all('a[href*="/n/"]')
                new_count = len([link for link in new_links 
                               if await self.is_article_link(link)])
                               
                if new_count == current_count:
                    print(f"  ✅ これ以上記事が見つかりません: {new_count}記事")
                    break
                    
        print(f"🎯 最終記事数: {previous_article_count}")
        
    async def is_article_link(self, link):
        """有効な記事リンクかチェック"""
        try:
            href = await link.get_attribute('href')
            if href and '/n/' in href and not href.endswith('/n/'):
                if re.match(r'.*/n/[a-zA-Z0-9_-]+', href):
                    return '/info/n/' not in href
        except:
            pass
        return False
            
    async def get_author_articles_quick(self, author_url: str) -> List[Dict]:
        """著者の記事一覧をクイック取得"""
        articles = []
        
        # 記事タブに移動
        if not author_url.endswith('/all'):
            author_url = author_url.rstrip('/') + '/all'
            
        print(f"📖 記事一覧を取得中: {author_url}")
        
        try:
            await self.page.goto(author_url, wait_until="domcontentloaded", timeout=30000)
            await self.page.wait_for_timeout(3000)
            
            # 「もっと見る」ボタンを自動クリックして全記事を読み込み
            print("🔄 全記事を読み込み中...")
            await self.load_all_articles()
                
            # 全記事のリンクを収集
            print("📝 記事リンクを収集中...")
            all_links = await self.page.query_selector_all('a[href*="/n/"]')
            
            for link in all_links:
                if await self.is_article_link(link):
                    href = await link.get_attribute('href')
                    full_url = urljoin(self.base_url, href)
                    full_url = full_url.split('?')[0].split('#')[0]
                    
                    # 重複チェック
                    if not any(a['url'] == full_url for a in articles):
                        articles.append({'url': full_url})
                            
            print(f"✅ {len(articles)} 記事を発見しました")
            return articles
            
        except Exception as e:
            print(f"❌ エラー: {e}")
            return []
            
    async def scrape_article_content(self, url: str, index: int, total: int) -> Dict:
        """記事内容を取得"""
        print(f"📄 記事 {index}/{total}: {url}")
        
        try:
            await self.page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await self.page.wait_for_timeout(2000)
            
            # HTMLを取得して解析
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
            
            # タイトル取得
            page_title = await self.page.title()
            if page_title and '｜note' in page_title:
                data['タイトル'] = page_title.split('｜note')[0].strip()
            elif page_title:
                data['タイトル'] = page_title
                
            # 公開日取得
            time_elem = soup.select_one('time')
            if time_elem:
                data['公開日'] = time_elem.get('datetime', time_elem.get_text(strip=True))
                
            # 本文取得
            content_selectors = [
                '.note-common-styles__textnote-body',
                '.p-article__content', 
                'article .content',
                '.note-body',
                '[data-testid="article-body"]'
            ]
            
            content_text = ""
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    content_text = content_elem.get_text(separator='\n', strip=True)
                    break
                    
            if not content_text:
                # 全てのp要素から本文を抽出
                paragraphs = soup.find_all('p')
                content_text = '\n'.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
                
            data['本文'] = content_text
            
            # 有料記事チェック
            if any(phrase in content for phrase in ['有料', 'この記事は有料', '続きをみるには']):
                data['価格'] = '有料'
                if 'この続きをみるには' in content:
                    data['購入状況'] = '未購入'
                    
            print(f"✅ '{data['タイトル'][:30]}...' を取得完了")
            return data
            
        except Exception as e:
            print(f"❌ エラー: {str(e)}")
            return {
                'url': url,
                'タイトル': f'エラー: {url}',
                '本文': f'取得エラー: {str(e)}',
                '公開日': '',
                '価格': 'N/A',
                '購入状況': 'エラー'
            }
            
    async def run_scraping(self, author_url: str):
        """スクレイピング実行"""
        await self.initialize()
        
        try:
            # 記事一覧を取得
            articles = await self.get_author_articles_quick(author_url)
            
            if not articles:
                print("❌ 記事が見つかりませんでした")
                return
                
            # 各記事の内容を取得
            results = []
            for i, article in enumerate(articles, 1):
                result = await self.scrape_article_content(article['url'], i, len(articles))
                results.append(result)
                await asyncio.sleep(1.5)  # サーバー負荷軽減
                
            # CSVに保存
            df = pd.DataFrame(results)
            df.insert(0, '番号', range(1, len(df) + 1))
            
            # カラム順序を調整
            columns = ['番号', '公開日', 'タイトル', '本文', '価格', '購入状況']
            df = df[columns]
            
            # ファイル名生成
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            filename = f"ihayato_quick_{timestamp}.csv"
            filepath = os.path.join(os.getcwd(), filename)
            
            # CSV保存
            df.to_csv(filepath, index=False, encoding='utf-8-sig')
            
            # ファイルサイズ計算
            file_size = os.path.getsize(filepath) / 1024  # KB
            
            print(f"\n🎉 完了! {len(results)} 記事を {filename} に保存しました")
            print(f"📁 ファイルサイズ: {file_size:.1f} KB")
            print(f"📂 保存先: {filepath}")
            
        finally:
            await self.close()


async def main():
    parser = argparse.ArgumentParser(description='Note Scraper Quick')
    parser.add_argument('url', help='著者のnote URL')
    parser.add_argument('--headless', action='store_true', help='ヘッドレスモードで実行')
    
    args = parser.parse_args()
    
    print("🚀 Note Scraper Quick を開始")
    print(f"📝 対象: {args.url}")
    
    scraper = NoteScraperQuick(headless=args.headless)
    await scraper.run_scraping(args.url)
    
    print("\n✅ 処理完了!")


if __name__ == "__main__":
    asyncio.run(main())