"""
本文フォーマットモジュール
完成データ品質の本文フォーマットを実装
"""

from typing import List
from bs4 import BeautifulSoup
from urllib.parse import urlparse


class ContentFormatter:
    """コンテンツをフォーマットするクラス"""
    
    def extract_formatted_content(self, soup: BeautifulSoup) -> str:
        """完成データ品質の本文フォーマット抽出"""
        content_parts = []
        
        # メインの記事コンテンツを取得
        article_body = soup.find('div', class_='note-common-styles__textnote-body')
        if not article_body:
            article_body = soup.find('div', class_='note-common-styles__textnote-body-container')
        
        if article_body:
            content_parts = self._process_content_elements(article_body)
        
        # 改行を「→」で結合
        return '\n'.join(content_parts)
    
    def _process_content_elements(self, element) -> List[str]:
        """コンテンツ要素を処理して完成データ形式に変換"""
        parts = []
        
        for child in element.children:
            if child.name is None:  # テキストノード
                text = child.strip()
                if text:
                    parts.append(text)
            
            elif child.name == 'p':
                # パラグラフ
                p_content = self._process_paragraph(child)
                if p_content:
                    parts.append(p_content)
                    parts.append('→')  # 改行
            
            elif child.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                # 見出し
                heading_text = child.get_text(strip=True)
                if heading_text:
                    parts.append(f"**{heading_text}**")
                    parts.append('→')
            
            elif child.name == 'blockquote':
                # 引用
                quote_text = child.get_text(strip=True)
                if quote_text:
                    parts.append(f"> {quote_text}")
                    parts.append('→')
            
            elif child.name == 'hr':
                # 区切り線
                parts.append('====')
                parts.append('→')
            
            elif child.name == 'img':
                # 画像
                img_src = child.get('src', '')
                img_alt = child.get('alt', '画像')
                if img_src:
                    parts.append(f"![{img_alt}]({img_src})")
                    parts.append('→')
            
            elif child.name == 'figure':
                # 図表（画像含む）
                img = child.find('img')
                figcaption = child.find('figcaption')
                
                if img:
                    img_src = img.get('src', '')
                    img_alt = img.get('alt', '画像')
                    if img_src:
                        parts.append(f"![{img_alt}]({img_src})")
                        if figcaption:
                            caption_text = figcaption.get_text(strip=True)
                            parts.append(f"*{caption_text}*")
                        parts.append('→')
            
            elif child.name == 'div':
                # 埋め込みコンテンツ
                embed_content = self._process_embed_content(child)
                if embed_content:
                    parts.append(embed_content)
                    parts.append('→')
            
            elif child.name == 'ul' or child.name == 'ol':
                # リスト
                list_items = child.find_all('li')
                for li in list_items:
                    li_text = li.get_text(strip=True)
                    if li_text:
                        prefix = '- ' if child.name == 'ul' else '1. '
                        parts.append(f"{prefix}{li_text}")
                parts.append('→')
        
        return parts
    
    def _process_paragraph(self, p_element) -> str:
        """パラグラフを処理"""
        text_parts = []
        
        for child in p_element.children:
            if child.name is None:  # テキストノード
                text = child.strip()
                if text:
                    text_parts.append(text)
            
            elif child.name == 'strong' or child.name == 'b':
                # 太字
                strong_text = child.get_text(strip=True)
                if strong_text:
                    text_parts.append(f"**{strong_text}**")
            
            elif child.name == 'em' or child.name == 'i':
                # 斜体
                em_text = child.get_text(strip=True)
                if em_text:
                    text_parts.append(f"*{em_text}*")
            
            elif child.name == 'a':
                # リンク
                link_text = child.get_text(strip=True)
                link_href = child.get('href', '')
                if link_text and link_href:
                    text_parts.append(f"[{link_text}]({link_href})")
                elif link_href:
                    text_parts.append(f"[{link_href}]({link_href})")
            
            elif child.name == 'br':
                # 改行
                text_parts.append('→')
            
            else:
                # その他の要素
                other_text = child.get_text(strip=True)
                if other_text:
                    text_parts.append(other_text)
        
        return ''.join(text_parts)
    
    def _process_embed_content(self, div_element) -> str:
        """埋め込みコンテンツを処理"""
        # 埋め込みコンテンツの特定パターンを検出
        embed_link = div_element.find('a')
        if embed_link:
            href = embed_link.get('href', '')
            title_elem = embed_link.find('h3') or embed_link.find('h2') or embed_link.find('strong')
            desc_elem = embed_link.find('p')
            
            if href and title_elem:
                title = title_elem.get_text(strip=True)
                desc = desc_elem.get_text(strip=True) if desc_elem else ''
                domain = urlparse(href).netloc
                
                # 完成データ形式の埋め込み
                return f"[埋め込みコンテンツ: [**{title}***{desc}**{domain}*]({href})[{href}]({href})]({href})"
        
        return ''