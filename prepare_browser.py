#!/usr/bin/env python3
"""
ブラウザ準備スクリプト
ブラウザを起動し、手動操作後にセッション情報を保存
"""

import asyncio
import argparse
import json
import os
from datetime import datetime
from playwright.async_api import async_playwright

# 設定ファイルとセッションファイルのパス
SESSION_FILE = "browser_session.json"
SETUP_DONE_FILE = "setup_done.txt"


async def prepare_browser(profile_url: str, headless: bool = False):
    """ブラウザを起動してセッション情報を保存"""
    
    print("🚀 ブラウザ準備を開始します")
    print(f"📝 対象: {profile_url}")
    
    async with async_playwright() as p:
        # ブラウザ起動（永続化コンテキスト使用）
        context_dir = "./browser_context"
        os.makedirs(context_dir, exist_ok=True)
        
        print("\n======================================================================")
        print("🚨 重要: ブラウザ準備モード")
        print("======================================================================")
        print("このスクリプトはブラウザを起動し、手動操作の準備をします。")
        print("スクレイピングは開始しません。")
        print("======================================================================\n")
        
        # 永続化コンテキストでブラウザを起動
        context = await p.chromium.launch_persistent_context(
            context_dir,
            headless=headless,
            locale='ja-JP',
            viewport={'width': 1280, 'height': 800}
        )
        
        page = context.pages[0] if context.pages else await context.new_page()
        
        # 記事一覧ページに移動
        list_url = f"{profile_url.rstrip('/')}/all"
        print(f"📄 記事一覧に移動: {list_url}")
        await page.goto(list_url, wait_until='networkidle')
        
        # セッション情報を保存
        session_info = {
            "profile_url": profile_url,
            "list_url": list_url,
            "context_dir": context_dir,
            "created_at": datetime.now().isoformat(),
            "browser_state": "active"
        }
        
        with open(SESSION_FILE, 'w', encoding='utf-8') as f:
            json.dump(session_info, f, ensure_ascii=False, indent=2)
        
        print("\n======================================================================")
        print("🔧 手動操作フェーズ")
        print("======================================================================")
        print("📋 次の手順を実行してください:")
        print("1. 📝 ブラウザでログインしてください")
        print("2. 🔄 「もっとみる」ボタンをすべてクリックしてください")
        print("   （すべての記事が表示されるまで）")
        print("3. ✅ 完了したら setup_done.txt ファイルを作成してください")
        print("\n👆 完了後、以下のコマンドを実行:")
        print(f"   touch {SETUP_DONE_FILE}")
        print("======================================================================\n")
        
        # setup_done.txtファイルの作成を待機
        print(f"⏰ {SETUP_DONE_FILE} ファイルの作成を待機中...")
        while not os.path.exists(SETUP_DONE_FILE):
            await asyncio.sleep(2)
        
        print("\n✅ セットアップ完了を確認しました!")
        print("🔐 ブラウザセッション情報を保存しました")
        print(f"📁 セッション情報: {SESSION_FILE}")
        print(f"📁 コンテキスト: {context_dir}")
        
        # ブラウザは開いたまま維持
        print("\n⚠️  ブラウザは開いたままです")
        print("📌 次のステップ: start_scraping.py を実行してください")
        print("\n======================================================================")
        print("💡 ヒント: 別のターミナルで以下を実行:")
        print(f"   python start_scraping.py")
        print("======================================================================\n")
        
        # ブラウザを開いたまま維持（無限待機）
        print("🔄 ブラウザを維持中... (Ctrl+Cで終了)")
        try:
            while True:
                await asyncio.sleep(60)
        except KeyboardInterrupt:
            print("\n⏹️  ブラウザ準備を終了します")
            await context.close()


def main():
    parser = argparse.ArgumentParser(description='ブラウザ準備スクリプト')
    parser.add_argument('profile_url', help='プロフィールURL (例: https://note.com/ihayato)')
    parser.add_argument('--no-headless', action='store_true', help='ブラウザを表示する')
    
    args = parser.parse_args()
    
    # 既存のセッションをクリーンアップ
    if os.path.exists(SETUP_DONE_FILE):
        os.remove(SETUP_DONE_FILE)
        print(f"🧹 既存の {SETUP_DONE_FILE} を削除しました")
    
    # headlessモードの設定
    headless = not args.no_headless
    
    # 実行
    asyncio.run(prepare_browser(args.profile_url, headless))


if __name__ == "__main__":
    main()