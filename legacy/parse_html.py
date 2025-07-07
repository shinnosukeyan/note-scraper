#!/usr/bin/env python3
"""
HTML内容から記事を抽出
"""

import sys
import os
from datetime import datetime
from typing import List, Dict
import pandas as pd
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin

def extract_articles_from_html(html_content: str):
    """HTMLから記事を抽出"""
    soup = BeautifulSoup(html_content, 'html.parser')
    
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
    
    # 記事情報を抽出
    articles = []
    for i, url in enumerate(article_links, 1):
        title = f"記事{i}"  # 基本タイトル
        
        # URLから記事IDを抽出
        article_id = url.split('/n/')[-1] if '/n/' in url else ""
        
        articles.append({
            '番号': i,
            '公開日': "",
            'タイトル': title,
            '本文': f"記事URL: {url}",
            '価格': "不明",
            '購入状況': "不明",
            'URL': url
        })
    
    return articles

def main():
    html_file = "page_source.html"
    
    if not os.path.exists(html_file):
        print(f"❌ {html_file} が見つかりません")
        print("📋 手順:")
        print("1. ブラウザで右クリック→「ページのソースを表示」")
        print("2. 全選択（Cmd+A）→コピー（Cmd+C）")
        print("3. テキストエディタで page_source.html として保存")
        print("4. このスクリプトを再実行")
        return
    
    print(f"📄 {html_file} を読み込み中...")
    
    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # 記事を抽出
    articles = extract_articles_from_html(html_content)
    
    if not articles:
        print("❌ 記事が見つかりませんでした")
        return
    
    # CSV保存
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    filename = f"ihayato_from_html_{timestamp}.csv"
    
    df = pd.DataFrame(articles)
    df.to_csv(filename, index=False, encoding='utf-8-sig')
    
    print(f"🎉 完了! {len(articles)} 記事を {filename} に保存しました")

if __name__ == "__main__":
    main()