"""
記事収集モジュール
"""

import re
from typing import List, Dict
from urllib.parse import urljoin
from bs4 import BeautifulSoup


class ArticleCollector:
    """記事情報を収集するクラス"""
    
    def __init__(self, base_url: str = "https://note.com"):
        self.base_url = base_url
        
    async def collect_article_links(self, page) -> List[str]:
        """ページから記事リンクを収集"""
        articles = []
        
        # 記事リンクを収集
        all_links = await page.query_selector_all('a[href*="/n/"]')
        
        for link in all_links:
            try:
                href = await link.get_attribute('href')
                if href and self._is_valid_article_link(href):
                    full_url = urljoin(self.base_url, href)
                    full_url = full_url.split('?')[0].split('#')[0]
                    
                    # 重複チェック
                    if full_url not in articles:
                        articles.append(full_url)
                        
            except Exception:
                continue
        
        return articles
    
    def _is_valid_article_link(self, href: str) -> bool:
        """有効な記事リンクかチェック"""
        if '/n/' in href and not href.endswith('/n/'):
            if re.match(r'.*/n/[a-zA-Z0-9_-]+', href):
                return '/info/n/' not in href
        return False
    
    def extract_article_metadata(self, soup: BeautifulSoup) -> Dict[str, str]:
        """記事のメタデータを抽出"""
        metadata = {
            'date': '',
            'price': '無料',
            'purchase_status': '無料'
        }
        
        # 公開日取得
        date_element = soup.find('time')
        if date_element and date_element.get('datetime'):
            metadata['date'] = date_element['datetime']
        
        # 価格情報取得
        price_element = soup.find('span', string=re.compile(r'￥|円'))
        if price_element:
            metadata['price'] = '有料'
            metadata['purchase_status'] = '購入済み or 無料'
        
        return metadata