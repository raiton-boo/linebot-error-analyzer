"""
LINE Bot Error Analyzer - 非同期処理デモ

このデモでは以下の高度な機能を実演します：
1. 非同期エラー分析
2. 並行処理でのバッチ分析
3. 大量データの効率的な処理
4. エラーハンドリングとリトライ機構
"""

import sys
import os
import asyncio
import time
from typing import List, Dict, Any

# プロジェクトルートを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from line_bot_error_analyzer import AsyncLineErrorAnalyzer
from line_bot_error_analyzer.core.models import ErrorCategory, ErrorSeverity


async def demo_async_basic():
    """基本的な非同期分析デモ"""

    print("⚡ 1. 基本的な非同期分析")
    print("-" * 40)

    analyzer = AsyncLineErrorAnalyzer()

    # 非同期で分析するエラー例
    async_errors = [
        {"status_code": 401, "message": "Token expired"},
        {"status_code": 429, "message": "Rate limit exceeded"},
        {"status_code": 500, "message": "Service unavailable"},
    ]

    for i, error in enumerate(async_errors, 1):
        print(f"\n例 {i}: 非同期分析 - {error['message']}")

        start_time = time.time()
        try:
            result = await analyzer.analyze(error)
            end_time = time.time()

            print(f"   ✅ 結果: {result.category.value}")
            print(f"   ⏱️  処理時間: {(end_time - start_time)*1000:.2f}ms")
            print(f"   🔄 リトライ可能: {'はい' if result.is_retryable else 'いいえ'}")

        except Exception as e:
            print(f"   ❌ エラー: {e}")


async def demo_concurrent_analysis():
    """並行処理でのバッチ分析デモ"""

    print("\n\n🚀 2. 並行バッチ分析")
    print("-" * 40)

    analyzer = AsyncLineErrorAnalyzer()

    # 大量のエラーデータを生成
    concurrent_errors = []
    error_templates = [
        {"status_code": 400, "message": "Bad request #{i}"},
        {"status_code": 401, "message": "Unauthorized access #{i}"},
        {"status_code": 403, "message": "Forbidden operation #{i}"},
        {"status_code": 404, "message": "Resource not found #{i}"},
        {"status_code": 429, "message": "Rate limited #{i}"},
        {"status_code": 500, "message": "Server error #{i}"},
    ]

    # 各テンプレートから複数のエラーを生成
    for i in range(10):
        for template in error_templates:
            error = template.copy()
            error["message"] = template["message"].format(i=i + 1)
            error["request_id"] = f"req-{i+1}-{template['status_code']}"
            concurrent_errors.append(error)

    print(f"📦 {len(concurrent_errors)}件のエラーを並行分析中...")

    start_time = time.time()
    try:
        # 並行処理で分析実行
        results = await analyzer.analyze_multiple(concurrent_errors)
        end_time = time.time()

        # 統計情報を計算
        total_time = end_time - start_time
        per_item_time = (total_time / len(results)) * 1000

        print(f"⏱️  総処理時間: {total_time:.2f}秒")
        print(f"📊 1件あたり平均: {per_item_time:.2f}ms")
        print(f"🎯 処理レート: {len(results)/total_time:.1f}件/秒")

        # カテゴリ別統計
        category_stats = {}
        severity_stats = {}

        for result in results:
            cat = result.category.value
            category_stats[cat] = category_stats.get(cat, 0) + 1

            sev = result.severity.value
            severity_stats[sev] = severity_stats.get(sev, 0) + 1

        print(f"\n📈 分析結果統計:")
        print(f"   カテゴリ別分布:")
        for category, count in sorted(category_stats.items()):
            percentage = (count / len(results)) * 100
            print(f"     • {category}: {count}件 ({percentage:.1f}%)")

    except Exception as e:
        print(f"   ❌ 並行分析エラー: {e}")


async def demo_error_handling_with_retry():
    """エラーハンドリングとリトライのデモ"""

    print("\n\n🔧 3. エラーハンドリング & リトライ")
    print("-" * 40)

    analyzer = AsyncLineErrorAnalyzer()

    # リトライが必要になりそうなエラー例
    retry_errors = [
        {
            "status_code": 429,
            "message": "Rate limit exceeded",
            "headers": {"Retry-After": "5"},
        },
        {"status_code": 503, "message": "Service temporarily unavailable"},
        {"status_code": 502, "message": "Bad gateway"},
        {"status_code": 504, "message": "Gateway timeout"},
    ]

    async def analyze_with_retry(error: Dict[str, Any], max_retries: int = 3) -> None:
        """リトライ機能付きの分析関数"""

        for attempt in range(max_retries + 1):
            try:
                print(f"   🔄 試行 {attempt + 1}/{max_retries + 1}: {error['message']}")

                result = await analyzer.analyze(error)

                print(f"   ✅ 成功: {result.category.value}")

                if result.is_retryable and result.retry_after:
                    print(f"   ⏰ リトライ推奨間隔: {result.retry_after}秒")

                return  # 成功したら終了

            except Exception as e:
                if attempt < max_retries:
                    wait_time = 2**attempt  # 指数バックオフ
                    print(f"   ⚠️  失敗 (試行{attempt + 1}): {e}")
                    print(f"   ⏳ {wait_time}秒待機してリトライ...")
                    await asyncio.sleep(wait_time)
                else:
                    print(f"   ❌ 最終的に失敗: {e}")

    # 各エラーをリトライ機能付きで分析
    for i, error in enumerate(retry_errors, 1):
        print(f"\n例 {i}: {error['message']}")
        await analyze_with_retry(error)


async def demo_streaming_analysis():
    """ストリーミング分析デモ"""

    print("\n\n🌊 4. ストリーミング分析")
    print("-" * 40)

    analyzer = AsyncLineErrorAnalyzer()

    async def generate_error_stream():
        """エラーストリームを生成するジェネレータ"""
        error_patterns = [
            {"status_code": 400, "message": "Invalid parameter"},
            {"status_code": 401, "message": "Authentication failed"},
            {"status_code": 500, "message": "Internal error"},
        ]

        for i in range(15):
            pattern = error_patterns[i % len(error_patterns)]
            error = pattern.copy()
            error["message"] = f"{pattern['message']} #{i+1}"
            error["timestamp"] = time.time()

            yield error
            await asyncio.sleep(0.1)  # ストリーミングの間隔

    print("🔄 リアルタイムエラーストリーム分析開始...")

    processed_count = 0
    start_time = time.time()

    try:
        async for error in generate_error_stream():
            result = await analyzer.analyze(error)
            processed_count += 1

            # リアルタイム表示
            elapsed = time.time() - start_time
            rate = processed_count / elapsed if elapsed > 0 else 0

            print(
                f"   📊 {processed_count:2d}: {result.category.value:15s} "
                f"| レート: {rate:.1f}/秒 | {error['message']}"
            )

    except Exception as e:
        print(f"   ❌ ストリーミング分析エラー: {e}")

    total_time = time.time() - start_time
    final_rate = processed_count / total_time if total_time > 0 else 0
    print(
        f"\n📈 ストリーミング完了: {processed_count}件を{total_time:.2f}秒で処理 "
        f"(平均 {final_rate:.1f}件/秒)"
    )


async def main():
    """メイン実行関数"""

    print("⚡ LINE Bot Error Analyzer - 非同期処理デモ")
    print("=" * 60)

    try:
        await demo_async_basic()
        await demo_concurrent_analysis()
        await demo_error_handling_with_retry()
        await demo_streaming_analysis()

        print("\n\n🎉 全ての非同期デモが完了しました！")
        print("\n🚀 パフォーマンスのポイント:")
        print("   • 非同期処理により高いスループットを実現")
        print("   • 並行処理で大量データを効率的に処理")
        print("   • 適切なエラーハンドリングとリトライ機構")
        print("   • リアルタイムストリーミング分析対応")

    except Exception as e:
        print(f"\n❌ デモ実行中にエラーが発生しました: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    # Python 3.7+のasyncio.run()を使用
    asyncio.run(main())
