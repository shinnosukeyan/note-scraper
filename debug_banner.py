#!/usr/bin/env python3
"""
バナー検出のデバッグスクリプト
"""

import asyncio
from src.browser import BrowserManager
from src.formatter import ContentFormatter
from bs4 import BeautifulSoup

async def debug_banner_detection():
    browser = BrowserManager()
    await browser.initialize()
    
    # 7月6日の記事を開く
    await browser.navigate_to_article('https://note.com/ihayato/n/n10da884ab703')
    
    # ページ内容を取得
    content = await browser.get_page_content()
    soup = BeautifulSoup(content, 'html.parser')
    
    # フォーマッターで処理
    formatter = ContentFormatter()
    formatted_content = formatter.extract_formatted_content(soup)
    
    # バナー部分を抽出
    lines = formatted_content.split('\n')
    print(f"📊 総行数: {len(lines)}")
    
    banner_found = False
    for i, line in enumerate(lines):
        if 'クリプトニンジャモバイル' in line:
            print(f'🔍 行 {i}: {line}')
            banner_found = True
            
        # バナー形式も探す
        if '[バナー:' in line and 'クリプト' in line:
            print(f'✅ バナー検出: {line}')
            banner_found = True
    
    if not banner_found:
        print('❌ バナーが見つかりませんでした')
        
    # 記事本文のfigure要素を直接確認
    article_body = soup.find('div', class_='note-common-styles__textnote-body')
    if article_body:
        figures = article_body.find_all('figure')
        print(f"\n🔍 figure要素数: {len(figures)}")
        
        for i, fig in enumerate(figures):
            if fig.get('embedded-service') == 'external-article':
                print(f"Figure {i}: embedded-service = external-article")
                print(f"data-src: {fig.get('data-src')}")
                
                # embedContainerの処理をテスト
                embed_container = fig.find('div', attrs={'data-name': 'embedContainer'})
                if embed_container:
                    result = formatter._process_embed_content(embed_container)
                    print(f"処理結果: {result}")
    
    await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_banner_detection())