"""
LINE Bot イベント処理 - 実用パターン

実際のLINE Bot SDK使用時のイベント処理でのエラーハンドリングパターンです。

注意：このファイル内のerror辞書は、実際のLINE APIで発生する可能性のあるエラーパターンを
示すためのサンプルです。実際のAPIエラーは`e`オブジェクトから取得されます。
"""

import os
import sys
from fastapi import Request, FastAPI, HTTPException
from linebot.v3.webhook import WebhookParser
from linebot.v3.messaging import (
    AsyncApiClient,
    AsyncMessagingApi,
    Configuration,
    ReplyMessageRequest,
    TextMessage,
)
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent,
    FollowEvent,
    UnfollowEvent,
    PostbackEvent,
)
from line_bot_error_analyzer import LineErrorAnalyzer


# 設定とエラーハンドリング
analyzer = LineErrorAnalyzer()

# 環境変数の取得とエラーハンドリング
channel_secret = os.getenv("LINE_CHANNEL_SECRET", None)
channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", None)

if channel_secret is None or channel_access_token is None:
    error = {
        "status_code": 500,
        "message": "Missing environment variables",
        "endpoint": "config",
    }
    analysis = analyzer.analyze(error)
    print(f"❌ 設定エラー: {analysis.recommended_action}")
    sys.exit(1)

# LINE Bot API設定
configuration = Configuration(access_token=channel_access_token)
app = FastAPI()
async_api_client = AsyncApiClient(configuration)
line_bot_api = AsyncMessagingApi(async_api_client)
parser = WebhookParser(channel_secret)


async def handle_message_event(event: MessageEvent):
    """メッセージイベントの処理"""

    if not isinstance(event.message, TextMessageContent):
        return

    try:
        # エコーバック
        await line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=f"受信: {event.message.text}")],
            )
        )
    except Exception as e:
        # メッセージ送信エラー
        status = getattr(e, "status", None)
        error = {
            "status_code": status or 500,
            "message": f"Reply error: {str(e)}",
            "endpoint": "reply",
        }
        analysis = analyzer.analyze(error)
        print(f"❌ メッセージ送信エラー: {analysis.recommended_action}")


async def handle_follow_event(event: FollowEvent):
    """フォローイベントの処理"""

    try:
        await line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text="フォローありがとうございます！")],
            )
        )
    except Exception as e:
        status = getattr(e, "status", None)
        error = {
            "status_code": status or 500,
            "message": f"Follow reply error: {str(e)}",
            "endpoint": "reply",
        }
        analysis = analyzer.analyze(error)
        print(f"❌ フォロー応答エラー: {analysis.recommended_action}")


async def handle_unfollow_event(event: UnfollowEvent):
    """アンフォローイベントの処理"""

    # アンフォローのログ記録
    user_id = event.source.user_id
    print(f"📤 ユーザーがアンフォローしました: {user_id}")


async def handle_postback_event(event: PostbackEvent):
    """ポストバックイベントの処理"""

    try:
        data = event.postback.data
        await line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=f"ポストバック受信: {data}")],
            )
        )
    except Exception as e:
        status = getattr(e, "status", None)
        error = {
            "status_code": status or 500,
            "message": f"Postback reply error: {str(e)}",
            "endpoint": "reply",
        }
        analysis = analyzer.analyze(error)
        print(f"❌ ポストバック応答エラー: {analysis.recommended_action}")


@app.post("/callback")
async def handle_callback(request: Request):
    """Webhookコールバック - イベント処理付き"""

    try:
        # 署名の取得
        signature = request.headers["X-Line-Signature"]
    except KeyError:
        error = {
            "status_code": 400,
            "message": "Missing X-Line-Signature header",
            "endpoint": "webhook",
        }
        analysis = analyzer.analyze(error)
        print(f"❌ ヘッダーエラー: {analysis.recommended_action}")
        raise HTTPException(status_code=400, detail="Missing signature header")

    # リクエストボディの取得
    body = await request.body()
    body = body.decode()

    try:
        # 署名検証
        events = parser.parse(body, signature)
    except InvalidSignatureError:
        error = {
            "status_code": 400,
            "message": "Invalid signature",
            "endpoint": "webhook",
        }
        analysis = analyzer.analyze(error)
        print(f"❌ 署名エラー: {analysis.recommended_action}")
        raise HTTPException(status_code=400, detail="Invalid signature")

    # イベント処理
    for event in events:
        try:
            if isinstance(event, MessageEvent):
                await handle_message_event(event)
            elif isinstance(event, FollowEvent):
                await handle_follow_event(event)
            elif isinstance(event, UnfollowEvent):
                await handle_unfollow_event(event)
            elif isinstance(event, PostbackEvent):
                await handle_postback_event(event)
            else:
                print(f"🔄 未対応のイベント: {type(event).__name__}")

        except Exception as e:
            # イベント処理エラー
            error = {
                "status_code": 500,
                "message": f"Event processing error: {str(e)}",
                "endpoint": "event",
            }
            analysis = analyzer.analyze(error)
            print(f"❌ イベント処理エラー: {analysis.recommended_action}")

    return "OK"


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

import json
from line_bot_error_analyzer import LineErrorAnalyzer


def handle_line_event(event: dict) -> dict:
    """
    LINE イベントの処理

    Args:
        event: イベントデータ

    Returns:
        dict: 処理結果
    """

    analyzer = LineErrorAnalyzer()

    try:
        event_type = event.get("type")

        if event_type == "message":
            return handle_message_event(event)
        elif event_type == "follow":
            return handle_follow_event(event)
        elif event_type == "unfollow":
            return handle_unfollow_event(event)
        elif event_type == "join":
            return handle_join_event(event)
        else:
            print(f"ℹ️ 未対応のイベント: {event_type}")
            return {"status": "ignored", "event_type": event_type}

    except Exception as e:
        error = {
            "status_code": 500,
            "message": f"Event handling error: {str(e)}",
            "endpoint": "event_processing",
        }
        analysis = analyzer.analyze(error)
        print(f"❌ イベント処理エラー: {analysis.recommended_action}")
        return {"error": str(e)}


def handle_message_event(event: dict) -> dict:
    """メッセージイベントの処理"""

    analyzer = LineErrorAnalyzer()

    try:
        reply_token = event.get("replyToken")
        message = event.get("message", {})
        message_type = message.get("type")

        if not reply_token:
            error = {
                "status_code": 400,
                "message": "Missing reply token",
                "endpoint": "message_event",
            }
            analysis = analyzer.analyze(error)
            print(f"❌ リプライトークンなし: {analysis.recommended_action}")
            return {"error": "Missing reply token"}

        # テストWebhookの場合はスキップ
        if reply_token == "00000000000000000000000000000000":
            print("ℹ️ テストWebhookをスキップ")
            return {"status": "test_webhook"}

        print(f"📝 メッセージ受信: {message_type}")

        if message_type == "text":
            text = message.get("text", "")
            print(f"  テキスト: {text}")
            return {
                "status": "success",
                "message_type": "text",
                "reply_token": reply_token,
            }

        elif message_type == "image":
            print("  画像メッセージ")
            return {
                "status": "success",
                "message_type": "image",
                "reply_token": reply_token,
            }

        else:
            print(f"  その他のメッセージ: {message_type}")
            return {
                "status": "success",
                "message_type": message_type,
                "reply_token": reply_token,
            }

    except Exception as e:
        error = {
            "status_code": 500,
            "message": f"Message event error: {str(e)}",
            "endpoint": "message_event",
        }
        analysis = analyzer.analyze(error)
        print(f"❌ メッセージ処理エラー: {analysis.recommended_action}")
        return {"error": str(e)}


def handle_follow_event(event: dict) -> dict:
    """フォローイベントの処理"""

    try:
        user_id = event.get("source", {}).get("userId")
        print(f"👤 新規フォロー: {user_id}")
        return {"status": "success", "event_type": "follow", "user_id": user_id}

    except Exception as e:
        analyzer = LineErrorAnalyzer()
        error = {
            "status_code": 500,
            "message": f"Follow event error: {str(e)}",
            "endpoint": "follow_event",
        }
        analysis = analyzer.analyze(error)
        print(f"❌ フォローイベント処理エラー: {analysis.recommended_action}")
        return {"error": str(e)}


def handle_unfollow_event(event: dict) -> dict:
    """アンフォローイベントの処理"""

    try:
        user_id = event.get("source", {}).get("userId")
        print(f"👋 アンフォロー: {user_id}")
        return {"status": "success", "event_type": "unfollow", "user_id": user_id}

    except Exception as e:
        analyzer = LineErrorAnalyzer()
        error = {
            "status_code": 500,
            "message": f"Unfollow event error: {str(e)}",
            "endpoint": "unfollow_event",
        }
        analysis = analyzer.analyze(error)
        print(f"❌ アンフォローイベント処理エラー: {analysis.recommended_action}")
        return {"error": str(e)}


def handle_join_event(event: dict) -> dict:
    """グループ参加イベントの処理"""

    try:
        source = event.get("source", {})
        group_id = source.get("groupId")
        room_id = source.get("roomId")

        if group_id:
            print(f"🏢 グループ参加: {group_id}")
            return {"status": "success", "event_type": "join", "group_id": group_id}
        elif room_id:
            print(f"🏠 ルーム参加: {room_id}")
            return {"status": "success", "event_type": "join", "room_id": room_id}
        else:
            print("ℹ️ 参加イベント（詳細不明）")
            return {"status": "success", "event_type": "join"}

    except Exception as e:
        analyzer = LineErrorAnalyzer()
        error = {
            "status_code": 500,
            "message": f"Join event error: {str(e)}",
            "endpoint": "join_event",
        }
        analysis = analyzer.analyze(error)
        print(f"❌ 参加イベント処理エラー: {analysis.recommended_action}")
        return {"error": str(e)}


def process_webhook_events(body: str) -> dict:
    """
    Webhook イベントの一括処理

    Args:
        body: リクエストボディ（JSON文字列）

    Returns:
        dict: 処理結果
    """

    analyzer = LineErrorAnalyzer()

    try:
        # JSONの解析
        data = json.loads(body)
        events = data.get("events", [])

        print(f"📨 {len(events)}件のイベントを処理開始")

        results = []
        for event in events:
            result = handle_line_event(event)
            results.append(result)

        success_count = sum(1 for r in results if r.get("status") == "success")
        error_count = sum(1 for r in results if "error" in r)

        print(f"✅ 処理完了: 成功{success_count}件、エラー{error_count}件")

        return {
            "success": True,
            "total_events": len(events),
            "success_count": success_count,
            "error_count": error_count,
            "results": results,
        }

    except json.JSONDecodeError as e:
        error = {
            "status_code": 400,
            "message": f"JSON decode error: {str(e)}",
            "endpoint": "webhook_processing",
        }
        analysis = analyzer.analyze(error)
        print(f"❌ JSON解析エラー: {analysis.recommended_action}")
        return {"error": "Invalid JSON format"}

    except Exception as e:
        error = {
            "status_code": 500,
            "message": f"Webhook processing error: {str(e)}",
            "endpoint": "webhook_processing",
        }
        analysis = analyzer.analyze(error)
        print(f"❌ Webhook処理エラー: {analysis.recommended_action}")
        return {"error": str(e)}


# 実装例
def create_simple_webhook_example():
    """シンプルなWebhook実装例"""

    example_code = '''
from flask import Flask, request, abort
from simple_webhook_processing import process_webhook_events
from simple_signature_validation import validate_line_signature

app = Flask(__name__)

@app.route("/webhook", methods=['POST'])
def webhook():
    """LINE Webhook エンドポイント"""
    
    # リクエストデータの取得
    body = request.get_data(as_text=True)
    signature = request.headers.get('X-Line-Signature', '')
    
    # 署名検証
    if not validate_line_signature(body, signature):
        abort(400)
    
    # イベント処理
    result = process_webhook_events(body)
    
    if "error" in result:
        print(f"処理エラー: {result['error']}")
        abort(500)
    
    print(f"処理結果: {result['success_count']}件成功")
    return 'OK'

if __name__ == "__main__":
    app.run(debug=True)
'''

    return example_code


if __name__ == "__main__":
    print("📨 LINE Bot Webhook処理 - シンプル版デモ")
    print("=" * 50)

    # テスト用のWebhookデータ
    test_webhook = {
        "events": [
            {
                "type": "message",
                "replyToken": "test-reply-token",
                "source": {"type": "user", "userId": "test-user"},
                "message": {"type": "text", "text": "Hello!"},
            },
            {"type": "follow", "source": {"type": "user", "userId": "new-user"}},
        ]
    }

    # テスト実行
    test_body = json.dumps(test_webhook)
    result = process_webhook_events(test_body)
    print(f"\n結果: {result}")

    print("\n📄 実装例:")
    print(create_simple_webhook_example())
