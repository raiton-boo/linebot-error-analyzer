#!/usr/bin/env python3
"""統合テストケース"""

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
                "log": """(401)
Reason: Unauthorized
HTTP response headers: HTTPHeaderDict({'server': 'legy'})
HTTP response body: {"message":"Invalid channel access token"}""",
                "expected_status": 401,
                "expected_category": ErrorCategory.AUTHENTICATION_ERROR,
                "description_keywords": ["認証", "トークン"],
            },
            {
                "log": """(400)
HTTP response body: {"message":"The request body has 2 error(s)","details":[{"message":"May not be empty","property":"messages[0].text"}]}""",
                "expected_status": 400,
                "expected_category": ErrorCategory.CLIENT_ERROR,
                "description_keywords": ["リクエスト", "エラー"],
            },
            {
                "log": """(429)
Reason: Too Many Requests
HTTP response body: {"message":"Rate limit exceeded"}""",
                "expected_status": 429,
                "expected_category": ErrorCategory.RATE_LIMIT_ERROR,
                "description_keywords": ["制限", "レート"],
            },
        ]

        for i, scenario in enumerate(real_scenarios):
            with self.subTest(scenario=i):
                result = self.sync_analyzer.analyze(scenario["log"])

                self.assertEqual(result.status_code, scenario["expected_status"])
                self.assertEqual(result.category, scenario["expected_category"])

                # 説明にキーワードが含まれているか確認
                for keyword in scenario["description_keywords"]:
                    self.assertIn(keyword, result.description)

    def test_sync_async_consistency(self):
        """同期版と非同期版の一貫性テスト"""
        test_cases = [
            (400, "Bad Request"),
            (404, "Not Found"),
            (500, "Internal Server Error"),
            ('(403) {"message":"Forbidden"}',),
        ]

        async def async_test():
            for case in test_cases:
                sync_result = self.sync_analyzer.analyze(*case)
                async_result = await self.async_analyzer.analyze(*case)

                # 基本的な結果が同じであることを確認
                self.assertEqual(sync_result.status_code, async_result.status_code)
                self.assertEqual(sync_result.category, async_result.category)
                self.assertEqual(sync_result.is_retryable, async_result.is_retryable)
                # 説明は基本的に同じ（細かい差異は許容）
                self.assertIn(sync_result.category.value, async_result.description)

        # 非同期テスト実行
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(async_test())
        finally:
            loop.close()

    def test_api_pattern_comprehensive_flow(self):
        """APIパターン指定での包括的なフロー"""
        # ユーザープロフィール取得のフロー
        profile_scenarios = [
            {
                "log": '(404) {"message":"Not found"}',
                "pattern": ApiPattern.USER_PROFILE,
                "expected_category": ErrorCategory.USER_BLOCKED,
                "action_keywords": ["ブロック", "確認"],
            },
            {
                "log": '(403) {"message":"Forbidden"}',
                "pattern": ApiPattern.USER_PROFILE,
                "expected_category": ErrorCategory.PERMISSION_ERROR,
                "action_keywords": ["権限", "確認"],
            },
        ]

        for scenario in profile_scenarios:
            result = self.sync_analyzer.analyze(scenario["log"], scenario["pattern"])

            self.assertEqual(result.category, scenario["expected_category"])
            for keyword in scenario["action_keywords"]:
                self.assertIn(keyword, result.recommended_action)

    def test_log_parser_integration(self):
        """LogParserとの統合テスト"""
        complex_log = """(500)
Reason: Internal Server Error  
HTTP response headers: HTTPHeaderDict({
    'server': 'legy',
    'content-type': 'application/json',
    'x-line-request-id': 'test-request-123',
    'date': 'Fri, 16 Aug 2025 12:34:56 GMT'
})
HTTP response body: {
    "message": "Internal server error occurred",
    "details": {
        "error_code": "INTERNAL_ERROR",
        "timestamp": "2025-08-16T12:34:56Z"
    }
}"""

        # 1. LogParserで直接パース
        parse_result = self.log_parser.parse(complex_log)

        self.assertTrue(parse_result.parse_success)
        self.assertEqual(parse_result.status_code, 500)
        self.assertEqual(parse_result.request_id, "test-request-123")
        self.assertIn("Internal server error", parse_result.message)

        # 2. Analyzerで解析
        analysis_result = self.sync_analyzer.analyze(complex_log)

        self.assertEqual(analysis_result.status_code, 500)
        self.assertEqual(analysis_result.category, ErrorCategory.SERVER_ERROR)
        self.assertEqual(analysis_result.request_id, "test-request-123")
        self.assertTrue(analysis_result.is_retryable)

    def test_error_database_integration(self):
        """エラーデータベースとの統合テスト"""
        # 特定エラーコードの詳細解析
        specific_errors = [
            (401, "認証エラー"),
            (403, "権限エラー"),
            (404, "リソース"),
            (429, "レート制限"),
            (500, "サーバーエラー"),
        ]

        for status_code, expected_keyword in specific_errors:
            result = self.sync_analyzer.analyze(status_code, "Test error")

            # データベースから適切な情報が取得されることを確認
            self.assertIn(expected_keyword, result.description)
            self.assertIsNotNone(result.recommended_action)
            self.assertTrue(len(result.recommended_action) > 10)

    def test_performance_under_load(self):
        """負荷時のパフォーマンステスト"""
        import time
        import threading

        results = []
        errors = []
        start_time = time.time()

        def analyze_batch():
            try:
                for i in range(50):
                    result = self.sync_analyzer.analyze(404, f"Load test message {i}")
                    results.append(result)
            except Exception as e:
                errors.append(e)

        # 4つのスレッドで並行実行（合計200回の解析）
        threads = []
        for _ in range(4):
            thread = threading.Thread(target=analyze_batch)
            threads.append(thread)

        # 全スレッド開始
        for thread in threads:
            thread.start()

        # 全スレッド完了待ち
        for thread in threads:
            thread.join()

        end_time = time.time()

        # 結果検証
        self.assertEqual(len(errors), 0, f"Load test errors: {errors}")
        self.assertEqual(len(results), 200)

        # パフォーマンス要件（200回の解析が3秒以内）
        total_time = end_time - start_time
        self.assertLess(total_time, 3.0, f"Load test too slow: {total_time}s")

    def test_mixed_input_types_integration(self):
        """混在した入力タイプの統合テスト"""
        mixed_inputs = [
            # ステータスコード + メッセージ
            (400, "Bad Request"),
            # ログ文字列
            "(401) Unauthorized",
            # JSON文字列
            '{"message": "Rate limit exceeded"}',
            # 複雑なログ
            '(404)\nHTTP response body: {"message":"Not found"}',
        ]

        for input_data in mixed_inputs:
            with self.subTest(input=str(input_data)[:30]):
                if isinstance(input_data, tuple):
                    result = self.sync_analyzer.analyze(*input_data)
                else:
                    result = self.sync_analyzer.analyze(input_data)

                # 全てのケースで有効な結果が返ることを確認
                self.assertIsNotNone(result.status_code)
                self.assertIsNotNone(result.category)
                self.assertIsInstance(result.description, str)
                self.assertTrue(len(result.description) > 0)

    def test_full_workflow_simulation(self):
        """完全なワークフローシミュレーション"""
        # LINE Botアプリケーションでの実際の使用パターン
        workflow_steps = [
            # Step 1: メッセージ送信エラー
            {
                "action": "message_push",
                "error": '(404) {"message":"Not found"}',
                "pattern": ApiPattern.MESSAGE_PUSH,
                "expected_category": ErrorCategory.USER_BLOCKED,
            },
            # Step 2: ユーザープロフィール確認
            {
                "action": "get_profile",
                "error": '(404) {"message":"Not found"}',
                "pattern": ApiPattern.USER_PROFILE,
                "expected_category": ErrorCategory.USER_BLOCKED,
            },
            # Step 3: リッチメニュー設定エラー
            {
                "action": "rich_menu",
                "error": '(400) {"message":"Invalid rich menu JSON"}',
                "pattern": ApiPattern.RICH_MENU_CREATE,
                "expected_category": ErrorCategory.CLIENT_ERROR,
            },
        ]

        workflow_results = []

        for step in workflow_steps:
            result = self.sync_analyzer.analyze(step["error"], step["pattern"])

            workflow_results.append(
                {
                    "action": step["action"],
                    "result": result,
                    "success": result.category == step["expected_category"],
                }
            )

        # 全ステップが適切に処理されることを確認
        for step_result in workflow_results:
            self.assertTrue(
                step_result["success"], f"Failed workflow step: {step_result['action']}"
            )

        # ワークフロー全体の成功
        all_successful = all(sr["success"] for sr in workflow_results)
        self.assertTrue(all_successful, "Workflow simulation failed")


if __name__ == "__main__":
    unittest.main()
