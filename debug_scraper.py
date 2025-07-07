#!/usr/bin/env python3
"""
デバッグ用スクレイパー - 問題を特定するため
"""

import asyncio
from playwright.async_api import async_playwright
import re
from urllib.parse import urljoin

async def debug_note_page(author_url: str):
    """Note著者ページのデバッグ"""
    
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=False)
    page = await browser.new_page()
    
    try:
        print(f"🔍 デバッグ開始: {author_url}")
        
        # ページにアクセス
        await page.goto(author_url, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(5000)
        
        print(f"📄 現在のURL: {page.url}")
        print(f"📄 ページタイトル: {await page.title()}")
        
        # より詳細なリンク解析
        all_links = await page.query_selector_all('a[href]')
        print(f"🔗 全リンク数: {len(all_links)}")
        
        note_links = []
        other_links = []
        
        for i, link in enumerate(all_links):
            href = await link.get_attribute('href')
            if href:
                text = await link.text_content() or ""
                # note記事リンクの検出
                if '/n/' in href and re.match(r'.*/n/[a-zA-Z0-9_-]+', href):
                    full_url = urljoin("https://note.com", href)
                    full_url = full_url.split('?')[0].split('#')[0]
                    if full_url not in note_links:
                        note_links.append(full_url)
                        print(f"  📝 記事: {full_url} - '{text[:50]}...'")
                elif 'note.com' in href or href.startswith('/'):
                    other_links.append((href, text[:50]))
        
        print(f"\n📝 Note記事リンク: {len(note_links)}個")
        print(f"🔗 その他のリンク: {len(other_links)}個")
        
        # その他のリンクを詳細表示
        if len(other_links) > 0:
            print("\n🔍 その他のリンク詳細:")
            for href, text in other_links[:10]:  # 最初の10個だけ表示
                print(f"  {href} - '{text}...'")
        
        # スクロールして追加の記事を読み込む
        print("\n🔄 スクロールして追加コンテンツを読み込み中...")
        for i in range(3):
            await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            await page.wait_for_timeout(2000)
            
        # 再度リンクを取得
        all_links_after = await page.query_selector_all('a[href]')
        print(f"🔗 スクロール後のリンク数: {len(all_links_after)}")
        
        note_links_after = []
        for link in all_links_after:
            href = await link.get_attribute('href')
            if href and '/n/' in href and re.match(r'.*/n/[a-zA-Z0-9_-]+', href):
                full_url = urljoin("https://note.com", href)
                full_url = full_url.split('?')[0].split('#')[0]
                if full_url not in note_links_after:
                    note_links_after.append(full_url)
        
        print(f"📝 スクロール後の記事リンク: {len(note_links_after)}個")
        note_links = note_links_after
        
        print(f"\n✅ Note記事リンク ({len(note_links)}個):")
        for i, url in enumerate(note_links, 1):
            print(f"  {i}: {url}")
            
        # ページ構造を確認
        print(f"\n🏗️  ページ構造:")
        
        # よく使われるセレクタをチェック
        selectors_to_check = [
            ('article', 'article要素'),
            ('.note-common-styles__textnote-wrapper', 'note記事ラッパー'),
            ('.p-article', 'p-article'),
            ('[data-testid="article"]', 'テストID記事'),
            ('.o-noteContentText', 'note本文'),
        ]
        
        for selector, description in selectors_to_check:
            elements = await page.query_selector_all(selector)
            print(f"  {description}: {len(elements)}個")
            
        input("\nEnterキーでブラウザを閉じます...")
        
    finally:
        await browser.close()

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("使い方: python debug_scraper.py <author_url>")
        sys.exit(1)
        
    asyncio.run(debug_note_page(sys.argv[1]))