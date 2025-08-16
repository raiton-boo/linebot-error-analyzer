#!/usr/bin/env python3
"""APIパターン特有のテストケース"""

import unittest
import asyncio
import sys
import os

# プロジェクトのルートをPATHに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from linebot_error_analyzer import LineErrorAnalyzer, AsyncLineErrorAnalyzer
from linebot_error_analyzer.models import ApiPattern, ErrorCategory


class TestApiPatterns(unittest.TestCase):
    """APIパターン特有の機能テスト"""

    def setUp(self):
        """テストセットアップ"""
        self.analyzer = LineErrorAnalyzer()
        self.async_analyzer = AsyncLineErrorAnalyzer()

    def test_user_profile_blocked_vs_not_found(self):
        """ユーザープロフィール取得：ブロック vs 存在しない"""
        # ブロックされている場合
        blocked_log = '(404) {"message":"Not found"}'
        result_blocked = self.analyzer.analyze(blocked_log, ApiPattern.USER_PROFILE)

        self.assertEqual(result_blocked.category, ErrorCategory.USER_BLOCKED)
        self.assertIn("ブロック", result_blocked.description)

        # 明確に存在しないユーザーの場合
        not_found_log = '(404) {"message":"User not found"}'
        result_not_found = self.analyzer.analyze(not_found_log, ApiPattern.USER_PROFILE)

        # メッセージが明確な場合は適切に分類される
        self.assertIsNotNone(result_not_found.category)

    def test_message_api_patterns(self):
        """メッセージ送信APIのパターンテスト"""
        test_cases = [
            (ApiPattern.MESSAGE_PUSH, "プッシュメッセージ"),
            (ApiPattern.MESSAGE_REPLY, "リプライメッセージ"),
            (ApiPattern.MESSAGE_MULTICAST, "マルチキャストメッセージ"),
        ]

        error_log = '(404) {"message":"Not found"}'

        for pattern, description in test_cases:
            with self.subTest(pattern=pattern):
                result = self.analyzer.analyze(error_log, pattern)
                self.assertEqual(result.category, ErrorCategory.USER_BLOCKED)
                self.assertIn(description, result.description)

    def test_webhook_api_patterns(self):
        """Webhook関連APIのパターンテスト"""
        webhook_patterns = [
            ApiPattern.WEBHOOK_SETTINGS,
            ApiPattern.WEBHOOK_TEST,
        ]

        error_log = '(400) {"message":"Invalid webhook URL"}'

        for pattern in webhook_patterns:
            with self.subTest(pattern=pattern):
                result = self.analyzer.analyze(error_log, pattern)
                self.assertEqual(result.status_code, 400)
                self.assertEqual(result.category, ErrorCategory.CLIENT_ERROR)

    def test_rich_menu_patterns(self):
        """リッチメニュー関連のパターンテスト"""
        rich_menu_patterns = [
            ApiPattern.RICH_MENU_CREATE,
            ApiPattern.RICH_MENU_UPDATE,
            ApiPattern.RICH_MENU_DELETE,
            ApiPattern.RICH_MENU_SET_USER,
        ]

        error_log = '(413) {"message":"Request entity too large"}'

        for pattern in rich_menu_patterns:
            with self.subTest(pattern=pattern):
                result = self.analyzer.analyze(error_log, pattern)
                self.assertEqual(result.status_code, 413)
                self.assertIn("サイズ", result.description)

    def test_group_room_patterns(self):
        """グループ・ルーム関連のパターンテスト"""
        group_patterns = [
            ApiPattern.GROUP_MEMBERS,
            ApiPattern.GROUP_PROFILE,
            ApiPattern.ROOM_MEMBERS,
            ApiPattern.ROOM_PROFILE,
        ]

        error_log = '(403) {"message":"Forbidden"}'

        for pattern in group_patterns:
            with self.subTest(pattern=pattern):
                result = self.analyzer.analyze(error_log, pattern)
                self.assertEqual(result.status_code, 403)
                self.assertEqual(result.category, ErrorCategory.PERMISSION_ERROR)

    def test_async_api_patterns(self):
        """非同期でのAPIパターンテスト"""

        async def async_test():
            error_log = '(429) {"message":"Rate limit exceeded"}'
            result = await self.async_analyzer.analyze(
                error_log, ApiPattern.MESSAGE_PUSH
            )

            self.assertEqual(result.status_code, 429)
            self.assertEqual(result.category, ErrorCategory.RATE_LIMIT_ERROR)
            self.assertTrue(result.is_retryable)
            return result

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            result = loop.run_until_complete(async_test())
            self.assertIsNotNone(result)
        finally:
            loop.close()

    def test_pattern_specific_solutions(self):
        """パターン特有の解決策テスト"""
        test_cases = [
            (ApiPattern.MESSAGE_PUSH, 404, "ユーザーID"),
            (ApiPattern.USER_PROFILE, 404, "ブロック"),
            (ApiPattern.RICH_MENU_CREATE, 400, "JSON"),
        ]

        for pattern, status_code, expected_keyword in test_cases:
            with self.subTest(pattern=pattern, status=status_code):
                error_log = f'({status_code}) {{"message":"Error occurred"}}'
                result = self.analyzer.analyze(error_log, pattern)

                self.assertEqual(result.status_code, status_code)
                # 推奨アクションに期待キーワードが含まれることを確認
                self.assertIn(expected_keyword, result.recommended_action)

    def test_no_pattern_vs_with_pattern(self):
        """パターン指定なしと指定ありの比較"""
        error_log = '(404) {"message":"Not found"}'

        # パターン指定なし
        result_no_pattern = self.analyzer.analyze(error_log)

        # パターン指定あり
        result_with_pattern = self.analyzer.analyze(error_log, ApiPattern.USER_PROFILE)

        # パターン指定により異なる結果になることを確認
        self.assertNotEqual(result_no_pattern.category, result_with_pattern.category)
        self.assertNotEqual(
            result_no_pattern.description, result_with_pattern.description
        )


if __name__ == "__main__":
    unittest.main()
