#!/usr/bin/env python3
"""AsyncLineErrorAnalyzer のテストケース"""

import unittest
import asyncio
import sys
import os

# プロジェクトのルートをPATHに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from linebot_error_analyzer import AsyncLineErrorAnalyzer
from linebot_error_analyzer.models import ApiPattern, ErrorCategory
from linebot_error_analyzer.exceptions import AnalyzerError


class TestAsyncLineErrorAnalyzer(unittest.TestCase):
    """AsyncLineErrorAnalyzer の基本機能テスト"""

    def setUp(self):
        """テストセットアップ"""
        self.analyzer = AsyncLineErrorAnalyzer()
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        """テストクリーンアップ"""
        self.loop.close()

    def test_create_async_analyzer(self):
        """非同期アナライザーの作成テスト"""
        self.assertIsInstance(self.analyzer, AsyncLineErrorAnalyzer)

    def test_analyze_async_http_error_400(self):
        """非同期HTTP 400エラーの解析テスト"""

        async def async_test():
            result = await self.analyzer.analyze("(400) Bad Request")

            self.assertEqual(result.status_code, 400)
            self.assertEqual(result.category, ErrorCategory.INVALID_PARAM)
            self.assertFalse(result.is_retryable)
            return result

        result = self.loop.run_until_complete(async_test())
        self.assertIsNotNone(result)

    def test_analyze_async_http_error_401(self):
        """非同期HTTP 401エラーの解析テスト"""

        async def async_test():
            result = await self.analyzer.analyze("(401) Unauthorized")

            self.assertEqual(result.status_code, 401)
            self.assertEqual(result.category, ErrorCategory.AUTH_ERROR)
            self.assertFalse(result.is_retryable)
            return result

        result = self.loop.run_until_complete(async_test())
        self.assertIsNotNone(result)

    def test_analyze_async_http_error_429(self):
        """非同期HTTP 429エラーの解析テスト"""

        async def async_test():
            result = await self.analyzer.analyze("(429) Too Many Requests")

            self.assertEqual(result.status_code, 429)
            self.assertEqual(result.category, ErrorCategory.RATE_LIMIT)
            self.assertTrue(result.is_retryable)
            return result

        result = self.loop.run_until_complete(async_test())
        self.assertIsNotNone(result)

    def test_analyze_async_http_error_500(self):
        """非同期HTTP 500エラーの解析テスト"""

        async def async_test():
            result = await self.analyzer.analyze("(500) Internal Server Error")

            self.assertEqual(result.status_code, 500)
            self.assertEqual(result.category, ErrorCategory.SERVER_ERROR)
            self.assertTrue(result.is_retryable)
            return result

        result = self.loop.run_until_complete(async_test())
        self.assertIsNotNone(result)

    def test_analyze_async_invalid_input(self):
        """非同期無効入力の解析テスト"""

        async def async_test():
            with self.assertRaises(AnalyzerError):
                await self.analyzer.analyze("")

        self.loop.run_until_complete(async_test())

    def test_analyze_async_multiple_errors(self):
        """非同期複数エラーの解析テスト"""

        async def async_test():
            errors = [
                "(400) Bad Request",
                "(401) Unauthorized",
                "(500) Internal Server Error",
            ]

            results = []
            for error in errors:
                result = await self.analyzer.analyze(error)
                results.append(result)

            self.assertEqual(len(results), 3)
            self.assertEqual(results[0].status_code, 400)
            self.assertEqual(results[1].status_code, 401)
            self.assertEqual(results[2].status_code, 500)
            return results

        results = self.loop.run_until_complete(async_test())
        self.assertIsNotNone(results)

    def test_analyze_async_with_api_pattern(self):
        """非同期APIパターン指定での解析テスト"""

        async def async_test():
            error_log = "(404) User not found"
            result = await self.analyzer.analyze(error_log, ApiPattern.USER_PROFILE)

            self.assertEqual(result.status_code, 404)
            self.assertEqual(result.category, ErrorCategory.RESOURCE_NOT_FOUND)
            return result

        result = self.loop.run_until_complete(async_test())
        self.assertIsNotNone(result)


if __name__ == "__main__":
    unittest.main()
