"""
LINE Bot Error Analyzer - 基本的な使用例デモ

このデモでは以下の基本機能を実演します：
1. 辞書形式エラーの分析
2. SDK例外の分析シミュレーション
3. 複数エラーの一括分析
4. エラー情報の出力形式
"""

import sys
import os

# プロジェクトルートを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from linebot_error_analyzer import LineErrorAnalyzer
from linebot_error_analyzer.models import ErrorCategory


def demo_dict_analysis():
    """辞書形式エラーの分析デモ"""

    print("📋 1. 辞書形式エラーの分析")
    print("-" * 40)

    analyzer = LineErrorAnalyzer()

    # 様々な辞書形式エラーの例
    dict_errors = [
        {
            "status_code": 401,
            "message": "Invalid channel access token",
            "headers": {"Content-Type": "application/json"},
            "request_id": "demo-request-001",
        },
        {
            "status_code": 400,
            "message": "Required field missing: replyToken",
            "error_code": "40001",
        },
        {
            "status_code": 429,
            "message": "Rate limit exceeded",
            "headers": {"Retry-After": "60"},
        },
        {"status_code": 500, "message": "Internal server error"},
    ]

    for i, error in enumerate(dict_errors, 1):
        print(f"\n例 {i}: {error.get('message', 'Unknown error')}")

        try:
            result = analyzer.analyze(error)

            print(f"   ステータス: {result.status_code}")
            print(f"   カテゴリ: {result.category.value}")
            print(f"   重要度: {result.severity.value}")
            print(f"   リトライ可能: {'はい' if result.is_retryable else 'いいえ'}")
            print(f"   対処法: {result.recommended_action}")

            if result.retry_after:
                print(f"   リトライ間隔: {result.retry_after}秒")

        except Exception as e:
            print(f"   ❌ 分析エラー: {e}")


def demo_mock_sdk_errors():
    """SDK例外の分析シミュレーションデモ"""

    print("\n\n🔧 2. SDK例外シミュレーション")
    print("-" * 40)

    analyzer = LineErrorAnalyzer()

    # SDK例外をシミュレートする辞書
    sdk_like_errors = [
        {
            "status_code": 403,
            "message": "Forbidden",
            "headers": {"Content-Type": "application/json"},
            "text": '{"message": "Insufficient permissions for this resource"}',
        },
        {
            "status_code": 404,
            "message": "Not Found",
            "headers": {"Content-Type": "application/json"},
            "text": '{"message": "User not found"}',
        },
    ]

    for i, error in enumerate(sdk_like_errors, 1):
        print(f"\n例 {i}: SDK風エラー - {error['message']}")

        try:
            result = analyzer.analyze(error)

            print(f"   解析結果:")
            print(f"     • カテゴリ: {result.category.value}")
            print(f"     • 説明: {result.description}")
            print(f"     • ドキュメント: {result.documentation_url}")

        except Exception as e:
            print(f"   ❌ 分析エラー: {e}")


def demo_batch_analysis():
    """複数エラーの一括分析デモ"""

    print("\n\n📊 3. 複数エラーの一括分析")
    print("-" * 40)

    analyzer = LineErrorAnalyzer()

    # 開発中によく遭遇するエラーセット
    batch_errors = [
        {"status_code": 401, "message": "Invalid channel access token"},
        {"status_code": 400, "message": "Invalid JSON format"},
        {"status_code": 403, "message": "Insufficient permissions"},
        {"status_code": 429, "message": "Rate limit exceeded"},
        {"status_code": 500, "message": "Internal server error"},
        {"status_code": 502, "message": "Bad gateway"},
    ]

    print(f"📦 {len(batch_errors)}件のエラーを一括分析中...")

    try:
        results = analyzer.analyze_multiple(batch_errors)

        # 統計情報
        categories = {}
        severities = {}
        retryable_count = 0

        for result in results:
            # カテゴリ統計
            cat = result.category.value
            categories[cat] = categories.get(cat, 0) + 1

            # 重要度統計
            sev = result.severity.value
            severities[sev] = severities.get(sev, 0) + 1

            # リトライ可能統計
            if result.is_retryable:
                retryable_count += 1

        print(f"\n📈 分析統計:")
        print(f"   • 総エラー数: {len(results)}")
        print(f"   • リトライ可能: {retryable_count}/{len(results)}")

        print(f"\n📂 カテゴリ別分布:")
        for category, count in categories.items():
            print(f"   • {category}: {count}件")

        print(f"\n🚨 重要度別分布:")
        for severity, count in severities.items():
            print(f"   • {severity}: {count}件")

    except Exception as e:
        print(f"   ❌ 一括分析エラー: {e}")


def demo_output_formats():
    """出力形式のデモ"""

    print("\n\n📄 4. 出力形式の例")
    print("-" * 40)

    analyzer = LineErrorAnalyzer()

    error = {
        "status_code": 400,
        "message": "Invalid reply token",
        "request_id": "demo-request-999",
    }

    try:
        result = analyzer.analyze(error)

        print("\n🔤 文字列表現:")
        print(f"   {str(result)}")

        print("\n📋 辞書形式:")
        result_dict = result.to_dict()
        for key, value in result_dict.items():
            if key not in ["error_data", "raw_error"]:  # 長い内容は省略
                print(f"   {key}: {value}")

        print("\n🌐 JSON形式 (一部):")
        import json

        json_str = result.to_json()
        json_data = json.loads(json_str)
        # 重要な情報のみ表示
        important_keys = [
            "status_code",
            "category",
            "severity",
            "is_retryable",
            "message",
        ]
        for key in important_keys:
            if key in json_data:
                print(f"   {key}: {json.dumps(json_data[key], ensure_ascii=False)}")

    except Exception as e:
        print(f"   ❌ 出力フォーマットエラー: {e}")


if __name__ == "__main__":
    try:
        print("🚀 LINE Bot Error Analyzer - 基本デモ開始")
        print("=" * 60)

        demo_dict_analysis()
        demo_mock_sdk_errors()
        demo_batch_analysis()
        demo_output_formats()

        print("\n\n✅ 全ての基本デモが完了しました！")
        print("\n📚 次のステップ:")
        print("   • demos/advanced/async_demo.py - 非同期処理のデモ")
        print("   • demos/integration/ - 実際のアプリケーション統合例")
        print("   • examples/ - より実践的な使用例")

    except Exception as e:
        print(f"\n❌ デモ実行中にエラーが発生しました: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
