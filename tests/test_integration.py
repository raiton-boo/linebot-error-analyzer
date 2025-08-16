"""
統合テスト - 実際のLINE Bot SDK との組み合わせテスト
"""

import unittest
from unittest.mock import Mock, patch
import json
from linebot_error_analyzer import LineErrorAnalyzer, AsyncLineErrorAnalyzer
from linebot_error_analyzer.models import ErrorCategory


class TestLineSDKIntegration(unittest.TestCase):
    """LINE SDK統合テスト"""

    def setUp(self):
        self.analyzer = LineErrorAnalyzer()

    def test_v3_api_exception_integration(self):
        """v3 ApiException との統合テスト"""
        # v3 ApiException を模擬
        mock_exception = Mock()
        mock_exception.__module__ = "linebot.v3.messaging.exceptions"
        mock_exception.status = 400
        mock_exception.body = json.dumps(
            {
                "message": "Invalid request body",
                "details": [{"message": "May not be empty", "property": "messages"}],
            }
        )
        mock_exception.headers = {
            "X-Line-Request-Id": "test-request-123",
            "Content-Type": "application/json",
        }
        mock_exception.reason = "Bad Request"

        result = self.analyzer.analyze(mock_exception)

        # 結果の検証
        self.assertEqual(result.status_code, 400)
        self.assertEqual(result.message, "Invalid request body")
        self.assertEqual(result.category, ErrorCategory.INVALID_PARAM)
        # ErrorSeverity関連のアサーションは削除済み
        self.assertFalse(result.is_retryable)
        self.assertEqual(result.request_id, "test-request-123")
        self.assertEqual(len(result.details), 1)
        self.assertEqual(result.details[0]["property"], "messages")

    def test_v3_signature_error_integration(self):
        """v3 InvalidSignatureError との統合テスト"""
        mock_signature_error = Mock()
        mock_signature_error.__module__ = "linebot.v3.exceptions"
        mock_signature_error.__class__.__name__ = "InvalidSignatureError"
        mock_signature_error.__str__ = lambda self: "Invalid signature"
        # v3 ApiExceptionに必要な属性
        mock_signature_error.status = 400
        mock_signature_error.headers = {}
        mock_signature_error.reason = "Invalid signature"
        mock_signature_error.body = None

        result = self.analyzer.analyze(mock_signature_error)

        self.assertEqual(result.status_code, 400)
        self.assertEqual(result.category, ErrorCategory.INVALID_SIGNATURE)
        # ErrorSeverity関連のアサーションは削除済み
        self.assertFalse(result.is_retryable)

    def test_v2_linebot_api_error_integration(self):
        """v2 LineBotApiError との統合テスト"""
        # v2 LineBotApiError を模擬
        mock_error_obj = Mock()
        mock_error_obj.message = "The request body has 2 error(s)"
        mock_error_obj.details = [
            {"message": "May not be empty", "property": "replyToken"},
            {"message": "size must be between 1 and 5", "property": "messages"},
        ]

        mock_exception = Mock()
        mock_exception.__module__ = "linebot.exceptions"
        mock_exception.status_code = 400
        mock_exception.error = mock_error_obj
        mock_exception.headers = {}  # 空の辞書として設定
        mock_exception.request_id = "v2-request-456"
        mock_exception.accepted_request_id = None

        result = self.analyzer.analyze(mock_exception)

        self.assertEqual(result.status_code, 400)
        self.assertEqual(result.message, "The request body has 2 error(s)")
        self.assertEqual(result.category, ErrorCategory.INVALID_PARAM)
        self.assertEqual(result.request_id, "v2-request-456")
        self.assertEqual(len(result.details), 2)

    def test_v2_signature_error_integration(self):
        """v2 InvalidSignatureError との統合テスト"""
        mock_signature_error = Mock()
        mock_signature_error.__module__ = "linebot.exceptions"
        mock_signature_error.__class__.__name__ = "InvalidSignatureError"
        mock_signature_error.__str__ = lambda: "Invalid signature"
        # v2 LineBotApiErrorに必要な属性
        mock_signature_error.status_code = 400
        mock_signature_error.headers = {}
        mock_signature_error.request_id = "test-request-123"
        mock_signature_error.accepted_request_id = None
        mock_signature_error.error = Mock(message="Invalid signature", details=[])

        result = self.analyzer.analyze(mock_signature_error)

        self.assertEqual(result.status_code, 400)
        self.assertEqual(result.category, ErrorCategory.INVALID_SIGNATURE)
        # ErrorSeverity関連のアサーションは削除済み

    def test_http_response_integration(self):
        """HTTPレスポンスとの統合テスト"""
        # requests.Response を模擬
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.text = json.dumps(
            {"message": "Too Many Requests", "retryAfter": 3600}
        )
        mock_response.headers = {
            "X-Line-Request-Id": "rate-limit-789",
            "Retry-After": "3600",
        }

        result = self.analyzer.analyze(mock_response)

        self.assertEqual(result.status_code, 429)
        self.assertEqual(result.category, ErrorCategory.RATE_LIMIT)
        # ErrorSeverity関連のアサーションは削除済み
        self.assertTrue(result.is_retryable)
        # retry_afterは3600秒（Retry-Afterヘッダーから取得）
        self.assertEqual(result.retry_after, 3600)

    def test_mixed_error_types_batch(self):
        """異なるエラータイプの混合バッチテスト"""
        # 様々なタイプのエラーを混合
        errors = []

        # v3 ApiException
        v3_error = Mock()
        v3_error.__module__ = "linebot.v3.messaging.exceptions"
        v3_error.status = 401
        v3_error.body = '{"message": "Invalid channel access token"}'
        v3_error.headers = []
        errors.append(v3_error)

        # v2 LineBotApiError
        v2_error_obj = Mock()
        v2_error_obj.message = "Invalid reply token"
        v2_error_obj.details = []

        v2_error = Mock()
        v2_error.__module__ = "linebot.exceptions"
        v2_error.status_code = 400
        v2_error.error = v2_error_obj
        v2_error.headers = {}
        v2_error.request_id = None
        v2_error.accepted_request_id = None
        errors.append(v2_error)

        # 辞書形式エラー
        dict_error = {"status_code": 500, "message": "Internal server error"}
        errors.append(dict_error)

        # HTTPレスポンス
        response_error = Mock()
        response_error.status_code = 503
        response_error.text = '{"message": "Service temporarily unavailable"}'
        response_error.headers = {}
        errors.append(response_error)

        results = self.analyzer.analyze_multiple(errors)

        # 結果の検証
        self.assertEqual(len(results), 4)

        # v3エラーの検証
        self.assertEqual(results[0].status_code, 401)
        self.assertEqual(results[0].category, ErrorCategory.AUTH_ERROR)

        # v2エラーの検証（Invalid reply tokenは INVALID_REPLY_TOKEN カテゴリ）
        self.assertEqual(results[1].status_code, 400)
        self.assertEqual(results[1].category, ErrorCategory.INVALID_REPLY_TOKEN)

        # 辞書エラーの検証
        self.assertEqual(results[2].status_code, 500)
        self.assertEqual(results[2].category, ErrorCategory.SERVER_ERROR)

        # レスポンスエラーの検証
        self.assertEqual(results[3].status_code, 503)
        self.assertEqual(results[3].category, ErrorCategory.SERVER_ERROR)


class TestAsyncSDKIntegration(unittest.IsolatedAsyncioTestCase):
    """非同期SDK統合テスト"""

    async def asyncSetUp(self):
        self.analyzer = AsyncLineErrorAnalyzer()

    async def test_async_mixed_errors_processing(self):
        """非同期での混合エラー処理テスト"""
        # 大量の異なるタイプのエラーを生成
        errors = []

        # 各タイプのエラーを1000個ずつ作成
        for i in range(1000):
            # v3 ApiException タイプ
            v3_error = Mock()
            v3_error.__module__ = "linebot.v3.messaging.exceptions"
            v3_error.status = 400 + (i % 100)
            v3_error.body = f'{{"message": "v3 error {i}"}}'
            v3_error.headers = []
            errors.append(v3_error)

            # 辞書タイプ
            dict_error = {"status_code": 500 + (i % 100), "message": f"Dict error {i}"}
            errors.append(dict_error)

        # 非同期バッチ処理
        results = await self.analyzer.analyze_batch(errors, batch_size=100)

        # 結果の検証
        self.assertEqual(len(results), 2000)

        # v3エラーの検証（偶数インデックス）
        for i in range(0, 2000, 2):
            result = results[i]
            expected_status = 400 + ((i // 2) % 100)
            self.assertEqual(result.status_code, expected_status)

        # 辞書エラーの検証（奇数インデックス）
        for i in range(1, 2000, 2):
            result = results[i]
            expected_status = 500 + ((i // 2) % 100)
            self.assertEqual(result.status_code, expected_status)

    async def test_concurrent_analyzer_instances(self):
        """複数の分析器インスタンスの並行実行テスト"""
        import asyncio

        async def analyze_with_instance(instance_id):
            """個別インスタンスでの分析"""
            local_analyzer = AsyncLineErrorAnalyzer()
            errors = [
                {"status_code": 400, "message": f"Instance {instance_id} error {i}"}
                for i in range(100)
            ]
            results = await local_analyzer.analyze_multiple(errors)
            return instance_id, len(results)

        # 10個のインスタンスを並行実行
        tasks = [analyze_with_instance(i) for i in range(10)]
        results = await asyncio.gather(*tasks)

        # 結果の検証
        self.assertEqual(len(results), 10)
        for instance_id, count in results:
            self.assertEqual(count, 100)


class TestRealWorldScenarios(unittest.TestCase):
    """実世界シナリオテスト"""

    def setUp(self):
        self.analyzer = LineErrorAnalyzer()

    def test_webhook_error_scenario(self):
        """Webhookエラーシナリオテスト"""
        # Webhook処理中に発生する典型的なエラー
        webhook_errors = [
            # 無効な署名
            Mock(
                __module__="linebot.v3.exceptions",
                __class__=Mock(
                    __name__="InvalidSignatureError",
                    __module__="linebot.v3.exceptions",
                ),
            ),
            # 無効なリプライトークン
            {
                "status_code": 400,
                "message": "Invalid reply token",
                "details": [{"property": "replyToken", "message": "Invalid format"}],
            },
            # メッセージサイズ超過
            {
                "status_code": 413,
                "message": "Request entity too large",
                "details": [{"property": "messages", "message": "Size exceeds limit"}],
            },
            # レート制限
            Mock(
                status_code=429,
                text='{"message": "Rate limit exceeded"}',
                headers={"Retry-After": "300"},
            ),
            # サーバーエラー
            {"status_code": 500, "message": "Internal server error"},
        ]

        results = self.analyzer.analyze_multiple(webhook_errors)

        # 各エラーの適切な処理を確認
        self.assertEqual(len(results), 5)

        # 署名エラー
        self.assertEqual(results[0].category, ErrorCategory.INVALID_SIGNATURE)
        self.assertFalse(results[0].is_retryable)

        # パラメータエラー
        self.assertEqual(results[1].category, ErrorCategory.INVALID_REPLY_TOKEN)
        self.assertFalse(results[1].is_retryable)

        # ペイロードサイズエラー
        self.assertEqual(results[2].status_code, 413)
        self.assertFalse(results[2].is_retryable)

        # レート制限エラー
        self.assertEqual(results[3].category, ErrorCategory.RATE_LIMIT)
        self.assertTrue(results[3].is_retryable)

        # サーバーエラー
        self.assertEqual(results[4].category, ErrorCategory.SERVER_ERROR)
        self.assertTrue(results[4].is_retryable)

    def test_bot_development_workflow(self):
        """Bot開発ワークフローテスト"""
        # 開発中によく遭遇するエラーの組み合わせ
        development_errors = []

        # 設定ミス系エラー
        config_errors = [
            {"status_code": 401, "message": "Invalid channel access token"},
            {"status_code": 401, "message": "Invalid channel secret"},
            {"status_code": 403, "message": "Insufficient permissions"},
        ]
        development_errors.extend(config_errors)

        # 実装ミス系エラー
        implementation_errors = [
            {"status_code": 400, "message": "Invalid JSON format"},
            {"status_code": 400, "message": "Required field missing: replyToken"},
            {"status_code": 400, "message": "Invalid message type"},
        ]
        development_errors.extend(implementation_errors)

        # 環境/インフラ系エラー
        infrastructure_errors = [
            {"status_code": 503, "message": "Service unavailable"},
            {"status_code": 504, "message": "Gateway timeout"},
            {"status_code": 500, "message": "Internal server error"},
        ]
        development_errors.extend(infrastructure_errors)

        results = self.analyzer.analyze_multiple(development_errors)

        # カテゴリ別の分析
        auth_errors = [r for r in results if r.category == ErrorCategory.AUTH_ERROR]
        param_errors = [r for r in results if r.category == ErrorCategory.INVALID_PARAM]
        server_errors = [r for r in results if r.category == ErrorCategory.SERVER_ERROR]
        access_denied_errors = [
            r for r in results if r.category == ErrorCategory.ACCESS_DENIED
        ]
        timeout_errors = [
            r for r in results if r.category == ErrorCategory.TIMEOUT_ERROR
        ]
        json_errors = [r for r in results if r.category == ErrorCategory.INVALID_JSON]

        # カテゴリ別エラー数の確認
        self.assertEqual(len(auth_errors), 2)  # 認証関連エラー (401x2)
        self.assertEqual(len(param_errors), 1)  # パラメータエラー (replyToken missing)
        self.assertEqual(len(json_errors), 2)  # JSONエラー (format, message type)
        self.assertEqual(len(server_errors), 2)  # サーバーエラー (500, 503)
        self.assertEqual(len(access_denied_errors), 1)  # アクセス拒否エラー (403)
        self.assertEqual(len(timeout_errors), 1)  # タイムアウトエラー (504)

        # 合計エラー数の確認
        total_errors = (
            len(auth_errors)
            + len(param_errors)
            + len(json_errors)
            + len(server_errors)
            + len(access_denied_errors)
            + len(timeout_errors)
        )
        self.assertEqual(total_errors, 9)

        # 重要度の確認
        # ErrorSeverity関連のアサーションは削除済み
        # ErrorSeverity関連のアサーションは削除済み

        self.assertGreater(len(critical_errors), 0)  # 致命的エラーが存在
        self.assertGreater(len(high_errors), 0)  # 高重要度エラーが存在

        # リトライ可能性の確認
        retryable_errors = [r for r in results if r.is_retryable]
        non_retryable_errors = [r for r in results if not r.is_retryable]

        self.assertGreater(len(retryable_errors), 0)
        self.assertGreater(len(non_retryable_errors), 0)

    def test_monitoring_and_alerting_scenario(self):
        """監視・アラートシナリオテスト"""
        # 監視システムが検知すべきエラーパターン
        monitoring_errors = []

        # 高頻度エラー（アラート対象）
        for i in range(100):
            monitoring_errors.append(
                {
                    "status_code": 401,
                    "message": "Authentication failed",
                    "timestamp": f"2024-01-01T{10 + i//10:02d}:00:00Z",
                }
            )

        # 重要なエラー（即座にアラート）
        critical_errors = [
            {"status_code": 500, "message": "Database connection failed"},
            {"status_code": 503, "message": "All instances down"},
            {"status_code": 429, "message": "Rate limit exceeded for premium account"},
        ]
        monitoring_errors.extend(critical_errors)

        results = self.analyzer.analyze_multiple(monitoring_errors)

        # アラート対象の分析
        auth_failures = [r for r in results if r.category == ErrorCategory.AUTH_ERROR]
        server_errors = [r for r in results if r.category == ErrorCategory.SERVER_ERROR]
        rate_limits = [r for r in results if r.category == ErrorCategory.RATE_LIMIT]

        # 高頻度認証エラー
        self.assertEqual(len(auth_failures), 100)

        # 重要なサーバーエラー
        self.assertEqual(len(server_errors), 2)

        # レート制限
        self.assertEqual(len(rate_limits), 1)

        # アラート優先度の評価
        immediate_alerts = [
            r
            for r in results
            # ErrorSeverity関連のアサーションは削除済み
            and r.category in [ErrorCategory.SERVER_ERROR, ErrorCategory.RATE_LIMIT]
        ]

        self.assertGreater(len(immediate_alerts), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
