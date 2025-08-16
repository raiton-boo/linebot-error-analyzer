#!/usr/bin/env python3
"""LineErrorAnalyzer のテストケース"""

import unittest
import sys
import os

# プロジェクトのルートをPATHに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from linebot_error_analyzer import LineErrorAnalyzer
from linebot_error_analyzer.models import ApiPattern, ErrorCategory


class TestLineErrorAnalyzer(unittest.TestCase):
    """LineErrorAnalyzer の基本機能テスト"""

    def setUp(self):
        """テストセットアップ"""
        self.analyzer = LineErrorAnalyzer()

    def test_create_analyzer(self):
        """アナライザーの作成テスト"""
        self.assertIsInstance(self.analyzer, LineErrorAnalyzer)

    def test_analyze_http_error_400(self):
        """HTTP 400エラーの解析テスト"""
        result = self.analyzer.analyze(400, "Bad Request")
        
        self.assertEqual(result.status_code, 400)
        self.assertEqual(result.category, ErrorCategory.CLIENT_ERROR)
        self.assertFalse(result.is_retryable)
        self.assertIn("Bad Request", result.description)

    def test_analyze_http_error_401(self):
        """HTTP 401エラーの解析テスト"""
        result = self.analyzer.analyze(401, "Unauthorized")
        
        self.assertEqual(result.status_code, 401)
        self.assertEqual(result.category, ErrorCategory.AUTHENTICATION_ERROR)
        self.assertFalse(result.is_retryable)
        self.assertIn("認証", result.description.lower())

    def test_analyze_http_error_404(self):
        """HTTP 404エラーの解析テスト"""
        result = self.analyzer.analyze(404, "Not Found")
        
        self.assertEqual(result.status_code, 404)
        self.assertEqual(result.category, ErrorCategory.RESOURCE_NOT_FOUND)
        self.assertFalse(result.is_retryable)

    def test_analyze_http_error_429(self):
        """HTTP 429エラー（レート制限）の解析テスト"""
        result = self.analyzer.analyze(429, "Too Many Requests")
        
        self.assertEqual(result.status_code, 429)
        self.assertEqual(result.category, ErrorCategory.RATE_LIMIT_EXCEEDED)
        self.assertTrue(result.is_retryable)

    def test_analyze_http_error_500(self):
        """HTTP 500エラーの解析テスト"""
        result = self.analyzer.analyze(500, "Internal Server Error")
        
        self.assertEqual(result.status_code, 500)
        self.assertEqual(result.category, ErrorCategory.SERVER_ERROR)
        self.assertTrue(result.is_retryable)

    def test_analyze_real_error_log(self):
        """実際のエラーログの解析テスト"""
        error_log = """(404)
Reason: Not Found
HTTP response headers: HTTPHeaderDict({'server': 'legy', 'x-line-request-id': 'abc123'})
HTTP response body: {"message":"Not found"}"""

        result = self.analyzer.analyze(error_log)
        
        self.assertEqual(result.status_code, 404)
        self.assertEqual(result.category, ErrorCategory.RESOURCE_NOT_FOUND)
        self.assertEqual(result.request_id, "abc123")
        self.assertFalse(result.is_retryable)

    def test_analyze_with_api_pattern_user_profile(self):
        """APIパターン指定でのユーザープロフィール取得エラーテスト"""
        error_log = """(404)
HTTP response body: {"message":"Not found"}"""

        result = self.analyzer.analyze(error_log, api_pattern=ApiPattern.USER_PROFILE)
        
        self.assertEqual(result.status_code, 404)
        self.assertEqual(result.category, ErrorCategory.USER_BLOCKED)

    def test_analyze_with_api_pattern_message_push(self):
        """APIパターン指定でのメッセージ送信エラーテスト"""
        error_log = """(404)
HTTP response body: {"message":"Not found"}"""

        result = self.analyzer.analyze(error_log, api_pattern=ApiPattern.MESSAGE_PUSH)
        
        self.assertEqual(result.status_code, 404)
        self.assertEqual(result.category, ErrorCategory.USER_BLOCKED)

    def test_analyze_invalid_input(self):
        """無効な入力のテスト"""
        with self.assertRaises(ValueError):
            self.analyzer.analyze(None)

        with self.assertRaises(ValueError):
            self.analyzer.analyze("")


if __name__ == "__main__":
    unittest.main()
