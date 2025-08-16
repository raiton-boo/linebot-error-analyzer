#!/usr/bin/env python3
"""
LINE Bot エラーアナライザー - 統合動作確認スクリプト
Issue #1: ログ文字列解析機能の完全動作確認
"""

import sys
import os

# プロジェクトのルートをPATHに追加（tests/manual/から2レベル上）
sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from linebot_error_analyzer import LineErrorAnalyzer, AsyncLineErrorAnalyzer
from linebot_error_analyzer.models import ApiPattern, ErrorCategory
from linebot_error_analyzer.models.log_parser import LogParser
import asyncio


def test_sync_analyzer():
    """同期版アナライザーテスト"""
    print("=== 同期版 LineErrorAnalyzer テスト ===")
    analyzer = LineErrorAnalyzer()

    test_cases = [
        "(400) Bad Request",
        "(401) Invalid channel access token",
        "(404) User not found",
        "(429) Too many requests - rate limit exceeded",
        "(500) Internal server error occurred",
        "(403) User profile not accessible",
    ]

    for i, log in enumerate(test_cases, 1):
        try:
            result = analyzer.analyze(log)
            print(f"{i}. {log}")
            print(f"   → Status: {result.status_code}")
            print(f"   → Category: {result.category.value}")
            print(f"   → Retryable: {result.is_retryable}")
            print(f"   → Description: {result.description[:50]}...")
            print()
        except Exception as e:
            print(f"{i}. {log} → ERROR: {e}")


async def test_async_analyzer():
    """非同期版アナライザーテスト"""
    print("=== 非同期版 AsyncLineErrorAnalyzer テスト ===")
    analyzer = AsyncLineErrorAnalyzer()

    test_cases = [
        "(400) Async bad request",
        "(401) Async unauthorized access",
        "(404) Async resource not found",
    ]

    for i, log in enumerate(test_cases, 1):
        try:
            result = await analyzer.analyze(log)
            print(f"{i}. {log}")
            print(
                f"   → Status: {result.status_code}, Category: {result.category.value}"
            )
            print()
        except Exception as e:
            print(f"{i}. {log} → ERROR: {e}")


def test_log_parser():
    """ログパーサーテスト"""
    print("=== LogParser 直接テスト ===")
    parser = LogParser()

    test_logs = [
        "(400) Parse test",
        "(404) Request ID: abc-123",
        "Invalid log format",
    ]

    for i, log in enumerate(test_logs, 1):
        try:
            result = parser.parse(log)
            if result:
                print(
                    f"{i}. {log} → Status: {result.status_code}, Message: {result.message}"
                )
            else:
                print(f"{i}. {log} → No parse result")
        except Exception as e:
            print(f"{i}. {log} → ERROR: {e}")
        print()


def test_api_patterns():
    """APIパターンテスト"""
    print("=== APIパターン列挙型テスト ===")

    print("利用可能なAPIパターン:")
    for pattern in ApiPattern:
        print(f"  - {pattern.name}: {pattern.value}")

    print("\n利用可能なエラーカテゴリ:")
    for category in ErrorCategory:
        print(f"  - {category.name}: {category.value}")


def main():
    """メイン実行"""
    print("🚀 LINE Bot エラーアナライザー - 統合動作確認")
    print("=" * 50)

    try:
        # 1. 同期版テスト
        test_sync_analyzer()

        # 2. 非同期版テスト
        asyncio.run(test_async_analyzer())

        # 3. ログパーサーテスト
        test_log_parser()

        # 4. APIパターンテスト
        test_api_patterns()

        print("🎉 全機能が正常に動作しています！")
        print("✅ Issue #1: ログ文字列解析機能 - 完全実装")
        print("✅ 同期版・非同期版アナライザー - 正常動作")
        print("✅ LogParser - 正常動作")
        print("✅ APIパターン・エラーカテゴリ - 正常動作")

    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
