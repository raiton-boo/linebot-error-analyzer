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
            result = await self.analyzer.analyze(400, "Bad Request")
            
            self.assertEqual(result.status_code, 400)
            self.assertEqual(result.category, ErrorCategory.CLIENT_ERROR)
            self.assertFalse(result.is_retryable)
            return result

        result = self.loop.run_until_complete(async_test())
        self.assertIsNotNone(result)

    def test_analyze_async_http_error_401(self):
        """非同期HTTP 401エラーの解析テスト"""
        async def async_test():
            result = await self.analyzer.analyze(401, "Unauthorized")
            
            self.assertEqual(result.status_code, 401)
            self.assertEqual(result.category, ErrorCategory.AUTHENTICATION_ERROR)
            self.assertFalse(result.is_retryable)
            return result

        result = self.loop.run_until_complete(async_test())
        self.assertIsNotNone(result)

    def test_analyze_async_real_error_log(self):
        """非同期での実際のエラーログ解析テスト"""
        async def async_test():
            error_log = """(404)
Reason: Not Found
HTTP response headers: HTTPHeaderDict({'x-line-request-id': 'test-123'})
HTTP response body: {"message":"Not found"}"""

            result = await self.analyzer.analyze(error_log)
            
            self.assertEqual(result.status_code, 404)
            self.assertEqual(result.category, ErrorCategory.RESOURCE_NOT_FOUND)
            self.assertEqual(result.request_id, "test-123")
            return result

        result = self.loop.run_until_complete(async_test())
        self.assertIsNotNone(result)

    def test_analyze_async_with_api_pattern(self):
        """非同期でのAPIパターン指定テスト"""
        async def async_test():
            error_log = """(404)
HTTP response body: {"message":"Not found"}"""

            result = await self.analyzer.analyze(error_log, api_pattern=ApiPattern.USER_PROFILE)
            
            self.assertEqual(result.status_code, 404)
            self.assertEqual(result.category, ErrorCategory.USER_BLOCKED)
            return result

        result = self.loop.run_until_complete(async_test())
        self.assertIsNotNone(result)

    def test_analyze_async_multiple_requests(self):
        """非同期での複数リクエスト同時処理テスト"""
        async def async_test():
            tasks = []
            
            # 複数の異なるエラーを同時に解析
            for status_code in [400, 401, 404, 429, 500]:
                task = self.analyzer.analyze(status_code, f"Error {status_code}")
                tasks.append(task)
            
            results = await asyncio.gather(*tasks)
            
            # 結果検証
            self.assertEqual(len(results), 5)
            for i, result in enumerate(results):
                expected_status = [400, 401, 404, 429, 500][i]
                self.assertEqual(result.status_code, expected_status)
            
            return results

        results = self.loop.run_until_complete(async_test())
        self.assertEqual(len(results), 5)


if __name__ == "__main__":
    unittest.main()
