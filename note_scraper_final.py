#!/usr/bin/env python3
"""
Note Scraper Final - 完全版
イケハヤさんのNote記事を600記事以上取得
完成データの品質で本文フォーマットを実装
"""

import asyncio
import sys
import os
from datetime import datetime
from typing import List, Dict, Optional
import pandas as pd
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, Page, Browser
import re
import time
from urllib.parse import urljoin, urlparse


class NoteScraperFinal:
    """完全版Noteスクレイパー"""
    
    def __init__(self):
        self.headless = False
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.base_url = "https://note.com"
        self.articles: List[Dict] = []
        
    async def initialize(self):
        """ブラウザを初期化（タイムアウト完全無効化）"""
        print("🚀 Note Scraper Final を初期化中...")
        
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
        
        # タイムアウト完全無効化
        context = await self.browser.new_context(
            viewport={'width': 1280, 'height': 720},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        )
        context.set_default_timeout(0)  # タイムアウト無し
        
        self.page = await context.new_page()
        self.page.set_default_timeout(0)  # タイムアウト無し
        
        print("✅ ブラウザ初期化完了（タイムアウト無効化済み）")
    
    async def manual_setup(self, profile_url: str):
        """手動準備フェーズ"""
        print("\n" + "="*70)
        print("🔧 手動準備フェーズ開始")
        print("="*70)
        
        # 記事一覧ページに移動
        article_list_url = profile_url.rstrip('/') + '/all'
        print(f"📄 記事一覧に移動: {article_list_url}")
        
        await self.page.goto(article_list_url, wait_until="domcontentloaded", timeout=0)
        await self.page.wait_for_timeout(3000)
        
        print("\n📋 手動作業の手順:")
        print("1. 📝 ブラウザでログインしてください")
        print("2. 🔄 「もっとみる」ボタンを全部クリックしてください")
        print("   （600記事以上が全て表示されるまで）")
        print("3. ✅ 完了したら、このターミナルでEnterキーを押してください")
        print()
        print("⚠️  重要:")
        print("   - タイムアウトは設定されていません")
        print("   - ブラウザは自動で閉じません")
        print("   - 時間をかけても大丈夫です")
        print()
        
        # 完了まで待機（ファイル監視方式）
        setup_file = "/Users/yusukeohata/Desktop/development/note-scraper/setup_done.txt"
        
        print("👆 完了したら、以下のコマンドを別ターミナルで実行してください:")
        print(f"   touch {setup_file}")
        print()
        print("⏰ setup_done.txt ファイルの作成を待機中...")
        
        while True:
            if os.path.exists(setup_file):
                print("✅ セットアップ完了を確認しました")
                os.remove(setup_file)  # ファイルを削除
                break
            
            await asyncio.sleep(3)  # 3秒ごとにチェック
        
        print("✅ 手動準備完了！自動処理を開始します")
    
    async def collect_articles(self) -> List[Dict]:
        """記事リンクを収集"""
        print("\n📝 記事リンクを収集中...")
        
        articles = []
        
        # 少し待機
        await self.page.wait_for_timeout(2000)
        
        # 記事リンクを収集
        all_links = await self.page.query_selector_all('a[href*="/n/"]')
        
        for link in all_links:
            try:
                href = await link.get_attribute('href')
                if href and '/n/' in href and not href.endswith('/n/'):
                    if re.match(r'.*/n/[a-zA-Z0-9_-]+', href):
                        if '/info/n/' not in href:
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
        
        print(f"✅ {len(articles)} 記事を発見しました")
        return articles
    
    async def scrape_article(self, article: Dict, index: int, total: int) -> Dict:
        """記事をスクレイピング（完成データ品質）"""
        url = article['url']
        
        try:
            print(f"📄 記事 {index}/{total}: {url}")
            
            # ページに移動（タイムアウト無し）
            await self.page.goto(url, wait_until="domcontentloaded", timeout=0)
            await self.page.wait_for_timeout(2000)
            
            # タイトル取得
            page_title = await self.page.title()
            if page_title and '｜note' in page_title:
                article['title'] = page_title.split('｜note')[0].strip()
            
            # ページ内容を取得
            content = await self.page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            # 本文取得（完成データ品質）
            article['content'] = await self.extract_formatted_content(soup)
            
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
            
            print(f"✅ '{article['title'][:50]}...' を取得完了")
            
        except Exception as e:
            print(f"❌ スクレイピングエラー: {url} - {e}")
            article['title'] = f"エラー: {e}"
            article['content'] = f"エラーが発生しました: {e}"
        
        return article
    
    async def extract_formatted_content(self, soup: BeautifulSoup) -> str:
        """完成データ品質の本文フォーマット抽出"""
        content_parts = []
        
        # メインの記事コンテンツを取得
        article_body = soup.find('div', class_='note-common-styles__textnote-body')
        if not article_body:
            article_body = soup.find('div', class_='note-common-styles__textnote-body-container')
        
        if article_body:
            content_parts = self.process_content_elements(article_body)
        
        # 改行を「→」で結合
        return '\n'.join(content_parts)
    
    def process_content_elements(self, element) -> List[str]:
        """コンテンツ要素を処理して完成データ形式に変換"""
        parts = []
        
        for child in element.children:
            if child.name is None:  # テキストノード
                text = child.strip()
                if text:
                    parts.append(text)
            
            elif child.name == 'p':
                # パラグラフ
                p_content = self.process_paragraph(child)
                if p_content:
                    parts.append(p_content)
                    parts.append('→')  # 改行
            
            elif child.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                # 見出し
                heading_text = child.get_text(strip=True)
                if heading_text:
                    parts.append(f"**{heading_text}**")
                    parts.append('→')
            
            elif child.name == 'blockquote':
                # 引用
                quote_text = child.get_text(strip=True)
                if quote_text:
                    parts.append(f"> {quote_text}")
                    parts.append('→')
            
            elif child.name == 'hr':
                # 区切り線
                parts.append('====')
                parts.append('→')
            
            elif child.name == 'img':
                # 画像
                img_src = child.get('src', '')
                img_alt = child.get('alt', '画像')
                if img_src:
                    parts.append(f"![{img_alt}]({img_src})")
                    parts.append('→')
            
            elif child.name == 'figure':
                # 図表（画像含む）
                img = child.find('img')
                figcaption = child.find('figcaption')
                
                if img:
                    img_src = img.get('src', '')
                    img_alt = img.get('alt', '画像')
                    if img_src:
                        parts.append(f"![{img_alt}]({img_src})")
                        if figcaption:
                            caption_text = figcaption.get_text(strip=True)
                            parts.append(f"*{caption_text}*")
                        parts.append('→')
            
            elif child.name == 'div':
                # 埋め込みコンテンツ
                embed_content = self.process_embed_content(child)
                if embed_content:
                    parts.append(embed_content)
                    parts.append('→')
            
            elif child.name == 'ul' or child.name == 'ol':
                # リスト
                list_items = child.find_all('li')
                for li in list_items:
                    li_text = li.get_text(strip=True)
                    if li_text:
                        prefix = '- ' if child.name == 'ul' else '1. '
                        parts.append(f"{prefix}{li_text}")
                parts.append('→')
        
        return parts
    
    def process_paragraph(self, p_element) -> str:
        """パラグラフを処理"""
        text_parts = []
        
        for child in p_element.children:
            if child.name is None:  # テキストノード
                text = child.strip()
                if text:
                    text_parts.append(text)
            
            elif child.name == 'strong' or child.name == 'b':
                # 太字
                strong_text = child.get_text(strip=True)
                if strong_text:
                    text_parts.append(f"**{strong_text}**")
            
            elif child.name == 'em' or child.name == 'i':
                # 斜体
                em_text = child.get_text(strip=True)
                if em_text:
                    text_parts.append(f"*{em_text}*")
            
            elif child.name == 'a':
                # リンク
                link_text = child.get_text(strip=True)
                link_href = child.get('href', '')
                if link_text and link_href:
                    text_parts.append(f"[{link_text}]({link_href})")
                elif link_href:
                    text_parts.append(f"[{link_href}]({link_href})")
            
            elif child.name == 'br':
                # 改行
                text_parts.append('→')
            
            else:
                # その他の要素
                other_text = child.get_text(strip=True)
                if other_text:
                    text_parts.append(other_text)
        
        return ''.join(text_parts)
    
    def process_embed_content(self, div_element) -> str:
        """埋め込みコンテンツを処理"""
        # 埋め込みコンテンツの特定パターンを検出
        embed_link = div_element.find('a')
        if embed_link:
            href = embed_link.get('href', '')
            title_elem = embed_link.find('h3') or embed_link.find('h2') or embed_link.find('strong')
            desc_elem = embed_link.find('p')
            
            if href and title_elem:
                title = title_elem.get_text(strip=True)
                desc = desc_elem.get_text(strip=True) if desc_elem else ''
                domain = urlparse(href).netloc
                
                # 完成データ形式の埋め込み
                return f"[埋め込みコンテンツ: [**{title}***{desc}**{domain}*]({href})[{href}]({href})]({href})"
        
        return ''
    
    async def save_to_csv(self, articles: List[Dict], filename: str):
        """CSVファイルに保存"""
        print(f"\n💾 CSVファイルに保存中: {filename}")
        
        # DataFrameに変換
        df_data = []
        for i, article in enumerate(articles, 1):
            df_data.append({
                '番号': i,
                '公開日': article['date'],
                'タイトル': article['title'],
                '本文': article['content'],
                '価格': article['price'],
                '購入状況': article['purchase_status'],
                'URL': article['url']
            })
        
        df = pd.DataFrame(df_data)
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        
        # ファイルサイズ確認
        file_size = os.path.getsize(filename)
        file_size_mb = file_size / (1024 * 1024)
        
        print(f"✅ 保存完了!")
        print(f"📁 ファイル: {filename}")
        print(f"📊 記事数: {len(articles)}")
        print(f"💾 ファイルサイズ: {file_size_mb:.1f} MB")
    
    async def run(self, profile_url: str):
        """メイン処理"""
        try:
            print("🚀 Note Scraper Final を開始")
            print(f"📝 対象: {profile_url}")
            print()
            
            # 初期化
            await self.initialize()
            
            # 手動準備フェーズ
            await self.manual_setup(profile_url)
            
            # 記事収集
            articles = await self.collect_articles()
            
            if not articles:
                print("❌ 記事が見つかりませんでした")
                return
            
            # 各記事をスクレイピング
            print(f"\n📄 {len(articles)} 記事のスクレイピングを開始...")
            
            for i, article in enumerate(articles, 1):
                await self.scrape_article(article, i, len(articles))
                await asyncio.sleep(1.5)  # サーバー負荷軽減
            
            # CSV保存
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            filename = f"ihayato_final_{timestamp}.csv"
            await self.save_to_csv(articles, filename)
            
            print(f"\n🎉 スクレイピング完了!")
            print(f"📁 最終ファイル: {filename}")
            print(f"📊 取得記事数: {len(articles)}")
            
        except KeyboardInterrupt:
            print("\n⏸️  ユーザーによる中断")
        except Exception as e:
            print(f"❌ エラー: {e}")
        finally:
            if self.browser:
                await self.browser.close()


async def main():
    """メイン関数"""
    profile_url = "https://note.com/ihayato"
    
    scraper = NoteScraperFinal()
    await scraper.run(profile_url)


if __name__ == "__main__":
    asyncio.run(main())