#!/usr/bin/env python3
"""パフォーマンステストケース"""

import unittest
import time
import asyncio
import sys
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

# プロジェクトのルートをPATHに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from linebot_error_analyzer import LineErrorAnalyzer, AsyncLineErrorAnalyzer
from linebot_error_analyzer.models import ApiPattern


class TestPerformance(unittest.TestCase):
    """パフォーマンステストケース"""

    def setUp(self):
        """テストセットアップ"""
        self.sync_analyzer = LineErrorAnalyzer()
        self.async_analyzer = AsyncLineErrorAnalyzer()

    def test_single_analysis_performance(self):
        """単一解析のパフォーマンステスト"""
        test_cases = [
            (400, "Bad Request"),
            (401, "Unauthorized"),
            (404, "Not Found"),
            (429, "Too Many Requests"),
            (500, "Internal Server Error")
        ]

        total_time = 0
        iterations = 100

        for _ in range(iterations):
            for status_code, message in test_cases:
                start_time = time.perf_counter()
                result = self.sync_analyzer.analyze(status_code, message)
                end_time = time.perf_counter()
                
                total_time += (end_time - start_time)
                
                # 結果の妥当性確認
                self.assertEqual(result.status_code, status_code)
                self.assertIsNotNone(result.category)

        avg_time_per_analysis = total_time / (iterations * len(test_cases))
        
        # 1回の解析が10ms以下で完了することを期待
        self.assertLess(avg_time_per_analysis, 0.01, 
                       f"Average analysis time too slow: {avg_time_per_analysis:.6f}s")

    def test_batch_analysis_performance(self):
        """バッチ解析のパフォーマンステスト"""
        # 大量のテストケースを準備
        test_data = []
        for i in range(1000):
            status_code = 400 + (i % 100)  # 400-499の範囲
            message = f"Test error {i}"
            test_data.append((status_code, message))

        start_time = time.perf_counter()
        
        results = []
        for status_code, message in test_data:
            result = self.sync_analyzer.analyze(status_code, message)
            results.append(result)
        
        end_time = time.perf_counter()
        
        # 結果検証
        self.assertEqual(len(results), 1000)
        for result in results:
            self.assertIsNotNone(result.status_code)
            self.assertIsNotNone(result.category)
        
        total_time = end_time - start_time
        throughput = len(test_data) / total_time
        
        # スループットが500req/s以上であることを期待
        self.assertGreater(throughput, 500, 
                          f"Throughput too low: {throughput:.2f} req/s")

    def test_concurrent_analysis_performance(self):
        """並行解析のパフォーマンステスト"""
        test_data = [(400 + i, f"Concurrent test {i}") for i in range(100)]
        
        def analyze_single(data):
            status_code, message = data
            return self.sync_analyzer.analyze(status_code, message)

        start_time = time.perf_counter()
        
        # ThreadPoolExecutorで並行実行
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(analyze_single, data) for data in test_data]
            results = [future.result() for future in as_completed(futures)]
        
        end_time = time.perf_counter()
        
        # 結果検証
        self.assertEqual(len(results), 100)
        
        total_time = end_time - start_time
        
        # 並行実行により時間短縮されることを期待（単純計算より速い）
        self.assertLess(total_time, 1.0, 
                       f"Concurrent execution too slow: {total_time:.3f}s")

    def test_async_performance_comparison(self):
        """非同期版のパフォーマンス比較テスト"""
        test_data = [(400 + i, f"Async test {i}") for i in range(100)]
        
        # 非同期バッチ処理
        async def async_batch_analysis():
            tasks = []
            for status_code, message in test_data:
                task = self.async_analyzer.analyze(status_code, message)
                tasks.append(task)
            
            return await asyncio.gather(*tasks)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            start_time = time.perf_counter()
            async_results = loop.run_until_complete(async_batch_analysis())
            async_time = time.perf_counter() - start_time
            
            # 同期版との比較用
            start_time = time.perf_counter()
            sync_results = []
            for status_code, message in test_data:
                result = self.sync_analyzer.analyze(status_code, message)
                sync_results.append(result)
            sync_time = time.perf_counter() - start_time
            
            # 結果検証
            self.assertEqual(len(async_results), len(sync_results))
            
            # パフォーマンス比較（非同期版が極端に遅くないことを確認）
            self.assertLess(async_time, sync_time * 2, 
                           f"Async version too slow: {async_time:.3f}s vs {sync_time:.3f}s")
            
        finally:
            loop.close()

    def test_memory_usage_stability(self):
        """メモリ使用量の安定性テスト"""
        import gc
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # 大量の解析を実行
        for i in range(5000):
            status_code = 400 + (i % 100)
            message = f"Memory test {i}"
            result = self.sync_analyzer.analyze(status_code, message)
            self.assertIsNotNone(result)
            
            # 定期的にガベージコレクション
            if i % 1000 == 0:
                gc.collect()
        
        # 最終メモリ使用量
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # メモリ増加が50MB以下であることを期待
        max_memory_increase = 50 * 1024 * 1024  # 50MB
        self.assertLess(memory_increase, max_memory_increase, 
                       f"Memory usage increased too much: {memory_increase / 1024 / 1024:.2f}MB")

    def test_error_log_parsing_performance(self):
        """エラーログパース性能テスト"""
        # 複雑なエラーログのテンプレート
        complex_log_template = """({status_code})
Reason: {reason}
HTTP response headers: HTTPHeaderDict({{'server': 'legy', 'cache-control': 'no-cache, no-store, max-age=0, must-revalidate', 'content-type': 'application/json', 'date': 'Fri, 25 Jul 2025 18:23:24 GMT', 'expires': '0', 'pragma': 'no-cache', 'x-content-type-options': 'nosniff', 'x-frame-options': 'DENY', 'x-line-request-id': 'test-{request_id}', 'x-xss-protection': '1; mode=block', 'content-length': '23'}})
HTTP response body: {{"message":"{message}"}}"""

        test_logs = []
        for i in range(500):
            log = complex_log_template.format(
                status_code=400 + (i % 100),
                reason=f"Error {i}",
                request_id=f"req-{i}",
                message=f"Test message {i}"
            )
            test_logs.append(log)

        start_time = time.perf_counter()
        
        results = []
        for log in test_logs:
            result = self.sync_analyzer.analyze(log)
            results.append(result)
        
        end_time = time.perf_counter()
        
        # 結果検証
        self.assertEqual(len(results), 500)
        for i, result in enumerate(results):
            expected_status = 400 + (i % 100)
            self.assertEqual(result.status_code, expected_status)
            self.assertEqual(result.request_id, f"req-{i}")
        
        total_time = end_time - start_time
        avg_time = total_time / len(test_logs)
        
        # ログパース時間が適切であることを確認
        self.assertLess(avg_time, 0.005, 
                       f"Log parsing too slow: {avg_time:.6f}s per log")

    def test_api_pattern_analysis_performance(self):
        """APIパターン解析のパフォーマンステスト"""
        error_log = """(404)
HTTP response body: {"message":"Not found"}"""
        
        patterns = list(ApiPattern)
        iterations = 200
        
        start_time = time.perf_counter()
        
        for _ in range(iterations):
            for pattern in patterns:
                result = self.sync_analyzer.analyze(error_log, api_pattern=pattern)
                self.assertIsNotNone(result.category)
        
        end_time = time.perf_counter()
        
        total_analyses = iterations * len(patterns)
        total_time = end_time - start_time
        avg_time = total_time / total_analyses
        
        # APIパターン指定時も高速であることを確認
        self.assertLess(avg_time, 0.002, 
                       f"API pattern analysis too slow: {avg_time:.6f}s per analysis")


if __name__ == "__main__":
    # psutilが必要なテストはオプション
    try:
        import psutil
    except ImportError:
        print("Warning: psutil not available, skipping memory usage tests")
    
    unittest.main()
