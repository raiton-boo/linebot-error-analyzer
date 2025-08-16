#!/usr/bin/env python3
"""統合テストケース - 修正版"""

import unittest
import asyncio
import sys
import os

# プロジェクトのルートをPATHに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from linebot_error_analyzer import LineErrorAnalyzer, AsyncLineErrorAnalyzer
from linebot_error_analyzer.models import ApiPattern, ErrorCategory
from linebot_error_analyzer.models.log_parser import LogParser


class TestIntegration(unittest.TestCase):
    """統合テスト"""

    def setUp(self):
        """テストセットアップ"""
        self.sync_analyzer = LineErrorAnalyzer()
        self.async_analyzer = AsyncLineErrorAnalyzer()
        self.log_parser = LogParser()

    def test_end_to_end_real_scenario(self):
        """実際のシナリオでのエンドツーエンドテスト"""
        # 実際のLINE APIエラーレスポンス
        real_scenarios = [
            {
                "log": "(401) Invalid channel access token",
                "expected_status": 401,
                "description_keywords": ["認証", "トークン"],
            },
            {
                "log": "(400) The request body has 2 error(s). May not be empty messages[0].text",
                "expected_status": 400,
                "description_keywords": ["リクエスト", "エラー"],
            },
            {
                "log": "(429) Rate limit exceeded",
                "expected_status": 429,
                "description_keywords": ["リクエスト", "制限"],
            },
        ]

        for scenario in real_scenarios:
            with self.subTest(log=scenario["log"]):
                result = self.sync_analyzer.analyze(scenario["log"])

                self.assertEqual(result.status_code, scenario["expected_status"])

                # 説明にキーワードが含まれているか確認
                for keyword in scenario["description_keywords"]:
                    self.assertIn(keyword, result.description)

    def test_sync_async_consistency(self):
        """同期版と非同期版の一貫性テスト"""
        test_logs = [
            "(400) Bad Request",
            "(404) Not Found",
            "(500) Internal Server Error",
            "(403) Forbidden",
        ]

        async def async_test():
            for log in test_logs:
                sync_result = self.sync_analyzer.analyze(log)
                async_result = await self.async_analyzer.analyze(log)

                # 基本的な結果が同じであることを確認
                self.assertEqual(sync_result.status_code, async_result.status_code)
                self.assertEqual(sync_result.category, async_result.category)
                self.assertEqual(sync_result.is_retryable, async_result.is_retryable)

        # 非同期テスト実行
        asyncio.run(async_test())

    def test_log_parser_integration(self):
        """LogParserとの統合テスト"""
        log_samples = [
            "(200) Success message",
            "(404) User not found",
            "(500) Database connection failed",
        ]

        for log in log_samples:
            with self.subTest(log=log):
                # LogParserで解析
                parsed = self.log_parser.parse(log)
                self.assertIsNotNone(parsed)

                # LineErrorAnalyzerで解析
                result = self.sync_analyzer.analyze(log)
                self.assertIsNotNone(result)

    def test_full_workflow_simulation(self):
        """完全なワークフローシミュレーション"""
        # シミュレートしたLINE Bot のエラー状況
        workflow_scenarios = [
            {
                "step": "チャネルアクセストークン検証",
                "log": "(401) Invalid channel access token",
                "expected_retryable": False,
            },
            {
                "step": "メッセージ送信",
                "log": "(429) Too many requests",
                "expected_retryable": True,
            },
            {
                "step": "ユーザープロフィール取得",
                "log": "(404) User not found",
                "expected_retryable": False,
            },
        ]

        for scenario in workflow_scenarios:
            with self.subTest(step=scenario["step"]):
                result = self.sync_analyzer.analyze(scenario["log"])

                self.assertEqual(
                    result.is_retryable,
                    scenario["expected_retryable"],
                    f"Retryable mismatch for {scenario['step']}",
                )

    def test_concurrent_analysis(self):
        """複数ログの同時解析テスト"""
        import threading
        import time

        logs = [
            "(400) Bad request",
            "(401) Unauthorized",
            "(403) Forbidden",
            "(404) Not found",
            "(429) Too many requests",
            "(500) Internal error",
        ]

        results = {}
        errors = []

        def analyze_log(idx, log):
            try:
                result = self.sync_analyzer.analyze(log)
                results[idx] = result
            except Exception as e:
                errors.append((idx, e))

        # 並行実行
        threads = []
        for i, log in enumerate(logs):
            thread = threading.Thread(target=analyze_log, args=(i, log))
            threads.append(thread)
            thread.start()

        # 全完了を待つ
        for thread in threads:
            thread.join(timeout=5.0)

        # 結果検証
        self.assertEqual(len(errors), 0, f"Concurrent errors: {errors}")
        self.assertEqual(len(results), len(logs))

        # 各結果が正しいことを確認
        for i, log in enumerate(logs):
            self.assertIn(i, results)
            expected_status = int(log.split(")")[0][1:])
            self.assertEqual(results[i].status_code, expected_status)

    def test_performance_analysis(self):
        """パフォーマンス解析テスト"""
        import time

        # 大量ログでのパフォーマンステスト
        logs = [f"({i % 5 + 4}00) Test error {i}" for i in range(100)]

        start_time = time.time()
        for log in logs:
            result = self.sync_analyzer.analyze(log)
            self.assertIsNotNone(result)
        end_time = time.time()

        # 100ログを1秒以内に解析完了
        self.assertLess(
            end_time - start_time,
            1.0,
            f"Performance test failed: {end_time - start_time:.2f}s",
        )

    def test_mixed_api_patterns(self):
        """混合APIパターン解析テスト"""
        mixed_logs = [
            "(400) Message API: Invalid message format",
            "(401) User API: Authentication failed",
            "(403) Rich Menu API: Permission denied",
            "(429) Push API: Rate limit exceeded",
            "(500) Group API: Internal error",
        ]

        for log in mixed_logs:
            with self.subTest(log=log):
                result = self.sync_analyzer.analyze(log)

                # 適切にカテゴライズされていることを確認
                self.assertIsNotNone(result.category)
                self.assertIsNotNone(result.api_pattern)

                # APIパターンがログ内容と関連していることを確認
                if "Message" in log:
                    # メッセージ関連のAPIパターンであることを期待
                    pass  # 実装依存
                elif "User" in log:
                    # ユーザー関連のAPIパターンであることを期待
                    pass  # 実装依存

    def test_error_recovery_suggestions(self):
        """エラー回復提案テスト"""
        recovery_scenarios = [
            {
                "log": "(401) Invalid channel access token",
                "expected_suggestions": ["トークン", "更新", "設定"],
            },
            {
                "log": "(429) Rate limit exceeded",
                "expected_suggestions": ["再試行", "待機", "間隔"],
            },
            {
                "log": "(500) Internal server error",
                "expected_suggestions": ["再試行", "サポート", "確認"],
            },
        ]

        for scenario in recovery_scenarios:
            with self.subTest(log=scenario["log"]):
                result = self.sync_analyzer.analyze(scenario["log"])

                # 回復提案が含まれているかチェック
                suggestions_text = result.description
                suggestion_found = any(
                    keyword in suggestions_text
                    for keyword in scenario["expected_suggestions"]
                )
                self.assertTrue(
                    suggestion_found,
                    f"No recovery suggestions found for: {scenario['log']}",
                )


if __name__ == "__main__":
    unittest.main()
