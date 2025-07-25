"""
階層構造エラーデータベースの使用例

エンドポイント指定例:
- "message.message_push" → メッセージカテゴリのプッシュメッセージ
- "audience.audience_create" → オーディエンスカテゴリの作成操作
- "rich_menu.rich_menu_image" → リッチメニューカテゴリの画像アップロード
"""

from linebot_error_analyzer.database.error_database import ErrorDatabase


def demonstrate_hierarchical_structure():
    """階層構造の使用例を示すデモ関数"""

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

    print("=== 階層構造エラー分析デモ ===\n")

    for endpoint, status_code, description in hierarchical_examples:
        print(f"エンドポイント: {endpoint}")
        print(f"HTTPステータス: {status_code}")
        print(f"説明: {description}")

        # エラー分析実行
        try:
            category, severity, retryable = db.analyze_error(
                status_code=status_code, message="", endpoint=endpoint
            )

            print(f"エラーカテゴリ: {category}")
            print(f"重要度: {severity}")
            print(f"リトライ可能: {retryable}")

            # 詳細情報取得
            details = db.get_endpoint_error_details(endpoint, status_code)
            if details:
                print(f"対処法: {details['action']}")
                print(f"ドキュメント: {details['doc_url']}")

        except Exception as e:
            print(f"エラー分析失敗: {e}")

        print("-" * 50)


if __name__ == "__main__":
    demonstrate_hierarchical_structure()
