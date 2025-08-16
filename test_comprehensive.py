#!/usr/bin/env python3
"""APIパターン指定での実際のエラーログテスト"""

import sys
import os
import asyncio

# プロジェクトのルートをPATHに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_api_pattern_analysis():
    """APIパターン指定での解析テスト"""

    # 実際のエラーログ
    real_error_log = """(404)
Reason: Not Found
HTTP response headers: HTTPHeaderDict({'server': 'legy', 'cache-control': 'no-cache, no-store, max-age=0, must-revalidate', 'content-type': 'application/json', 'date': 'Fri, 25 Jul 2025 18:23:24 GMT', 'expires': '0', 'pragma': 'no-cache', 'x-content-type-options': 'nosniff', 'x-frame-options': 'DENY', 'x-line-request-id': 'e40f3c8f-ab14-4042-9194-4c26ee828b80', 'x-xss-protection': '1; mode=block', 'content-length': '23'})
HTTP response body: {"message":"Not found"}"""

    print("🎯 APIパターン指定テスト")
    print("=" * 60)

    try:
        from linebot_error_analyzer.analyzer import LineErrorAnalyzer
        from linebot_error_analyzer.models import ApiPattern

        analyzer = LineErrorAnalyzer()

        # 主要なAPIパターンでテスト
        test_patterns = [
            ApiPattern.MESSAGE_REPLY,
            ApiPattern.MESSAGE_PUSH,
            ApiPattern.USER_PROFILE,
            ApiPattern.RICH_MENU_CREATE,
            ApiPattern.WEBHOOK_SETTINGS,
        ]

        for pattern in test_patterns:
            print(f"\n🔧 パターン: {pattern.value}")
            print("-" * 40)

            try:
                result = analyzer.analyze(real_error_log, pattern)
                print(f"✅ カテゴリ: {result.category}")
                print(f"✅ 説明: {result.description}")
                print(f"✅ 推奨対処: {result.recommended_action}")

                # 詳細解決策があるかチェック
                if hasattr(result, "solutions") and result.solutions:
                    print(f"✅ 詳細解決策: {len(result.solutions)}件")
                    for i, solution in enumerate(
                        result.solutions[:2]
                    ):  # 最初の2件のみ表示
                        print(f"   {i+1}. {solution.get('title', '解決策')}")

            except Exception as e:
                print(f"❌ パターン {pattern.value} でエラー: {e}")

    except Exception as e:
        print(f"❌ 全体エラー: {e}")
        import traceback

        traceback.print_exc()


async def test_async_api_pattern_analysis():
    """非同期版APIパターン指定テスト"""

    real_error_log = """(404)
Reason: Not Found
HTTP response headers: HTTPHeaderDict({'server': 'legy', 'cache-control': 'no-cache, no-store, max-age=0, must-revalidate', 'content-type': 'application/json', 'date': 'Fri, 25 Jul 2025 18:23:24 GMT', 'expires': '0', 'pragma': 'no-cache', 'x-content-type-options': 'nosniff', 'x-frame-options': 'DENY', 'x-line-request-id': 'e40f3c8f-ab14-4042-9194-4c26ee828b80', 'x-xss-protection': '1; mode=block', 'content-length': '23'})
HTTP response body: {"message":"Not found"}"""

    print(f"\n🚀 非同期APIパターン指定テスト:")
    print("=" * 60)

    try:
        from linebot_error_analyzer.async_analyzer import AsyncLineErrorAnalyzer
        from linebot_error_analyzer.models import ApiPattern

        async_analyzer = AsyncLineErrorAnalyzer()

        # 2つのパターンで非同期テスト
        test_patterns = [ApiPattern.MESSAGE_REPLY, ApiPattern.USER_PROFILE]

        for pattern in test_patterns:
            print(f"\n🔧 非同期パターン: {pattern.value}")
            print("-" * 40)

            result = await async_analyzer.analyze(real_error_log, pattern)
            print(f"✅ カテゴリ: {result.category}")
            print(f"✅ 説明: {result.description}")
            print(f"✅ 推奨対処: {result.recommended_action}")

    except Exception as e:
        print(f"❌ 非同期APIパターンエラー: {e}")
        import traceback

        traceback.print_exc()


def test_various_error_logs():
    """さまざまなエラーログ形式のテスト"""

    print(f"\n📋 さまざまなエラーログ形式テスト:")
    print("=" * 60)

    test_logs = [
        # シンプルなHTTPエラー
        "HTTP Error 401: Unauthorized - Invalid channel access token",
        # ステータスコードのみ
        "Request failed with status code (400): Invalid request body",
        # JSON形式エラー
        '{"message": "The request body has 2 error(s)", "details": [{"message": "May not be empty", "property": "messages[0].text"}]}',
        # レート制限エラー
        "Rate limit exceeded (429): Too many requests. Please try again later.",
    ]

    try:
        from linebot_error_analyzer.analyzer import LineErrorAnalyzer

        analyzer = LineErrorAnalyzer()

        for i, log in enumerate(test_logs, 1):
            print(f"\n📝 テストログ {i}: {log[:50]}...")
            print("-" * 30)

            try:
                result = analyzer.analyze(log)
                print(f"✅ ステータス: {result.status_code}")
                print(f"✅ カテゴリ: {result.category}")
                print(f"✅ リトライ可能: {result.is_retryable}")

            except Exception as e:
                print(f"❌ 解析エラー: {e}")

    except Exception as e:
        print(f"❌ 全体エラー: {e}")


def main():
    """メイン関数"""
    print("🎯 LINE Bot Error Analyzer - 包括テスト")
    print("=" * 70)

    # APIパターン指定テスト
    test_api_pattern_analysis()

    # さまざまなエラーログ形式テスト
    test_various_error_logs()

    # 非同期APIパターンテスト
    print(f"\n🔄 非同期テスト実行中...")
    try:
        asyncio.run(test_async_api_pattern_analysis())
    except Exception as e:
        print(f"❌ 非同期テスト失敗: {e}")

    print(f"\n🎉 包括テスト完了!")


if __name__ == "__main__":
    main()
