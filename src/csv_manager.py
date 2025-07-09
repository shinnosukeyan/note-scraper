"""
CSV管理モジュール
既存CSVの読み込み、新規データの追加、保存を管理
"""

import os
from typing import List, Dict, Optional, Set
import pandas as pd
from datetime import datetime


class CSVManager:
    """CSV読み書きを管理するクラス"""
    
    def __init__(self):
        self.column_order = ['番号', '公開日', 'タイトル', '本文', '価格', '購入状況', 'URL']
    
    def load_existing_csv(self, csv_path: str) -> Dict[str, any]:
        """既存CSVを読み込み、データと統計情報を返す"""
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"CSVファイルが見つかりません: {csv_path}")
        
        try:
            df = pd.read_csv(csv_path, encoding='utf-8-sig')
            
            # 統計情報
            if 'URL' in df.columns:
                existing_urls = set(df['URL'].dropna().tolist())
            else:
                existing_urls = set()  # URL列がない場合は空のset
            
            stats = {
                'total_articles': len(df),
                'date_range': self._get_date_range(df),
                'latest_date': self._get_latest_date(df),
                'existing_urls': existing_urls,
                'has_url_column': 'URL' in df.columns
            }
            
            print(f"✅ 既存CSV読み込み完了: {csv_path}")
            print(f"📊 記事数: {stats['total_articles']}")
            print(f"📅 期間: {stats['date_range']}")
            
            return {
                'dataframe': df,
                'stats': stats
            }
            
        except Exception as e:
            raise Exception(f"CSV読み込みエラー: {e}")
    
    def extract_existing_urls(self, csv_path: str) -> Set[str]:
        """既存CSVからURL一覧を抽出"""
        data = self.load_existing_csv(csv_path)
        return data['stats']['existing_urls']
    
    def merge_and_save(self, existing_csv_path: str, new_articles: List[Dict], 
                      output_path: Optional[str] = None) -> Dict[str, any]:
        """既存データと新規記事をマージして保存"""
        
        # 既存データ読み込み
        existing_data = self.load_existing_csv(existing_csv_path)
        existing_df = existing_data['dataframe']
        
        if not new_articles:
            print("📝 新規記事がありません。既存データをそのまま保持します。")
            return {
                'success': True,
                'filename': existing_csv_path,
                'new_articles_count': 0,
                'total_articles_count': len(existing_df)
            }
        
        # 新規記事をDataFrameに変換
        new_df = self._create_dataframe_from_articles(new_articles, 
                                                     start_number=len(existing_df) + 1)
        
        # 既存DFにURL列がない場合は追加
        if 'URL' not in existing_df.columns:
            existing_df['URL'] = ''
            print("ℹ️  既存データにURL列を追加しました")
        
        # データをマージ
        merged_df = pd.concat([existing_df, new_df], ignore_index=True)
        
        # 番号を再振り（重複防止）
        merged_df['番号'] = range(1, len(merged_df) + 1)
        
        # 出力パス決定
        if output_path is None:
            # outputフォルダ作成（存在しない場合）
            os.makedirs("output", exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            base_name = os.path.splitext(os.path.basename(existing_csv_path))[0]
            output_path = f"output/{base_name}_updated_{timestamp}.csv"
        
        # 保存
        merged_df.to_csv(output_path, index=False, encoding='utf-8-sig')
        
        # 結果情報
        file_size = os.path.getsize(output_path)
        file_size_mb = file_size / (1024 * 1024)
        
        result = {
            'success': True,
            'filename': output_path,
            'new_articles_count': len(new_articles),
            'total_articles_count': len(merged_df),
            'file_size_mb': round(file_size_mb, 1)
        }
        
        print(f"✅ マージ・保存完了!")
        print(f"📁 ファイル: {output_path}")
        print(f"📈 新規記事: {result['new_articles_count']}")
        print(f"📊 総記事数: {result['total_articles_count']}")
        print(f"💾 ファイルサイズ: {result['file_size_mb']} MB")
        
        return result
    
    def _create_dataframe_from_articles(self, articles: List[Dict], start_number: int = 1) -> pd.DataFrame:
        """記事リストからDataFrameを作成"""
        df_data = []
        for i, article in enumerate(articles):
            df_data.append({
                '番号': start_number + i,
                '公開日': article.get('date', ''),
                'タイトル': article.get('title', ''),
                '本文': article.get('content', ''),
                '価格': article.get('price', ''),
                '購入状況': article.get('purchase_status', ''),
                'URL': article.get('url', '')
            })
        
        return pd.DataFrame(df_data)
    
    def _get_date_range(self, df: pd.DataFrame) -> str:
        """データの日付範囲を取得"""
        if '公開日' not in df.columns:
            return "不明"
        
        dates = pd.to_datetime(df['公開日'], errors='coerce').dropna()
        if len(dates) == 0:
            return "不明"
        
        min_date = dates.min().strftime('%Y-%m-%d')
        max_date = dates.max().strftime('%Y-%m-%d')
        return f"{min_date} 〜 {max_date}"
    
    def _get_latest_date(self, df: pd.DataFrame) -> Optional[str]:
        """最新の記事日付を取得"""
        if '公開日' not in df.columns:
            return None
        
        dates = pd.to_datetime(df['公開日'], errors='coerce').dropna()
        if len(dates) == 0:
            return None
        
        return dates.max().strftime('%Y-%m-%d %H:%M:%S')
    
    def validate_csv_format(self, csv_path: str) -> bool:
        """CSVファイルの形式を検証"""
        try:
            df = pd.read_csv(csv_path, encoding='utf-8-sig')
            
            # URL列の有効性確認
            if 'URL' in df.columns:
                valid_urls = df['URL'].dropna()
                non_empty_urls = [url for url in valid_urls if url.strip()]
                
                if len(non_empty_urls) == 0:
                    print("ℹ️  URLが空です（全記事を新規として扱います）")
            else:
                print("ℹ️  URL列がありません（全記事を新規として扱います）")
            
            print(f"✅ CSV形式検証: 正常 ({len(df)}記事)")
            return True
            
        except Exception as e:
            print(f"❌ CSV検証エラー: {e}")
            return False