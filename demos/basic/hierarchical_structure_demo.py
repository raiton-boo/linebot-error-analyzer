"""
階層構造エラーデータベースの基本デモ

このデモでは以下を実演します：
1. エンドポイント指定によるエラー分析
2. 階層構造での詳細情報取得
3. カテゴリ別のエラー処理例

エンドポイント指定例:
- "message.message_push" → メッセージカテゴリのプッシュメッセージ
- "audience.audience_create" → オーディエンスカテゴリの作成操作
- "rich_menu.rich_menu_image" → リッチメニューカテゴリの画像アップロード
"""

import sys
import os

# プロジェクトルートを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from linebot_error_analyzer.database.error_database import ErrorDatabase
from linebot_error_analyzer.models import ErrorCategory


def demonstrate_hierarchical_structure():
    """階層構造の使用例を示すデモ関数"""

    print("🔍 LINE Bot Error Analyzer - 階層構造デモ")
    print("=" * 60)

    # データベースインスタンス作成
    db = ErrorDatabase()

    # 階層構造でのエラー分析例
    hierarchical_examples = [
        # メッセージ関連のエラー
        ("message.message_push", 400, "プッシュメッセージ送信エラー"),
        ("message.message_reply", 404, "応答メッセージ送信エラー"),
        ("message.message_narrowcast", 403, "ナローキャスト送信権限エラー"),
        # オーディエンス関連のエラー
        ("audience.audience_create", 400, "オーディエンス作成エラー"),
        ("audience.audience_get", 404, "オーディエンス取得エラー"),
        # リッチメニュー関連のエラー
        ("rich_menu.rich_menu_image", 413, "リッチメニュー画像サイズエラー"),
        ("rich_menu.rich_menu_link", 400, "リッチメニュー設定エラー"),
        # Webhook関連のエラー
        ("webhook.webhook_settings", 400, "Webhook設定エラー"),
        # 分析関連のエラー
        ("insights.insights_demographic", 403, "人口統計取得権限エラー"),
    ]

    for i, (endpoint, status_code, description) in enumerate(hierarchical_examples, 1):
        print(f"\n📋 例 {i}: {description}")
        print(f"   エンドポイント: {endpoint}")
        print(f"   HTTPステータス: {status_code}")

        # エラー分析実行
        try:
            category, severity, retryable = db.analyze_error(
                status_code=status_code, message="", endpoint=endpoint
            )

            retry_emoji = "🔄" if retryable else "❌"

            print(f"   ✅ エラーカテゴリ: {category.value}")
            print(f"   重要度: {severity.value}")
            print(f"   {retry_emoji} リトライ可能: {'はい' if retryable else 'いいえ'}")

            # 詳細情報取得
            details = db.get_endpoint_error_details(endpoint, status_code)
            if details:
                print(f"   💡 対処法: {details['action']}")
                print(f"   📚 ドキュメント: {details['doc_url']}")

        except Exception as e:
            print(f"   ❌ エラー分析失敗: {e}")

        if i < len(hierarchical_examples):
            print("   " + "-" * 50)

    print(f"\n✨ デモ完了！{len(hierarchical_examples)}件のエラーを分析しました。")


def demonstrate_category_filtering():
    """カテゴリ別フィルタリングのデモ"""

    print("\n\n🎯 カテゴリ別フィルタリングデモ")
    print("=" * 60)

    db = ErrorDatabase()

    # さまざまなエラーを分析
    errors = [
        (401, "Invalid channel access token"),
        (400, "Invalid JSON format"),
        (403, "Insufficient permissions"),
        (500, "Internal server error"),
        (429, "Rate limit exceeded"),
    ]

    results = []
    for status_code, message in errors:
        category, severity, retryable = db.analyze_error(status_code, message)
        results.append(
            {
                "status": status_code,
                "message": message,
                "category": category,
                "severity": severity,
                "retryable": retryable,
            }
        )

    # カテゴリ別にグループ化
    categories = {}
    for result in results:
        cat = result["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(result)

    # カテゴリ別に表示
    for category, errors in categories.items():
        print(f"\n📂 {category.value} カテゴリ:")
        for error in errors:
            retry_text = "リトライ可能" if error["retryable"] else "リトライ不可"
            print(f"   • {error['status']}: {error['message']} ({retry_text})")


if __name__ == "__main__":
    try:
        demonstrate_hierarchical_structure()
        demonstrate_category_filtering()

        print(f"\n🎉 すべてのデモが正常に完了しました！")
        print("📖 他のデモも試してみてください：")
        print("   - demos/basic/simple_analysis_demo.py")
        print("   - demos/advanced/async_demo.py")
        print("   - demos/integration/fastapi_demo.py")

    except Exception as e:
        print(f"\n❌ デモ実行中にエラーが発生しました: {e}")
        sys.exit(1)
