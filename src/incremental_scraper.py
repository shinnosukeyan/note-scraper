"""
増分スクレイピングモジュール
新規記事のみを効率的にスクレイピング
"""

import asyncio
from typing import List, Dict, Set
from bs4 import BeautifulSoup

from .browser import BrowserManager
from .collector import ArticleCollector
from .formatter import ContentFormatter


class IncrementalScraper:
    """新規記事のみを効率的にスクレイピングするクラス"""
    
    def __init__(self, headless: bool = False):
        self.browser_manager = BrowserManager(headless)
        self.collector = ArticleCollector()
        self.formatter = ContentFormatter()
        
    async def scrape_new_articles_only(self, new_urls: List[str]) -> List[Dict]:
        """新規記事URLのみをスクレイピング"""
        if not new_urls:
            print("📝 新規記事がありません")
            return []
        
        print(f"🚀 新規記事のスクレイピング開始: {len(new_urls)}件")
        
        try:
            # ブラウザ初期化
            await self.browser_manager.initialize()
            
            articles = []
            for i, url in enumerate(new_urls, 1):
                print(f"📄 新規記事 {i}/{len(new_urls)}: {url}")
                
                try:
                    article = await self._scrape_single_article(url)
                    articles.append(article)
                    
                    # 進捗表示
                    if article.get('title'):
                        print(f"✅ '{article['title'][:50]}...' を取得完了")
                    else:
                        print(f"✅ 記事取得完了（タイトル取得失敗）")
                    
                    # サーバー負荷軽減
                    await asyncio.sleep(1.5)
                    
                except Exception as e:
                    print(f"❌ スクレイピングエラー: {url} - {e}")
                    # エラーでも空のデータで継続
                    articles.append({
                        'url': url,
                        'title': f"エラー: {e}",
                        'content': f"エラーが発生しました: {e}",
                        'date': '',
                        'price': '',
                        'purchase_status': ''
                    })
            
            print(f"🎉 新規記事スクレイピング完了: {len(articles)}件")
            return articles
            
        finally:
            await self.browser_manager.close()
    
    async def _scrape_single_article(self, url: str) -> Dict:
        """単一記事をスクレイピング"""
        # ページに移動
        await self.browser_manager.navigate_to_article(url)
        
        # タイトル取得（改良版）
        page_title = await self.browser_manager.get_page_title()
        title = ''
        if page_title:
            # noteの様々なタイトル形式に対応
            if '｜イケハヤ' in page_title:
                title = page_title.split('｜イケハヤ')[0].strip()
            elif '｜note' in page_title:
                title = page_title.split('｜note')[0].strip()
            elif '|note' in page_title:
                title = page_title.split('|note')[0].strip()
            elif ' - note' in page_title:
                title = page_title.split(' - note')[0].strip()
            else:
                title = page_title.strip()
        
        # ページ内容を取得してパース
        content = await self.browser_manager.get_page_content()
        soup = BeautifulSoup(content, 'html.parser')
        
        # 本文とメタデータ取得
        formatted_content = self.formatter.extract_formatted_content(soup)
        metadata = self.collector.extract_article_metadata(soup)
        
        # デバッグ: バナー検出状況
        if '[バナー:' in formatted_content or '[画像バナー:' in formatted_content:
            print(f"🔍 バナー検出: {url}")
        
        # 記事情報を作成
        return {
            'url': url,
            'title': title,
            'content': formatted_content,
            'date': metadata['date'],
            'price': metadata['price'],
            'purchase_status': metadata['purchase_status']
        }
    
    async def quick_validate_urls(self, urls: List[str]) -> List[str]:
        """URLの有効性を素早くチェック"""
        print(f"🔍 URL有効性チェック開始: {len(urls)}件")
        
        valid_urls = []
        
        try:
            await self.browser_manager.initialize()
            
            for i, url in enumerate(urls):
                try:
                    # 軽量チェック（ページタイトルのみ取得）
                    await self.browser_manager.navigate_to_article(url)
                    title = await self.browser_manager.get_page_title()
                    
                    if title and ('note' in title.lower() or len(title) > 5):
                        valid_urls.append(url)
                    else:
                        print(f"⚠️  無効なページ: {url}")
                    
                    # 高速チェックのため短い間隔
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    print(f"❌ URLチェックエラー: {url} - {e}")
                    continue
        
        finally:
            await self.browser_manager.close()
        
        print(f"✅ URL有効性チェック完了: {len(urls)}件 → {len(valid_urls)}件（有効）")
        return valid_urls
    
    async def get_all_article_urls_from_page(self, profile_url: str, 
                                           manual_setup: bool = True) -> List[str]:
        """記事一覧ページから全記事URLを取得（外部でブラウザ管理される場合も対応）"""
        print(f"🌐 記事一覧からURL取得開始: {profile_url}")
        
        # 外部でブラウザが既に初期化されている場合はそれを使用
        browser_initialized_externally = self.browser_manager.page is not None
        
        try:
            if not browser_initialized_externally:
                await self.browser_manager.initialize()
            
            # 記事一覧ページに移動
            article_list_url = await self.browser_manager.navigate_to_article_list(profile_url)
            print(f"📄 記事一覧に移動: {article_list_url}")
            
            if manual_setup:
                await self._wait_for_manual_setup()
            
            # 記事リンクを収集
            article_urls = await self.collector.collect_article_links(self.browser_manager.page)
            
            print(f"✅ 記事URL取得完了: {len(article_urls)}件")
            return article_urls
            
        finally:
            # 外部でブラウザが管理されている場合は閉じない
            if not browser_initialized_externally:
                await self.browser_manager.close()
    
    async def _wait_for_manual_setup(self):
        """手動セットアップ待機"""
        import os
        
        print("\n" + "="*70)
        print("🔧 記事一覧の準備")
        print("="*70)
        print("📋 手順:")
        print("1. 📝 ログインしてください（必要に応じて）")
        print("2. 🔄 「もっとみる」ボタンをクリックして全記事を表示してください")
        print("3. ✅ 完了したら setup_done.txt ファイルを作成してください")
        print()
        
        setup_file = "/Users/yusukeohata/Desktop/development/note-scraper/setup_done.txt"
        
        # 既存のファイルがあれば削除
        if os.path.exists(setup_file):
            os.remove(setup_file)
            print("🗑️  前回のsetup_done.txtファイルを削除しました")
        
        print("👆 完了したら、以下のコマンドを実行してください:")
        print(f"   touch {setup_file}")
        print()
        print("⏰ setup_done.txt ファイルの作成を待機中...")
        print("   ※ このメッセージが表示されている間は、ファイルスクレイピングは開始されません")
        
        # より確実な監視ループ
        wait_count = 0
        while True:
            wait_count += 1
            if wait_count % 10 == 0:  # 30秒ごとに進捗を表示
                print(f"⏰ 待機中... ({wait_count * 3}秒経過)")
            
            if os.path.exists(setup_file):
                print("✅ セットアップ完了を確認しました")
                try:
                    os.remove(setup_file)
                    print("✅ setup_done.txt ファイルを削除しました")
                except Exception as e:
                    print(f"⚠️  ファイル削除エラー: {e}")
                break
            
            await asyncio.sleep(3)
        
        print("✅ 手動準備完了！URL収集を開始します")
        print("🔄 記事収集フェーズに移行します...")
    
    async def batch_scrape_with_progress(self, urls: List[str], batch_size: int = 5) -> List[Dict]:
        """バッチ処理で進捗表示付きスクレイピング"""
        if not urls:
            return []
        
        print(f"📦 バッチスクレイピング開始: {len(urls)}件 ({batch_size}件/バッチ)")
        
        try:
            await self.browser_manager.initialize()
            
            all_articles = []
            
            # バッチに分割
            for batch_num in range(0, len(urls), batch_size):
                batch_urls = urls[batch_num:batch_num + batch_size]
                batch_index = batch_num // batch_size + 1
                total_batches = (len(urls) + batch_size - 1) // batch_size
                
                print(f"\n📦 バッチ {batch_index}/{total_batches} 処理中 ({len(batch_urls)}件)")
                
                batch_articles = []
                for i, url in enumerate(batch_urls):
                    global_index = batch_num + i + 1
                    print(f"📄 記事 {global_index}/{len(urls)}: {url}")
                    
                    try:
                        article = await self._scrape_single_article(url)
                        batch_articles.append(article)
                        
                        if article.get('title'):
                            print(f"✅ '{article['title'][:50]}...' を取得完了")
                        
                        await asyncio.sleep(1.5)
                        
                    except Exception as e:
                        print(f"❌ エラー: {e}")
                        batch_articles.append({
                            'url': url,
                            'title': f"エラー: {e}",
                            'content': f"エラーが発生しました: {e}",
                            'date': '',
                            'price': '',
                            'purchase_status': ''
                        })
                
                all_articles.extend(batch_articles)
                print(f"✅ バッチ {batch_index} 完了 ({len(batch_articles)}件)")
            
            print(f"🎉 全バッチ処理完了: {len(all_articles)}件")
            return all_articles
            
        finally:
            await self.browser_manager.close()