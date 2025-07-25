"""
LINE Bot ユーザー管理 - 実用パターン

実際のLINE Bot SDK使用時のユーザー関連APIでのエラーハンドリングパターンです。

注意：このファイル内のerror辞書は、実際のLINE APIで発生する可能性のあるエラーパターンを
示すためのサンプルです。実際のAPIエラーは`e`オブジェクトから取得されます。
"""

import os
import sys
from linebot.v3.messaging import AsyncApiClient, AsyncMessagingApi, Configuration
from linebot.v3.exceptions import InvalidSignatureError
from line_bot_error_analyzer import LineErrorAnalyzer


# 設定とエラーハンドリング
analyzer = LineErrorAnalyzer()

# 環境変数の取得とエラーハンドリング
channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", None)

if channel_access_token is None:
    error = {
        "status_code": 500,
        "message": "Missing LINE_CHANNEL_ACCESS_TOKEN",
        "endpoint": "config",
    }
    analysis = analyzer.analyze(error)
    print(f"❌ 設定エラー: {analysis.recommended_action}")
    sys.exit(1)

# LINE Bot API設定
configuration = Configuration(access_token=channel_access_token)
async_api_client = AsyncApiClient(configuration)
line_bot_api = AsyncMessagingApi(async_api_client)


async def get_user_profile(user_id: str):
    """ユーザープロフィールの取得"""

    try:
        profile = await line_bot_api.get_profile(user_id=user_id)
        print(f"✅ プロフィール取得成功: {profile.display_name}")
        return {
            "success": True,
            "profile": {
                "user_id": profile.user_id,
                "display_name": profile.display_name,
                "picture_url": profile.picture_url,
                "status_message": profile.status_message,
            },
        }

    except Exception as e:
        status = getattr(e, "status", None)

        if status == 403:
            # 実際のLINE APIで発生する可能性のあるエラーパターン
            error = {
                "status_code": 403,
                "message": "User privacy settings",
                "endpoint": "profile",
            }
            analysis = analyzer.analyze(error)
            print(f"❌ プライバシー設定エラー: {analysis.recommended_action}")
        elif status == 404:
            # 実際のLINE APIで発生する可能性のあるエラーパターン
            error = {
                "status_code": 404,
                "message": "User not found",
                "endpoint": "profile",
            }
            analysis = analyzer.analyze(error)
            print(f"❌ ユーザー未発見: {analysis.recommended_action}")
        else:
            # その他の予期しないエラー
            error = {
                "status_code": status or 500,
                "message": f"Profile error: {str(e)}",
                "endpoint": "profile",
            }
            analysis = analyzer.analyze(error)
            print(f"❌ プロフィール取得エラー: {analysis.recommended_action}")

        return {"error": str(e), "status": status}


async def get_group_member_profile(group_id: str, user_id: str):
    """グループメンバーのプロフィール取得"""

    try:
        profile = await line_bot_api.get_group_member_profile(
            group_id=group_id, user_id=user_id
        )
        print(f"✅ グループメンバープロフィール取得成功: {profile.display_name}")
        return {
            "success": True,
            "profile": {
                "user_id": profile.user_id,
                "display_name": profile.display_name,
                "picture_url": profile.picture_url,
            },
        }

    except Exception as e:
        status = getattr(e, "status", None)

        if status == 403:
            # 実際のLINE APIで発生する可能性のあるエラーパターン
            error = {
                "status_code": 403,
                "message": "Group access denied",
                "endpoint": "group.member",
            }
            analysis = analyzer.analyze(error)
            print(f"❌ グループアクセス拒否: {analysis.recommended_action}")
        elif status == 404:
            # 実際のLINE APIで発生する可能性のあるエラーパターン
            error = {
                "status_code": 404,
                "message": "User not in group",
                "endpoint": "group.member",
            }
            analysis = analyzer.analyze(error)
            print(f"❌ ユーザーがグループにいません: {analysis.recommended_action}")
        else:
            # その他の予期しないエラー
            error = {
                "status_code": status or 500,
                "message": f"Group member error: {str(e)}",
                "endpoint": "group.member",
            }
            analysis = analyzer.analyze(error)
            print(f"❌ グループメンバー取得エラー: {analysis.recommended_action}")

        return {"error": str(e), "status": status}


async def get_room_member_profile(room_id: str, user_id: str):
    """ルームメンバーのプロフィール取得"""

    try:
        profile = await line_bot_api.get_room_member_profile(
            room_id=room_id, user_id=user_id
        )
        print(f"✅ ルームメンバープロフィール取得成功: {profile.display_name}")
        return {
            "success": True,
            "profile": {
                "user_id": profile.user_id,
                "display_name": profile.display_name,
                "picture_url": profile.picture_url,
            },
        }

    except Exception as e:
        status = getattr(e, "status", None)

        if status == 404:
            # 実際のLINE APIで発生する可能性のあるエラーパターン
            error = {
                "status_code": 404,
                "message": "User not in room",
                "endpoint": "room.member",
            }
            analysis = analyzer.analyze(error)
            print(f"❌ ユーザーがルームにいません: {analysis.recommended_action}")
        else:
            # その他の予期しないエラー
            error = {
                "status_code": status or 500,
                "message": f"Room member error: {str(e)}",
                "endpoint": "room.member",
            }
            analysis = analyzer.analyze(error)
            print(f"❌ ルームメンバー取得エラー: {analysis.recommended_action}")

        return {"error": str(e), "status": status}


async def get_followers_count(date: str = None):
    """フォロワー数の取得"""

    try:
        if date:
            # 特定の日付のフォロワー数
            insight = await line_bot_api.get_followers_demographics(date=date)
        else:
            # 最新のフォロワー数
            insight = await line_bot_api.get_followers_demographics()

        print(f"✅ フォロワー数取得成功: {insight.followers}人")
        return {
            "success": True,
            "followers": insight.followers,
            "targeted_reaches": insight.targeted_reaches,
            "blocks": insight.blocks,
        }

    except Exception as e:
        status = getattr(e, "status", None)

        if status == 403:
            # 実際のLINE APIで発生する可能性のあるエラーパターン
            error = {
                "status_code": 403,
                "message": "Statistics not available",
                "endpoint": "insight",
            }
            analysis = analyzer.analyze(error)
            print(f"❌ 統計データアクセス拒否: {analysis.recommended_action}")
        elif status == 400:
            # 実際のLINE APIで発生する可能性のあるエラーパターン
            error = {
                "status_code": 400,
                "message": "Invalid date format",
                "endpoint": "insight",
            }
            analysis = analyzer.analyze(error)
            print(f"❌ 日付フォーマットエラー: {analysis.recommended_action}")
        else:
            # その他の予期しないエラー
            error = {
                "status_code": status or 500,
                "message": f"Followers error: {str(e)}",
                "endpoint": "insight",
            }
            analysis = analyzer.analyze(error)
            print(f"❌ フォロワー数取得エラー: {analysis.recommended_action}")

        return {"error": str(e), "status": status}


# 使用例
async def example_usage():
    """使用例の実行"""

    print("👤 ユーザー管理の例:")

    # テスト用のID（実際の値に置き換えてください）
    test_user_id = "U1234567890123456789012345678901234567890123456789"
    test_group_id = "C1234567890123456789012345678901234567890123456789"
    test_room_id = "R1234567890123456789012345678901234567890123456789"

    # ユーザープロフィール取得
    await get_user_profile(test_user_id)

    # グループメンバープロフィール取得
    await get_group_member_profile(test_group_id, test_user_id)

    # ルームメンバープロフィール取得
    await get_room_member_profile(test_room_id, test_user_id)

    # フォロワー数取得
    await get_followers_count()

    # 特定日のフォロワー数取得
    await get_followers_count("20240101")


if __name__ == "__main__":
    import asyncio

    print("👤 LINE Bot ユーザー管理 - 実用パターン")
    print("=" * 50)

    # 例の実行
    asyncio.run(example_usage())
