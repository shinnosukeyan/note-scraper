#!/usr/bin/env python3
"""
既存ブラウザからの直接抽出
"""

import asyncio
import sys
import os
from datetime import datetime
from typing import List, Dict, Optional
import pandas as pd
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
import re
from urllib.parse import urljoin

async def main():
    print("📋 既存ブラウザに接続して記事を抽出します")
    print("⚠️  注意: 既に開いているブラウザを使用します")
    
    # 既存のブラウザに接続
    async with async_playwright() as p:
        # 既存のChromeブラウザに接続を試行
        try:
            browser = await p.chromium.connect_over_cdp("http://localhost:9222")
            print("✅ 既存ブラウザに接続しました")
        except:
            print("❌ 既存ブラウザに接続できませんでした")
            print("💡 新しいブラウザを起動します")
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context()
            page = await context.new_page()
            await page.goto("https://note.com/ihayato/all")
            print("✅ 新しいブラウザでページを開きました")
            print("🔄 手動でログイン→もっとみる全クリック後、Enterを押してください")
            input()
        
        # 最初のページを取得
        contexts = browser.contexts
        if contexts:
            pages = await contexts[0].pages()
            if pages:
                page = pages[0]
                print(f"📄 現在のページ: {await page.url()}")
                
                # ページ内容を解析
                content = await page.content()
                soup = BeautifulSoup(content, 'html.parser')
                
                # 記事リンクを収集
                article_links = []
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    if '/n/' in href and not href.endswith('/n/'):
                        if re.match(r'.*/n/[a-zA-Z0-9_-]+', href):
                            if '/info/n/' not in href:
                                full_url = urljoin("https://note.com", href)
                                full_url = full_url.split('?')[0].split('#')[0]
                                if full_url not in article_links:
                                    article_links.append(full_url)
                
                print(f"✅ {len(article_links)} 記事を発見しました")
                
                # 各記事をスクレイピング
                articles = []
                for i, url in enumerate(article_links, 1):
                    print(f"📄 記事 {i}/{len(article_links)}: {url}")
                    
                    try:
                        await page.goto(url)
                        await page.wait_for_timeout(2000)
                        
                        # タイトル取得
                        title = await page.title()
                        if title and '｜note' in title:
                            title = title.split('｜note')[0].strip()
                        
                        # 本文取得
                        content = await page.content()
                        soup = BeautifulSoup(content, 'html.parser')
                        
                        article_body = soup.find('div', class_='note-common-styles__textnote-body')
                        body_text = article_body.get_text(strip=True) if article_body else ""
                        
                        # 日付取得
                        date_element = soup.find('time')
                        date = date_element['datetime'] if date_element and date_element.get('datetime') else ""
                        
                        # 価格情報
                        price_element = soup.find('span', string=re.compile(r'￥|円'))
                        price = "有料" if price_element else "無料"
                        purchase_status = "購入済み or 無料" if price_element else "無料"
                        
                        articles.append({
                            '番号': i,
                            '公開日': date,
                            'タイトル': title,
                            '本文': body_text,
                            '価格': price,
                            '購入状況': purchase_status
                        })
                        
                        print(f"✅ '{title[:50]}...' を取得完了")
                        
                    except Exception as e:
                        print(f"❌ エラー: {e}")
                        continue
                    
                    await asyncio.sleep(1.5)
                
                # CSV保存
                timestamp = datetime.now().strftime("%Y%m%d_%H%M")
                filename = f"ihayato_extracted_{timestamp}.csv"
                
                df = pd.DataFrame(articles)
                df.to_csv(filename, index=False, encoding='utf-8-sig')
                
                print(f"\n🎉 完了! {len(articles)} 記事を {filename} に保存しました")
                
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())