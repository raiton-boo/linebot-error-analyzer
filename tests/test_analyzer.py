#!/usr/bin/env python3
"""LineErrorAnalyzer のテストケース"""

import unittest
import sys
import os

# プロジェクトのルートをPATHに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from linebot_error_analyzer import LineErrorAnalyzer
from linebot_error_analyzer.models import ApiPattern, ErrorCategory
from linebot_error_analyzer.exceptions import AnalyzerError


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
        result = self.analyzer.analyze("(400) Bad Request")

        self.assertEqual(result.status_code, 400)
        self.assertEqual(result.category, ErrorCategory.INVALID_PARAM)
        self.assertFalse(result.is_retryable)
        # 日本語の説明を期待
        self.assertIsNotNone(result.description)

    def test_analyze_http_error_401(self):
        """HTTP 401エラーの解析テスト"""
        result = self.analyzer.analyze("(401) Unauthorized")

        self.assertEqual(result.status_code, 401)
        self.assertEqual(result.category, ErrorCategory.AUTH_ERROR)
        self.assertFalse(result.is_retryable)

    def test_analyze_http_error_404(self):
        """HTTP 404エラーの解析テスト"""
        result = self.analyzer.analyze("(404) Not Found")

        self.assertEqual(result.status_code, 404)
        self.assertEqual(result.category, ErrorCategory.RESOURCE_NOT_FOUND)
        self.assertFalse(result.is_retryable)

    def test_analyze_http_error_429(self):
        """HTTP 429エラーの解析テスト"""
        result = self.analyzer.analyze("(429) Too Many Requests")

        self.assertEqual(result.status_code, 429)
        self.assertEqual(result.category, ErrorCategory.RATE_LIMIT)
        self.assertTrue(result.is_retryable)

    def test_analyze_http_error_500(self):
        """HTTP 500エラーの解析テスト"""
        result = self.analyzer.analyze("(500) Internal Server Error")

        self.assertEqual(result.status_code, 500)
        self.assertEqual(result.category, ErrorCategory.SERVER_ERROR)
        self.assertTrue(result.is_retryable)

    def test_analyze_invalid_input(self):
        """無効な入力の解析テスト"""
        # 空文字列の場合、AnalyzerErrorが発生することを期待
        with self.assertRaises(AnalyzerError):
            self.analyzer.analyze("")

    def test_analyze_real_error_log(self):
        """実際のエラーログの解析テスト"""
        error_log = "[2023-08-16T10:15:30Z] Request failed with status code (400): Invalid request body"
        result = self.analyzer.analyze(error_log)

        self.assertEqual(result.status_code, 400)
        self.assertEqual(result.category, ErrorCategory.INVALID_PARAM)
        self.assertFalse(result.is_retryable)

    def test_analyze_with_api_pattern_message_push(self):
        """APIパターン指定での解析テスト（プッシュメッセージ）"""
        error_log = "(400) Invalid request"
        result = self.analyzer.analyze(error_log, ApiPattern.MESSAGE_PUSH)

        self.assertEqual(result.status_code, 400)
        self.assertIsNotNone(result.category)

    def test_analyze_with_api_pattern_user_profile(self):
        """APIパターン指定での解析テスト（ユーザープロフィール）"""
        error_log = "(404) User not found"
        result = self.analyzer.analyze(error_log, ApiPattern.USER_PROFILE)

        self.assertEqual(result.status_code, 404)
        self.assertEqual(result.category, ErrorCategory.RESOURCE_NOT_FOUND)


if __name__ == "__main__":
    unittest.main()
