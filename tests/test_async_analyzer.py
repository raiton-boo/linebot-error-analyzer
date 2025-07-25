"""
非同期 LINE Bot エラー分析器のテストケース
"""

import asyncio
import unittest
from unittest.mock import Mock, patch
from linebot_error_analyzer import AsyncLineErrorAnalyzer, ErrorCategory, ErrorSeverity
from linebot_error_analyzer.exceptions import AnalyzerError


class TestAsyncLineErrorAnalyzer(unittest.IsolatedAsyncioTestCase):
    """AsyncLineErrorAnalyzer のテストクラス"""

    async def asyncSetUp(self):
        """非同期テストセットアップ"""
        self.analyzer = AsyncLineErrorAnalyzer()

    async def test_analyze_dict_auth_error(self):
        """認証エラーの辞書形式非同期分析テスト"""
        error_data = {"status_code": 401, "message": "not authorized"}
        result = await self.analyzer.analyze(error_data)

        self.assertEqual(result.category, ErrorCategory.AUTH_ERROR)
        self.assertEqual(result.status_code, 401)
        self.assertEqual(result.severity, ErrorSeverity.CRITICAL)
        self.assertFalse(result.is_retryable)

    async def test_analyze_dict_rate_limit(self):
        """レート制限エラーの非同期分析テスト"""
        error_data = {
            "status_code": 429,
            "message": "Too many requests - rate limit exceeded",
        }

        result = await self.analyzer.analyze(error_data)

        self.assertEqual(result.status_code, 429)
        self.assertEqual(result.category, ErrorCategory.RATE_LIMIT)
        self.assertEqual(result.severity, ErrorSeverity.MEDIUM)
        self.assertTrue(result.is_retryable)
        self.assertEqual(result.retry_after, 60)
        self.assertIn("制限", result.description)

    async def test_analyze_dict_invalid_reply_token(self):
        """無効な返信トークンエラーの非同期分析テスト"""
        error_data = {
            "status_code": 400,
            "message": "Invalid reply token",
            "details": [
                {"message": "Reply token has expired", "property": "replyToken"}
            ],
        }

        result = await self.analyzer.analyze(error_data)

        self.assertEqual(result.status_code, 400)
        self.assertEqual(result.category, ErrorCategory.INVALID_REPLY_TOKEN)
        self.assertEqual(result.severity, ErrorSeverity.HIGH)
        self.assertFalse(result.is_retryable)
        self.assertIsNotNone(result.details)
        self.assertEqual(len(result.details), 1)

    async def test_analyze_dict_server_error(self):
        """サーバーエラーの非同期分析テスト"""
        error_data = {"status_code": 500, "message": "Internal server error occurred"}

        result = await self.analyzer.analyze(error_data)

        self.assertEqual(result.status_code, 500)
        self.assertEqual(result.category, ErrorCategory.SERVER_ERROR)
        self.assertEqual(result.severity, ErrorSeverity.HIGH)
        self.assertTrue(result.is_retryable)
        self.assertEqual(result.retry_after, 10)

    async def test_analyze_v3_api_exception_mock(self):
        """v3系 ApiException のモック非同期分析テスト"""
        mock_error = Mock()
        mock_error.__module__ = "linebot.v3.messaging.exceptions"
        mock_error.status = 404
        mock_error.reason = "Not Found"
        mock_error.body = '{"message": "User not found"}'
        mock_error.headers = [("X-Line-Request-Id", "test-id-001")]

        result = await self.analyzer.analyze(mock_error)

        self.assertEqual(result.status_code, 404)
        self.assertEqual(result.category, ErrorCategory.USER_NOT_FOUND)
        self.assertEqual(result.message, "User not found")

    async def test_analyze_v3_signature_error_mock(self):
        """v3系 InvalidSignatureError のモック非同期分析テスト"""
        mock_error = Mock()
        mock_error.__module__ = "linebot.v3.exceptions"
        mock_error.status = 400
        mock_error.headers = {}
        mock_error.body = '{"message": "Invalid signature"}'
        mock_error.reason = "Invalid signature"

        result = await self.analyzer.analyze(mock_error)

        self.assertEqual(result.status_code, 400)
        self.assertEqual(result.category, ErrorCategory.INVALID_SIGNATURE)
        self.assertEqual(result.severity, ErrorSeverity.CRITICAL)
        self.assertFalse(result.is_retryable)

    async def test_analyze_v2_linebot_api_error_mock(self):
        """v2系 LineBotApiError のモック非同期分析テスト"""
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

        result = await self.analyzer.analyze(mock_error)

        self.assertEqual(result.status_code, 400)
        self.assertEqual(result.message, "Failed to send message")
        self.assertEqual(result.request_id, "test-id-002")

    async def test_analyze_response_like_object(self):
        """HTTPレスポンス類似オブジェクトの非同期分析テスト"""
        mock_response = Mock()
        mock_response.status_code = 403
        mock_response.text = '{"message": "plan subscription required"}'
        mock_response.headers = {"Content-Type": "application/json"}

        result = await self.analyzer.analyze(mock_response)

        self.assertEqual(result.status_code, 403)
        self.assertEqual(result.category, ErrorCategory.PLAN_LIMITATION)
        self.assertEqual(result.severity, ErrorSeverity.HIGH)
        self.assertFalse(result.is_retryable)

    async def test_analyze_multiple_errors(self):
        """複数エラーの非同期一括分析テスト"""
        errors = [
            {"status_code": 401, "message": "Invalid token"},
            {"status_code": 429, "message": "Rate limit exceeded"},
            {"status_code": 500, "message": "Server error"},
        ]

        results = await self.analyzer.analyze_multiple(errors)

        self.assertEqual(len(results), 3)
        self.assertEqual(results[0].category, ErrorCategory.INVALID_TOKEN)
        self.assertEqual(results[1].category, ErrorCategory.RATE_LIMIT)
        self.assertEqual(results[2].category, ErrorCategory.SERVER_ERROR)

    async def test_analyze_batch_processing(self):
        """バッチ処理の非同期分析テスト"""
        errors = [
            {"status_code": 401, "message": "Invalid token"},
            {"status_code": 429, "message": "Rate limit exceeded"},
            {"status_code": 500, "message": "Server error"},
            {"status_code": 404, "message": "User not found"},
            {"status_code": 400, "message": "Invalid request"},
        ]

        # バッチサイズを2に設定してテスト
        results = await self.analyzer.analyze_batch(errors, batch_size=2)

        self.assertEqual(len(results), 5)
        self.assertEqual(results[0].category, ErrorCategory.INVALID_TOKEN)
        self.assertEqual(results[1].category, ErrorCategory.RATE_LIMIT)
        self.assertEqual(results[2].category, ErrorCategory.SERVER_ERROR)
        self.assertEqual(results[3].category, ErrorCategory.USER_NOT_FOUND)
        self.assertEqual(results[4].category, ErrorCategory.INVALID_PARAM)

    async def test_unsupported_error_type(self):
        """サポートされていないエラータイプの非同期テスト"""
        unsupported_error = "string error"

        with self.assertRaises(AnalyzerError):
            await self.analyzer.analyze(unsupported_error)

    async def test_concurrent_analysis(self):
        """並行分析のパフォーマンステスト"""
        errors = [
            {"status_code": 401, "message": "Invalid token"},
            {"status_code": 429, "message": "Rate limit exceeded"},
            {"status_code": 500, "message": "Server error"},
        ] * 10  # 30個のエラー

        # 並行実行時間を測定
        import time

        start_time = time.time()
        results = await self.analyzer.analyze_multiple(errors)
        end_time = time.time()

        # すべてのエラーが正しく分析されることを確認
        self.assertEqual(len(results), 30)

        # 並行処理により高速であることを確認（単純な目安）
        execution_time = end_time - start_time
        self.assertLess(execution_time, 1.0)  # 1秒以内

    async def test_error_handling_in_batch(self):
        """バッチ処理でのエラーハンドリングテスト"""
        errors = [
            {"status_code": 401, "message": "invalid token"},  # より具体的なメッセージ
            "invalid_error_type",  # 不正なエラータイプ
            {
                "status_code": 429,
                "message": "rate limit exceeded",
            },  # より具体的なメッセージ
        ]

        results = await self.analyzer.analyze_multiple(errors)

        self.assertEqual(len(results), 3)
        self.assertEqual(results[0].category, ErrorCategory.INVALID_TOKEN)
        # 不正なエラータイプはUNKNOWNとして処理される
        self.assertEqual(results[1].category, ErrorCategory.UNKNOWN)
        self.assertEqual(results[2].category, ErrorCategory.RATE_LIMIT)


class TestAsyncPerformance(unittest.IsolatedAsyncioTestCase):
    """非同期処理のパフォーマンステスト"""

    async def asyncSetUp(self):
        self.analyzer = AsyncLineErrorAnalyzer()

    async def test_large_batch_processing(self):
        """大量データのバッチ処理テスト"""
        # 100個のエラーを生成
        errors = []
        for i in range(100):
            errors.append(
                {
                    "status_code": 401 if i % 3 == 0 else 429 if i % 3 == 1 else 500,
                    "message": f"Error message {i}",
                }
            )

        import time

        start_time = time.time()
        results = await self.analyzer.analyze_batch(errors, batch_size=10)
        end_time = time.time()

        # すべてのエラーが処理されることを確認
        self.assertEqual(len(results), 100)

        # 処理時間が妥当であることを確認
        execution_time = end_time - start_time
        self.assertLess(execution_time, 5.0)  # 5秒以内


if __name__ == "__main__":
    unittest.main(verbosity=2)
