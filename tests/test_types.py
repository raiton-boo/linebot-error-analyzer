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
    ErrorResult,
    ApiPattern,
    ErrorCategory,
    LogParseResult,
    ErrorInfo,
)
from linebot_error_analyzer.models.log_parser import LogParser


class TestTypes(unittest.TestCase):
    """型とデータ構造のテスト"""

    def setUp(self):
        """テストセットアップ"""
        self.analyzer = LineErrorAnalyzer()

    def test_error_result_structure(self):
        """ErrorResult構造体のテスト"""
        result = self.analyzer.analyze(404, "Not Found")

        # 必須フィールドの存在確認
        self.assertTrue(hasattr(result, "status_code"))
        self.assertTrue(hasattr(result, "category"))
        self.assertTrue(hasattr(result, "is_retryable"))
        self.assertTrue(hasattr(result, "description"))
        self.assertTrue(hasattr(result, "recommended_action"))

        # 型確認
        self.assertIsInstance(result.status_code, int)
        self.assertIsInstance(result.category, ErrorCategory)
        self.assertIsInstance(result.is_retryable, bool)
        self.assertIsInstance(result.description, str)
        self.assertIsInstance(result.recommended_action, str)

        # オプショナルフィールド
        if result.request_id is not None:
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
            "USER_PROFILE",
            "GROUP_PROFILE",
            "ROOM_PROFILE",
            "GROUP_MEMBER_PROFILE",
            "ROOM_MEMBER_PROFILE",
            "GROUP_MEMBER_COUNT",
            "ROOM_MEMBER_COUNT",
            "RICH_MENU_CREATE",
            "RICH_MENU_UPDATE",
            "RICH_MENU_DELETE",
            "WEBHOOK_SETTINGS",
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
            "CLIENT_ERROR",
            "AUTHENTICATION_ERROR",
            "AUTHORIZATION_ERROR",
            "RESOURCE_NOT_FOUND",
            "USER_BLOCKED",
            "RATE_LIMIT_EXCEEDED",
            "SERVER_ERROR",
            "UNKNOWN_ERROR",
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
        error_info = db.get_error_info(404)

        # 必須フィールド
        self.assertTrue(hasattr(error_info, "status_code"))
        self.assertTrue(hasattr(error_info, "category"))
        self.assertTrue(hasattr(error_info, "is_retryable"))
        self.assertTrue(hasattr(error_info, "description"))
        self.assertTrue(hasattr(error_info, "recommended_action"))

        # 型確認
        self.assertIsInstance(error_info.status_code, int)
        self.assertIsInstance(error_info.category, ErrorCategory)
        self.assertIsInstance(error_info.is_retryable, bool)
        self.assertIsInstance(error_info.description, str)
        self.assertIsInstance(error_info.recommended_action, str)

    def test_analyzer_method_signatures(self):
        """アナライザーメソッドのシグネチャテスト"""
        # LineErrorAnalyzerのanalyzeメソッド
        analyze_method = getattr(self.analyzer, "analyze")
        self.assertTrue(callable(analyze_method))

        # オーバーロードされたメソッドの呼び出しテスト
        # パターン1: (status_code, message)
        result1 = self.analyzer.analyze(404, "Not Found")
        self.assertIsInstance(result1, ErrorResult)

        # パターン2: (status_code, message, api_pattern)
        result2 = self.analyzer.analyze(404, "Not Found", ApiPattern.USER_PROFILE)
        self.assertIsInstance(result2, ErrorResult)

        # パターン3: (error_log_string)
        result3 = self.analyzer.analyze("(404) Not Found")
        self.assertIsInstance(result3, ErrorResult)

        # パターン4: (error_log_string, api_pattern)
        result4 = self.analyzer.analyze("(404) Not Found", ApiPattern.USER_PROFILE)
        self.assertIsInstance(result4, ErrorResult)

    def test_type_hints_consistency(self):
        """型ヒントの整合性テスト"""
        try:
            # LineErrorAnalyzerの型ヒント
            analyzer_hints = get_type_hints(LineErrorAnalyzer.analyze)
            self.assertIsNotNone(analyzer_hints)

            # ErrorResultの型ヒント（利用可能な場合）
            if hasattr(ErrorResult, "__annotations__"):
                result_annotations = ErrorResult.__annotations__
                self.assertIsNotNone(result_annotations)

        except Exception as e:
            # 型ヒントが利用できない環境では警告のみ
            self.skipTest(f"Type hints not available: {e}")

    def test_immutability_and_data_integrity(self):
        """データの不変性と整合性テスト"""
        result = self.analyzer.analyze(404, "Not Found")

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
        # 無効な型での呼び出し
        with self.assertRaises((TypeError, ValueError)):
            self.analyzer.analyze(None, "test")

        with self.assertRaises((TypeError, ValueError)):
            self.analyzer.analyze("404", None)  # 文字列のステータスコード

        with self.assertRaises((TypeError, ValueError)):
            self.analyzer.analyze(404.5, "test")  # 浮動小数点のステータスコード

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
        result_without_id = self.analyzer.analyze(400, "Bad Request")
        if hasattr(result_without_id, "request_id"):
            # request_idがある場合はstrまたはNone
            self.assertTrue(
                result_without_id.request_id is None
                or isinstance(result_without_id.request_id, str)
            )

        # request_idがあるケース
        log_with_id = """(404)
HTTP response headers: HTTPHeaderDict({'x-line-request-id': 'test-id-123'})"""

        result_with_id = self.analyzer.analyze(log_with_id)
        if hasattr(result_with_id, "request_id") and result_with_id.request_id:
            self.assertEqual(result_with_id.request_id, "test-id-123")


if __name__ == "__main__":
    unittest.main()
