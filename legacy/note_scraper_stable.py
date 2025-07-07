#!/usr/bin/env python3
"""
Note Scraper Stable - 安定版
ログイン問題を修正し、保存先を明確にした版本
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


class NoteScraperStable:
    """安定版Noteスクレイパー"""
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.base_url = "https://note.com"
        
    async def initialize(self):
        """ブラウザを初期化（安定化設定）"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor',
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-first-run',
                '--disable-background-timer-throttling',
                '--disable-backgrounding-occluded-windows',
                '--disable-renderer-backgrounding',
                '--disable-field-trial-config'
            ],
            slow_mo=100  # 100ms の遅延を追加して安定性向上
        )
        
        # より安定したコンテキストを作成
        context = await self.browser.new_context(
            viewport={'width': 1280, 'height': 720},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            extra_http_headers={
                'Accept-Language': 'ja-JP,ja;q=0.9,en;q=0.8'
            }
        )
        
        self.page = await context.new_page()
        
        # ページイベントのハンドリング
        self.page.on("dialog", lambda dialog: asyncio.create_task(dialog.dismiss()))
        
    async def close(self):
        """ブラウザを閉じる"""
        if self.browser:
            await self.browser.close()
            
    async def wait_for_login_stable(self):
        """改善版手動ログイン待機"""
        print("\n" + "="*80)
        print("🔐 手動ログインモード - 有料記事取得のため")
        print("="*80)
        print("📋 手順:")
        print("1. ブラウザでnote.comが開きます")
        print("2. 右上の「ログイン」ボタンをクリック")
        print("3. メールアドレス・パスワードを手動入力")
        print("4. ⚠️  重要: タブキーは使わず、全てマウスでクリックしてください")
        print("5. ⚠️  予測変換が出た場合:")
        print("   - 予測変換をクリックせず、最後まで手入力してください")
        print("   - または、Escキーで予測変換を閉じてから続行してください")
        print("6. ログイン完了後、イケハヤさんの有料記事が読める状態にしてください")
        print("7. ログイン完了したら、下記の方法で通知してください")
        print("="*80)
        print("💡 ログイン後、有料記事の本文が見えるかテストページで確認してください")
        print("="*80)
        
        # Noteのトップページに移動
        try:
            await self.page.goto(self.base_url, wait_until="domcontentloaded", timeout=30000)
            await self.page.wait_for_timeout(3000)
            print("✅ note.comを開きました - ブラウザでログインしてください")
        except Exception as e:
            print(f"❌ ページ読み込みエラー: {e}")
            
        # ユーザーの入力を待機（改良版）
        print("\n🔑 ログイン完了後、以下のいずれかの方法で続行してください:")
        print("   1. このターミナルでEnterキーを押す")
        print("   2. または、login_done.txt ファイルを作成する")
        print(f"   例: touch {os.getcwd()}/login_done.txt")
        
        try:
            input()
        except EOFError:
            print("⏳ ファイル待機モードに切り替えます...")
            login_file = os.path.join(os.getcwd(), "login_done.txt")
            print(f"📁 {login_file} の作成を待機中...")
            
            import time
            max_wait_time = 600  # 10分間待機
            elapsed_time = 0
            
            while not os.path.exists(login_file) and elapsed_time < max_wait_time:
                time.sleep(1)
                elapsed_time += 1
                if elapsed_time % 30 == 0:  # 30秒ごとにメッセージ表示
                    print(f"\n⏰ 待機中... ({elapsed_time//60}分{elapsed_time%60}秒経過)")
                    print("💡 ブラウザが閉じた場合は、Ctrl+Cで終了して再実行してください")
                else:
                    print(".", end="", flush=True)
            
            if elapsed_time >= max_wait_time:
                print("\n⏰ タイムアウト: 10分経過しました")
                return
            
            # ファイルを削除
            os.remove(login_file)
            print("\n✅ ログイン完了を確認しました")
        
        # ログイン確認
        try:
            await self.page.wait_for_timeout(2000)
            
            # より詳細なログイン確認
            current_url = self.page.url
            content = await self.page.content()
            
            print(f"🌐 現在のURL: {current_url}")
            
            # ログイン状態の詳細確認
            login_indicators = [
                ('ログアウト', 'ログアウト'),
                ('マイページ', 'mypage'),
                ('設定', 'settings'),
                ('アカウント', 'account'),
                ('プロフィール', 'profile')
            ]
            
            logged_in = False
            for indicator, desc in login_indicators:
                if indicator in content.lower():
                    print(f"✅ ログイン確認: {desc}が見つかりました")
                    logged_in = True
                    break
            
            if not logged_in:
                print("⚠️  明確なログイン状態を確認できませんが、処理を続行します")
                print("💡 有料記事が正しく取得できない場合は、ログイン状態を再確認してください")
            else:
                print("🎉 ログイン状態を確認しました！有料記事の取得が可能です")
                
        except Exception as e:
            print(f"⚠️  ログイン確認エラー: {e}")
            print("💡 処理は続行しますが、有料記事が取得できない可能性があります")
            
    async def get_author_articles_stable(self, author_url: str) -> List[Dict]:
        """著者の記事一覧を安定取得"""
        articles = []
        page_num = 1
        max_pages = 50  # 無限ループ防止
        
        print(f"\n📖 著者ページを調査中: {author_url}")
        
        # 記事タブに移動（/all を追加）
        if not author_url.endswith('/all'):
            author_url = author_url.rstrip('/') + '/all'
            print(f"📝 記事タブに移動: {author_url}")
        
        while page_num <= max_pages:
            try:
                # ページURLの構築
                if '?' in author_url:
                    url = f"{author_url}&page={page_num}"
                else:
                    url = f"{author_url}?page={page_num}"
                    
                print(f"ページ {page_num} を取得中...")
                await self.page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await self.page.wait_for_timeout(3000)
                
                # スクロールして追加記事を読み込む（無限スクロール対応）
                print("  - 追加記事を読み込み中...")
                previous_article_count = 0
                scroll_attempts = 0
                max_scroll_attempts = 5
                
                while scroll_attempts < max_scroll_attempts:
                    # 現在の記事数を取得
                    current_links = await self.page.query_selector_all('a[href*="/n/"]')
                    current_count = 0
                    for link in current_links:
                        href = await link.get_attribute('href')
                        if href and '/n/' in href and not href.endswith('/n/'):
                            if re.match(r'.*/n/[a-zA-Z0-9_-]+', href):
                                full_url = urljoin(self.base_url, href)
                                if '/info/n/' not in full_url:
                                    current_count += 1
                    
                    if current_count > previous_article_count:
                        print(f"    記事数: {previous_article_count} → {current_count}")
                        previous_article_count = current_count
                        scroll_attempts = 0  # 記事が増えたらリセット
                    else:
                        scroll_attempts += 1
                    
                    # スクロールして追加読み込み
                    await self.page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                    await self.page.wait_for_timeout(1000)
                    
                    # 読み込み中の表示があれば待機
                    loading_element = await self.page.query_selector('.loading, .spinner, [aria-label="読み込み中"]')
                    if loading_element:
                        await self.page.wait_for_timeout(3000)
                        
                print(f"  - 最終記事数: {previous_article_count}")
                
                # スクロール後に全ての記事リンクを取得
                article_links = []
                all_links = await self.page.query_selector_all('a[href]')
                debug_count = 0
                excluded_count = 0
                
                for link in all_links:
                    href = await link.get_attribute('href')
                    if href and '/n/' in href and not href.endswith('/n/'):
                        debug_count += 1
                        # note記事のURLパターンをチェック
                        if re.match(r'.*/n/[a-zA-Z0-9_-]+', href):
                            full_url = urljoin(self.base_url, href)
                            # クエリパラメータを除去
                            full_url = full_url.split('?')[0].split('#')[0]
                            # 汎用的な記事リンクを除外
                            if '/info/n/' not in full_url:
                                if not any(a['url'] == full_url for a in article_links):
                                    article_links.append({'url': full_url})
                                    # デバッグ: 最初の10記事のURLを出力
                                    if len(article_links) <= 10:
                                        print(f"    追加: {full_url}")
                                else:
                                    excluded_count += 1
                            else:
                                excluded_count += 1
                        else:
                            excluded_count += 1
                
                print(f"  - デバッグ: /n/リンク総数: {debug_count}, 除外: {excluded_count}, 有効: {len(article_links)}")
                
                print(f"  - 取得したリンク数: {len(article_links)}")
                                
                if not article_links:
                    print(f"ページ {page_num}: 記事が見つかりません - 終了")
                    break
                    
                print(f"ページ {page_num}: {len(article_links)} 記事を発見")
                
                # 重複を避けて追加
                for article in article_links:
                    if not any(a['url'] == article['url'] for a in articles):
                        articles.append(article)
                
                # 次のページの確認（より広範囲なセレクタ）
                next_selectors = [
                    'a[rel="next"]',
                    '.pagination a[aria-label="Next"]',
                    '.pagination a[aria-label="次へ"]',
                    'a[href*="page="]',
                    '.pagination .next'
                ]
                
                next_exists = None
                for selector in next_selectors:
                    try:
                        next_exists = await self.page.query_selector(selector)
                        if next_exists:
                            break
                    except:
                        continue
                
                if not next_exists:
                    print("最後のページに到達しました")
                    break
                    
                page_num += 1
                await asyncio.sleep(2)  # サーバー負荷軽減
                
            except Exception as e:
                print(f"ページ {page_num} でエラー: {e}")
                break
                
        print(f"\n✅ 合計 {len(articles)} 記事を発見しました")
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
            
            # タイトル取得（より幅広いセレクタで試行）
            title_selectors = [
                'h1', 
                '.p-article__title', 
                '.note-common-styles__textnote-title',
                '[data-testid="article-title"]',
                '.o-articleTitle',
                'article h1',
                '.note-title',
                'title'
            ]
            for selector in title_selectors:
                title_elem = soup.select_one(selector)
                if title_elem:
                    title_text = title_elem.get_text(strip=True)
                    if title_text and title_text != 'note':  # noteのデフォルトタイトルを除外
                        data['タイトル'] = title_text
                        break
                        
            # タイトルが取得できない場合、ページタイトルから抽出
            if not data['タイトル']:
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
            content_text = await self._extract_content_stable(soup)
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
            
    async def _extract_content_stable(self, soup: BeautifulSoup) -> str:
        """本文を安定取得"""
        # 本文コンテナを探す
        content_selectors = [
            '.note-common-styles__textnote-body',
            '.p-article__content', 
            'article .content',
            '.note-body'
        ]
        
        article_body = None
        for selector in content_selectors:
            article_body = soup.select_one(selector)
            if article_body:
                break
                
        if not article_body:
            # フォールバック: より広範囲で探す
            article_body = soup.find('main') or soup.find('article') or soup
            
        # テキスト抽出
        paragraphs = []
        
        # 段落ごとに処理
        for element in article_body.find_all(['p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            text = element.get_text(strip=True)
            if text and len(text) > 10:  # 短すぎるテキストは除外
                # 太字の処理
                if element.find(['strong', 'b']):
                    for bold in element.find_all(['strong', 'b']):
                        bold_text = bold.get_text(strip=True)
                        if bold_text:
                            text = text.replace(bold_text, f'**{bold_text}**')
                            
                paragraphs.append(text)
                
        # リンクの処理
        for link in article_body.find_all('a', href=True):
            link_text = link.get_text(strip=True)
            href = link.get('href')
            if link_text and href:
                paragraphs.append(f'[{link_text}]({href})')
                
        # 画像の処理
        for img in article_body.find_all('img'):
            alt = img.get('alt', '画像')
            src = img.get('src', '')
            if src:
                paragraphs.append(f'[画像: {alt}]\n{src}')
                
        return '\n\n'.join(paragraphs)
        
    async def scrape_author_complete(self, author_url: str, output_filename: str) -> str:
        """著者の全記事を完全スクレイピング"""
        full_path = os.path.abspath(output_filename)
        print(f"\n🎯 出力先: {full_path}")
        
        # 記事一覧を取得
        articles = await self.get_author_articles_stable(author_url)
        
        if not articles:
            print("❌ 記事が見つかりませんでした")
            return full_path
            
        # 各記事を取得
        results = []
        for i, article in enumerate(articles, 1):
            result = await self.scrape_article_content(article['url'], i, len(articles))
            results.append(result)
            await asyncio.sleep(1.5)  # サーバー負荷軽減
            
        # データフレーム作成
        df = pd.DataFrame(results)
        
        # 公開日でソート
        if '公開日' in df.columns:
            df['公開日_sort'] = pd.to_datetime(df['公開日'], errors='coerce')
            df = df.sort_values('公開日_sort', na_position='last')
            df = df.drop('公開日_sort', axis=1)
            
        # 通し番号を追加
        df.insert(0, '番号', range(1, len(df) + 1))
        
        # 列の順序を正しく設定: 番号,公開日,タイトル,本文,価格,購入状況
        columns_order = ['番号', '公開日', 'タイトル', '本文', '価格', '購入状況']
        existing_columns = [col for col in columns_order if col in df.columns]
        df = df[existing_columns]
        
        # 不要な列を削除
        if 'url' in df.columns:
            df = df.drop('url', axis=1)
            
        # CSV保存
        df.to_csv(output_filename, index=False, encoding='utf-8-sig')
        
        print(f"\n🎉 完了! {len(df)} 記事を {full_path} に保存しました")
        print(f"📁 ファイルサイズ: {os.path.getsize(output_filename) / 1024:.1f} KB")
        
        return full_path


async def main():
    parser = argparse.ArgumentParser(description="Note著者記事スクレイパー（安定版）")
    parser.add_argument("author_url", help="著者のNoteページURL")
    parser.add_argument("-o", "--output", help="出力ファイル名")
    parser.add_argument("--no-headless", action="store_true", help="ブラウザを表示")
    parser.add_argument("--login", action="store_true", help="手動ログイン")
    
    args = parser.parse_args()
    
    # 出力ファイル名の決定
    if args.output:
        if not args.output.endswith('.csv'):
            output_filename = f"{args.output}.csv"
        else:
            output_filename = args.output
    else:
        author_name = urlparse(args.author_url).path.strip('/')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        output_filename = f"{author_name}_{timestamp}.csv"
        
    print(f"🚀 Note Scraper 安定版を開始")
    print(f"📝 対象: {args.author_url}")
    print(f"💾 出力: {os.path.abspath(output_filename)}")
    
    scraper = NoteScraperStable(headless=not args.no_headless)
    
    try:
        await scraper.initialize()
        
        if args.login:
            await scraper.wait_for_login_stable()
            
        output_path = await scraper.scrape_author_complete(args.author_url, output_filename)
        
        print(f"\n✅ 処理完了!")
        print(f"📂 保存先: {output_path}")
        
    except KeyboardInterrupt:
        print("\n⚠️  処理が中断されました")
    except Exception as e:
        print(f"\n❌ エラー: {str(e)}")
    finally:
        await scraper.close()


if __name__ == "__main__":
    asyncio.run(main())