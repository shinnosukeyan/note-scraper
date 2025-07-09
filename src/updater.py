"""
メイン更新ロジックモジュール
すべてのコンポーネントを統合して増分更新を実行
"""

import asyncio
from typing import List, Dict, Optional
from pathlib import Path

from .csv_manager import CSVManager
from .url_differ import URLDiffer
from .incremental_scraper import IncrementalScraper


class NoteScrapeUpdater:
    """Note記事の増分更新を管理するクラス"""
    
    def __init__(self, profile_url: str, headless: bool = False):
        self.profile_url = profile_url
        self.csv_manager = CSVManager()
        self.url_differ = URLDiffer()
        self.scraper = IncrementalScraper(headless)
    
    async def update_from_csv(self, existing_csv_path: str, 
                             manual_setup: bool = True,
                             output_path: Optional[str] = None) -> Dict[str, any]:
        """既存CSVから増分更新を実行"""
        
        print("🚀 Note記事の増分更新を開始します")
        print(f"📄 対象プロフィール: {self.profile_url}")
        print(f"📁 既存CSV: {existing_csv_path}")
        print("=" * 70)
        
        try:
            # ステップ1: 既存CSVの読み込み
            print("📂 ステップ1: 既存データの読み込み")
            existing_data = self.csv_manager.load_existing_csv(existing_csv_path)
            existing_urls = existing_data['stats']['existing_urls']
            
            # ステップ2: 現在の記事一覧を取得
            print("\n🌐 ステップ2: 現在の記事一覧を取得")
            current_urls = await self.scraper.get_all_article_urls_from_page(
                self.profile_url, manual_setup=manual_setup
            )
            
            # ステップ3: 新規URLを計算
            print("\n🔍 ステップ3: 新規記事の特定")
            new_urls = self.url_differ.calculate_new_urls(existing_urls, current_urls)
            
            # ステップ4: 新規記事のスクレイピング
            print(f"\n📝 ステップ4: 新規記事のスクレイピング")
            if new_urls:
                new_articles = await self.scraper.scrape_new_articles_only(new_urls)
            else:
                print("📝 新規記事がありません")
                new_articles = []
            
            # ステップ5: データのマージと保存
            print(f"\n💾 ステップ5: データのマージと保存")
            result = self.csv_manager.merge_and_save(
                existing_csv_path, new_articles, output_path
            )
            
            # 結果サマリー
            print("\n" + "=" * 70)
            print("🎉 更新完了!")
            print(f"📊 既存記事: {len(existing_urls)}件")
            print(f"📊 現在記事: {len(current_urls)}件")
            print(f"📊 新規記事: {len(new_urls)}件")
            print(f"📁 出力ファイル: {result['filename']}")
            print(f"💾 ファイルサイズ: {result['file_size_mb']} MB")
            print("=" * 70)
            
            return {
                'success': True,
                'existing_count': len(existing_urls),
                'current_count': len(current_urls),
                'new_count': len(new_urls),
                'new_articles': new_articles,
                'output_file': result['filename'],
                'file_size_mb': result['file_size_mb']
            }
            
        except Exception as e:
            print(f"❌ 更新エラー: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def update_with_validation(self, existing_csv_path: str,
                                   manual_setup: bool = True,
                                   validate_urls: bool = True,
                                   batch_size: int = 5,
                                   output_path: Optional[str] = None) -> Dict[str, any]:
        """URL検証付きの増分更新"""
        
        print("🚀 URL検証付き増分更新を開始します")
        
        try:
            # 基本更新を実行
            update_result = await self.update_from_csv(
                existing_csv_path, manual_setup, output_path
            )
            
            if not update_result['success']:
                return update_result
            
            new_urls = [article['url'] for article in update_result['new_articles']]
            
            # URL検証（オプション）
            if validate_urls and new_urls:
                print(f"\n🔍 ステップ6: 新規URLの検証")
                valid_urls = await self.scraper.quick_validate_urls(new_urls)
                invalid_count = len(new_urls) - len(valid_urls)
                
                if invalid_count > 0:
                    print(f"⚠️  無効なURL: {invalid_count}件")
                    update_result['invalid_urls_count'] = invalid_count
            
            return update_result
            
        except Exception as e:
            print(f"❌ 検証付き更新エラー: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def batch_update_with_progress(self, existing_csv_path: str,
                                       manual_setup: bool = True,
                                       batch_size: int = 5,
                                       output_path: Optional[str] = None) -> Dict[str, any]:
        """バッチ処理付きの増分更新"""
        
        print("🚀 バッチ処理付き増分更新を開始します")
        
        try:
            # ステップ1-3: 基本的な準備（新規URL取得まで）
            existing_data = self.csv_manager.load_existing_csv(existing_csv_path)
            existing_urls = existing_data['stats']['existing_urls']
            
            current_urls = await self.scraper.get_all_article_urls_from_page(
                self.profile_url, manual_setup=manual_setup
            )
            
            new_urls = self.url_differ.calculate_new_urls(existing_urls, current_urls)
            
            # ステップ4: バッチ処理でスクレイピング
            if new_urls:
                new_articles = await self.scraper.batch_scrape_with_progress(
                    new_urls, batch_size
                )
            else:
                print("📝 新規記事がありません")
                new_articles = []
            
            # ステップ5: マージと保存
            result = self.csv_manager.merge_and_save(
                existing_csv_path, new_articles, output_path
            )
            
            print(f"\n🎉 バッチ更新完了! 新規記事: {len(new_articles)}件")
            
            return {
                'success': True,
                'existing_count': len(existing_urls),
                'current_count': len(current_urls),
                'new_count': len(new_urls),
                'new_articles': new_articles,
                'output_file': result['filename'],
                'file_size_mb': result['file_size_mb']
            }
            
        except Exception as e:
            print(f"❌ バッチ更新エラー: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def check_csv_compatibility(self, csv_path: str) -> bool:
        """CSVファイルの互換性をチェック"""
        try:
            return self.csv_manager.validate_csv_format(csv_path)
        except Exception as e:
            print(f"❌ CSV互換性チェックエラー: {e}")
            return False
    
    async def get_current_article_count(self, manual_setup: bool = True) -> int:
        """現在の記事数を取得（更新前の確認用）"""
        try:
            current_urls = await self.scraper.get_all_article_urls_from_page(
                self.profile_url, manual_setup=manual_setup
            )
            return len(current_urls)
        except Exception as e:
            print(f"❌ 記事数取得エラー: {e}")
            return 0
    
    def analyze_update_potential(self, existing_csv_path: str) -> Dict[str, any]:
        """更新の必要性を分析（実際のスクレイピング前の事前チェック）"""
        try:
            existing_data = self.csv_manager.load_existing_csv(existing_csv_path)
            stats = existing_data['stats']
            
            analysis = {
                'existing_articles': stats['total_articles'],
                'latest_date': stats['latest_date'],
                'date_range': stats['date_range'],
                'has_url_column': stats.get('has_url_column', True),
                'ready_for_update': True,
                'recommendations': []
            }
            
            # 推奨事項
            if stats['total_articles'] < 10:
                analysis['recommendations'].append("既存記事数が少ないため、全件再取得も検討してください")
            
            if stats['latest_date']:
                analysis['recommendations'].append(f"最新記事日付: {stats['latest_date']}")
            
            return analysis
            
        except Exception as e:
            return {
                'ready_for_update': False,
                'error': str(e)
            }