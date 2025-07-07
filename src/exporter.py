"""
CSV出力モジュール
"""

import os
from typing import List, Dict
import pandas as pd


class CSVExporter:
    """CSV出力を処理するクラス"""
    
    def save_to_csv(self, articles: List[Dict], filename: str) -> Dict[str, any]:
        """CSVファイルに保存"""
        # DataFrameに変換
        df_data = []
        for i, article in enumerate(articles, 1):
            df_data.append({
                '番号': i,
                '公開日': article.get('date', ''),
                'タイトル': article.get('title', ''),
                '本文': article.get('content', ''),
                '価格': article.get('price', ''),
                '購入状況': article.get('purchase_status', ''),
                'URL': article.get('url', '')
            })
        
        df = pd.DataFrame(df_data)
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        
        # ファイル情報を返す
        file_size = os.path.getsize(filename)
        file_size_mb = file_size / (1024 * 1024)
        
        return {
            'filename': filename,
            'article_count': len(articles),
            'file_size_mb': round(file_size_mb, 1)
        }