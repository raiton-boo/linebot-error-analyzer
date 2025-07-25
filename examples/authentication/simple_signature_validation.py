"""
LINE Bot 署名検証 - 実用パターン

実際のLINE Bot SDK使用時のエラーハンドリングパターンです。

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
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from linebot_error_analyzer import LineErrorAnalyzer


# 設定とエラーハンドリング
analyzer = LineErrorAnalyzer()

# 環境変数の取得とエラーハンドリング
channel_secret = os.getenv("LINE_CHANNEL_SECRET", None)
channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", None)

if channel_secret is None:
    # 環境変数が設定されていない場合のエラー（開発者向け）
    error = {
        "status_code": 500,
        "message": "Missing LINE_CHANNEL_SECRET",
        "endpoint": "config",
    }
    analysis = analyzer.analyze(error)
    print(f"❌ 設定エラー: {analysis.recommended_action}")
    sys.exit(1)

if channel_access_token is None:
    # 環境変数が設定されていない場合のエラー（開発者向け）
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
app = FastAPI()
async_api_client = AsyncApiClient(configuration)
line_bot_api = AsyncMessagingApi(async_api_client)
parser = WebhookParser(channel_secret)


@app.post("/callback")
async def handle_callback(request: Request):
    """Webhookコールバック - エラーハンドリング付き"""

    try:
        # 署名の取得
        signature = request.headers["X-Line-Signature"]
    except KeyError:
        # X-Line-Signatureヘッダーがない場合（LINE Webhookでない可能性）
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
        # 署名が無効な場合（実際のLINE APIで発生する可能性のあるエラー）
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
        if not isinstance(event, MessageEvent):
            continue
        if not isinstance(event.message, TextMessageContent):
            continue

        try:
            # メッセージ送信
            await line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=event.message.text)],
                )
            )
        except Exception as e:
            # メッセージ送信エラーのハンドリング
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

    return "OK"


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
