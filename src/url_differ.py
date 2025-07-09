"""
URL差分計算モジュール
既存URLと取得URLから新規URLを計算
"""

from typing import List, Set, Dict
import re
from urllib.parse import urljoin, urlparse


class URLDiffer:
    """URL差分を計算するクラス"""
    
    def __init__(self, base_url: str = "https://note.com"):
        self.base_url = base_url
    
    def calculate_new_urls(self, existing_urls: Set[str], current_urls: List[str]) -> List[str]:
        """新規URLを計算"""
        # 既存URLを正規化
        normalized_existing = set(self._normalize_url(url) for url in existing_urls)
        
        # 現在のURLを正規化
        normalized_current = [self._normalize_url(url) for url in current_urls]
        
        # 重複除去
        unique_current = list(dict.fromkeys(normalized_current))  # 順序保持で重複除去
        
        # 新規URLを計算
        new_urls = [url for url in unique_current if url not in normalized_existing]
        
        print(f"📊 URL差分計算結果:")
        print(f"   既存記事: {len(normalized_existing)}件")
        print(f"   現在取得: {len(unique_current)}件")
        print(f"   新規記事: {len(new_urls)}件")
        
        return new_urls
    
    def _normalize_url(self, url: str) -> str:
        """URLを正規化（クエリパラメータ除去、完全URL化）"""
        if not url:
            return ""
        
        # 相対URLを絶対URLに変換
        if url.startswith('/'):
            url = urljoin(self.base_url, url)
        
        # URLパースしてクエリパラメータとフラグメントを除去
        parsed = urlparse(url)
        normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        
        # 末尾のスラッシュを統一
        normalized = normalized.rstrip('/')
        
        return normalized
    
    def validate_note_urls(self, urls: List[str]) -> List[str]:
        """Noteの記事URLのみを抽出・検証"""
        valid_urls = []
        
        for url in urls:
            if self._is_valid_note_article_url(url):
                valid_urls.append(url)
        
        print(f"🔍 URL検証結果: {len(urls)}件 → {len(valid_urls)}件（有効）")
        
        return valid_urls
    
    def _is_valid_note_article_url(self, url: str) -> bool:
        """有効なNote記事URLかチェック"""
        if not url:
            return False
        
        # 正規化
        normalized = self._normalize_url(url)
        
        # Note記事のパターンチェック
        patterns = [
            r'https://note\.com/[^/]+/n/[a-zA-Z0-9_-]+$',  # 標準形式
        ]
        
        for pattern in patterns:
            if re.match(pattern, normalized):
                # 除外パターンチェック
                if '/info/n/' in normalized:
                    return False
                return True
        
        return False
    
    def sort_urls_by_date_hint(self, urls: List[str], reverse: bool = True) -> List[str]:
        """URLから日付ヒントで並び替え（新しい順がデフォルト）"""
        # Note記事のURLにはID部分があるが、日付情報は直接含まれないことが多い
        # そのため、元の順序を保持（記事一覧ページの順序は通常新しい順）
        
        if reverse:
            return urls  # 新しい順（記事一覧ページの順序そのまま）
        else:
            return list(reversed(urls))  # 古い順
    
    def group_urls_by_batch(self, urls: List[str], batch_size: int = 10) -> List[List[str]]:
        """URLをバッチサイズごとにグループ化"""
        batches = []
        for i in range(0, len(urls), batch_size):
            batch = urls[i:i + batch_size]
            batches.append(batch)
        
        print(f"📦 バッチ分割: {len(urls)}件 → {len(batches)}バッチ（{batch_size}件/バッチ）")
        
        return batches
    
    def analyze_url_patterns(self, urls: List[str]) -> Dict[str, any]:
        """URL パターンを分析"""
        analysis = {
            'total_count': len(urls),
            'unique_count': len(set(urls)),
            'duplicate_count': len(urls) - len(set(urls)),
            'domains': {},
            'path_patterns': {}
        }
        
        for url in urls:
            parsed = urlparse(url)
            domain = parsed.netloc
            
            # ドメイン統計
            analysis['domains'][domain] = analysis['domains'].get(domain, 0) + 1
            
            # パスパターン統計
            if '/n/' in parsed.path:
                pattern = 'note_article'
            elif '/m/' in parsed.path:
                pattern = 'magazine'
            else:
                pattern = 'other'
            
            analysis['path_patterns'][pattern] = analysis['path_patterns'].get(pattern, 0) + 1
        
        return analysis
    
    def filter_recent_urls(self, urls: List[str], limit: int) -> List[str]:
        """最新のURL群を取得（先頭から指定件数）"""
        if len(urls) <= limit:
            return urls
        
        recent_urls = urls[:limit]
        print(f"📅 最新記事フィルタ: {len(urls)}件 → {len(recent_urls)}件")
        
        return recent_urls