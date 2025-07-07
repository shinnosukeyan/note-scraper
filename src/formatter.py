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
                # 埋め込みコンテンツ・バナー
                embed_content = self._process_embed_content(child)
                if embed_content:
                    parts.append(embed_content)
                    parts.append('→')
            
            elif child.name == 'a':
                # 直接のリンク・バナー
                link_content = self._process_link_banner(child)
                if link_content:
                    parts.append(link_content)
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
        """埋め込みコンテンツ・バナーを処理"""
        # 複数のパターンでバナー・埋め込みを検出
        
        # パターン1: Noteの外部記事ウィジェット（バナー）
        classes = div_element.get('class', [])
        if isinstance(classes, list) and 'external-article-widget' in classes:
            embed_link = div_element.find('a')
            if embed_link:
                return self._extract_banner_info(embed_link)
        elif isinstance(classes, str) and 'external-article-widget' in classes:
            embed_link = div_element.find('a')
            if embed_link:
                return self._extract_banner_info(embed_link)
        
        # パターン2: embedContainer（埋め込み全般）
        if div_element.get('data-name') == 'embedContainer':
            # 中身を再帰的に処理
            inner_divs = div_element.find_all('div')
            for inner_div in inner_divs:
                result = self._process_embed_content(inner_div)
                if result:
                    return result
        
        # パターン3: data-embed-service属性（サービス埋め込み）
        if div_element.get('data-embed-service'):
            service = div_element.get('data-embed-service')
            embed_link = div_element.find('a')
            if embed_link:
                banner_info = self._extract_banner_info(embed_link)
                if service == 'external-article':
                    return banner_info
                else:
                    return f"[{service}埋め込み: {banner_info}]"
        
        # パターン4: リンク付きdiv（一般）
        embed_link = div_element.find('a')
        if embed_link:
            return self._extract_banner_info(embed_link)
        
        # パターン2: iframe埋め込み（YouTube、Twitter等）
        iframe = div_element.find('iframe')
        if iframe:
            iframe_src = iframe.get('src', '')
            if iframe_src:
                if 'youtube.com' in iframe_src or 'youtu.be' in iframe_src:
                    return f"[YouTube埋め込み]({iframe_src})"
                elif 'twitter.com' in iframe_src or 'x.com' in iframe_src:
                    return f"[Twitter埋め込み]({iframe_src})"
                else:
                    return f"[埋め込みコンテンツ]({iframe_src})"
        
        # パターン3: data属性付きdiv（特殊埋め込み）
        if div_element.get('data-href') or div_element.get('data-url'):
            data_url = div_element.get('data-href') or div_element.get('data-url')
            text_content = div_element.get_text(strip=True)
            if text_content:
                return f"[バナー: {text_content}]({data_url})"
            else:
                return f"[埋め込みリンク]({data_url})"
        
        # パターン4: 画像付きdiv（バナーの可能性）
        img = div_element.find('img')
        if img:
            img_src = img.get('src', '')
            img_alt = img.get('alt', '')
            text_content = div_element.get_text(strip=True)
            
            # 周辺にリンクがある場合
            parent_link = div_element.find_parent('a')
            if parent_link:
                link_href = parent_link.get('href', '')
                if link_href:
                    if text_content:
                        return f"[バナー: {text_content}]({link_href})"
                    elif img_alt:
                        return f"[画像バナー: {img_alt}]({link_href})"
                    else:
                        return f"[画像バナー]({link_href})"
            
            # 画像のみの場合
            if img_src:
                if text_content:
                    return f"[画像: {text_content}]({img_src})"
                elif img_alt:
                    return f"[画像: {img_alt}]({img_src})"
                else:
                    return f"[画像]({img_src})"
        
        return ''
    
    def _process_link_banner(self, a_element) -> str:
        """直接のリンク・バナーを処理"""
        return self._extract_banner_info(a_element)
    
    def _extract_banner_info(self, link_element) -> str:
        """リンク要素からバナー情報を抽出"""
        href = link_element.get('href', '')
        if not href:
            return ''
        
        # タイトル取得（優先順位順）
        title_elem = (link_element.find('h3') or 
                     link_element.find('h2') or 
                     link_element.find('h1') or
                     link_element.find('strong') or
                     link_element.find('b') or
                     link_element.find('span', class_=lambda x: x and 'title' in str(x).lower()))
        
        # 説明文取得
        desc_elem = (link_element.find('p') or 
                    link_element.find('div', class_=lambda x: x and any(word in str(x).lower() for word in ['desc', 'summary', 'text'])))
        
        # 画像取得
        img_elem = link_element.find('img')
        
        # 情報を組み立て
        title = title_elem.get_text(strip=True) if title_elem else ''
        desc = desc_elem.get_text(strip=True) if desc_elem else ''
        img_alt = img_elem.get('alt', '') if img_elem else ''
        img_src = img_elem.get('src', '') if img_elem else ''
        
        # ドメイン取得
        domain = urlparse(href).netloc
        
        # バナータイプを判定
        if img_elem and (title or img_alt):
            # 画像付きバナー
            banner_title = title or img_alt
            if desc:
                return f"[画像バナー: {banner_title} - {desc}]({href})"
            else:
                return f"[画像バナー: {banner_title}]({href})"
        
        elif title and desc:
            # 完全なバナー情報
            return f"[バナー: {title} - {desc}]({href})"
        
        elif title:
            # タイトルのみ
            return f"[バナー: {title}]({href})"
        
        elif img_alt:
            # 画像のみ
            return f"[画像バナー: {img_alt}]({href})"
        
        elif domain:
            # ドメインのみ
            full_text = link_element.get_text(strip=True)
            if full_text and len(full_text) < 100:  # 短いテキストの場合
                return f"[リンク: {full_text}]({href})"
            else:
                return f"[リンク: {domain}]({href})"
        
        else:
            # 最低限の情報
            return f"[リンク]({href})"