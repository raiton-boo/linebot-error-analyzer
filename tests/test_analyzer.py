"""
LINE Bot エラー分析器のテストケース
"""

import unittest
from unittest.mock import Mock, patch
from linebot_error_analyzer import LineErrorAnalyzer, ErrorCategory, ErrorSeverity
from linebot_error_analyzer.exceptions import AnalyzerError


class TestLineErrorAnalyzer(unittest.TestCase):
    """LineErrorAnalyzer のテストクラス"""

    def setUp(self):
        """テストセットアップ"""
        self.analyzer = LineErrorAnalyzer()

    def test_analyze_dict_auth_error(self):
        """認証エラーの辞書形式分析テスト"""
        error_data = {"status_code": 401, "message": "not authorized"}
        result = self.analyzer.analyze(error_data)

        self.assertEqual(result.category, ErrorCategory.AUTH_ERROR)
        self.assertEqual(result.status_code, 401)
        self.assertEqual(result.severity, ErrorSeverity.CRITICAL)
        self.assertFalse(result.is_retryable)

    def test_analyze_dict_rate_limit(self):
        """レート制限エラーの分析テスト"""
        error_data = {
            "status_code": 429,
            "message": "Too many requests - rate limit exceeded",
        }

        result = self.analyzer.analyze(error_data)

        self.assertEqual(result.status_code, 429)
        self.assertEqual(result.category, ErrorCategory.RATE_LIMIT)
        self.assertEqual(result.severity, ErrorSeverity.MEDIUM)
        self.assertTrue(result.is_retryable)
        self.assertEqual(result.retry_after, 60)
        self.assertIn("制限", result.description)

    def test_analyze_dict_invalid_reply_token(self):
        """無効な返信トークンエラーの分析テスト"""
        error_data = {
            "status_code": 400,
            "message": "Invalid reply token",
            "details": [
                {"message": "Reply token has expired", "property": "replyToken"}
            ],
        }

        result = self.analyzer.analyze(error_data)

        self.assertEqual(result.status_code, 400)
        self.assertEqual(result.category, ErrorCategory.INVALID_REPLY_TOKEN)
        self.assertEqual(result.severity, ErrorSeverity.HIGH)
        self.assertFalse(result.is_retryable)
        self.assertIsNotNone(result.details)
        self.assertEqual(len(result.details), 1)

    def test_analyze_dict_server_error(self):
        """サーバーエラーの分析テスト"""
        error_data = {"status_code": 500, "message": "Internal server error occurred"}

        result = self.analyzer.analyze(error_data)

        self.assertEqual(result.status_code, 500)
        self.assertEqual(result.category, ErrorCategory.SERVER_ERROR)
        self.assertEqual(result.severity, ErrorSeverity.HIGH)
        self.assertTrue(result.is_retryable)
        self.assertEqual(result.retry_after, 10)

    def test_analyze_v3_api_exception_mock(self):
        """v3系 ApiException のモック分析テスト"""
        mock_error = Mock()
        mock_error.__module__ = "linebot.v3.messaging.exceptions"
        mock_error.status = 404
        mock_error.reason = "Not Found"
        mock_error.body = '{"message": "User not found"}'
        mock_error.headers = [("X-Line-Request-Id", "test-id-001")]

        result = self.analyzer.analyze(mock_error)

        self.assertEqual(result.status_code, 404)
        self.assertEqual(result.category, ErrorCategory.USER_NOT_FOUND)
        self.assertEqual(result.message, "User not found")

    def test_analyze_v3_signature_error_mock(self):
        """v3系 InvalidSignatureError のモック分析テスト"""
        # InvalidSignatureErrorの専用分析を使わずに、
        # ApiExceptionとして分析されることをテストします
        mock_error = Mock()
        mock_error.__module__ = "linebot.v3.exceptions"
        mock_error.status = 400
        mock_error.headers = {}
        mock_error.body = '{"message": "Invalid signature"}'
        mock_error.reason = "Invalid signature"

        result = self.analyzer.analyze(mock_error)

        self.assertEqual(result.status_code, 400)
        self.assertEqual(result.category, ErrorCategory.INVALID_SIGNATURE)
        self.assertEqual(result.severity, ErrorSeverity.CRITICAL)
        self.assertFalse(result.is_retryable)

    def test_analyze_v2_linebot_api_error_mock(self):
        """v2系 LineBotApiError のモック分析テスト"""
        mock_error_obj = Mock()
        mock_error_obj.message = "Failed to send message"
        mock_error_obj.details = []

        mock_error = Mock()
        mock_error.__module__ = "linebot.exceptions"
        mock_error.status_code = 400
        mock_error.headers = {"X-Line-Request-Id": "test-id-002"}
        mock_error.request_id = "test-id-002"
        mock_error.accepted_request_id = None
        mock_error.error = mock_error_obj

        result = self.analyzer.analyze(mock_error)

        self.assertEqual(result.status_code, 400)
        self.assertEqual(result.message, "Failed to send message")
        self.assertEqual(result.request_id, "test-id-002")

    def test_analyze_response_like_object(self):
        """HTTPレスポンス類似オブジェクトの分析テスト"""
        mock_response = Mock()
        mock_response.status_code = 403
        mock_response.text = '{"message": "plan subscription required"}'
        mock_response.headers = {"Content-Type": "application/json"}

        result = self.analyzer.analyze(mock_response)

        self.assertEqual(result.status_code, 403)
        self.assertEqual(result.category, ErrorCategory.PLAN_LIMITATION)
        self.assertEqual(result.severity, ErrorSeverity.HIGH)
        self.assertFalse(result.is_retryable)

    def test_analyze_multiple_errors(self):
        """複数エラーの一括分析テスト"""
        errors = [
            {"status_code": 401, "message": "Invalid token"},
            {"status_code": 429, "message": "Rate limit exceeded"},
            {"status_code": 500, "message": "Server error"},
        ]

        results = self.analyzer.analyze_multiple(errors)

        self.assertEqual(len(results), 3)
        self.assertEqual(results[0].category, ErrorCategory.INVALID_TOKEN)
        self.assertEqual(results[1].category, ErrorCategory.RATE_LIMIT)
        self.assertEqual(results[2].category, ErrorCategory.SERVER_ERROR)

    def test_unsupported_error_type(self):
        """サポートされていないエラータイプのテスト"""
        unsupported_error = "string error"

        with self.assertRaises(AnalyzerError):
            self.analyzer.analyze(unsupported_error)

    def test_error_info_to_dict(self):
        """ErrorInfo の辞書変換テスト"""
        error_data = {"status_code": 400, "message": "Invalid parameter"}

        result = self.analyzer.analyze(error_data)
        result_dict = result.to_dict()

        self.assertIn("basic", result_dict)
        self.assertIn("analysis", result_dict)
        self.assertIn("guidance", result_dict)
        self.assertIn("raw_data", result_dict)

        self.assertEqual(result_dict["basic"]["status_code"], 400)
        self.assertEqual(result_dict["analysis"]["category"], result.category.value)

    def test_error_info_to_json(self):
        """ErrorInfo のJSON変換テスト"""
        error_data = {"status_code": 400, "message": "Invalid parameter"}

        result = self.analyzer.analyze(error_data)
        json_str = result.to_json()

        self.assertIsInstance(json_str, str)
        self.assertIn("basic", json_str)
        self.assertIn("analysis", json_str)
        self.assertIn("guidance", json_str)

    def test_error_info_str_representation(self):
        """ErrorInfo の文字列表現テスト"""
        error_data = {"status_code": 404, "message": "Not found"}

        result = self.analyzer.analyze(error_data)
        str_repr = str(result)

        self.assertIn("LineErrorInfo", str_repr)
        self.assertIn("Category", str_repr)
        self.assertIn("Severity", str_repr)
        self.assertIn("404", str_repr)


class TestErrorCategories(unittest.TestCase):
    """エラーカテゴリのテストクラス"""

    def setUp(self):
        self.analyzer = LineErrorAnalyzer()

    def test_all_major_categories_covered(self):
        """主要なエラーカテゴリが網羅されているかテスト"""
        test_cases = [
            # 認証関連
            (
                {"status_code": 401, "message": "invalid token"},
                ErrorCategory.INVALID_TOKEN,
            ),
            (
                {"status_code": 401, "message": "authentication failed"},
                ErrorCategory.AUTH_ERROR,
            ),
            (
                {"status_code": 400, "message": "invalid signature"},
                ErrorCategory.INVALID_SIGNATURE,
            ),
            # レート制限関連
            (
                {"status_code": 429, "message": "rate limit exceeded"},
                ErrorCategory.RATE_LIMIT,
            ),
            (
                {"status_code": 429, "message": "too many requests"},
                ErrorCategory.RATE_LIMIT,
            ),
            (
                {"status_code": 429, "message": "monthly limit"},
                ErrorCategory.QUOTA_EXCEEDED,
            ),
            # リクエスト関連
            (
                {"status_code": 400, "message": "invalid json"},
                ErrorCategory.INVALID_JSON,
            ),
            (
                {"status_code": 400, "message": "request body error"},
                ErrorCategory.INVALID_REQUEST_BODY,
            ),
            (
                {"status_code": 413, "message": "payload too large"},
                ErrorCategory.PAYLOAD_TOO_LARGE,
            ),
            # 返信トークン関連
            (
                {"status_code": 400, "message": "invalid reply token"},
                ErrorCategory.INVALID_REPLY_TOKEN,
            ),
            # ユーザー関連
            (
                {"status_code": 404, "message": "user not found"},
                ErrorCategory.USER_NOT_FOUND,
            ),
            (
                {"status_code": 404, "message": "not found"},
                ErrorCategory.RESOURCE_NOT_FOUND,
            ),
            # サーバー関連
            (
                {"status_code": 500, "message": "internal server error"},
                ErrorCategory.SERVER_ERROR,
            ),
            (
                {"status_code": 500, "message": "server error"},
                ErrorCategory.SERVER_ERROR,
            ),
        ]

        for error_data, expected_category in test_cases:
            with self.subTest(error_data=error_data):
                result = self.analyzer.analyze(error_data)
                self.assertEqual(
                    result.category,
                    expected_category,
                    f"Expected {expected_category} for {error_data}",
                )


if __name__ == "__main__":
    unittest.main(verbosity=2)
