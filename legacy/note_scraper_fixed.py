#!/usr/bin/env python3
"""
Note Scraper Fixed - 「もっとみる」ボタン修正版
18記事で止まる問題を修正
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


class NoteScraperFixed:
    """修正版Noteスクレイパー"""
    
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
            
    async def wait_for_setup(self, author_url: str):
        """手動セットアップ待機"""
        print("\n" + "="*80)
        print("🔐 手動セットアップモード")
        print("="*80)
        print("📋 手順:")
        print("1. ブラウザでnoteが開きます")
        print("2. 【重要】ログインしてください")
        print("3. 【重要】手動で「もっとみる」を全てクリックしてください")
        print("4. 600記事程度まで展開してください")
        print("5. 完了後、下記のファイルを作成してください")
        print("="*80)
        
        # 記事一覧ページに移動
        article_list_url = author_url.rstrip('/') + '/all'
        
        try:
            await self.page.goto(article_list_url, wait_until="domcontentloaded")
            await self.page.wait_for_timeout(3000)
            print(f"✅ 記事一覧ページを開きました: {article_list_url}")
        except Exception as e:
            print(f"❌ エラー: {e}")
            
        # セットアップ完了待機
        setup_file = os.path.join(os.getcwd(), "setup_done.txt")
        print(f"\n📁 セットアップ完了後、以下のファイルを作成してください:")
        print(f"   touch {setup_file}")
        print(f"   または Claude Codeで「セットアップ完了」と入力")
        
        while not os.path.exists(setup_file):
            time.sleep(1)
            print(".", end="", flush=True)
            
        os.remove(setup_file)
        print("\n✅ セットアップ完了を確認しました")
        
    async def fixed_load_more_articles(self):
        """修正版「もっとみる」クリック処理"""
        print("🔄 修正版「もっとみる」クリック処理開始...")
        
        max_attempts = 50
        previous_count = 0
        no_change_count = 0
        
        for attempt in range(max_attempts):
            print(f"\n--- 試行 {attempt + 1} ---")
            
            # 現在の記事数を確認
            current_links = await self.page.query_selector_all('a[href*="/n/"]')
            current_count = len([link for link in current_links if await self.is_valid_article_link(link)])
            
            print(f"現在の記事数: {current_count}")
            
            # 記事数が変わらない場合の処理
            if current_count == previous_count:
                no_change_count += 1
                print(f"記事数変化なし (連続{no_change_count}回)")
                if no_change_count >= 3:
                    print("✅ 全記事読み込み完了")
                    break
            else:
                no_change_count = 0
                previous_count = current_count
            
            # 「もっとみる」ボタンを探す（修正版）
            buttons = await self.page.query_selector_all('button:has-text("もっとみる")')
            print(f"「もっとみる」ボタン数: {len(buttons)}")
            
            button_clicked = False
            
            # 各ボタンを調査して有効なものをクリック
            for i, button in enumerate(buttons):
                try:
                    is_visible = await button.is_visible()
                    is_enabled = await button.is_enabled()
                    
                    print(f"  ボタン{i+1}: 可視={is_visible}, 有効={is_enabled}")
                    
                    if is_visible and is_enabled:
                        # 有効なボタンを発見
                        print(f"  ✅ ボタン{i+1}をクリック")
                        
                        # 安全にクリック
                        try:
                            await button.click()
                            button_clicked = True
                            
                            # 読み込み待機
                            await self.page.wait_for_timeout(4000)
                            
                            # 記事数の変化をチェック
                            new_links = await self.page.query_selector_all('a[href*="/n/"]')
                            new_count = len([link for link in new_links if await self.is_valid_article_link(link)])
                            
                            print(f"  クリック後の記事数: {new_count}")
                            
                            if new_count > current_count:
                                print(f"  ✅ {new_count - current_count} 記事が追加されました")
                                break
                            else:
                                print(f"  ❌ 記事数が増えていません")
                                
                        except Exception as e:
                            print(f"  ❌ クリックエラー: {str(e)}")
                            
                except Exception as e:
                    print(f"  ❌ ボタン{i+1}調査エラー: {str(e)}")
                    continue
            
            if not button_clicked:
                print("❌ 有効なボタンが見つかりません")
                
                # 代替手段: スクロールで無限読み込み
                print("🔄 スクロールで無限読み込みを試行")
                await self.page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                await self.page.wait_for_timeout(3000)
                
                # スクロール後の記事数チェック
                scroll_links = await self.page.query_selector_all('a[href*="/n/"]')
                scroll_count = len([link for link in scroll_links if await self.is_valid_article_link(link)])
                
                print(f"スクロール後の記事数: {scroll_count}")
                
                if scroll_count == current_count:
                    print("✅ これ以上記事は読み込めません")
                    break
                    
        print(f"\n🎯 最終記事数: {previous_count}")
        
    async def is_valid_article_link(self, link):
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
        """全記事を収集"""
        print("📝 全記事を収集中...")
        
        articles = []
        
        # 全記事リンクを取得
        all_links = await self.page.query_selector_all('a[href*="/n/"]')
        
        for link in all_links:
            try:
                if await self.is_valid_article_link(link):
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
            await self.page.wait_for_timeout(1500)
            
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
                paragraphs = soup.find_all('p')
                content_text = '\n'.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
                
            data['本文'] = content_text
            
            # 有料記事チェック
            if any(phrase in content for phrase in ['有料', 'この記事は有料', '続きをみるには']):
                data['価格'] = '有料'
                if 'この続きをみるには' in content or 'ログインして続きを読む' in content:
                    data['購入状況'] = '未購入'
                    
            print(f"✅ '{data['タイトル'][:30]}...' 取得完了")
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
            # 手動セットアップ待機
            await self.wait_for_setup(author_url)
            
            # 修正版「もっとみる」クリック処理
            await self.fixed_load_more_articles()
            
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
            filename = f"ihayato_fixed_{timestamp}.csv"
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
    parser = argparse.ArgumentParser(description='Note Scraper Fixed')
    parser.add_argument('url', help='著者のnote URL')
    parser.add_argument('--headless', action='store_true', help='ヘッドレスモードで実行')
    
    args = parser.parse_args()
    
    print("🚀 Note Scraper Fixed を開始")
    print(f"📝 対象: {args.url}")
    
    scraper = NoteScraperFixed(headless=args.headless)
    await scraper.run_scraping(args.url)
    
    print("\n✅ 処理完了!")


if __name__ == "__main__":
    asyncio.run(main())