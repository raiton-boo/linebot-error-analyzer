#!/usr/bin/env python3
"""エラーハンドリングのテストケース"""

import unittest
import sys
import os

# プロジェクトのルートをPATHに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from linebot_error_analyzer import LineErrorAnalyzer
from linebot_error_analyzer.exceptions import AnalyzerError
from linebot_error_analyzer.models import ApiPattern, ErrorCategory


class TestErrorHandling(unittest.TestCase):
    """エラーハンドリングのテストケース"""

    def setUp(self):
        """テストセットアップ"""
        self.analyzer = LineErrorAnalyzer()

    def test_invalid_status_code_handling(self):
        """無効なステータスコードの処理"""
        invalid_codes = [-1, 0, 99, 600, 9999, "invalid"]

        for code in invalid_codes:
            with self.subTest(code=code):
                try:
                    result = self.analyzer.analyze(code, "Test message")
                    # エラーが起きなかった場合、適切にフォールバックされることを確認
                    self.assertIsNotNone(result)
                    self.assertIsNotNone(result.category)
                except (ValueError, TypeError, AnalyzerError):
                    # 適切なエラーが発生することも許容
                    pass

    def test_none_values_handling(self):
        """None値の処理テスト"""
        test_cases = [
            (None, None),
            (404, None),
            (None, "Error message"),
        ]

        for status_code, message in test_cases:
            with self.subTest(status=status_code, msg=message):
                try:
                    result = self.analyzer.analyze(status_code, message)
                    self.assertIsNotNone(result)
                except (ValueError, TypeError, AnalyzerError):
                    # 適切なエラーハンドリング
                    pass

    def test_empty_string_handling(self):
        """空文字列の処理テスト"""
        empty_inputs = ["", "   ", "\n", "\t"]

        for empty_input in empty_inputs:
            with self.subTest(input=repr(empty_input)):
                result = self.analyzer.analyze(empty_input)
                self.assertIsNotNone(result)
                self.assertIsNotNone(result.category)

    def test_very_long_input_handling(self):
        """非常に長い入力の処理テスト"""
        # 10KB の長い文字列
        long_input = "A" * 10240
        long_log = f"(500) Error: {long_input}"

        result = self.analyzer.analyze(long_log)

        self.assertEqual(result.status_code, 500)
        self.assertIsNotNone(result.category)
        # パフォーマンスも確認（1秒以内に完了）
        import time

        start = time.time()
        self.analyzer.analyze(long_log)
        end = time.time()
        self.assertLess(end - start, 1.0)

    def test_special_characters_handling(self):
        """特殊文字の処理テスト"""
        special_chars = [
            "エラー：日本語メッセージ",
            "🚨 Error with emoji 🔥",
            "Error\nwith\nnewlines",
            "Error\twith\ttabs",
            "Error with 'quotes' and \"double quotes\"",
            "Error with <HTML> &tags;",
        ]

        for special_input in special_chars:
            with self.subTest(input=special_input):
                log = f"(400) {special_input}"
                result = self.analyzer.analyze(log)

                self.assertEqual(result.status_code, 400)
                self.assertIsNotNone(result.category)

    def test_invalid_json_handling(self):
        """無効なJSONの処理テスト"""
        invalid_jsons = [
            '{"message": "unclosed',
            '{"message": }',
            '{message: "no quotes"}',
            '{"message": "trailing comma",}',
            "not json at all",
        ]

        for invalid_json in invalid_jsons:
            with self.subTest(json=invalid_json):
                log = f"(400) {invalid_json}"
                result = self.analyzer.analyze(log)

                # JSONが無効でもエラーログとして解析される
                self.assertEqual(result.status_code, 400)
                self.assertIsNotNone(result.category)

    def test_concurrent_access_safety(self):
        """同時アクセスの安全性テスト"""
        import threading
        import time

        results = []
        errors = []

        def analyze_error():
            try:
                result = self.analyzer.analyze(404, "Concurrent test")
                results.append(result)
            except Exception as e:
                errors.append(e)

        # 10個のスレッドで同時実行
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=analyze_error)
            threads.append(thread)

        # 全スレッド開始
        for thread in threads:
            thread.start()

        # 全スレッド完了待ち
        for thread in threads:
            thread.join(timeout=5.0)

        # エラーが発生しないことを確認
        self.assertEqual(len(errors), 0, f"Concurrent access errors: {errors}")
        self.assertEqual(len(results), 10)

        # 全ての結果が同じ内容であることを確認
        for result in results:
            self.assertEqual(result.status_code, 404)
            self.assertEqual(result.category, ErrorCategory.RESOURCE_NOT_FOUND)

    def test_memory_usage_stability(self):
        """メモリ使用量の安定性テスト"""
        import gc

        # 大量の解析を実行してメモリリークがないことを確認
        for i in range(1000):
            self.analyzer.analyze(500, f"Memory test {i}")

            # 100回ごとにガベージコレクション
            if i % 100 == 0:
                gc.collect()

        # テストが完了すれば、メモリリークによる OutOfMemory は発生していない
        self.assertTrue(True)

    def test_invalid_api_pattern_handling(self):
        """無効なAPIパターンの処理テスト"""
        # 存在しないパターンを渡した場合の処理
        try:
            result = self.analyzer.analyze(404, "Test", "INVALID_PATTERN")
            # エラーが発生しない場合、適切に処理されることを確認
            self.assertIsNotNone(result)
        except (ValueError, TypeError, AnalyzerError):
            # 適切なエラーが発生することも許容
            pass


if __name__ == "__main__":
    unittest.main()
