"""
LINE Bot メッセージ送信 - 実用パターン

実際のLINE Bot SDK使用時のメッセージ送信でのエラーハンドリングパターンです。

注意：このファイル内のerror辞書は、実際のLINE APIで発生する可能性のあるエラーパターンを
示すためのサンプルです。実際のAPIエラーは`e`オブジェクトから取得されます。
"""

import os
import sys
from linebot.v3.messaging import (
    AsyncApiClient,
    AsyncMessagingApi,
    Configuration,
    ReplyMessageRequest,
    PushMessageRequest,
    TextMessage,
    StickerMessage,
    ImageMessage,
    FlexMessage,
    FlexContainer,
)
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


async def send_reply_message(reply_token: str, text: str):
    """リプライメッセージの送信"""

    try:
        await line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=reply_token, messages=[TextMessage(text=text)]
            )
        )
        print(f"✅ リプライ送信成功: {text}")
        return {"success": True}

    except Exception as e:
        status = getattr(e, "status", None)

        if status == 400:
            # 実際のLINE APIで発生する可能性のあるエラーパターン
            error = {
                "status_code": 400,
                "message": "Invalid reply token or message",
                "endpoint": "reply",
            }
            analysis = analyzer.analyze(error)
            print(f"❌ リクエストエラー: {analysis.recommended_action}")
        elif status == 403:
            # 実際のLINE APIで発生する可能性のあるエラーパターン
            error = {
                "status_code": 403,
                "message": "User blocked or terms not agreed",
                "endpoint": "reply",
            }
            analysis = analyzer.analyze(error)
            print(f"❌ 送信権限エラー: {analysis.recommended_action}")
        else:
            # その他の予期しないエラー
            error = {
                "status_code": status or 500,
                "message": f"Reply error: {str(e)}",
                "endpoint": "reply",
            }
            analysis = analyzer.analyze(error)
            print(f"❌ 送信エラー: {analysis.recommended_action}")

        return {"error": str(e), "status": status}


async def send_push_message(user_id: str, text: str):
    """プッシュメッセージの送信"""

    try:
        await line_bot_api.push_message(
            PushMessageRequest(to=user_id, messages=[TextMessage(text=text)])
        )
        print(f"✅ プッシュ送信成功: {text}")
        return {"success": True}

    except Exception as e:
        status = getattr(e, "status", None)

        if status == 400:
            error = {
                "status_code": 400,
                "message": "Invalid user ID or message",
                "endpoint": "push",
            }
            analysis = analyzer.analyze(error)
            print(f"❌ リクエストエラー: {analysis.recommended_action}")
        elif status == 403:
            error = {
                "status_code": 403,
                "message": "User blocked or terms not agreed",
                "endpoint": "push",
            }
            analysis = analyzer.analyze(error)
            print(f"❌ 送信権限エラー: {analysis.recommended_action}")
        else:
            error = {
                "status_code": status or 500,
                "message": f"Push error: {str(e)}",
                "endpoint": "push",
            }
            analysis = analyzer.analyze(error)
            print(f"❌ 送信エラー: {analysis.recommended_action}")

        return {"error": str(e), "status": status}


async def send_sticker_message(reply_token: str, package_id: str, sticker_id: str):
    """スタンプメッセージの送信"""

    try:
        await line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=reply_token,
                messages=[StickerMessage(package_id=package_id, sticker_id=sticker_id)],
            )
        )
        print(f"✅ スタンプ送信成功: {package_id}/{sticker_id}")
        return {"success": True}

    except Exception as e:
        status = getattr(e, "status", None)
        error = {
            "status_code": status or 500,
            "message": f"Sticker error: {str(e)}",
            "endpoint": "sticker",
        }
        analysis = analyzer.analyze(error)
        print(f"❌ スタンプ送信エラー: {analysis.recommended_action}")
        return {"error": str(e), "status": status}


async def send_image_message(reply_token: str, original_url: str, preview_url: str):
    """画像メッセージの送信"""

    try:
        await line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=reply_token,
                messages=[
                    ImageMessage(
                        original_content_url=original_url, preview_image_url=preview_url
                    )
                ],
            )
        )
        print(f"✅ 画像送信成功: {original_url}")
        return {"success": True}

    except Exception as e:
        status = getattr(e, "status", None)
        error = {
            "status_code": status or 500,
            "message": f"Image error: {str(e)}",
            "endpoint": "image",
        }
        analysis = analyzer.analyze(error)
        print(f"❌ 画像送信エラー: {analysis.recommended_action}")
        return {"error": str(e), "status": status}


async def send_multiple_messages(reply_token: str, messages: list):
    """複数メッセージの送信"""

    try:
        await line_bot_api.reply_message(
            ReplyMessageRequest(reply_token=reply_token, messages=messages)
        )
        print(f"✅ 複数メッセージ送信成功: {len(messages)}件")
        return {"success": True, "count": len(messages)}

    except Exception as e:
        status = getattr(e, "status", None)

        if status == 400:
            error = {
                "status_code": 400,
                "message": "Invalid messages or too many",
                "endpoint": "multiple",
            }
            analysis = analyzer.analyze(error)
            print(f"❌ メッセージエラー: {analysis.recommended_action}")
        else:
            error = {
                "status_code": status or 500,
                "message": f"Multiple send error: {str(e)}",
                "endpoint": "multiple",
            }
            analysis = analyzer.analyze(error)
            print(f"❌ 複数送信エラー: {analysis.recommended_action}")

        return {"error": str(e), "status": status}


# 使用例
async def example_usage():
    """使用例の実行"""

    # テスト用のトークン（実際の値に置き換えてください）
    test_reply_token = "test-reply-token"
    test_user_id = "test-user-id"

    print("📤 メッセージ送信の例:")

    # テキストメッセージ
    await send_reply_message(test_reply_token, "こんにちは！")

    # プッシュメッセージ
    await send_push_message(test_user_id, "お知らせです")

    # スタンプ
    await send_sticker_message(test_reply_token, "11537", "52002734")

    # 複数メッセージ
    messages = [
        TextMessage(text="メッセージ1"),
        TextMessage(text="メッセージ2"),
        StickerMessage(package_id="11537", sticker_id="52002734"),
    ]
    await send_multiple_messages(test_reply_token, messages)


if __name__ == "__main__":
    import asyncio

    print("📤 LINE Bot メッセージ送信 - 実用パターン")
    print("=" * 50)

    # 例の実行
    asyncio.run(example_usage())

import json
import os
from line_bot_error_analyzer import LineErrorAnalyzer


def send_reply_message(
    reply_token: str, messages: list, channel_access_token: str = None
) -> dict:
    """
    Reply APIでメッセージを送信

    Args:
        reply_token: リプライトークン
        messages: 送信するメッセージのリスト
        channel_access_token: チャンネルアクセストークン

    Returns:
        dict: 送信結果
    """

    analyzer = LineErrorAnalyzer()

    try:
        # アクセストークンの取得
        if not channel_access_token:
            channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

        if not channel_access_token:
            error = {
                "status_code": 500,
                "message": "Channel access token not found",
                "endpoint": "reply_message",
            }
            analysis = analyzer.analyze(error)
            print(f"❌ 設定エラー: {analysis.recommended_action}")
            return {"error": "Token not found"}

        # リプライトークンの検証
        if not reply_token:
            error = {
                "status_code": 400,
                "message": "Missing reply token",
                "endpoint": "reply_message",
            }
            analysis = analyzer.analyze(error)
            print(f"❌ リプライトークンエラー: {analysis.recommended_action}")
            return {"error": "Missing reply token"}

        # テスト用トークンのチェック
        if reply_token == "00000000000000000000000000000000":
            print("ℹ️ テスト用トークンのためスキップ")
            return {"status": "test_token_skipped"}

        # メッセージの検証
        if not messages or len(messages) == 0:
            error = {
                "status_code": 400,
                "message": "No messages to send",
                "endpoint": "reply_message",
            }
            analysis = analyzer.analyze(error)
            print(f"❌ メッセージエラー: {analysis.recommended_action}")
            return {"error": "No messages"}

        if len(messages) > 5:
            error = {
                "status_code": 400,
                "message": "Too many messages (max 5)",
                "endpoint": "reply_message",
            }
            analysis = analyzer.analyze(error)
            print(f"❌ メッセージ数制限: {analysis.recommended_action}")
            return {"error": "Too many messages"}

        # ここで実際のAPI呼び出しを行う
        # requests.post('https://api.line.me/v2/bot/message/reply', ...)

        print(f"✅ Reply API送信成功: {len(messages)}件のメッセージ")
        return {"status": "success", "message_count": len(messages)}

    except Exception as e:
        error = {
            "status_code": 500,
            "message": f"Reply message error: {str(e)}",
            "endpoint": "reply_message",
        }
        analysis = analyzer.analyze(error)
        print(f"❌ 送信エラー: {analysis.recommended_action}")
        return {"error": str(e)}


def send_push_message(
    to: str, messages: list, channel_access_token: str = None
) -> dict:
    """
    Push APIでメッセージを送信

    Args:
        to: 送信先（ユーザーID、グループID、ルームID）
        messages: 送信するメッセージのリスト
        channel_access_token: チャンネルアクセストークン

    Returns:
        dict: 送信結果
    """

    analyzer = LineErrorAnalyzer()

    try:
        # アクセストークンの取得
        if not channel_access_token:
            channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

        if not channel_access_token:
            error = {
                "status_code": 500,
                "message": "Channel access token not found",
                "endpoint": "push_message",
            }
            analysis = analyzer.analyze(error)
            print(f"❌ 設定エラー: {analysis.recommended_action}")
            return {"error": "Token not found"}

        # 送信先の検証
        if not to:
            error = {
                "status_code": 400,
                "message": "Missing destination",
                "endpoint": "push_message",
            }
            analysis = analyzer.analyze(error)
            print(f"❌ 送信先エラー: {analysis.recommended_action}")
            return {"error": "Missing destination"}

        # ID形式の簡易チェック
        if not (to.startswith("U") or to.startswith("C") or to.startswith("R")):
            error = {
                "status_code": 400,
                "message": "Invalid destination format",
                "endpoint": "push_message",
            }
            analysis = analyzer.analyze(error)
            print(f"❌ 送信先フォーマットエラー: {analysis.recommended_action}")
            return {"error": "Invalid destination format"}

        # メッセージの検証
        if not messages or len(messages) == 0:
            error = {
                "status_code": 400,
                "message": "No messages to send",
                "endpoint": "push_message",
            }
            analysis = analyzer.analyze(error)
            print(f"❌ メッセージエラー: {analysis.recommended_action}")
            return {"error": "No messages"}

        if len(messages) > 5:
            error = {
                "status_code": 400,
                "message": "Too many messages (max 5)",
                "endpoint": "push_message",
            }
            analysis = analyzer.analyze(error)
            print(f"❌ メッセージ数制限: {analysis.recommended_action}")
            return {"error": "Too many messages"}

        # ここで実際のAPI呼び出しを行う
        # requests.post('https://api.line.me/v2/bot/message/push', ...)

        print(f"✅ Push API送信成功: {to} へ {len(messages)}件のメッセージ")
        return {"status": "success", "destination": to, "message_count": len(messages)}

    except Exception as e:
        error = {
            "status_code": 500,
            "message": f"Push message error: {str(e)}",
            "endpoint": "push_message",
        }
        analysis = analyzer.analyze(error)
        print(f"❌ 送信エラー: {analysis.recommended_action}")
        return {"error": str(e)}


def create_text_message(text: str) -> dict:
    """テキストメッセージの作成"""

    analyzer = LineErrorAnalyzer()

    if not text:
        error = {
            "status_code": 400,
            "message": "Empty text message",
            "endpoint": "message_creation",
        }
        analysis = analyzer.analyze(error)
        print(f"❌ テキストエラー: {analysis.recommended_action}")
        return {}

    if len(text) > 5000:
        error = {
            "status_code": 400,
            "message": "Text too long (max 5000 chars)",
            "endpoint": "message_creation",
        }
        analysis = analyzer.analyze(error)
        print(f"❌ テキスト長制限: {analysis.recommended_action}")
        return {}

    return {"type": "text", "text": text}


def create_sticker_message(package_id: str, sticker_id: str) -> dict:
    """スタンプメッセージの作成"""

    analyzer = LineErrorAnalyzer()

    if not package_id or not sticker_id:
        error = {
            "status_code": 400,
            "message": "Missing sticker parameters",
            "endpoint": "message_creation",
        }
        analysis = analyzer.analyze(error)
        print(f"❌ スタンプパラメータエラー: {analysis.recommended_action}")
        return {}

    return {"type": "sticker", "packageId": package_id, "stickerId": sticker_id}


# 実装例
def create_messaging_example():
    """メッセージ送信の実装例"""

    example_code = '''
from flask import Flask, request
from simple_message_sending import send_reply_message, create_text_message
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
        return 'Invalid signature', 400
    
    # イベント処理
    result = process_webhook_events(body)
    
    if "error" in result:
        return 'Processing error', 500
    
    # メッセージイベントに対する返信
    for event_result in result.get('results', []):
        if event_result.get('status') == 'success' and 'reply_token' in event_result:
            reply_token = event_result['reply_token']
            
            # Echo機能
            if event_result.get('message_type') == 'text':
                message = create_text_message("メッセージを受信しました！")
                if message:
                    send_reply_message(reply_token, [message])
    
    return 'OK'

if __name__ == "__main__":
    app.run(debug=True)
'''

    return example_code


if __name__ == "__main__":
    print("💬 LINE Bot メッセージ送信 - シンプル版デモ")
    print("=" * 50)

    # 環境変数の設定例
    os.environ["LINE_CHANNEL_ACCESS_TOKEN"] = "test-access-token"

    # テスト用メッセージ
    test_messages = [
        create_text_message("こんにちは！"),
        create_sticker_message("1", "1"),
    ]

    print("✅ 正常なReply送信:")
    result = send_reply_message("test-reply-token", test_messages)
    print(f"結果: {result}")

    print("\n✅ 正常なPush送信:")
    result = send_push_message(
        "U1234567890123456789012345678901234567890123456789", test_messages
    )
    print(f"結果: {result}")

    print("\n❌ エラーケース:")
    result = send_reply_message("", test_messages)
    print(f"結果: {result}")

    print("\n📄 実装例:")
    print(create_messaging_example())
