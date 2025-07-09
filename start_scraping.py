#!/usr/bin/env python3
"""
スクレイピング実行スクリプト
保存されたブラウザセッションを使用してスクレイピングを実行
"""

import asyncio
import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright

# srcモジュールの追加
sys.path.append(str(Path(__file__).parent / 'src'))

from src.collector import ArticleCollector
from src.formatter import ContentFormatter
from src.exporter import CSVExporter
from src.scraper import NoteScraper

# 設定ファイルのパス
SESSION_FILE = "browser_session.json"
SETUP_DONE_FILE = "setup_done.txt"


async def start_scraping(limit: int = None):
    """保存されたセッションを使用してスクレイピングを実行"""
    
    # セッション情報の読み込み
    if not os.path.exists(SESSION_FILE):
        print("❌ セッション情報が見つかりません")
        print(f"💡 先に prepare_browser.py を実行してください")
        return {'success': False, 'error': 'Session file not found'}
    
    # setup_done.txtの確認
    if not os.path.exists(SETUP_DONE_FILE):
        print("❌ セットアップが完了していません")
        print(f"💡 {SETUP_DONE_FILE} ファイルを作成してください")
        return {'success': False, 'error': 'Setup not completed'}
    
    with open(SESSION_FILE, 'r', encoding='utf-8') as f:
        session_info = json.load(f)
    
    print("🚀 スクレイピングを開始します")
    print(f"📝 対象: {session_info['profile_url']}")
    print(f"🔐 セッション作成時刻: {session_info['created_at']}")
    
    # 必要なオブジェクトの初期化
    collector = ArticleCollector()
    formatter = ContentFormatter()
    exporter = CSVExporter()
    
    async with async_playwright() as p:
        # 既存のコンテキストに接続
        context_dir = session_info['context_dir']
        
        try:
            # 永続化コンテキストに再接続
            context = await p.chromium.launch_persistent_context(
                context_dir,
                headless=False,  # 既に表示されているブラウザを使用
                locale='ja-JP',
                viewport={'width': 1280, 'height': 800}
            )
            
            # アクティブなページを取得
            if not context.pages:
                print("❌ アクティブなページが見つかりません")
                return {'success': False, 'error': 'No active pages found'}
            
            page = context.pages[0]
            current_url = page.url
            
            print(f"📄 現在のページ: {current_url}")
            
            # 記事一覧ページにいることを確認
            if '/all' not in current_url:
                list_url = session_info['list_url']
                print(f"📄 記事一覧に移動: {list_url}")
                await page.goto(list_url, wait_until='networkidle')
            
            # 記事URLの収集
            print("🔍 記事URLを収集中...")
            article_urls = await collector.collect_article_links(page)
            print(f"✅ {len(article_urls)} 記事を発見")
            
            # 記事数制限適用
            if limit and len(article_urls) > limit:
                article_urls = article_urls[:limit]
                print(f"⚡ 記事数を {limit} 記事に制限")
            
            if not article_urls:
                print("❌ 記事が見つかりませんでした")
                return {'success': False, 'error': 'No articles found'}
            
            # 各記事をスクレイピング
            articles = []
            print(f"\n📄 {len(article_urls)} 記事のスクレイピングを開始...")
            
            for i, url in enumerate(article_urls, 1):
                print(f"📄 記事 {i}/{len(article_urls)}: {url}")
                
                try:
                    await page.goto(url, wait_until='networkidle', timeout=30000)
                    await asyncio.sleep(2)
                    
                    # ページHTMLを取得
                    html = await page.content()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # メタデータ取得
                    title_elem = soup.find('h1', class_='note-common-styles__textnote-title')
                    title = title_elem.get_text(strip=True) if title_elem else '...'
                    
                    # 公開日時
                    published_elem = soup.find('time')
                    published_at = published_elem.get('datetime', '') if published_elem else ''
                    
                    # 本文フォーマット
                    content = formatter.extract_formatted_content(soup)
                    
                    # バナー検出のデバッグ
                    figures = soup.find_all('figure', attrs={'embedded-service': 'external-article'})
                    if figures:
                        print(f"🔍 バナー検出: {url}")
                    
                    # 価格情報
                    if soup.find('button', string=lambda x: x and '購入' in x):
                        price = '有料'
                        status = '未購入'
                    else:
                        price = '無料'
                        status = '無料'
                    
                    articles.append({
                        'url': url,
                        'title': title,
                        'published_at': published_at,
                        'content': content,
                        'price': price,
                        'status': status
                    })
                    
                    if title != '...':
                        print(f"✅ '{title[:30]}...' を取得完了" if len(title) > 30 else f"✅ '{title}' を取得完了")
                    
                except Exception as e:
                    print(f"❌ エラー: {e}")
                    articles.append({
                        'url': url,
                        'title': 'エラー',
                        'published_at': '',
                        'content': f'取得エラー: {str(e)}',
                        'price': 'N/A',
                        'status': 'エラー'
                    })
            
            # CSV保存
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            filename = f"output/ihayato_final_{timestamp}.csv"
            
            # outputフォルダ作成（存在しない場合）
            os.makedirs("output", exist_ok=True)
            
            result = exporter.save_to_csv(articles, filename)
            
            print(f"\n🎉 スクレイピング完了!")
            print(f"📁 ファイル: {result['filename']}")
            print(f"📊 記事数: {result['article_count']}")
            print(f"💾 サイズ: {result['file_size_mb']} MB")
            
            # コンテキストを閉じる
            await context.close()
            
            return result
            
        except Exception as e:
            print(f"❌ エラーが発生しました: {e}")
            return {'success': False, 'error': str(e)}


def main():
    parser = argparse.ArgumentParser(description='スクレイピング実行スクリプト')
    parser.add_argument('--limit', type=int, help='取得記事数の上限')
    
    args = parser.parse_args()
    
    # 実行
    result = asyncio.run(start_scraping(args.limit))
    
    if result['success']:
        print("\n✅ すべての処理が完了しました")
    else:
        print(f"\n❌ エラーで終了: {result.get('error', '不明なエラー')}")
        sys.exit(1)


if __name__ == "__main__":
    main()