"""
ブラウザ操作モジュール
"""

import asyncio
from typing import Optional
from playwright.async_api import async_playwright, Page, Browser


class BrowserManager:
    """ブラウザ操作を管理するクラス"""
    
    def __init__(self, headless: bool = False):
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        
    async def initialize(self):
        """ブラウザを初期化（タイムアウト無効化）"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-web-security',
                '--disable-dev-shm-usage',
                '--no-first-run'
            ]
        )
        
        # タイムアウト完全無効化
        context = await self.browser.new_context(
            viewport={'width': 1280, 'height': 720},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        )
        context.set_default_timeout(0)  # タイムアウト無し
        
        self.page = await context.new_page()
        self.page.set_default_timeout(0)  # タイムアウト無し
        
    async def navigate_to_article_list(self, profile_url: str):
        """記事一覧ページに移動"""
        article_list_url = profile_url.rstrip('/') + '/all'
        await self.page.goto(article_list_url, wait_until="domcontentloaded", timeout=0)
        await self.page.wait_for_timeout(3000)
        return article_list_url
        
    async def navigate_to_article(self, url: str):
        """個別記事ページに移動"""
        await self.page.goto(url, wait_until="domcontentloaded", timeout=0)
        await self.page.wait_for_timeout(2000)
        
    async def get_page_content(self) -> str:
        """現在のページのHTMLコンテンツを取得"""
        return await self.page.content()
        
    async def get_page_title(self) -> str:
        """現在のページのタイトルを取得"""
        return await self.page.title()
        
    async def close(self):
        """ブラウザを閉じる"""
        if self.browser:
            await self.browser.close()