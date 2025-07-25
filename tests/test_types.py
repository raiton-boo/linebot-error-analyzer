"""
型安全性のテストケース
"""

import unittest
from typing import Dict, Any, List
from line_bot_error_analyzer import (
    LineErrorAnalyzer,
    AsyncLineErrorAnalyzer,
    ErrorCategory,
    ErrorSeverity,
)
from line_bot_error_analyzer.core.models import LineErrorInfo
from line_bot_error_analyzer.utils.types import (
    StatusCode,
    ErrorMessage,
    RequestId,
    Headers,
    RawErrorData,
    ErrorCategoryLiteral,
    ErrorSeverityLiteral,
    SupportedErrorType,
    ErrorDataDict,
    is_valid_status_code,
    is_valid_error_message,
    is_error_data_dict,
    is_http_response_like,
    is_line_bot_v3_exception,
    is_line_bot_v2_error,
)
from line_bot_error_analyzer.exceptions import AnalyzerError


class TestTypeValidation(unittest.TestCase):
    """型検証のテストクラス"""

    def test_valid_status_code(self):
        """有効なステータスコードのテスト"""
        self.assertTrue(is_valid_status_code(200))
        self.assertTrue(is_valid_status_code(404))
        self.assertTrue(is_valid_status_code(500))

        # 無効なステータスコード
        self.assertFalse(is_valid_status_code(50))  # 範囲外
        self.assertFalse(is_valid_status_code(1000))  # 範囲外
        self.assertFalse(is_valid_status_code("200"))  # 文字列
        self.assertFalse(is_valid_status_code(None))  # None

    def test_valid_error_message(self):
        """有効なエラーメッセージのテスト"""
        self.assertTrue(is_valid_error_message("Valid error message"))
        self.assertTrue(is_valid_error_message("エラーメッセージ"))

        # 無効なエラーメッセージ
        self.assertFalse(is_valid_error_message(""))  # 空文字
        self.assertFalse(is_valid_error_message("   "))  # 空白のみ
        self.assertFalse(is_valid_error_message(None))  # None
        self.assertFalse(is_valid_error_message(123))  # 数値

    def test_error_data_dict_validation(self):
        """ErrorDataDict型の検証テスト"""
        # 有効なエラーデータ
        valid_data = {"status_code": 400, "message": "Invalid request"}
        self.assertTrue(is_error_data_dict(valid_data))

        # statusフィールドでも有効
        valid_data2 = {"status": 401, "error": "Authentication failed"}
        self.assertTrue(is_error_data_dict(valid_data2))

        # 無効なエラーデータ
        self.assertFalse(is_error_data_dict({}))  # 空辞書
        self.assertFalse(is_error_data_dict({"status_code": 400}))  # messageなし
        self.assertFalse(is_error_data_dict({"message": "error"}))  # statusなし
        self.assertFalse(is_error_data_dict("not_dict"))  # 辞書でない

    def test_line_error_info_validation(self):
        """LineErrorInfo の型検証テスト"""
        # 有効なデータでの作成
        valid_info = LineErrorInfo(
            status_code=400,
            error_code=None,
            message="Test error",
            category=ErrorCategory.INVALID_PARAM,
            severity=ErrorSeverity.HIGH,
            is_retryable=False,
            description="Test description",
            recommended_action="Test action",
        )

        self.assertEqual(valid_info.status_code, 400)
        self.assertEqual(valid_info.category, ErrorCategory.INVALID_PARAM)
        self.assertEqual(valid_info.severity, ErrorSeverity.HIGH)

        # 無効なステータスコードでエラー
        with self.assertRaises(ValueError):
            LineErrorInfo(
                status_code=50,  # 無効な範囲
                error_code=None,
                message="Test error",
                category=ErrorCategory.INVALID_PARAM,
                severity=ErrorSeverity.HIGH,
                is_retryable=False,
                description="Test description",
                recommended_action="Test action",
            )

        # 無効なメッセージでエラー
        with self.assertRaises(ValueError):
            LineErrorInfo(
                status_code=400,
                error_code=None,
                message="",  # 空メッセージ
                category=ErrorCategory.INVALID_PARAM,
                severity=ErrorSeverity.HIGH,
                is_retryable=False,
                description="Test description",
                recommended_action="Test action",
            )

    def test_analyzer_type_hints(self):
        """分析器の型ヒントテスト"""
        analyzer = LineErrorAnalyzer()

        # 正常なエラーデータ
        error_data: ErrorDataDict = {
            "status_code": 401,
            "message": "Authentication failed",
        }

        result = analyzer.analyze(error_data)
        self.assertIsInstance(result, LineErrorInfo)
        self.assertEqual(result.status_code, 401)

        # 複数エラーの分析
        errors: List[Dict[str, Any]] = [
            {"status_code": 401, "message": "Auth error"},
            {"status_code": 429, "message": "Rate limit"},
        ]

        results = analyzer.analyze_multiple(errors)
        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 2)
        for result in results:
            self.assertIsInstance(result, LineErrorInfo)


class TestAsyncTypeHints(unittest.IsolatedAsyncioTestCase):
    """非同期版の型ヒントテスト"""

    async def test_async_analyzer_type_hints(self):
        """非同期分析器の型ヒントテスト"""
        analyzer = AsyncLineErrorAnalyzer()

        # 正常なエラーデータ
        error_data: ErrorDataDict = {"status_code": 500, "message": "Server error"}

        result = await analyzer.analyze(error_data)
        self.assertIsInstance(result, LineErrorInfo)
        self.assertEqual(result.status_code, 500)

        # 複数エラーの非同期分析
        errors: List[Dict[str, Any]] = [
            {"status_code": 401, "message": "Auth error"},
            {"status_code": 429, "message": "Rate limit"},
            {"status_code": 500, "message": "Server error"},
        ]

        results = await analyzer.analyze_multiple(errors)
        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 3)
        for result in results:
            self.assertIsInstance(result, LineErrorInfo)

    async def test_async_batch_type_hints(self):
        """非同期バッチ処理の型ヒントテスト"""
        analyzer = AsyncLineErrorAnalyzer()

        # 大量のエラーデータ
        errors: List[ErrorDataDict] = []
        for i in range(20):
            errors.append({"status_code": 400 + (i % 5), "message": f"Error {i}"})

        results = await analyzer.analyze_batch(errors, batch_size=5)
        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 20)
        for result in results:
            self.assertIsInstance(result, LineErrorInfo)


class TestProtocolCompliance(unittest.TestCase):
    """プロトコル準拠性のテスト"""

    def test_http_response_like_protocol(self):
        """HTTPレスポンスライクプロトコルのテスト"""
        from unittest.mock import Mock

        # プロトコルに準拠するオブジェクト
        mock_response = Mock()
        mock_response.status_code = 403
        mock_response.text = '{"message": "Forbidden"}'
        mock_response.headers = {"Content-Type": "application/json"}

        self.assertTrue(is_http_response_like(mock_response))

        # プロトコルに準拠しないオブジェクト（textがない）
        incomplete_response = Mock()
        incomplete_response.status_code = 403
        incomplete_response.headers = {"Content-Type": "application/json"}
        # textプロパティを明示的に削除
        del incomplete_response.text

        self.assertFalse(is_http_response_like(incomplete_response))

    def test_line_bot_exception_detection(self):
        """LINE Bot例外検出のテスト"""
        from unittest.mock import Mock

        # v3 ApiException風オブジェクト
        v3_exception = Mock()
        v3_exception.__module__ = "linebot.v3.messaging.exceptions"
        v3_exception.status = 404
        v3_exception.body = '{"message": "Not found"}'

        self.assertTrue(is_line_bot_v3_exception(v3_exception))

        # v2 LineBotApiError風オブジェクト
        v2_error = Mock()
        v2_error.__module__ = "linebot.exceptions"
        v2_error.status_code = 400
        v2_error.error = Mock()

        self.assertTrue(is_line_bot_v2_error(v2_error))


class TestTypeCompatibility(unittest.TestCase):
    """型互換性のテスト"""

    def test_backwards_compatibility(self):
        """後方互換性のテスト"""
        analyzer = LineErrorAnalyzer()

        # 古い形式の辞書（Any型として）
        old_style_error: Any = {"status_code": 401, "message": "Old style error"}

        # 型ヒント強化後も動作することを確認
        result = analyzer.analyze(old_style_error)
        self.assertIsInstance(result, LineErrorInfo)
        self.assertEqual(result.status_code, 401)

    def test_mixed_type_analysis(self):
        """混合型分析のテスト"""
        analyzer = LineErrorAnalyzer()

        # 様々な型のエラーを混合
        mixed_errors = [
            {"status_code": 401, "message": "Dict error"},
            "string_error",  # 不正な型
            {"status_code": 429, "message": "Another dict error"},
        ]

        results = analyzer.analyze_multiple(mixed_errors)
        self.assertEqual(len(results), 3)

        # 1番目と3番目は正常に分析される
        self.assertEqual(results[0].status_code, 401)
        self.assertEqual(results[2].status_code, 429)

        # 2番目は分析失敗として処理される
        self.assertEqual(results[1].category, ErrorCategory.UNKNOWN)


if __name__ == "__main__":
    unittest.main(verbosity=2)
