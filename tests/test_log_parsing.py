#!/usr/bin/env python3
"""ログ文字列解        self.assertEqual(result.status_code, 404)
self.assertEqual(result.category, ErrorCategory.RESOURCE_NOT_FOUND)
self.assertEqual(result.request_id, 'abc123')
self.assertIn("リソース", result.description)トケース"""

import unittest
import sys
import os

# プロジェクトのルートをPATHに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from linebot_error_analyzer import LineErrorAnalyzer
from linebot_error_analyzer.models import ApiPattern, ErrorCategory
from linebot_error_analyzer.models.log_parser import LogParser


class TestLogParsing(unittest.TestCase):
    """ログ文字列解析の機能テスト"""

    def setUp(self):
        """テストセットアップ"""
        self.analyzer = LineErrorAnalyzer()
        self.log_parser = LogParser()

    def test_parse_real_error_log(self):
        """実際のエラーログの解析テスト"""
        real_log = """(404)
Reason: Not Found
HTTP response headers: HTTPHeaderDict({'server': 'legy', 'x-line-request-id': 'abc123'})
HTTP response body: {"message":"Not found"}"""

        result = self.analyzer.analyze(real_log)

        self.assertEqual(result.status_code, 404)
        self.assertEqual(result.category, ErrorCategory.RESOURCE_NOT_FOUND)
        self.assertEqual(result.request_id, "abc123")
        self.assertIn("リソース", result.description)

    def test_parse_with_api_pattern_user_profile(self):
        """APIパターン指定でのユーザープロフィール取得エラー"""
        log = """(404)
Reason: Not Found  
HTTP response body: {"message":"Not found"}"""

        result = self.analyzer.analyze(log, ApiPattern.USER_PROFILE)

        self.assertEqual(result.status_code, 404)
        self.assertEqual(result.category, ErrorCategory.USER_BLOCKED)
        self.assertIn("ユーザーがボットをブロック", result.description)

    def test_parse_message_push_blocked(self):
        """メッセージ送信でのブロック検出テスト"""
        log = """(404)
HTTP response body: {"message":"Not found"}"""

        result = self.analyzer.analyze(log, ApiPattern.MESSAGE_PUSH)

        self.assertEqual(result.status_code, 404)
        self.assertEqual(result.category, ErrorCategory.USER_BLOCKED)

    def test_parse_simple_http_error(self):
        """シンプルなHTTPエラー文字列の解析"""
        simple_errors = [
            "HTTP Error 401: Unauthorized",
            "Request failed with status code (400): Bad Request",
            "Rate limit exceeded (429): Too many requests",
        ]

        for error_str in simple_errors:
            with self.subTest(error=error_str):
                result = self.analyzer.analyze(error_str)
                self.assertIsNotNone(result.status_code)
                self.assertIsNotNone(result.category)

    def test_parse_json_error_response(self):
        """JSON形式のエラーレスポンスの解析"""
        json_error = '{"message": "The request body has 2 error(s)", "details": [{"message": "May not be empty", "property": "messages[0].text"}]}'

        result = self.analyzer.analyze(json_error)

        # JSON形式の場合、ステータスコードが不明でも解析できる
        self.assertIsNotNone(result.category)
        self.assertIn("request", result.description.lower())

    def test_log_parser_direct(self):
        """LogParserの直接テスト"""
        log = """(500)
Reason: Internal Server Error
HTTP response headers: HTTPHeaderDict({'x-line-request-id': 'test123'})
HTTP response body: {"message":"Server error"}"""

        parse_result = self.log_parser.parse(log)

        self.assertTrue(parse_result.parse_success)
        self.assertEqual(parse_result.status_code, 500)
        self.assertEqual(parse_result.request_id, "test123")
        self.assertEqual(parse_result.message, "Server error")

    def test_malformed_log_handling(self):
        """不正形式のログの処理テスト"""
        malformed_logs = [
            "",  # 空文字列
            "Invalid log format",  # 形式不正
            "123",  # 数字のみ
            "HTTP Error: Missing status code",  # ステータスコード不明
        ]

        for log in malformed_logs:
            with self.subTest(log=log):
                result = self.analyzer.analyze(log)
                # エラーが起きずに何らかの結果が返ることを確認
                self.assertIsNotNone(result)
                self.assertIsNotNone(result.category)

    def test_multiple_status_codes_in_log(self):
        """ログ内に複数のステータスコードがある場合"""
        log = "Previous error (401) but current error is (404) Not Found"

        result = self.analyzer.analyze(log)

        # 最初に見つかったステータスコードが使用される
        self.assertEqual(result.status_code, 401)

    def test_request_id_extraction(self):
        """リクエストID抽出のテスト"""
        logs_with_request_ids = [
            ("x-line-request-id: abc-123", "abc-123"),
            ("'x-line-request-id': 'def-456'", "def-456"),
            ('"x-line-request-id": "ghi-789"', "ghi-789"),
            ("request-id=jkl-000", "jkl-000"),
        ]

        for log, expected_id in logs_with_request_ids:
            with self.subTest(log=log):
                parse_result = self.log_parser.parse(f"(404) {log}")
                self.assertEqual(parse_result.request_id, expected_id)


if __name__ == "__main__":
    unittest.main()
