"""
コレクターのテスト
"""

import pytest
from bs4 import BeautifulSoup
from src.collector import ArticleCollector


class TestArticleCollector:
    def setup_method(self):
        self.collector = ArticleCollector()
    
    def test_is_valid_article_link(self):
        """記事リンクの検証テスト"""
        # 有効なリンク
        assert self.collector._is_valid_article_link('/n/abc123')
        assert self.collector._is_valid_article_link('https://note.com/user/n/abc123')
        
        # 無効なリンク
        assert not self.collector._is_valid_article_link('/n/')
        assert not self.collector._is_valid_article_link('/info/n/abc123')
        assert not self.collector._is_valid_article_link('/profile')
    
    def test_extract_article_metadata(self):
        """記事メタデータの抽出テスト"""
        html = '''
        <article>
            <time datetime="2025-07-07T10:00:00.000+09:00">2025年7月7日</time>
            <span>￥500</span>
        </article>
        '''
        soup = BeautifulSoup(html, 'html.parser')
        
        metadata = self.collector.extract_article_metadata(soup)
        
        assert metadata['date'] == '2025-07-07T10:00:00.000+09:00'
        assert metadata['price'] == '有料'
        assert metadata['purchase_status'] == '購入済み or 無料'
    
    def test_extract_article_metadata_free(self):
        """無料記事のメタデータ抽出テスト"""
        html = '''
        <article>
            <time datetime="2025-07-07T10:00:00.000+09:00">2025年7月7日</time>
        </article>
        '''
        soup = BeautifulSoup(html, 'html.parser')
        
        metadata = self.collector.extract_article_metadata(soup)
        
        assert metadata['price'] == '無料'
        assert metadata['purchase_status'] == '無料'