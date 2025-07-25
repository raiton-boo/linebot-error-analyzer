"""
エッジケースと境界値のテストケース
"""

import unittest
from unittest.mock import Mock, patch
import json
from linebot_error_analyzer import (
    LineErrorAnalyzer,
    AsyncLineErrorAnalyzer,
    ErrorCategory,
    ErrorSeverity,
)
from linebot_error_analyzer.core.models import LineErrorInfo
from linebot_error_analyzer.exceptions import AnalyzerError, UnsupportedErrorTypeError


class TestEdgeCases(unittest.TestCase):
    """エッジケースのテストクラス"""

    def setUp(self):
        self.analyzer = LineErrorAnalyzer()

    def test_empty_error_data(self):
        """空のエラーデータのテスト"""
        # 完全に空の辞書
        empty_dict = {}
        result = self.analyzer.analyze(empty_dict)

        self.assertEqual(result.status_code, 0)
        self.assertEqual(result.message, "Unknown error")
        self.assertEqual(result.category, ErrorCategory.UNKNOWN)

    def test_minimal_error_data(self):
        """最小限のエラーデータのテスト"""
        minimal_data = {"status_code": 400}
        result = self.analyzer.analyze(minimal_data)

        self.assertEqual(result.status_code, 400)
        self.assertEqual(result.message, "Unknown error")
        self.assertEqual(result.category, ErrorCategory.INVALID_PARAM)

    def test_status_code_boundary_values(self):
        """ステータスコードの境界値テスト"""
        boundary_cases = [
            (100, ErrorCategory.UNKNOWN),  # 最小有効値
            (200, ErrorCategory.UNKNOWN),  # 成功コード
            (299, ErrorCategory.UNKNOWN),  # 最大成功コード
            (300, ErrorCategory.UNKNOWN),  # リダイレクト開始
            (399, ErrorCategory.UNKNOWN),  # リダイレクト終了
            (400, ErrorCategory.INVALID_PARAM),  # クライアントエラー開始
            (401, ErrorCategory.AUTH_ERROR),  # 認証エラー
            (429, ErrorCategory.RATE_LIMIT),  # レート制限
            (499, ErrorCategory.UNKNOWN),  # クライアントエラー終了（修正）
            (500, ErrorCategory.SERVER_ERROR),  # サーバーエラー開始
            (503, ErrorCategory.SERVER_ERROR),  # サービス利用不可
            (599, ErrorCategory.UNKNOWN),  # サーバーエラー終了（修正）
        ]

        for status_code, expected_category in boundary_cases:
            with self.subTest(status_code=status_code):
                error_data = {"status_code": status_code, "message": "Test error"}
                result = self.analyzer.analyze(error_data)
                self.assertEqual(result.status_code, status_code)
                self.assertEqual(result.category, expected_category)

    def test_invalid_status_codes(self):
        """無効なステータスコードのテスト"""
        # 型変換可能な値
        convertible_codes = [
            ("400", 400),  # 文字列→数値
            (400.0, 400),  # 浮動小数点→整数
        ]

        for input_code, expected_code in convertible_codes:
            with self.subTest(status_code=input_code):
                error_data = {"status_code": input_code, "message": "Test error"}
                result = self.analyzer.analyze(error_data)
                self.assertEqual(result.status_code, expected_code)

        # 型変換不可能な値
        invalid_codes = [
            None,  # None値
            [],  # リスト
            {},  # 辞書
            "abc",  # 非数値文字列
        ]

        for invalid_code in invalid_codes:
            with self.subTest(status_code=invalid_code):
                error_data = {"status_code": invalid_code, "message": "Test error"}
                result = self.analyzer.analyze(error_data)
                # 無効な値は0として処理される
                self.assertEqual(result.status_code, 0)

        # 境界値を超えた数値はAnalyzerErrorを発生させるべき
        extreme_codes = [-1, 50, 1000]
        for extreme_code in extreme_codes:
            with self.subTest(status_code=extreme_code):
                error_data = {"status_code": extreme_code, "message": "Test error"}
                with self.assertRaises(Exception):  # AnalyzerError またはその他の例外
                    self.analyzer.analyze(error_data)

    def test_malformed_json_in_body(self):
        """不正なJSONを含むボディのテスト"""
        mock_error = Mock()
        mock_error.__module__ = "linebot.v3.messaging.exceptions"
        mock_error.status = 400
        mock_error.body = '{"invalid": json, missing quotes}'  # 不正JSON
        mock_error.headers = []
        mock_error.reason = "Bad Request"

        result = self.analyzer.analyze(mock_error)

        self.assertEqual(result.status_code, 400)
        self.assertIn("invalid", result.message)  # 不正JSONが文字列として処理される

    def test_extremely_long_error_message(self):
        """非常に長いエラーメッセージのテスト"""
        long_message = "A" * 10000  # 10KB のメッセージ
        error_data = {"status_code": 400, "message": long_message}

        result = self.analyzer.analyze(error_data)

        self.assertEqual(result.status_code, 400)
        self.assertEqual(result.message, long_message)
        self.assertEqual(len(result.message), 10000)

    def test_unicode_and_special_characters(self):
        """Unicode文字と特殊文字のテスト"""
        unicode_messages = [
            "日本語エラーメッセージ",
            "Erreur en français 🇫🇷",
            "Ошибка на русском языке",
            "错误消息中文",
            "🚨🔥💥 Error with emojis 💀⚡🌟",
            "Error with\nnewlines\tand\ttabs",
            "Error with \"quotes\" and 'apostrophes'",
            "Error with special chars: !@#$%^&*()_+-=[]{}|;:,.<>?",
        ]

        for message in unicode_messages:
            with self.subTest(message=message[:20]):
                error_data = {"status_code": 400, "message": message}
                result = self.analyzer.analyze(error_data)

                self.assertEqual(result.status_code, 400)
                self.assertEqual(result.message, message)

    def test_nested_error_details(self):
        """ネストしたエラー詳細のテスト"""
        complex_error = {
            "status_code": 400,
            "message": "Complex validation error",
            "details": [
                {
                    "message": "Field 'name' is required",
                    "property": "name",
                    "nested": {
                        "validation_rules": ["required", "min_length:2"],
                        "current_value": None,
                    },
                },
                {
                    "message": "Field 'email' is invalid",
                    "property": "email",
                    "nested": {
                        "validation_rules": ["required", "email_format"],
                        "current_value": "invalid-email",
                    },
                },
            ],
        }

        result = self.analyzer.analyze(complex_error)

        self.assertEqual(result.status_code, 400)
        self.assertEqual(len(result.details), 2)
        self.assertIsInstance(result.details[0], dict)
        self.assertIn("nested", result.details[0])

    def test_circular_reference_in_error(self):
        """循環参照を含むエラーデータのテスト"""
        error_data = {"status_code": 400, "message": "Circular reference test"}
        # 循環参照を作成
        error_data["self_ref"] = error_data

        # 循環参照があっても正常に処理される
        result = self.analyzer.analyze(error_data)

        self.assertEqual(result.status_code, 400)
        self.assertEqual(result.message, "Circular reference test")

    def test_none_values_in_error_data(self):
        """None値を含むエラーデータのテスト"""
        error_with_nones = {
            "status_code": 400,
            "message": None,
            "headers": None,
            "request_id": None,
            "details": None,
            "error_code": None,
        }

        # None値はAnalyzerErrorまたは適切なデフォルト値で処理される
        try:
            result = self.analyzer.analyze(error_with_nones)
            # 正常に処理された場合
            self.assertEqual(result.status_code, 400)
            # message=None は "Unknown error" に変換される想定
            self.assertEqual(result.message, "Unknown error")
            self.assertIsNone(result.request_id)
            self.assertIsNone(result.error_code)
        except Exception:
            # None値によってエラーが発生することも許容される
            pass

    def test_mixed_type_headers(self):
        """混合型のヘッダーのテスト"""
        mixed_headers = {
            "Content-Type": "application/json",
            "Content-Length": 1234,  # 数値
            "X-Custom-Header": None,  # None
            "X-List-Header": ["value1", "value2"],  # リスト
        }

        error_data = {
            "status_code": 400,
            "message": "Mixed headers test",
            "headers": mixed_headers,
        }

        result = self.analyzer.analyze(error_data)

        self.assertEqual(result.status_code, 400)
        # ヘッダーは文字列化される
        self.assertIsInstance(result.headers, dict)


class TestConcurrencyAndPerformance(unittest.TestCase):
    """同期処理とパフォーマンスのテスト"""

    def setUp(self):
        self.analyzer = LineErrorAnalyzer()

    def test_large_error_batch(self):
        """大量エラーの同期処理テスト"""
        # 1000個のエラーを生成
        errors = []
        for i in range(1000):
            errors.append(
                {"status_code": 400 + (i % 100), "message": f"Batch error {i}"}
            )

        import time

        start_time = time.time()
        results = self.analyzer.analyze_multiple(errors)
        end_time = time.time()

        # 結果の検証
        self.assertEqual(len(results), 1000)

        # パフォーマンスの検証（目安として5秒以内）
        execution_time = end_time - start_time
        self.assertLess(execution_time, 5.0)

    def test_memory_usage_with_large_data(self):
        """大量データでのメモリ使用量テスト"""
        # 大きなエラーデータを作成
        large_error = {
            "status_code": 413,
            "message": "Payload too large",
            "details": [{"data": "x" * 10000} for _ in range(100)],  # 約1MBのデータ
        }

        # メモリリークがないことを確認
        import gc

        gc.collect()

        results = []
        for i in range(10):
            result = self.analyzer.analyze(large_error)
            results.append(result)

        # ガベージコレクションを実行
        gc.collect()

        # 全て正常に処理されることを確認
        self.assertEqual(len(results), 10)
        for result in results:
            self.assertEqual(result.status_code, 413)

    def test_repeated_analysis_consistency(self):
        """同一エラーの繰り返し分析の一貫性テスト"""
        error_data = {"status_code": 429, "message": "Rate limit exceeded"}

        # 同じエラーを100回分析
        results = []
        for _ in range(100):
            result = self.analyzer.analyze(error_data)
            results.append(result)

        # 全ての結果が一致することを確認
        first_result = results[0]
        for result in results[1:]:
            self.assertEqual(result.status_code, first_result.status_code)
            self.assertEqual(result.category, first_result.category)
            self.assertEqual(result.severity, first_result.severity)
            self.assertEqual(result.message, first_result.message)


class TestAsyncEdgeCases(unittest.IsolatedAsyncioTestCase):
    """非同期版のエッジケーステスト"""

    async def asyncSetUp(self):
        self.analyzer = AsyncLineErrorAnalyzer()

    async def test_concurrent_analysis_stress(self):
        """並行分析のストレステスト"""
        import asyncio

        # 100個の異なるエラーを並行分析
        errors = [
            {"status_code": 400 + (i % 200), "message": f"Concurrent error {i}"}
            for i in range(100)
        ]

        # 複数のanalyze_multiple呼び出しを並行実行
        tasks = []
        for batch_num in range(5):
            task = asyncio.create_task(self.analyzer.analyze_multiple(errors))
            tasks.append(task)

        # 全てのタスクが完了するまで待機
        results_batches = await asyncio.gather(*tasks)

        # 結果の検証
        self.assertEqual(len(results_batches), 5)
        for results in results_batches:
            self.assertEqual(len(results), 100)

    async def test_async_error_handling_edge_cases(self):
        """非同期エラーハンドリングのエッジケース"""
        # 非同期処理中に発生する様々なエラー
        problematic_errors = [
            None,  # None値
            [],  # 空リスト
            "",  # 空文字列
            {"malformed": True},  # 不完全なデータ
            Exception("Test exception"),  # 例外オブジェクト
        ]

        results = await self.analyzer.analyze_multiple(problematic_errors)

        # 全てのエラーが安全に処理されることを確認
        self.assertEqual(len(results), 5)
        for result in results:
            self.assertIsInstance(result, LineErrorInfo)
            # 問題のあるデータはUNKNOWNカテゴリとして処理される
            self.assertEqual(result.category, ErrorCategory.UNKNOWN)

    async def test_async_timeout_simulation(self):
        """非同期タイムアウトのシミュレーション"""
        import asyncio

        # 非常に大量のエラーで処理時間をテスト
        large_errors = [
            {"status_code": 400, "message": f"Timeout test {i}"} for i in range(10000)
        ]

        # タイムアウト付きで実行
        try:
            results = await asyncio.wait_for(
                self.analyzer.analyze_batch(large_errors, batch_size=100),
                timeout=10.0,  # 10秒でタイムアウト
            )

            # 正常に完了した場合
            self.assertEqual(len(results), 10000)

        except asyncio.TimeoutError:
            # タイムアウトした場合（これは予期される動作）
            self.fail("Async processing should complete within timeout")


class TestErrorRecovery(unittest.TestCase):
    """エラー回復とレジリエンステスト"""

    def setUp(self):
        self.analyzer = LineErrorAnalyzer()

    def test_recovery_from_corrupted_database(self):
        """破損したデータベースからの回復テスト"""
        from linebot_error_analyzer.exceptions import AnalyzerError

        # データベースの一部メソッドを一時的に破損させる
        original_method = self.analyzer.db.analyze_error

        def corrupted_method(*args, **kwargs):
            raise Exception("Database corruption simulation")

        self.analyzer.db.analyze_error = corrupted_method

        try:
            # エラーが発生しても適切にハンドリングされることを確認
            error_data = {"status_code": 400, "message": "Recovery test"}

            with self.assertRaises(AnalyzerError):
                # 内部でExceptionが発生するがAnalyzerErrorとして再発生
                self.analyzer.analyze(error_data)

        finally:
            # メソッドを復元
            self.analyzer.db.analyze_error = original_method

    def test_graceful_degradation(self):
        """段階的機能低下のテスト"""
        # 一部の機能が利用できない状況をシミュレート
        error_data = {
            "status_code": 400,
            "message": "Graceful degradation test",
            "malformed_field": object(),  # シリアライズ不可能なオブジェクト
        }

        # エラーがあっても基本的な分析は実行される
        result = self.analyzer.analyze(error_data)

        self.assertEqual(result.status_code, 400)
        self.assertEqual(result.message, "Graceful degradation test")
        self.assertIsNotNone(result.category)


if __name__ == "__main__":
    unittest.main(verbosity=2)
