"""
LINE Bot グループ管理 - 実用パターン

実際のLINE Bot SDK使用時のグループ関連APIでのエラーハンドリングパターンです。

注意：このファイル内のerror辞書は、実際のLINE APIで発生する可能性のあるエラーパターンを
示すためのサンプルです。実際のAPIエラーは`e`オブジェクトから取得されます。
"""

import os
import sys
from linebot.v3.messaging import AsyncApiClient, AsyncMessagingApi, Configuration
from linebot.v3.exceptions import InvalidSignatureError
from linebot_error_analyzer import LineErrorAnalyzer


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


async def get_group_summary(group_id: str):
    """グループ情報の取得"""

    try:
        group_summary = await line_bot_api.get_group_summary(group_id=group_id)
        print(f"✅ グループ情報取得成功: {group_summary.group_name}")
        return {
            "success": True,
            "group": {
                "group_id": group_summary.group_id,
                "group_name": group_summary.group_name,
                "picture_url": group_summary.picture_url,
            },
        }

    except Exception as e:
        status = getattr(e, "status", None)

        if status == 403:
            # 実際のLINE APIで発生する可能性のあるエラーパターン
            error = {
                "status_code": 403,
                "message": "Group access denied",
                "endpoint": "group",
            }
            analysis = analyzer.analyze(error)
            print(f"❌ グループアクセス拒否: {analysis.recommended_action}")
        elif status == 404:
            # 実際のLINE APIで発生する可能性のあるエラーパターン
            error = {
                "status_code": 404,
                "message": "Group not found",
                "endpoint": "group",
            }
            analysis = analyzer.analyze(error)
            print(f"❌ グループが見つかりません: {analysis.recommended_action}")
        else:
            # その他の予期しないエラー
            error = {
                "status_code": status or 500,
                "message": f"Group error: {str(e)}",
                "endpoint": "group",
            }
            analysis = analyzer.analyze(error)
            print(f"❌ グループ情報取得エラー: {analysis.recommended_action}")

        return {"error": str(e), "status": status}


async def get_group_members_count(group_id: str):
    """グループメンバー数の取得"""

    try:
        members_count = await line_bot_api.get_group_members_count(group_id=group_id)
        print(f"✅ グループメンバー数取得成功: {members_count.count}人")
        return {"success": True, "count": members_count.count}

    except Exception as e:
        status = getattr(e, "status", None)

        if status == 403:
            error = {
                "status_code": 403,
                "message": "Group member count access denied",
                "endpoint": "group.members.count",
            }
            analysis = analyzer.analyze(error)
            print(f"❌ グループメンバー数アクセス拒否: {analysis.recommended_action}")
        elif status == 404:
            error = {
                "status_code": 404,
                "message": "Group not found",
                "endpoint": "group.members.count",
            }
            analysis = analyzer.analyze(error)
            print(f"❌ グループが見つかりません: {analysis.recommended_action}")
        else:
            error = {
                "status_code": status or 500,
                "message": f"Members count error: {str(e)}",
                "endpoint": "group.members.count",
            }
            analysis = analyzer.analyze(error)
            print(f"❌ グループメンバー数取得エラー: {analysis.recommended_action}")

        return {"error": str(e), "status": status}


async def get_room_members_count(room_id: str):
    """ルームメンバー数の取得"""

    try:
        members_count = await line_bot_api.get_room_members_count(room_id=room_id)
        print(f"✅ ルームメンバー数取得成功: {members_count.count}人")
        return {"success": True, "count": members_count.count}

    except Exception as e:
        status = getattr(e, "status", None)

        if status == 403:
            error = {
                "status_code": 403,
                "message": "Room member count access denied",
                "endpoint": "room.members.count",
            }
            analysis = analyzer.analyze(error)
            print(f"❌ ルームメンバー数アクセス拒否: {analysis.recommended_action}")
        elif status == 404:
            error = {
                "status_code": 404,
                "message": "Room not found",
                "endpoint": "room.members.count",
            }
            analysis = analyzer.analyze(error)
            print(f"❌ ルームが見つかりません: {analysis.recommended_action}")
        else:
            error = {
                "status_code": status or 500,
                "message": f"Room members count error: {str(e)}",
                "endpoint": "room.members.count",
            }
            analysis = analyzer.analyze(error)
            print(f"❌ ルームメンバー数取得エラー: {analysis.recommended_action}")

        return {"error": str(e), "status": status}


async def leave_group(group_id: str):
    """グループからの退出"""

    try:
        await line_bot_api.leave_group(group_id=group_id)
        print(f"✅ グループ退出成功: {group_id}")
        return {"success": True}

    except Exception as e:
        status = getattr(e, "status", None)

        if status == 403:
            error = {
                "status_code": 403,
                "message": "Cannot leave group",
                "endpoint": "group.leave",
            }
            analysis = analyzer.analyze(error)
            print(f"❌ グループ退出権限なし: {analysis.recommended_action}")
        elif status == 404:
            error = {
                "status_code": 404,
                "message": "Group not found",
                "endpoint": "group.leave",
            }
            analysis = analyzer.analyze(error)
            print(f"❌ グループが見つかりません: {analysis.recommended_action}")
        else:
            error = {
                "status_code": status or 500,
                "message": f"Leave group error: {str(e)}",
                "endpoint": "group.leave",
            }
            analysis = analyzer.analyze(error)
            print(f"❌ グループ退出エラー: {analysis.recommended_action}")

        return {"error": str(e), "status": status}


async def leave_room(room_id: str):
    """ルームからの退出"""

    try:
        await line_bot_api.leave_room(room_id=room_id)
        print(f"✅ ルーム退出成功: {room_id}")
        return {"success": True}

    except Exception as e:
        status = getattr(e, "status", None)

        if status == 403:
            error = {
                "status_code": 403,
                "message": "Cannot leave room",
                "endpoint": "room.leave",
            }
            analysis = analyzer.analyze(error)
            print(f"❌ ルーム退出権限なし: {analysis.recommended_action}")
        elif status == 404:
            error = {
                "status_code": 404,
                "message": "Room not found",
                "endpoint": "room.leave",
            }
            analysis = analyzer.analyze(error)
            print(f"❌ ルームが見つかりません: {analysis.recommended_action}")
        else:
            error = {
                "status_code": status or 500,
                "message": f"Leave room error: {str(e)}",
                "endpoint": "room.leave",
            }
            analysis = analyzer.analyze(error)
            print(f"❌ ルーム退出エラー: {analysis.recommended_action}")

        return {"error": str(e), "status": status}


async def get_group_member_ids(group_id: str, start: str = None):
    """グループメンバーIDリストの取得"""

    try:
        if start:
            member_ids = await line_bot_api.get_group_member_user_ids(
                group_id=group_id, start=start
            )
        else:
            member_ids = await line_bot_api.get_group_member_user_ids(group_id=group_id)

        print(f"✅ グループメンバーID取得成功: {len(member_ids.member_ids)}人分")
        return {
            "success": True,
            "member_ids": member_ids.member_ids,
            "next": member_ids.next,
        }

    except Exception as e:
        status = getattr(e, "status", None)

        if status == 403:
            error = {
                "status_code": 403,
                "message": "Group member IDs access denied",
                "endpoint": "group.members",
            }
            analysis = analyzer.analyze(error)
            print(f"❌ グループメンバーIDアクセス拒否: {analysis.recommended_action}")
        elif status == 404:
            error = {
                "status_code": 404,
                "message": "Group not found",
                "endpoint": "group.members",
            }
            analysis = analyzer.analyze(error)
            print(f"❌ グループが見つかりません: {analysis.recommended_action}")
        else:
            error = {
                "status_code": status or 500,
                "message": f"Member IDs error: {str(e)}",
                "endpoint": "group.members",
            }
            analysis = analyzer.analyze(error)
            print(f"❌ グループメンバーID取得エラー: {analysis.recommended_action}")

        return {"error": str(e), "status": status}


async def get_room_member_ids(room_id: str, start: str = None):
    """ルームメンバーIDリストの取得"""

    try:
        if start:
            member_ids = await line_bot_api.get_room_member_user_ids(
                room_id=room_id, start=start
            )
        else:
            member_ids = await line_bot_api.get_room_member_user_ids(room_id=room_id)

        print(f"✅ ルームメンバーID取得成功: {len(member_ids.member_ids)}人分")
        return {
            "success": True,
            "member_ids": member_ids.member_ids,
            "next": member_ids.next,
        }

    except Exception as e:
        status = getattr(e, "status", None)

        if status == 403:
            error = {
                "status_code": 403,
                "message": "Room member IDs access denied",
                "endpoint": "room.members",
            }
            analysis = analyzer.analyze(error)
            print(f"❌ ルームメンバーIDアクセス拒否: {analysis.recommended_action}")
        elif status == 404:
            error = {
                "status_code": 404,
                "message": "Room not found",
                "endpoint": "room.members",
            }
            analysis = analyzer.analyze(error)
            print(f"❌ ルームが見つかりません: {analysis.recommended_action}")
        else:
            error = {
                "status_code": status or 500,
                "message": f"Room member IDs error: {str(e)}",
                "endpoint": "room.members",
            }
            analysis = analyzer.analyze(error)
            print(f"❌ ルームメンバーID取得エラー: {analysis.recommended_action}")

        return {"error": str(e), "status": status}


# 使用例
async def example_usage():
    """使用例の実行"""

    print("👥 グループ管理の例:")

    # テスト用のID（実際の値に置き換えてください）
    test_group_id = "C1234567890123456789012345678901234567890123456789"
    test_room_id = "R1234567890123456789012345678901234567890123456789"

    # グループ情報取得
    await get_group_summary(test_group_id)

    # グループメンバー数取得
    await get_group_members_count(test_group_id)

    # ルームメンバー数取得
    await get_room_members_count(test_room_id)

    # グループメンバーIDリスト取得
    await get_group_member_ids(test_group_id)

    # ルームメンバーIDリスト取得
    await get_room_member_ids(test_room_id)


if __name__ == "__main__":
    import asyncio

    print("👥 LINE Bot グループ管理 - 実用パターン")
    print("=" * 50)

    # 例の実行
    asyncio.run(example_usage())
