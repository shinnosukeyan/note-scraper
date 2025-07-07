#!/usr/bin/env python3
"""
Note Scraper Auto - 完全自動版
ログインのみ手動、その他は全自動
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


class NoteScraperAuto:
    """完全自動版Noteスクレイパー"""
    
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
                '--no-first-run',
                '--disable-background-timer-throttling'
            ]
        )
        context = await self.browser.new_context(
            viewport={'width': 1280, 'height': 720},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        )
        self.page = await context.new_page()
        
    async def close(self):
        """ブラウザを閉じる"""
        if self.browser:
            await self.browser.close()
            
    async def wait_for_login_only(self, author_url: str):
        """ログインのみ手動待機"""
        print("\n" + "="*80)
        print("🔐 ログインのみ手動モード")
        print("="*80)
        print("📋 手順:")
        print("1. ブラウザでnoteが開きます")
        print("2. 【重要】ログインしてください")
        print("3. ログイン完了後、下記の方法で通知してください")
        print("4. その後は完全自動でスクレイピングします")
        print("="*80)
        
        # 記事一覧ページに移動
        article_list_url = author_url.rstrip('/') + '/all'
        
        try:
            await self.page.goto(article_list_url, wait_until="domcontentloaded", timeout=30000)
            await self.page.wait_for_timeout(3000)
            print(f"✅ 記事一覧ページを開きました: {article_list_url}")
            print("👆 ブラウザでログインしてください")
        except Exception as e:
            print(f"❌ ページ読み込みエラー: {e}")
            
        # ユーザーの入力を待機
        print(f"\n🔑 ログイン完了後、以下のいずれかの方法で通知してください:")
        print("   1. このClaude Codeで「ログイン完了」と入力")
        print("   2. または、Macのターミナルアプリで以下のコマンドを実行:")
        print(f"      touch {os.getcwd()}/login_done.txt")
        
        try:
            input()
            print("✅ ログイン完了を確認しました")
        except EOFError:
            print("⏳ ファイル待機モードに切り替えます...")
            login_file = os.path.join(os.getcwd(), "login_done.txt")
            print(f"📁 {login_file} の作成を待機中...")
            
            while not os.path.exists(login_file):
                time.sleep(1)
                print(".", end="", flush=True)
                
            # ファイルを削除
            os.remove(login_file)
            print("\n✅ ログイン完了を確認しました")
            
        return True
        
    async def auto_load_all_articles(self):
        """「もっとみる」を自動クリックして全記事を読み込み"""
        print("🔄 全記事を自動読み込み中...")
        max_attempts = 200  # 最大200回まで
        previous_article_count = 0
        
        for attempt in range(max_attempts):
            # 現在の記事数をカウント
            current_links = await self.page.query_selector_all('a[href*="/n/"]')
            current_count = len([link for link in current_links 
                               if await self.is_article_link(link)])
            
            print(f"  記事数: {current_count} (試行 {attempt + 1})")
            
            # 記事数が増えなくなったら数回試行して終了
            if current_count == previous_article_count and attempt > 2:
                print(f"  ✅ 全記事読み込み完了: {current_count}記事")
                break
                
            previous_article_count = current_count
            
            # 「もっとみる」ボタンを探してクリック（ひらがなも含む）
            more_button_selectors = [
                'button:has-text("もっと見る")',
                'button:has-text("もっとみる")',  # ひらがな追加
                'button:has-text("さらに読み込む")',
                'button:has-text("続きを読む")',
                '[data-testid="load-more"]',
                '.load-more',
                'button[aria-label="もっと見る"]',
                'button[aria-label="もっとみる"]',  # ひらがな追加
                'a:has-text("もっと見る")',
                'a:has-text("もっとみる")'  # ひらがな追加
            ]
            
            button_found = False
            for selector in more_button_selectors:
                try:
                    button = await self.page.query_selector(selector)
                    if button:
                        # ボタンが見える位置までスクロール
                        await button.scroll_into_view_if_needed()
                        await self.page.wait_for_timeout(1000)
                        
                        # ボタンをクリック
                        await button.click()
                        print(f"  🔄 「もっとみる」をクリック")
                        button_found = True
                        
                        # 読み込み待機
                        await self.page.wait_for_timeout(3000)
                        break
                        
                except Exception as e:
                    continue
            
            if not button_found:
                # ボタンが見つからない場合はスクロールで試行
                await self.page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                await self.page.wait_for_timeout(2000)
                
                # さらに待機して無限スクロールを試行
                await self.page.wait_for_timeout(3000)
                
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
        
    async def collect_all_articles(self) -> List[Dict]:
        """現在表示されている全記事を収集"""
        print("📝 表示されている全記事を収集中...")
        
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
                    if not any(a['url'] == full_url for a in articles):
                        articles.append({'url': full_url})
            except Exception as e:
                continue
                
        print(f"✅ {len(articles)} 記事を収集しました")
        return articles
        
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
            
            # タイトル取得（ページタイトルから）
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
                if 'この続きをみるには' in content or 'ログインして続きを読む' in content:
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
            # ログインのみ手動待機
            login_success = await self.wait_for_login_only(author_url)
            if not login_success:
                print("❌ ログインがタイムアウトしました")
                return
                
            # 「もっとみる」を自動クリックして全記事読み込み
            await self.auto_load_all_articles()
            
            # 表示されている全記事を収集
            articles = await self.collect_all_articles()
            
            if not articles:
                print("❌ 記事が見つかりませんでした")
                return
                
            print(f"\n🚀 {len(articles)} 記事のスクレイピングを開始します")
            
            # 各記事の内容を取得
            results = []
            for i, article in enumerate(articles, 1):
                result = await self.scrape_article_content(article['url'], i, len(articles))
                results.append(result)
                
                # 10記事ごとに進捗表示
                if i % 10 == 0:
                    print(f"💾 進捗: {i}/{len(articles)} 記事完了")
                    
                await asyncio.sleep(1.5)  # サーバー負荷軽減
                
            # CSVに保存
            df = pd.DataFrame(results)
            df.insert(0, '番号', range(1, len(df) + 1))
            
            # カラム順序を調整
            columns = ['番号', '公開日', 'タイトル', '本文', '価格', '購入状況']
            df = df[columns]
            
            # ファイル名生成
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            filename = f"ihayato_auto_{timestamp}.csv"
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
    parser = argparse.ArgumentParser(description='Note Scraper Auto')
    parser.add_argument('url', help='著者のnote URL')
    parser.add_argument('--headless', action='store_true', help='ヘッドレスモードで実行')
    
    args = parser.parse_args()
    
    print("🚀 Note Scraper Auto を開始")
    print(f"📝 対象: {args.url}")
    
    scraper = NoteScraperAuto(headless=args.headless)
    await scraper.run_scraping(args.url)
    
    print("\n✅ 処理完了!")


if __name__ == "__main__":
    asyncio.run(main())