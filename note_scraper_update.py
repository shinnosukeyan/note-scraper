#!/usr/bin/env python3
"""
Note記事増分更新スクリプト
既存CSVファイルから新規記事のみを追加
"""

import asyncio
import argparse
import sys
from pathlib import Path

# srcモジュールの追加
sys.path.append(str(Path(__file__).parent / 'src'))

from src.updater import NoteScrapeUpdater


async def main():
    parser = argparse.ArgumentParser(description='Note記事の増分更新')
    parser.add_argument('profile_url', help='NoteプロフィールURL (例: https://note.com/ihayato)')
    parser.add_argument('existing_csv', help='既存のCSVファイルパス')
    parser.add_argument('--output', '-o', help='出力CSVファイルパス（省略時は自動生成）')
    parser.add_argument('--no-manual', action='store_true', help='手動セットアップをスキップ')
    parser.add_argument('--headless', action='store_true', help='ヘッドレスモードで実行')
    parser.add_argument('--batch-size', type=int, default=5, help='バッチサイズ（デフォルト:5）')
    parser.add_argument('--validate', action='store_true', help='URL検証を実行')
    parser.add_argument('--batch', action='store_true', help='バッチ処理モードで実行')
    parser.add_argument('--check-only', action='store_true', help='更新可能性のチェックのみ実行')
    
    args = parser.parse_args()
    
    # パス存在確認
    csv_path = Path(args.existing_csv)
    if not csv_path.exists():
        print(f"❌ 既存CSVファイルが見つかりません: {args.existing_csv}")
        return 1
    
    # 更新ツール初期化
    updater = NoteScrapeUpdater(args.profile_url, headless=args.headless)
    
    try:
        # チェックのみモード
        if args.check_only:
            print("🔍 更新可能性をチェックしています...")
            
            # CSV互換性チェック
            if not updater.check_csv_compatibility(str(csv_path)):
                print("❌ CSVファイルに問題があります")
                return 1
            
            # 更新分析
            analysis = updater.analyze_update_potential(str(csv_path))
            
            print("\n📊 更新分析結果:")
            print(f"   既存記事数: {analysis.get('existing_articles', '不明')}")
            print(f"   最新記事日付: {analysis.get('latest_date', '不明')}")
            print(f"   記事期間: {analysis.get('date_range', '不明')}")
            
            if analysis.get('recommendations'):
                print("\n💡 推奨事項:")
                for rec in analysis['recommendations']:
                    print(f"   • {rec}")
            
            if analysis.get('ready_for_update'):
                print("\n✅ 更新準備完了")
                
                existing_count = analysis.get('existing_articles', 0)
                print(f"📊 既存記事数: {existing_count}件")
                
                if not analysis.get('has_url_column', True):
                    print("ℹ️  URL列がないため、全記事を新規として取得します")
                    print("💡 増分更新を実行してください")
                else:
                    print("💡 現在の記事数確認は実際の更新時に行います")
                    print("💡 増分更新を実行してください")
            else:
                print(f"❌ 更新準備エラー: {analysis.get('error', '不明')}")
                return 1
            
            return 0
        
        # 実際の更新実行
        print("🚀 増分更新を開始します")
        
        manual_setup = not args.no_manual
        
        # 更新モード選択
        if args.batch:
            print("📦 バッチ処理モードで実行")
            result = await updater.batch_update_with_progress(
                str(csv_path),
                manual_setup=manual_setup,
                batch_size=args.batch_size,
                output_path=args.output
            )
        elif args.validate:
            print("🔍 URL検証モードで実行")
            result = await updater.update_with_validation(
                str(csv_path),
                manual_setup=manual_setup,
                validate_urls=True,
                batch_size=args.batch_size,
                output_path=args.output
            )
        else:
            print("⚡ 標準モードで実行")
            result = await updater.update_from_csv(
                str(csv_path),
                manual_setup=manual_setup,
                output_path=args.output
            )
        
        # 結果表示
        if result['success']:
            print(f"\n🎉 更新成功!")
            print(f"📁 出力ファイル: {result['output_file']}")
            print(f"📊 新規記事: {result['new_count']}件")
            print(f"💾 ファイルサイズ: {result['file_size_mb']} MB")
            
            if result.get('invalid_urls_count'):
                print(f"⚠️  無効URL: {result['invalid_urls_count']}件")
            
            return 0
        else:
            print(f"❌ 更新失敗: {result['error']}")
            return 1
            
    except KeyboardInterrupt:
        print("\n\n⏹️  ユーザーにより中断されました")
        return 1
    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")
        return 1


def show_usage_examples():
    """使用例を表示"""
    print("""
使用例:

1. 基本的な増分更新:
   python note_scraper_update.py https://note.com/ihayato existing.csv

2. 出力ファイル指定:
   python note_scraper_update.py https://note.com/ihayato existing.csv -o updated.csv

3. 手動セットアップなし（テスト用）:
   python note_scraper_update.py https://note.com/ihayato existing.csv --no-manual

4. バッチ処理モード:
   python note_scraper_update.py https://note.com/ihayato existing.csv --batch --batch-size 10

5. URL検証付き:
   python note_scraper_update.py https://note.com/ihayato existing.csv --validate

6. ヘッドレスモード:
   python note_scraper_update.py https://note.com/ihayato existing.csv --headless

7. 更新可能性チェックのみ:
   python note_scraper_update.py https://note.com/ihayato existing.csv --check-only

推奨コマンド (イケハヤさんの場合):
   python note_scraper_update.py https://note.com/ihayato /Users/yusukeohata/Desktop/youtube-chanel/URLなし/07.イケハヤ2\\(note\\).csv --batch
""")


if __name__ == "__main__":
    if len(sys.argv) == 1:
        show_usage_examples()
        sys.exit(0)
    
    exit_code = asyncio.run(main())
    sys.exit(exit_code)