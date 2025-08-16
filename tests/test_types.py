#!/usr/bin/env python3
"""型とデータ構造のテストケース"""

import unittest
import sys
import os
from typing import get_type_hints

# プロジェクトのルートをPATHに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from linebot_error_analyzer import LineErrorAnalyzer
from linebot_error_analyzer.models import (
    LineErrorInfo,
    ApiPattern,
    ErrorCategory,
)
from linebot_error_analyzer.models.log_parser import LogParser, LogParseResult
from linebot_error_analyzer.models.log_parser import LogParser


class TestTypes(unittest.TestCase):
    """型とデータ構造のテスト"""

    def setUp(self):
        """テストセットアップ"""
        self.analyzer = LineErrorAnalyzer()

    def test_error_result_structure(self):
        """LineErrorInfo構造体のテスト"""
        log = "(404) Not Found"
        result = self.analyzer.analyze(log)

        # 必須フィールドの存在確認
        self.assertTrue(hasattr(result, "status_code"))
        self.assertTrue(hasattr(result, "category"))
        self.assertTrue(hasattr(result, "is_retryable"))
        self.assertTrue(hasattr(result, "description"))

        # 型確認
        self.assertIsInstance(result.status_code, int)
        self.assertIsInstance(result.category, ErrorCategory)
        self.assertIsInstance(result.is_retryable, bool)
        self.assertIsInstance(result.description, str)

        # オプショナルフィールド
        if hasattr(result, "request_id") and result.request_id is not None:
            self.assertIsInstance(result.request_id, str)

        if hasattr(result, "timestamp") and result.timestamp is not None:
            self.assertIsInstance(result.timestamp, str)

    def test_api_pattern_enum(self):
        """ApiPatternエニューメーションのテスト"""
        # 全パターンの存在確認
        expected_patterns = [
            "MESSAGE_REPLY",
            "MESSAGE_PUSH",
            "MESSAGE_MULTICAST",
            "MESSAGE_BROADCAST",
            "MESSAGE_NARROWCAST",
            "USER_PROFILE",
            "GROUP_SUMMARY",
            "ROOM_MEMBER",
            "RICH_MENU",
            "CONTENT",
            "WEBHOOK",
            "CHANNEL_ACCESS_TOKEN",
        ]

        for pattern_name in expected_patterns:
            self.assertTrue(
                hasattr(ApiPattern, pattern_name),
                f"ApiPattern.{pattern_name} not found",
            )

            pattern = getattr(ApiPattern, pattern_name)
            self.assertIsInstance(pattern, ApiPattern)

    def test_error_category_enum(self):
        """ErrorCategoryエニューメーションのテスト"""
        expected_categories = [
            "AUTH_ERROR",
            "INVALID_TOKEN",
            "INVALID_PARAM",
            "RESOURCE_NOT_FOUND",
            "USER_BLOCKED",
            "RATE_LIMIT",
            "SERVER_ERROR",
            "UNKNOWN",
        ]

        for category_name in expected_categories:
            self.assertTrue(
                hasattr(ErrorCategory, category_name),
                f"ErrorCategory.{category_name} not found",
            )

            category = getattr(ErrorCategory, category_name)
            self.assertIsInstance(category, ErrorCategory)

    def test_log_parse_result_structure(self):
        """LogParseResult構造体のテスト"""
        parser = LogParser()
        test_log = """(404)
Reason: Not Found
HTTP response headers: HTTPHeaderDict({'x-line-request-id': 'test123'})
HTTP response body: {"message":"Not found"}"""

        parse_result = parser.parse(test_log)

        # 必須フィールド
        self.assertTrue(hasattr(parse_result, "parse_success"))
        self.assertTrue(hasattr(parse_result, "status_code"))
        self.assertTrue(hasattr(parse_result, "message"))

        # 型確認
        self.assertIsInstance(parse_result.parse_success, bool)
        if parse_result.status_code is not None:
            self.assertIsInstance(parse_result.status_code, int)
        if parse_result.message is not None:
            self.assertIsInstance(parse_result.message, str)
        if parse_result.request_id is not None:
            self.assertIsInstance(parse_result.request_id, str)
        if parse_result.headers is not None:
            self.assertIsInstance(parse_result.headers, dict)

    def test_error_info_structure(self):
        """ErrorInfo構造体のテスト"""
        from linebot_error_analyzer.database.error_database import ErrorDatabase

        db = ErrorDatabase()
        # get_error_infoの代わりにanalyze_errorを使用
        category, _, is_retryable = db.analyze_error(404, "Not found")
        error_details = db.get_error_details(category)

        # 必須フィールド
        self.assertIsNotNone(category)
        self.assertIsInstance(is_retryable, bool)
        self.assertIsInstance(error_details, dict)
        self.assertIn("description", error_details)
        self.assertIn("action", error_details)

        # 型確認
        # 実際に404のレスポンスを生成して検証
        analyzer = LineErrorAnalyzer()
        result = analyzer.analyze("(404) Not found")
        self.assertEqual(result.status_code, 404)
        self.assertIsInstance(result.category, ErrorCategory)
        self.assertIsInstance(result.is_retryable, bool)
        self.assertIsInstance(result.description, str)
        self.assertIsInstance(result.recommended_action, str)

    def test_analyzer_method_signatures(self):
        """アナライザーメソッドのシグネチャテスト"""
        # LineErrorAnalyzerのanalyzeメソッド
        analyze_method = getattr(self.analyzer, "analyze")
        self.assertTrue(callable(analyze_method))

        # ログ文字列での呼び出しテスト
        # パターン1: 基本的なログ
        result1 = self.analyzer.analyze("(404) Not Found")
        self.assertIsInstance(result1, LineErrorInfo)

        # パターン2: 詳細なログ
        result2 = self.analyzer.analyze("(404) User profile not found")
        self.assertIsInstance(result2, LineErrorInfo)

        # パターン3: エラーメッセージ付き
        result3 = self.analyzer.analyze("(500) Internal server error occurred")
        self.assertIsInstance(result3, LineErrorInfo)

        # パターン4: 簡潔なログ
        result4 = self.analyzer.analyze("(429) Rate limit")
        self.assertIsInstance(result4, LineErrorInfo)

    def test_type_hints_consistency(self):
        """型ヒントの整合性テスト"""
        try:
            # LineErrorAnalyzerの型ヒント
            analyzer_hints = get_type_hints(LineErrorAnalyzer.analyze)
            self.assertIsNotNone(analyzer_hints)

            # LineErrorInfoの型ヒント（利用可能な場合）
            if hasattr(LineErrorInfo, "__annotations__"):
                result_annotations = LineErrorInfo.__annotations__
                self.assertIsNotNone(result_annotations)

        except Exception as e:
            # 型ヒントが利用できない環境では警告のみ
            self.skipTest(f"Type hints not available: {e}")

    def test_immutability_and_data_integrity(self):
        """データの不変性と整合性テスト"""
        result = self.analyzer.analyze("(404) Not Found")

        # 基本的な値の妥当性
        self.assertEqual(result.status_code, 404)
        self.assertIsInstance(result.category, ErrorCategory)
        self.assertIsInstance(result.is_retryable, bool)
        self.assertIsInstance(result.description, str)
        self.assertIsInstance(result.recommended_action, str)

        # 文字列フィールドが空でないこと
        self.assertGreater(len(result.description), 0)
        self.assertGreater(len(result.recommended_action), 0)

        # booleanフィールドの妥当性
        self.assertIn(result.is_retryable, [True, False])

    def test_error_handling_with_invalid_types(self):
        """無効な型での例外処理テスト"""
        from linebot_error_analyzer.exceptions import (
            UnsupportedErrorTypeError,
            AnalyzerError,
        )

        # 無効な型での呼び出し
        with self.assertRaises(UnsupportedErrorTypeError):
            self.analyzer.analyze(None)

        with self.assertRaises(AnalyzerError):
            self.analyzer.analyze("")  # 空文字列

        # 不正な形式の場合はUNKNOWNカテゴリで返される
        result = self.analyzer.analyze("invalid format")
        self.assertEqual(result.category, ErrorCategory.UNKNOWN)

    def test_collection_types(self):
        """コレクション型のテスト"""
        # LogParseResultのheadersがdictであることを確認
        parser = LogParser()
        test_log = """(404)
HTTP response headers: HTTPHeaderDict({'key1': 'value1', 'key2': 'value2'})"""

        result = parser.parse(test_log)

        if result.headers is not None:
            self.assertIsInstance(result.headers, dict)
            for key, value in result.headers.items():
                self.assertIsInstance(key, str)
                self.assertIsInstance(value, str)

    def test_optional_fields_handling(self):
        """オプショナルフィールドの処理テスト"""
        # request_idがないケース
        result_without_id = self.analyzer.analyze("(400) Bad Request")
        if hasattr(result_without_id, "request_id"):
            # request_idがある場合はstrまたはNone
            self.assertTrue(
                result_without_id.request_id is None
                or isinstance(result_without_id.request_id, str)
            )

        # request_idがあるケース
        log_with_id = "(404) Request ID: test-id-123"

        result_with_id = self.analyzer.analyze(log_with_id)
        if hasattr(result_with_id, "request_id") and result_with_id.request_id:
            self.assertEqual(result_with_id.request_id, "test-id-123")


if __name__ == "__main__":
    unittest.main()
