#!/usr/bin/env python3
"""
Note Scraper No Timeout - タイムアウト無し版
手動作業を絶対に邪魔しない設計
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


class NoteScraperNoTimeout:
    """タイムアウト無し版Noteスクレイパー"""
    
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
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-web-security',
                '--disable-dev-shm-usage',
                '--no-first-run'
            ]
        )
        context = await self.browser.new_context(
            viewport={'width': 1280, 'height': 720},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        )
        
        # 重要：全てのタイムアウトを無効化
        context.set_default_timeout(0)  # 0 = タイムアウト無し
        
        self.page = await context.new_page()
        
        # ページレベルでもタイムアウトを無効化
        self.page.set_default_timeout(0)
        
    async def navigate_to_profile(self, profile_url: str):
        """プロフィールページに移動"""
        print(f"🌐 プロフィールページに移動: {profile_url}")
        
        try:
            # タイムアウト無しで移動
            await self.page.goto(profile_url, wait_until="domcontentloaded", timeout=0)
            await self.page.wait_for_timeout(3000)
            
            # 記事一覧タブに移動
            article_list_url = profile_url.rstrip('/') + '/all'
            print(f"📄 記事一覧に移動: {article_list_url}")
            await self.page.goto(article_list_url, wait_until="domcontentloaded", timeout=0)
            await self.page.wait_for_timeout(3000)
            
        except Exception as e:
            print(f"❌ ページ移動エラー: {e}")
            raise
    
    async def wait_for_manual_setup(self):
        """手動セットアップ完了まで待機"""
        print("\n" + "="*60)
        print("🛠️  手動セットアップが必要です")
        print("="*60)
        print()
        print("📋 手順:")
        print("1. ブラウザでログインしてください")
        print("2. 「もっとみる」ボタンを全部クリックしてください")
        print("3. 全記事が表示されたら、別のターミナルで以下を実行:")
        print("   touch /Users/yusukeohata/Desktop/development/note-scraper/setup_done.txt")
        print()
        print("⚠️  重要: このスクリプトは手動作業を邪魔しません")
        print("   タイムアウトは設定されていません")
        print("   ブラウザは自動で閉じません")
        print()
        
        setup_file = "/Users/yusukeohata/Desktop/development/note-scraper/setup_done.txt"
        
        # setup_done.txtファイルができるまで待機
        while True:
            if os.path.exists(setup_file):
                print("✅ セットアップ完了を確認しました")
                os.remove(setup_file)  # ファイルを削除
                break
            
            print("⏰ 手動セットアップを待機中... (Ctrl+C で中断)")
            await asyncio.sleep(5)  # 5秒ごとにチェック
    
    async def collect_all_articles(self) -> List[Dict]:
        """現在表示されている全記事を収集"""
        print("\n📝 表示されている全記事を収集中...")
        
        articles = []
        
        # 少し待機してから収集開始
        await self.page.wait_for_timeout(2000)
        
        # 全記事リンクを取得
        all_links = await self.page.query_selector_all('a[href*="/n/"]')
        
        for link in all_links:
            try:
                if await self.is_article_link(link):
                    href = await link.get_attribute('href')
                    full_url = urljoin(self.base_url, href)
                    full_url = full_url.split('?')[0].split('#')[0]
                    
                    # 重複チェック
                    if not any(article['url'] == full_url for article in articles):
                        articles.append({
                            'url': full_url,
                            'title': '',
                            'content': '',
                            'date': '',
                            'price': '',
                            'purchase_status': ''
                        })
                        
            except Exception as e:
                continue
        
        print(f"🎯 収集した記事数: {len(articles)}")
        return articles
    
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
    
    async def scrape_article(self, article: Dict) -> Dict:
        """記事をスクレイピング"""
        url = article['url']
        
        try:
            print(f"📄 スクレイピング中: {url}")
            
            # タイムアウト無しで移動
            await self.page.goto(url, wait_until="domcontentloaded", timeout=0)
            await self.page.wait_for_timeout(2000)
            
            # タイトル取得（ページタイトルから）
            page_title = await self.page.title()
            if page_title and '｜note' in page_title:
                article['title'] = page_title.split('｜note')[0].strip()
            
            # ページ内容を取得
            content = await self.page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            # 本文取得
            article_body = soup.find('div', class_='note-common-styles__textnote-body')
            if article_body:
                article['content'] = article_body.get_text(strip=True)
            
            # 公開日取得
            date_element = soup.find('time')
            if date_element and date_element.get('datetime'):
                article['date'] = date_element['datetime']
            
            # 価格情報取得
            price_element = soup.find('span', string=re.compile(r'￥|円'))
            if price_element:
                article['price'] = '有料'
                article['purchase_status'] = '購入済み or 無料'
            else:
                article['price'] = '無料'
                article['purchase_status'] = '無料'
            
            print(f"✅ 完了: {article['title'][:50]}...")
            
        except Exception as e:
            print(f"❌ スクレイピングエラー: {url} - {e}")
            article['title'] = f"エラー: {e}"
        
        return article
    
    async def save_to_csv(self, articles: List[Dict], filename: str):
        """CSVファイルに保存"""
        print(f"💾 CSVファイルに保存: {filename}")
        
        # DataFrameに変換
        df_data = []
        for i, article in enumerate(articles, 1):
            df_data.append({
                '番号': i,
                '公開日': article['date'],
                'タイトル': article['title'],
                '本文': article['content'],
                '価格': article['price'],
                '購入状況': article['purchase_status']
            })
        
        df = pd.DataFrame(df_data)
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"✅ 保存完了: {len(articles)}記事")
    
    async def run(self, profile_url: str):
        """メイン処理"""
        try:
            await self.initialize()
            await self.navigate_to_profile(profile_url)
            
            # 手動セットアップ待機
            await self.wait_for_manual_setup()
            
            # 記事収集
            articles = await self.collect_all_articles()
            
            if not articles:
                print("❌ 記事が見つかりませんでした")
                return
            
            # 各記事をスクレイピング
            for article in articles:
                await self.scrape_article(article)
                await asyncio.sleep(1.5)  # サーバー負荷軽減
            
            # CSVファイルに保存
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            filename = f"ihayato_no_timeout_{timestamp}.csv"
            await self.save_to_csv(articles, filename)
            
            print(f"\n🎉 スクレイピング完了!")
            print(f"📁 ファイル: {filename}")
            print(f"📊 記事数: {len(articles)}")
            
        except KeyboardInterrupt:
            print("\n⏸️  ユーザーによる中断")
        except Exception as e:
            print(f"❌ エラー: {e}")
        finally:
            if self.browser:
                await self.browser.close()


async def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description='Note Scraper No Timeout')
    parser.add_argument('url', help='プロフィールURL')
    parser.add_argument('--headless', action='store_true', help='ヘッドレスモード')
    
    args = parser.parse_args()
    
    scraper = NoteScraperNoTimeout(headless=args.headless)
    await scraper.run(args.url)


if __name__ == "__main__":
    asyncio.run(main())