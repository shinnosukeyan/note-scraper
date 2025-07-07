"""
フォーマッターのテスト
"""

import pytest
from bs4 import BeautifulSoup
from src.formatter import ContentFormatter


class TestContentFormatter:
    def setup_method(self):
        self.formatter = ContentFormatter()
    
    def test_process_paragraph_with_bold(self):
        """太字テキストの処理テスト"""
        html = '<p>これは<strong>太字</strong>のテストです</p>'
        soup = BeautifulSoup(html, 'html.parser')
        p_element = soup.find('p')
        
        result = self.formatter._process_paragraph(p_element)
        assert result == 'これは**太字**のテストです'
    
    def test_process_paragraph_with_link(self):
        """リンクの処理テスト"""
        html = '<p>これは<a href="https://example.com">リンク</a>です</p>'
        soup = BeautifulSoup(html, 'html.parser')
        p_element = soup.find('p')
        
        result = self.formatter._process_paragraph(p_element)
        assert result == 'これは[リンク](https://example.com)です'
    
    def test_extract_formatted_content_basic(self):
        """基本的な本文フォーマットテスト"""
        html = '''
        <div class="note-common-styles__textnote-body">
            <p>第一段落です。</p>
            <p>第二段落です。</p>
        </div>
        '''
        soup = BeautifulSoup(html, 'html.parser')
        
        result = self.formatter.extract_formatted_content(soup)
        expected = '第一段落です。\n→\n第二段落です。\n→'
        assert result == expected