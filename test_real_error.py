#!/usr/bin/env python3
"""実際のエラーログを使ったテスト"""

import sys
import os
import asyncio

# プロジェクトのルートをPATHに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_imports():
    """インポートテスト"""
    print("🔧 インポートテスト")
    try:
        from linebot_error_analyzer.analyzer import LineErrorAnalyzer

        print("✅ LineErrorAnalyzer インポート成功")

        from linebot_error_analyzer.async_analyzer import AsyncLineErrorAnalyzer

        print("✅ AsyncLineErrorAnalyzer インポート成功")

        from linebot_error_analyzer.models import ApiPattern

        print("✅ ApiPattern インポート成功")
        print(f"   利用可能なパターン: {list(ApiPattern)}")

        from linebot_error_analyzer.models.log_parser import LogParser

        print("✅ LogParser インポート成功")

        return True
    except Exception as e:
        print(f"❌ インポートエラー: {e}")
        return False


def test_real_error_log():
    """実際のエラーログテスト"""

    # 実際のエラーログ
    real_error_log = """(404)
Reason: Not Found
HTTP response headers: HTTPHeaderDict({'server': 'legy', 'cache-control': 'no-cache, no-store, max-age=0, must-revalidate', 'content-type': 'application/json', 'date': 'Fri, 25 Jul 2025 18:23:24 GMT', 'expires': '0', 'pragma': 'no-cache', 'x-content-type-options': 'nosniff', 'x-frame-options': 'DENY', 'x-line-request-id': 'e40f3c8f-ab14-4042-9194-4c26ee828b80', 'x-xss-protection': '1; mode=block', 'content-length': '23'})
HTTP response body: {"message":"Not found"}"""

    print("\n🔍 実際のエラーログテスト")
    print("=" * 60)
    print(f"📄 エラーログ:\n{real_error_log[:200]}...")
    print("=" * 60)

    try:
        from linebot_error_analyzer.analyzer import LineErrorAnalyzer

        analyzer = LineErrorAnalyzer()

        # 基本的なログ解析
        print("\n📝 1. 基本的なエラーログ解析:")
        print("-" * 40)
        result = analyzer.analyze(real_error_log)
        print(f"✅ ステータスコード: {result.status_code}")
        print(f"✅ エラーカテゴリ: {result.category}")
        print(f"✅ リトライ可能: {result.is_retryable}")
        print(f"✅ 説明: {result.description}")
        print(f"✅ 推奨対処: {result.recommended_action}")
        if result.request_id:
            print(f"✅ リクエストID: {result.request_id}")

    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback

        traceback.print_exc()


def test_log_parser_direct():
    """LogParserの直接テスト"""

    real_error_log = """(404)
Reason: Not Found
HTTP response headers: HTTPHeaderDict({'server': 'legy', 'cache-control': 'no-cache, no-store, max-age=0, must-revalidate', 'content-type': 'application/json', 'date': 'Fri, 25 Jul 2025 18:23:24 GMT', 'expires': '0', 'pragma': 'no-cache', 'x-content-type-options': 'nosniff', 'x-frame-options': 'DENY', 'x-line-request-id': 'e40f3c8f-ab14-4042-9194-4c26ee828b80', 'x-xss-protection': '1; mode=block', 'content-length': '23'})
HTTP response body: {"message":"Not found"}"""

    print(f"\n🔧 LogParserの直接テスト:")
    print("-" * 40)

    try:
        from linebot_error_analyzer.models.log_parser import LogParser

        log_parser = LogParser()

        # パース結果の取得
        parse_result = log_parser.parse(real_error_log)

        print(f"✅ パース成功: {parse_result.parse_success}")
        print(f"✅ ステータスコード: {parse_result.status_code}")
        print(f"✅ メッセージ: {parse_result.message}")
        print(f"✅ リクエストID: {parse_result.request_id}")
        print(f"✅ ヘッダー数: {len(parse_result.headers)}")

        if parse_result.headers:
            print("   📋 ヘッダー情報:")
            for key, value in list(parse_result.headers.items())[
                :3
            ]:  # 最初の3個だけ表示
                print(f"      {key}: {value}")

    except Exception as e:
        print(f"❌ LogParserエラー: {e}")
        import traceback

        traceback.print_exc()


async def test_async_analyzer():
    """非同期アナライザーテスト"""

    real_error_log = """(404)
Reason: Not Found
HTTP response headers: HTTPHeaderDict({'server': 'legy', 'cache-control': 'no-cache, no-store, max-age=0, must-revalidate', 'content-type': 'application/json', 'date': 'Fri, 25 Jul 2025 18:23:24 GMT', 'expires': '0', 'pragma': 'no-cache', 'x-content-type-options': 'nosniff', 'x-frame-options': 'DENY', 'x-line-request-id': 'e40f3c8f-ab14-4042-9194-4c26ee828b80', 'x-xss-protection': '1; mode=block', 'content-length': '23'})
HTTP response body: {"message":"Not found"}"""

    print(f"\n🚀 非同期アナライザーテスト:")
    print("-" * 40)

    try:
        from linebot_error_analyzer.async_analyzer import AsyncLineErrorAnalyzer

        async_analyzer = AsyncLineErrorAnalyzer()

        # 基本解析
        result = await async_analyzer.analyze(real_error_log)
        print(f"✅ 非同期解析成功")
        print(f"   ステータスコード: {result.status_code}")
        print(f"   エラーカテゴリ: {result.category}")
        print(f"   リトライ可能: {result.is_retryable}")
        print(f"   説明: {result.description}")

    except Exception as e:
        print(f"❌ 非同期解析エラー: {e}")
        import traceback

        traceback.print_exc()


def main():
    """メイン関数"""
    print("🎯 LINE Bot Error Analyzer - 実際のエラーログテスト")
    print("=" * 70)

    # インポートテスト
    if not test_imports():
        return

    # 基本テスト
    test_real_error_log()

    # LogParserの直接テスト
    test_log_parser_direct()

    # 非同期テスト
    print(f"\n🔄 非同期テスト実行中...")
    try:
        asyncio.run(test_async_analyzer())
    except Exception as e:
        print(f"❌ 非同期テスト失敗: {e}")

    print(f"\n🎉 テスト完了!")


if __name__ == "__main__":
    main()
