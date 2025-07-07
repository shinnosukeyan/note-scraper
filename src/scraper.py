"""
メインスクレイパーモジュール
"""

import asyncio
import os
from typing import List, Dict
from bs4 import BeautifulSoup
from datetime import datetime

from .browser import BrowserManager
from .collector import ArticleCollector
from .formatter import ContentFormatter
from .exporter import CSVExporter


class NoteScraper:
    """Noteスクレイパーのメインクラス"""
    
    def __init__(self, headless: bool = False):
        self.browser_manager = BrowserManager(headless)
        self.collector = ArticleCollector()
        self.formatter = ContentFormatter()
        self.exporter = CSVExporter()
        
    async def run(self, profile_url: str) -> Dict[str, any]:
        """メイン処理"""
        try:
            print("🚀 Note Scraper を開始")
            print(f"📝 対象: {profile_url}")
            
            # ブラウザ初期化
            await self.browser_manager.initialize()
            print("✅ ブラウザ初期化完了")
            
            # 手動準備フェーズ
            await self._manual_setup_phase(profile_url)
            
            # 記事収集
            article_urls = await self.collector.collect_article_links(self.browser_manager.page)
            print(f"✅ {len(article_urls)} 記事を発見")
            
            # デバッグ: 記事数が少ない場合の詳細情報
            if len(article_urls) < 30:
                print(f"⚠️  記事数が少ないです ({len(article_urls)}記事)")
                print("🔍 ページ内の全リンクを調査中...")
                
                # 全リンクをデバッグ
                all_page_links = await self.browser_manager.page.query_selector_all('a')
                note_links = []
                for link in all_page_links:
                    try:
                        href = await link.get_attribute('href')
                        if href and '/n/' in href:
                            note_links.append(href)
                    except:
                        continue
                        
                print(f"🔍 ページ内の/n/リンク総数: {len(note_links)}")
                print(f"🔍 最初の10個: {note_links[:10]}")
                
                # スクロール状況確認
                scroll_height = await self.browser_manager.page.evaluate('document.body.scrollHeight')
                print(f"🔍 ページの高さ: {scroll_height}px")
                
                # もっとみるボタンの存在確認
                more_buttons = await self.browser_manager.page.query_selector_all('button')
                for button in more_buttons:
                    try:
                        text = await button.text_content()
                        if text and 'もっと' in text:
                            print(f"🔍 発見したボタン: '{text}'")
                    except:
                        continue
            
            if not article_urls:
                print("❌ 記事が見つかりませんでした")
                return {'success': False, 'error': 'No articles found'}
            
            # 各記事をスクレイピング
            articles = await self._scrape_articles(article_urls)
            
            # CSV保存
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            filename = f"ihayato_final_{timestamp}.csv"
            result = self.exporter.save_to_csv(articles, filename)
            
            print(f"🎉 スクレイピング完了!")
            print(f"📁 ファイル: {result['filename']}")
            print(f"📊 記事数: {result['article_count']}")
            print(f"💾 サイズ: {result['file_size_mb']} MB")
            
            return {
                'success': True,
                'filename': result['filename'],
                'article_count': result['article_count'],
                'file_size_mb': result['file_size_mb']
            }
            
        except Exception as e:
            print(f"❌ エラー: {e}")
            return {'success': False, 'error': str(e)}
        finally:
            await self.browser_manager.close()
    
    async def _manual_setup_phase(self, profile_url: str):
        """手動準備フェーズ"""
        print("\n" + "="*70)
        print("🔧 手動準備フェーズ開始")
        print("="*70)
        
        # 記事一覧ページに移動
        article_list_url = await self.browser_manager.navigate_to_article_list(profile_url)
        print(f"📄 記事一覧に移動: {article_list_url}")
        
        print("\n📋 手動作業の手順:")
        print("1. 📝 ブラウザでログインしてください")
        print("2. 🔄 「もっとみる」ボタンを全部クリックしてください")
        print("   （600記事以上が全て表示されるまで）")
        print("3. ✅ 完了したら setup_done.txt ファイルを作成してください")
        print()
        print("⚠️  重要:")
        print("   - タイムアウトは設定されていません")
        print("   - ブラウザは自動で閉じません")
        print("   - 時間をかけても大丈夫です")
        print()
        
        # 完了まで待機
        setup_file = "/Users/yusukeohata/Desktop/development/note-scraper/setup_done.txt"
        print("👆 完了したら、以下のコマンドを実行してください:")
        print(f"   touch {setup_file}")
        print()
        print("⏰ setup_done.txt ファイルの作成を待機中...")
        
        while True:
            if os.path.exists(setup_file):
                print("✅ セットアップ完了を確認しました")
                os.remove(setup_file)
                break
            await asyncio.sleep(3)
        
        print("✅ 手動準備完了！自動処理を開始します")
    
    async def _scrape_articles(self, article_urls: List[str]) -> List[Dict]:
        """記事をスクレイピング"""
        print(f"\n📄 {len(article_urls)} 記事のスクレイピングを開始...")
        
        articles = []
        for i, url in enumerate(article_urls, 1):
            try:
                print(f"📄 記事 {i}/{len(article_urls)}: {url}")
                
                # ページに移動
                await self.browser_manager.navigate_to_article(url)
                
                # タイトル取得
                page_title = await self.browser_manager.get_page_title()
                title = ''
                if page_title and '｜note' in page_title:
                    title = page_title.split('｜note')[0].strip()
                
                # ページ内容を取得してパース
                content = await self.browser_manager.get_page_content()
                soup = BeautifulSoup(content, 'html.parser')
                
                # 本文とメタデータ取得
                formatted_content = self.formatter.extract_formatted_content(soup)
                metadata = self.collector.extract_article_metadata(soup)
                
                # デバッグ: バナー検出状況
                if '[バナー:' in formatted_content or '[画像バナー:' in formatted_content:
                    print(f"🔍 バナー検出: {url}")
                
                # デバッグ: 埋め込み検出状況  
                if '[埋め込み' in formatted_content or '[YouTube' in formatted_content or '[Twitter' in formatted_content:
                    print(f"🔍 埋め込み検出: {url}")
                
                # 記事情報を作成
                article = {
                    'url': url,
                    'title': title,
                    'content': formatted_content,
                    'date': metadata['date'],
                    'price': metadata['price'],
                    'purchase_status': metadata['purchase_status']
                }
                
                articles.append(article)
                print(f"✅ '{title[:50]}...' を取得完了")
                
                # サーバー負荷軽減
                await asyncio.sleep(1.5)
                
            except Exception as e:
                print(f"❌ スクレイピングエラー: {url} - {e}")
                # エラーでも処理継続
                articles.append({
                    'url': url,
                    'title': f"エラー: {e}",
                    'content': f"エラーが発生しました: {e}",
                    'date': '',
                    'price': '',
                    'purchase_status': ''
                })
        
        return articles