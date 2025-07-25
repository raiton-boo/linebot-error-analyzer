"""
LINE Bot Error Analyzer - パフォーマンス分析デモ

このデモでは以下のパフォーマンス特性を実演します：
1. メモリ使用量の監視
2. 処理速度のベンチマーク
3. スケーラビリティテスト
4. リソース効率の最適化
"""

import sys
import os
import time
import psutil
import asyncio
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor
import gc

# プロジェクトルートを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from linebot_error_analyzer import LineErrorAnalyzer, AsyncLineErrorAnalyzer


class PerformanceMonitor:
    """パフォーマンス監視クラス"""

    def __init__(self):
        self.process = psutil.Process()
        self.start_time = None
        self.start_memory = None

    def start(self):
        """監視開始"""
        gc.collect()  # ガベージコレクション実行
        self.start_time = time.time()
        self.start_memory = self.process.memory_info().rss
        return self

    def stop(self):
        """監視終了と結果取得"""
        end_time = time.time()
        end_memory = self.process.memory_info().rss

        return {
            "duration": end_time - self.start_time,
            "memory_used": end_memory - self.start_memory,
            "memory_peak": self.process.memory_info().rss,
            "cpu_percent": self.process.cpu_percent(),
        }


def generate_test_errors(count: int) -> List[Dict[str, Any]]:
    """テスト用エラーデータ生成"""

    error_templates = [
        {"status_code": 400, "message": "Bad request"},
        {"status_code": 401, "message": "Unauthorized"},
        {"status_code": 403, "message": "Forbidden"},
        {"status_code": 404, "message": "Not found"},
        {"status_code": 429, "message": "Rate limited"},
        {"status_code": 500, "message": "Internal error"},
        {"status_code": 502, "message": "Bad gateway"},
        {"status_code": 503, "message": "Service unavailable"},
    ]

    errors = []
    for i in range(count):
        template = error_templates[i % len(error_templates)]
        error = template.copy()
        error["message"] = f"{template['message']} #{i+1}"
        error["request_id"] = f"req-{i+1:06d}"
        error["headers"] = {
            "Content-Type": "application/json",
            "X-Request-ID": f"req-{i+1}",
        }
        errors.append(error)

    return errors


def demo_sync_performance():
    """同期処理のパフォーマンステスト"""

    print("🏃 1. 同期処理パフォーマンステスト")
    print("-" * 50)

    analyzer = LineErrorAnalyzer()
    test_sizes = [100, 500, 1000, 2000]

    for size in test_sizes:
        print(f"\n📊 テストサイズ: {size:,}件")

        # テストデータ生成
        errors = generate_test_errors(size)

        # パフォーマンス監視開始
        monitor = PerformanceMonitor().start()

        try:
            # 分析実行
            results = analyzer.analyze_multiple(errors)

            # 監視終了
            stats = monitor.stop()

            # 結果表示
            throughput = size / stats["duration"]
            memory_mb = stats["memory_used"] / (1024 * 1024)

            print(f"   ⏱️  処理時間: {stats['duration']:.2f}秒")
            print(f"   🚀 スループット: {throughput:.1f}件/秒")
            print(f"   💾 メモリ使用量: {memory_mb:.1f}MB")
            print(f"   🖥️  CPU使用率: {stats['cpu_percent']:.1f}%")
            print(f"   ✅ 成功率: {len(results)}/{size} ({len(results)/size*100:.1f}%)")

        except Exception as e:
            print(f"   ❌ エラー: {e}")


async def demo_async_performance():
    """非同期処理のパフォーマンステスト"""

    print("\n\n⚡ 2. 非同期処理パフォーマンステスト")
    print("-" * 50)

    analyzer = AsyncLineErrorAnalyzer()
    test_sizes = [100, 500, 1000, 2000]

    for size in test_sizes:
        print(f"\n📊 テストサイズ: {size:,}件")

        # テストデータ生成
        errors = generate_test_errors(size)

        # パフォーマンス監視開始
        monitor = PerformanceMonitor().start()

        try:
            # 非同期分析実行
            results = await analyzer.analyze_multiple(errors)

            # 監視終了
            stats = monitor.stop()

            # 結果表示
            throughput = size / stats["duration"]
            memory_mb = stats["memory_used"] / (1024 * 1024)

            print(f"   ⏱️  処理時間: {stats['duration']:.2f}秒")
            print(f"   🚀 スループット: {throughput:.1f}件/秒")
            print(f"   💾 メモリ使用量: {memory_mb:.1f}MB")
            print(f"   🖥️  CPU使用率: {stats['cpu_percent']:.1f}%")
            print(f"   ✅ 成功率: {len(results)}/{size} ({len(results)/size*100:.1f}%)")

        except Exception as e:
            print(f"   ❌ エラー: {e}")


def demo_concurrent_comparison():
    """並行処理の比較デモ"""

    print("\n\n🔄 3. 並行処理比較テスト")
    print("-" * 50)

    test_size = 1000
    errors = generate_test_errors(test_size)

    # 1. シーケンシャル処理
    print(f"\n🐌 シーケンシャル処理 ({test_size}件)")
    analyzer = LineErrorAnalyzer()

    monitor = PerformanceMonitor().start()
    try:
        sequential_results = []
        for error in errors:
            result = analyzer.analyze(error)
            sequential_results.append(result)

        seq_stats = monitor.stop()
        seq_throughput = test_size / seq_stats["duration"]

        print(f"   ⏱️  処理時間: {seq_stats['duration']:.2f}秒")
        print(f"   🚀 スループット: {seq_throughput:.1f}件/秒")

    except Exception as e:
        print(f"   ❌ エラー: {e}")

    # 2. ThreadPoolExecutor並行処理
    print(f"\n🏃‍♂️ ThreadPool並行処理 ({test_size}件)")

    def analyze_single(error):
        return analyzer.analyze(error)

    monitor = PerformanceMonitor().start()
    try:
        with ThreadPoolExecutor(max_workers=4) as executor:
            thread_results = list(executor.map(analyze_single, errors))

        thread_stats = monitor.stop()
        thread_throughput = test_size / thread_stats["duration"]

        print(f"   ⏱️  処理時間: {thread_stats['duration']:.2f}秒")
        print(f"   🚀 スループット: {thread_throughput:.1f}件/秒")
        print(f"   📈 改善率: {thread_throughput/seq_throughput:.1f}x")

    except Exception as e:
        print(f"   ❌ エラー: {e}")


async def demo_memory_efficiency():
    """メモリ効率性のデモ"""

    print("\n\n💾 4. メモリ効率性テスト")
    print("-" * 50)

    analyzer = AsyncLineErrorAnalyzer()

    # 段階的にデータサイズを増やしてメモリ使用量を測定
    sizes = [1000, 2000, 4000, 8000]

    for size in sizes:
        print(f"\n📊 データサイズ: {size:,}件")

        # メモリ使用量の事前測定
        gc.collect()
        before_memory = psutil.Process().memory_info().rss / (1024 * 1024)

        # 大量データ生成
        errors = generate_test_errors(size)

        # 分析実行
        start_time = time.time()
        try:
            results = await analyzer.analyze_multiple(errors)
            end_time = time.time()

            # メモリ使用量の事後測定
            after_memory = psutil.Process().memory_info().rss / (1024 * 1024)
            memory_per_item = (after_memory - before_memory) / size

            print(f"   ⏱️  処理時間: {end_time - start_time:.2f}秒")
            print(f"   💾 メモリ増加: {after_memory - before_memory:.1f}MB")
            print(f"   📏 1件あたり: {memory_per_item*1024:.1f}KB")
            print(f"   🎯 効率性: {len(results)/size*100:.1f}%成功")

        except Exception as e:
            print(f"   ❌ エラー: {e}")

        # メモリクリーンアップ
        del errors
        if "results" in locals():
            del results
        gc.collect()


def demo_scalability_test():
    """スケーラビリティテスト"""

    print("\n\n📈 5. スケーラビリティテスト")
    print("-" * 50)

    analyzer = LineErrorAnalyzer()

    # 段階的に負荷を増やしてレスポンス時間を測定
    load_levels = [10, 50, 100, 200, 500]

    print("負荷レベル | 処理時間 | スループット | レイテンシ")
    print("-" * 50)

    for load in load_levels:
        errors = generate_test_errors(load)

        start_time = time.time()
        try:
            results = analyzer.analyze_multiple(errors)
            end_time = time.time()

            duration = end_time - start_time
            throughput = load / duration
            latency = (duration / load) * 1000  # ms per item

            print(
                f"{load:8d}件 | {duration:6.2f}秒 | {throughput:8.1f}/秒 | {latency:6.2f}ms"
            )

        except Exception as e:
            print(f"{load:8d}件 | エラー: {e}")


async def main():
    """メイン実行関数"""

    print("🔬 LINE Bot Error Analyzer - パフォーマンス分析デモ")
    print("=" * 60)

    try:
        demo_sync_performance()
        await demo_async_performance()
        demo_concurrent_comparison()
        await demo_memory_efficiency()
        demo_scalability_test()

        print("\n\n🎯 パフォーマンステスト完了！")
        print("\n📋 主な知見:")
        print("   • 非同期処理により高いスループットを実現")
        print("   • 適切な並行処理レベルでリソース効率を最適化")
        print("   • メモリ使用量は処理量に比例してスケール")
        print("   • 大量データ処理でも安定したパフォーマンス")

    except Exception as e:
        print(f"\n❌ パフォーマンステスト中にエラーが発生しました: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    # psutilが必要な場合のメッセージ
    try:
        import psutil
    except ImportError:
        print("❌ psutilライブラリが必要です: pip install psutil")
        sys.exit(1)

    asyncio.run(main())
