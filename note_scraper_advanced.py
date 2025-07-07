#!/usr/bin/env python3
"""
Note Scraper Advanced - Note記事の完全なスクレイピングツール
著者の全記事を取得し、構造を保持したままCSV形式で保存
"""

import asyncio
import sys
import os
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import pandas as pd
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, Page, Browser
import argparse
import json
import re
import time
from urllib.parse import urljoin, urlparse


class NoteScraperAdvanced:
    """Note記事の高度なスクレイピング機能を提供"""
    
    def __init__(self, headless: bool = True):
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
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        self.page = await context.new_page()
        
    async def close(self):
        """ブラウザを閉じる"""
        if self.browser:
            await self.browser.close()
            
    async def wait_for_login(self):
        """手動ログインを待機"""
        print("\n" + "="*60)
        print("手動ログインが必要です")
        print("="*60)
        print("1. ブラウザでnote.comにアクセスします")
        print("2. 手動でログインしてください")
        print("3. ログイン完了後、Enterキーを押してください")
        print("="*60)
        
        await self.page.goto(self.base_url)
        input("\nログイン完了後、Enterキーを押してください...")
        
    async def get_author_articles(self, author_url: str) -> List[Dict]:
        """著者の全記事を取得"""
        articles = []
        page_num = 1
        
        print(f"\n著者ページを取得中: {author_url}")
        
        while True:
            # ページURLの構築
            if '?' in author_url:
                url = f"{author_url}&page={page_num}"
            else:
                url = f"{author_url}?page={page_num}"
                
            await self.page.goto(url, wait_until="networkidle")
            await self.page.wait_for_timeout(2000)
            
            # 記事リストを取得
            article_elements = await self.page.query_selector_all('article a[href*="/n/"]')
            
            if not article_elements:
                break
                
            print(f"ページ {page_num}: {len(article_elements)} 記事を発見")
            
            for element in article_elements:
                href = await element.get_attribute('href')
                if href:
                    article_url = urljoin(self.base_url, href)
                    # 重複チェック
                    if not any(a['url'] == article_url for a in articles):
                        articles.append({'url': article_url})
            
            # 次のページボタンの確認
            next_button = await self.page.query_selector('a[rel="next"]')
            if not next_button:
                break
                
            page_num += 1
            await asyncio.sleep(1)  # サーバー負荷軽減
            
        print(f"\n合計 {len(articles)} 記事を発見しました")
        return articles
        
    async def scrape_article_detail(self, url: str) -> Dict:
        """記事の詳細情報を取得"""
        try:
            await self.page.goto(url, wait_until="networkidle")
            await self.page.wait_for_timeout(2000)
            
            # ページのHTMLを取得
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
            
            # タイトルの取得
            title_elem = soup.find('h1')
            if title_elem:
                data['タイトル'] = title_elem.get_text(strip=True)
                
            # 公開日の取得
            time_elem = soup.find('time')
            if time_elem:
                data['公開日'] = time_elem.get('datetime', '')
                
            # 本文の取得（構造を保持）
            article_body = await self._extract_article_body(soup)
            data['本文'] = article_body
            
            # 有料記事のチェック
            if '有料' in content or 'この記事は有料です' in content:
                data['価格'] = '有料'
                if 'この続きをみるには' in content:
                    data['購入状況'] = '未購入'
                    
            return data
            
        except Exception as e:
            print(f"Error scraping {url}: {str(e)}")
            return {'url': url, 'error': str(e)}
            
    async def _extract_article_body(self, soup: BeautifulSoup) -> str:
        """記事本文を構造を保持して抽出"""
        # 記事本文のコンテナを探す
        article_container = None
        for selector in ['div.note-common-styles__textnote-body', 'div.p-article__content', 'article']:
            article_container = soup.select_one(selector)
            if article_container:
                break
                
        if not article_container:
            return ""
            
        # 本文を構築
        body_parts = []
        
        for element in article_container.descendants:
            if element.name is None:  # テキストノード
                text = str(element).strip()
                if text:
                    body_parts.append(text)
                    
            elif element.name == 'br':  # 改行
                body_parts.append('\n')
                
            elif element.name in ['p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                # ブロック要素の後に改行を追加
                if body_parts and not body_parts[-1].endswith('\n'):
                    body_parts.append('\n\n')
                    
            elif element.name == 'img':  # 画像
                src = element.get('src', '')
                alt = element.get('alt', '画像')
                body_parts.append(f'\n[画像: {alt}]\n{src}\n')
                
            elif element.name == 'a':  # リンク
                href = element.get('href', '')
                text = element.get_text(strip=True)
                if href and text:
                    body_parts.append(f'[{text}]({href})')
                    
            elif element.name == 'blockquote':  # 引用
                quote_text = element.get_text(strip=True)
                if quote_text:
                    body_parts.append(f'\n> {quote_text}\n')
                    
            elif element.name in ['strong', 'b']:  # 太字
                text = element.get_text(strip=True)
                if text:
                    body_parts.append(f'**{text}**')
                    
        # 結合して整形
        body_text = ''.join(body_parts)
        # 連続する改行を調整
        body_text = re.sub(r'\n{3,}', '\n\n', body_text)
        return body_text.strip()
        
    async def scrape_author(self, author_url: str) -> pd.DataFrame:
        """著者の全記事をスクレイピング"""
        # 著者名を取得
        author_name = urlparse(author_url).path.strip('/')
        print(f"\n著者: {author_name} のスクレイピングを開始")
        
        # 全記事URLを取得
        articles = await self.get_author_articles(author_url)
        
        # 公開日で古い順にソート（後で詳細取得後に再ソート）
        results = []
        
        # 各記事の詳細を取得
        for i, article in enumerate(articles, 1):
            print(f"\n記事 {i}/{len(articles)}: {article['url']}")
            detail = await self.scrape_article_detail(article['url'])
            results.append(detail)
            await asyncio.sleep(1)  # サーバー負荷軽減
            
        # データフレームに変換
        df = pd.DataFrame(results)
        
        # 公開日でソート（古い順）
        if '公開日' in df.columns:
            df['公開日_sort'] = pd.to_datetime(df['公開日'], errors='coerce')
            df = df.sort_values('公開日_sort', na_position='last')
            df = df.drop('公開日_sort', axis=1)
            
        # 通し番号を追加
        df.insert(0, '番号', range(1, len(df) + 1))
        
        # 列の順序を調整
        columns_order = ['番号', '公開日', 'タイトル', '本文', '価格', '購入状況']
        existing_columns = [col for col in columns_order if col in df.columns]
        df = df[existing_columns]
        
        return df


async def main():
    parser = argparse.ArgumentParser(description="Note著者記事スクレイパー（高機能版）")
    parser.add_argument("author_url", help="著者のNoteページURL (例: https://note.com/username)")
    parser.add_argument("-o", "--output", help="出力ファイル名（拡張子なし）")
    parser.add_argument("--no-headless", action="store_true", help="ブラウザを表示モードで実行")
    parser.add_argument("--login", action="store_true", help="手動ログインモードを使用")
    
    args = parser.parse_args()
    
    # 出力ファイル名の決定
    if args.output:
        output_filename = f"{args.output}.csv"
    else:
        author_name = urlparse(args.author_url).path.strip('/')
        output_filename = f"{author_name}_notes.csv"
        
    # スクレイピング実行
    scraper = NoteScraperAdvanced(headless=not args.no_headless)
    try:
        await scraper.initialize()
        
        # ログインが必要な場合
        if args.login:
            await scraper.wait_for_login()
            
        # 著者の記事をスクレイピング
        df = await scraper.scrape_author(args.author_url)
        
        # CSVとして保存
        df.to_csv(output_filename, index=False, encoding='utf-8-sig')
        print(f"\n✓ {len(df)} 記事を {output_filename} に保存しました")
        
        # サマリー表示
        print("\n=== スクレイピング結果 ===")
        print(f"総記事数: {len(df)}")
        if '公開日' in df.columns:
            print(f"最古の記事: {df.iloc[0]['タイトル']} ({df.iloc[0]['公開日']})")
            print(f"最新の記事: {df.iloc[-1]['タイトル']} ({df.iloc[-1]['公開日']})")
            
    finally:
        await scraper.close()


if __name__ == "__main__":
    asyncio.run(main())