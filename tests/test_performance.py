"""
パフォーマンステスト
"""

import unittest
import asyncio
import time
import statistics
from concurrent.futures import ThreadPoolExecutor
from linebot_error_analyzer import LineErrorAnalyzer, AsyncLineErrorAnalyzer


class TestPerformance(unittest.TestCase):
    """パフォーマンステストクラス"""

    def setUp(self):
        self.analyzer = LineErrorAnalyzer()

    def test_single_analysis_performance(self):
        """単一エラー分析のパフォーマンステスト"""
        error_data = {"status_code": 400, "message": "Performance test error"}

        # 1000回実行して平均時間を測定
        times = []
        for _ in range(1000):
            start = time.perf_counter()
            self.analyzer.analyze(error_data)
            end = time.perf_counter()
            times.append(end - start)

        avg_time = statistics.mean(times)
        median_time = statistics.median(times)
        max_time = max(times)

        print(f"\n単一分析パフォーマンス:")
        print(f"平均時間: {avg_time*1000:.2f}ms")
        print(f"中央値: {median_time*1000:.2f}ms")
        print(f"最大時間: {max_time*1000:.2f}ms")

        # 1ms以下であることを確認（大部分のケース）
        self.assertLess(avg_time, 0.001)

    def test_batch_analysis_performance(self):
        """バッチ分析のパフォーマンステスト"""
        # 様々なサイズでテスト
        sizes = [10, 100, 1000, 5000]

        for size in sizes:
            with self.subTest(batch_size=size):
                errors = [
                    {"status_code": 400 + (i % 100), "message": f"Batch error {i}"}
                    for i in range(size)
                ]

                start = time.perf_counter()
                results = self.analyzer.analyze_multiple(errors)
                end = time.perf_counter()

                execution_time = end - start
                throughput = size / execution_time

                print(f"\nバッチサイズ {size}:")
                print(f"実行時間: {execution_time:.3f}秒")
                print(f"スループット: {throughput:.0f} errors/sec")

                # 結果の正確性を確認
                self.assertEqual(len(results), size)

                # パフォーマンス要件（最低100 errors/sec）
                self.assertGreater(throughput, 100)

    def test_memory_efficiency(self):
        """メモリ効率のテスト"""
        import psutil
        import os

        process = psutil.Process(os.getpid())

        # 初期メモリ使用量
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # 大量のエラーを処理
        large_batch = [
            {
                "status_code": 400,
                "message": f"Memory test error {i}",
                "details": [{"field": f"data_{j}" for j in range(10)}],
            }
            for i in range(10000)
        ]

        results = self.analyzer.analyze_multiple(large_batch)

        # 処理後のメモリ使用量
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        print(f"\nメモリ使用量:")
        print(f"初期: {initial_memory:.2f}MB")
        print(f"最終: {final_memory:.2f}MB")
        print(f"増加: {memory_increase:.2f}MB")

        # 結果を確認
        self.assertEqual(len(results), 10000)

        # メモリ増加が合理的な範囲内（500MB以下）
        self.assertLess(memory_increase, 500)

    def test_thread_safety_performance(self):
        """マルチスレッド環境でのパフォーマンステスト"""

        def worker_function(worker_id):
            """ワーカー関数"""
            local_analyzer = LineErrorAnalyzer()
            errors = [
                {"status_code": 400 + i, "message": f"Worker {worker_id} error {i}"}
                for i in range(100)
            ]

            start = time.perf_counter()
            results = local_analyzer.analyze_multiple(errors)
            end = time.perf_counter()

            return len(results), end - start

        # 10個のワーカーで並行実行
        with ThreadPoolExecutor(max_workers=10) as executor:
            start_total = time.perf_counter()
            futures = [executor.submit(worker_function, i) for i in range(10)]
            results = [future.result() for future in futures]
            end_total = time.perf_counter()

        total_time = end_total - start_total
        total_errors = sum(result[0] for result in results)
        avg_worker_time = statistics.mean(result[1] for result in results)

        print(f"\nマルチスレッドパフォーマンス:")
        print(f"総実行時間: {total_time:.3f}秒")
        print(f"処理したエラー数: {total_errors}")
        print(f"平均ワーカー時間: {avg_worker_time:.3f}秒")
        print(f"総スループット: {total_errors/total_time:.0f} errors/sec")

        # 全ワーカーが正常に完了
        self.assertEqual(len(results), 10)
        self.assertEqual(total_errors, 1000)


class TestAsyncPerformance(unittest.IsolatedAsyncioTestCase):
    """非同期パフォーマンステスト"""

    async def asyncSetUp(self):
        self.analyzer = AsyncLineErrorAnalyzer()

    async def test_async_batch_performance(self):
        """非同期バッチ処理のパフォーマンステスト"""
        # 様々なバッチサイズとワーカー数でテスト
        test_cases = [
            {"errors": 1000, "batch_size": 50, "max_workers": 10},
            {"errors": 5000, "batch_size": 100, "max_workers": 20},
            {"errors": 10000, "batch_size": 200, "max_workers": 50},
        ]

        for case in test_cases:
            with self.subTest(**case):
                errors = [
                    {"status_code": 400 + (i % 200), "message": f"Async error {i}"}
                    for i in range(case["errors"])
                ]

                start = time.perf_counter()
                results = await self.analyzer.analyze_batch(
                    errors,
                    batch_size=case["batch_size"],
                    max_workers=case["max_workers"],
                )
                end = time.perf_counter()

                execution_time = end - start
                throughput = case["errors"] / execution_time

                print(f"\n非同期バッチ処理 ({case}):")
                print(f"実行時間: {execution_time:.3f}秒")
                print(f"スループット: {throughput:.0f} errors/sec")

                # 結果の正確性を確認
                self.assertEqual(len(results), case["errors"])

                # 非同期処理は同期処理より高速であることを期待
                self.assertGreater(throughput, 500)

    async def test_concurrent_analysis_performance(self):
        """並行分析のパフォーマンステスト"""
        error_data = {"status_code": 429, "message": "Concurrent analysis test"}

        # 100個の分析タスクを並行実行
        tasks = [self.analyzer.analyze(error_data) for _ in range(100)]

        start = time.perf_counter()
        results = await asyncio.gather(*tasks)
        end = time.perf_counter()

        execution_time = end - start
        throughput = 100 / execution_time

        print(f"\n並行分析パフォーマンス:")
        print(f"実行時間: {execution_time:.3f}秒")
        print(f"スループット: {throughput:.0f} analyses/sec")

        # 全て正常に完了
        self.assertEqual(len(results), 100)

        # 高い並行性能を期待
        self.assertGreater(throughput, 1000)

    async def test_mixed_workload_performance(self):
        """混合ワークロードのパフォーマンステスト"""
        # 異なるタイプのエラーを混合
        mixed_errors = []

        # 辞書形式のエラー
        mixed_errors.extend(
            [{"status_code": 400 + i, "message": f"Dict error {i}"} for i in range(500)]
        )

        # レスポンス形式のエラー
        from unittest.mock import Mock

        for i in range(500):
            mock_response = Mock()
            mock_response.status_code = 500 + i
            mock_response.text = f'{{"message": "Mock error {i}"}}'
            mock_response.headers = {}
            mixed_errors.append(mock_response)

        start = time.perf_counter()
        results = await self.analyzer.analyze_multiple(mixed_errors)
        end = time.perf_counter()

        execution_time = end - start
        throughput = 1000 / execution_time

        print(f"\n混合ワークロードパフォーマンス:")
        print(f"実行時間: {execution_time:.3f}秒")
        print(f"スループット: {throughput:.0f} errors/sec")

        # 結果の検証
        self.assertEqual(len(results), 1000)

        # 辞書エラーの検証
        dict_results = results[:500]
        for i, result in enumerate(dict_results):
            self.assertEqual(result.status_code, 400 + i)

        # レスポンスエラーの検証
        response_results = results[500:]
        for i, result in enumerate(response_results):
            self.assertEqual(result.status_code, 500 + i)

    async def test_scalability_under_load(self):
        """負荷下でのスケーラビリティテスト"""
        # 段階的に負荷を増加
        load_levels = [100, 500, 1000, 2000, 5000]
        results_summary = []

        for load in load_levels:
            errors = [
                {"status_code": 400, "message": f"Load test error {i}"}
                for i in range(load)
            ]

            # 3回測定して平均を取る
            times = []
            for _ in range(3):
                start = time.perf_counter()
                results = await self.analyzer.analyze_batch(errors, batch_size=100)
                end = time.perf_counter()
                times.append(end - start)

            avg_time = statistics.mean(times)
            throughput = load / avg_time

            results_summary.append(
                {"load": load, "time": avg_time, "throughput": throughput}
            )

            print(f"\n負荷レベル {load}:")
            print(f"平均時間: {avg_time:.3f}秒")
            print(f"スループット: {throughput:.0f} errors/sec")

            # 結果の正確性を確認
            self.assertEqual(len(results), load)

        # スケーラビリティの分析
        print(f"\nスケーラビリティ分析:")
        for i, result in enumerate(results_summary):
            if i > 0:
                prev_result = results_summary[i - 1]
                load_increase = result["load"] / prev_result["load"]
                time_increase = result["time"] / prev_result["time"]
                efficiency = load_increase / time_increase

                print(
                    f"負荷 {prev_result['load']} → {result['load']}: "
                    f"効率比 {efficiency:.2f}"
                )

                # 効率が著しく低下していないことを確認（目安として0.5以上）
                self.assertGreater(efficiency, 0.5)


class TestResourceUtilization(unittest.TestCase):
    """リソース使用量テスト"""

    def setUp(self):
        self.analyzer = LineErrorAnalyzer()

    def test_cpu_utilization(self):
        """CPU使用率のテスト"""
        import psutil
        import threading

        # CPU使用率を監視するスレッド
        cpu_percentages = []
        monitoring = True

        def monitor_cpu():
            while monitoring:
                cpu_percentages.append(psutil.cpu_percent(interval=0.1))

        monitor_thread = threading.Thread(target=monitor_cpu)
        monitor_thread.start()

        try:
            # CPU集約的な処理
            large_errors = [
                {
                    "status_code": 400 + (i % 200),
                    "message": f"CPU test error {i}" * 10,  # 長いメッセージ
                    "details": [{"field": f"value_{j}"} for j in range(20)],
                }
                for i in range(5000)
            ]

            start = time.perf_counter()
            results = self.analyzer.analyze_multiple(large_errors)
            end = time.perf_counter()

        finally:
            monitoring = False
            monitor_thread.join()

        execution_time = end - start
        avg_cpu = statistics.mean(cpu_percentages) if cpu_percentages else 0
        max_cpu = max(cpu_percentages) if cpu_percentages else 0

        print(f"\nCPU使用率:")
        print(f"実行時間: {execution_time:.3f}秒")
        print(f"平均CPU使用率: {avg_cpu:.1f}%")
        print(f"最大CPU使用率: {max_cpu:.1f}%")

        # 結果の検証
        self.assertEqual(len(results), 5000)

        # CPU使用率が合理的な範囲内（90%以下）
        self.assertLess(max_cpu, 90)

    def test_file_descriptor_usage(self):
        """ファイルディスクリプタ使用量のテスト"""
        import psutil
        import os

        process = psutil.Process(os.getpid())

        # 初期のファイルディスクリプタ数
        initial_fds = process.num_fds() if hasattr(process, "num_fds") else 0

        # 大量の分析を実行
        for batch in range(10):
            errors = [
                {"status_code": 400, "message": f"FD test batch {batch} error {i}"}
                for i in range(1000)
            ]
            results = self.analyzer.analyze_multiple(errors)
            self.assertEqual(len(results), 1000)

        # 最終のファイルディスクリプタ数
        final_fds = process.num_fds() if hasattr(process, "num_fds") else 0
        fd_increase = final_fds - initial_fds

        print(f"\nファイルディスクリプタ使用量:")
        print(f"初期: {initial_fds}")
        print(f"最終: {final_fds}")
        print(f"増加: {fd_increase}")

        # ファイルディスクリプタのリークがないことを確認
        self.assertLess(abs(fd_increase), 10)


if __name__ == "__main__":
    # パフォーマンステストは詳細出力で実行
    unittest.main(verbosity=2, buffer=False)
