#!/usr/bin/env python3
"""エッジケースのテストケース"""

import unittest
import sys
import os

# プロジェクトのルートをPATHに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from linebot_error_analyzer import LineErrorAnalyzer, AsyncLineErrorAnalyzer
from linebot_error_analyzer.models import ApiPattern, ErrorCategory
from linebot_error_analyzer.exceptions import AnalyzerError


class TestEdgeCases(unittest.TestCase):
    """エッジケースのテスト"""

    def setUp(self):
        """テストセットアップ"""
        self.analyzer = LineErrorAnalyzer()

    def test_boundary_status_codes(self):
        """境界値のステータスコードテスト"""
        boundary_cases = [
            (100, "Informational"),
            (200, "OK"),
            (300, "Redirection"),
            (400, "Bad Request"),
            (500, "Internal Server Error"),
            (599, "Server Error"),
        ]

        for status_code, message in boundary_cases:
            with self.subTest(status=status_code):
                log = f"({status_code}) {message}"
                result = self.analyzer.analyze(log)
                self.assertEqual(result.status_code, status_code)
                # カテゴリは実装依存
                self.assertIsNotNone(result.category)

    def test_unicode_and_special_characters(self):
        """Unicode文字と特殊文字の処理"""
        special_messages = [
            ("日本語エラーメッセージ", "400"),
            ("🚫 Emoji error 🚫", "404"),
            ("Special chars: !@#$%^&*()", "500"),
            ("Mixed: English日本語🚫", "400"),
        ]

        for message, status_code in special_messages:
            with self.subTest(message=message):
                log = f"({status_code}) {message}"
                result = self.analyzer.analyze(log)
                self.assertIsNotNone(result)
                self.assertEqual(result.status_code, int(status_code))

    def test_extremely_long_inputs(self):
        """非常に長い入力の処理"""
        # 1MB の巨大な文字列
        huge_message = "A" * (1024 * 1024)

        # パフォーマンステスト：1秒以内に完了
        import time

        start_time = time.time()
        log = f"(500) {huge_message}"
        result = self.analyzer.analyze(log)
        end_time = time.time()

        self.assertLess(end_time - start_time, 1.0)
        self.assertEqual(result.status_code, 500)
        self.assertIsNotNone(result.category)

    def test_nested_json_structures(self):
        """ネストしたJSON構造の処理"""
        complex_json = """{
            "error": {
                "code": "INVALID_REQUEST",
                "message": "The request is invalid",
                "details": [
                    {
                        "field": "messages[0].text",
                        "message": "May not be empty"
                    },
                    {
                        "field": "messages[0].quickReply",
                        "message": "Invalid structure"
                    }
                ],
                "metadata": {
                    "timestamp": "2025-08-16T12:34:56Z",
                    "requestId": "req-12345"
                }
            }
        }"""

        log = f"(400) {complex_json}"
        result = self.analyzer.analyze(log)
        self.assertIsNotNone(result.category)

    def test_malformed_log_formats(self):
        """不正な形式のログの処理"""
        malformed_logs = [
            "",  # 空文字列
            "   ",  # 空白のみ
            "404",  # 数字のみ
            "(404",  # 括弧未閉じ
            "404)",  # 括弧開始なし
            "((404))",  # 二重括弧
            "HTTP Error without status",  # ステータスなし
            "Status: 404 but no message",  # メッセージなし
            "Multiple (404) status (500) codes",  # 複数ステータス
            "Invalid JSON: {message: }",  # 不正JSON
        ]

        for malformed_log in malformed_logs:
            with self.subTest(log=repr(malformed_log)):
                try:
                    result = self.analyzer.analyze(malformed_log)
                    # エラーが起きなければ適切な結果が返る
                    self.assertIsNotNone(result)
                    self.assertIsNotNone(result.category)
                except Exception as e:
                    # 適切なエラーハンドリング
                    self.assertIsInstance(e, (ValueError, TypeError, AnalyzerError))

    def test_api_pattern_edge_cases(self):
        """APIパターンのエッジケース"""
        # 存在しないパターンに類似したログを渡す
        try:
            log = "(404) Test NON_EXISTENT_PATTERN error"
            result = self.analyzer.analyze(log)
            self.assertIsNotNone(result)
        except (ValueError, AttributeError):
            # 適切なエラー処理
            pass

    def test_concurrent_different_patterns(self):
        """異なるパターンでのログ同時解析"""
        import threading
        import time

        results = {}
        errors = []

        def analyze_with_pattern(pattern_name, log_content):
            try:
                result = self.analyzer.analyze(log_content)
                results[pattern_name] = result
            except Exception as e:
                errors.append((pattern_name, e))

        # 複数パターンで同時実行
        test_logs = [
            ("USER_PROFILE", "(400) User profile fetch failed"),
            ("MESSAGE_PUSH", "(429) Message push rate limit exceeded"),
            ("RICH_MENU", "(500) Rich menu creation failed"),
        ]

        threads = []
        for name, log in test_logs:
            thread = threading.Thread(target=analyze_with_pattern, args=(name, log))
            threads.append(thread)

        # 全スレッド開始
        for thread in threads:
            thread.start()

        # 全スレッド完了待ち
        for thread in threads:
            thread.join(timeout=5.0)

        # エラーがないことを確認
        self.assertEqual(len(errors), 0, f"Concurrent errors: {errors}")
        self.assertEqual(len(results), 3)

    def test_memory_leak_prevention(self):
        """メモリリーク防止テスト"""
        import gc
        import sys

        # 初期メモリ参照数
        initial_refs = len(gc.get_objects())

        # 大量の解析を実行
        for i in range(100):
            log = f"(404) Memory test {i}"
            result = self.analyzer.analyze(log)
            # 結果を即座に削除
            del result

        # 強制ガベージコレクション
        gc.collect()

        # メモリ参照数が大幅に増加していないことを確認
        final_refs = len(gc.get_objects())
        ref_increase = final_refs - initial_refs

        # 参照数の増加が許容範囲内（100個未満）
        self.assertLess(
            ref_increase, 100, f"Memory leak suspected: {ref_increase} new references"
        )

    def test_error_message_encoding(self):
        """エラーメッセージのエンコーディングテスト"""
        encodings = [
            "UTF-8でのエラーメッセージ",
            b"\xe3\x82\xa8\xe3\x83\xa9\xe3\x83\xbc".decode("utf-8"),  # UTF-8バイト
            "ASCII compatible message",
        ]

        for message in encodings:
            with self.subTest(encoding=type(message).__name__):
                log = f"(400) {message}"
                result = self.analyzer.analyze(log)
                self.assertIsInstance(result.description, str)
                self.assertTrue(len(result.description) > 0)

    def test_floating_point_status_codes(self):
        """浮動小数点ステータスコードのログ"""
        float_codes = [400.0, 404.5, 500.9]

        for code in float_codes:
            with self.subTest(code=code):
                # ログ文字列に浮動小数点が含まれている場合
                log = f"({code}) Float test"
                try:
                    result = self.analyzer.analyze(log)
                    # パースできれば成功
                    self.assertIsNotNone(result)
                except (ValueError, TypeError):
                    # エラーハンドリングも許容
                    pass


if __name__ == "__main__":
    unittest.main()
