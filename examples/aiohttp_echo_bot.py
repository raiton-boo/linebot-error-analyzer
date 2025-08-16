#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
aiohttp Echo Bot with Error Analysis

LINE Bot SDK のaiohttp echo botサンプルにエラーアナライザーを組み込んだ例です。
完全非同期でエラーハンドリングを行います。

Requirements:
    pip install line-bot-sdk aiohttp linebot-error-analyzer

Usage:
    1. LINE Developersでチャネルを作成
    2. 環境変数を設定: CHANNEL_SECRET, CHANNEL_ACCESS_TOKEN
    3. python aiohttp_echo_bot.py --port 8000
    4. ngrokなどでトンネルを作成してWebhook URLを設定
"""

import os
import sys
import asyncio
import logging
from argparse import ArgumentParser

from aiohttp import web, ClientSession
from aiohttp.web import Request, Response, json_response

from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

# エラーアナライザーをインポート
from linebot_error_analyzer import AsyncLineErrorAnalyzer

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 環境変数から設定を読み込み
CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

if not CHANNEL_SECRET:
    logger.error("LINE_CHANNEL_SECRET environment variable is not set")
if not CHANNEL_ACCESS_TOKEN:
    logger.error("LINE_CHANNEL_ACCESS_TOKEN environment variable is not set")

# LINE Bot APIクライアントを初期化
line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN) if CHANNEL_ACCESS_TOKEN else None
handler = WebhookHandler(CHANNEL_SECRET) if CHANNEL_SECRET else None

# 非同期エラーアナライザーを初期化
error_analyzer = AsyncLineErrorAnalyzer()


async def handle_line_bot_error(error):
    """LINE Bot APIエラーを非同期で解析して対処"""
    if isinstance(error, LineBotApiError):
        # LINE Bot APIエラーのメッセージを抽出
        error_message = f"({error.status_code}) {error.message}"
    else:
        error_message = str(error)

    # 非同期でエラーを解析
    analysis = await error_analyzer.analyze(error_message)

    logger.info(f"🔍 エラー解析結果:")
    logger.info(
        f"   カテゴリ: {analysis.category.value if analysis.category else '不明'}"
    )
    logger.info(f"   説明: {analysis.description}")
    logger.info(f"   対処法: {analysis.recommended_action}")
    logger.info(f"   再試行可能: {'はい' if analysis.is_retryable else 'いいえ'}")

    if analysis.retry_after:
        logger.info(f"   再試行まで: {analysis.retry_after}秒")

    # エラーログを記録
    logger.error(f"LINE Bot error: {analysis.description}")

    return analysis


async def callback_handler(request: Request) -> Response:
    """LINE Webhook callback"""
    if not handler:
        logger.error("Webhook handler not configured")
        return web.Response(status=500, text="Webhook handler not configured")

    signature = request.headers.get("X-Line-Signature", "")
    body = await request.text()

    logger.info(f"Request body: {body}")

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        logger.error(
            "Invalid signature. Please check your channel access token/channel secret."
        )
        return web.Response(status=400, text="Invalid signature")
    except LineBotApiError as e:
        # エラーを解析（非同期でバックグラウンド実行）
        asyncio.create_task(handle_line_bot_error(e))

        # エラーの種類によって適切なHTTPステータスを返す
        if e.status_code >= 500:
            # サーバーエラーの場合は500を返してLINEプラットフォームに再送させる
            return web.Response(status=500, text="LINE server error")
        else:
            # クライアントエラーの場合は400を返す
            return web.Response(status=400, text="Client error")
    except Exception as e:
        # その他の予期しないエラー
        logger.error(f"Unexpected error: {str(e)}")
        asyncio.create_task(handle_line_bot_error(e))
        return web.Response(status=500, text="Internal server error")

    return web.Response(text="OK")


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    """メッセージイベントの処理"""
    try:
        if not line_bot_api:
            logger.error("LINE Bot API client not configured")
            return

        # エコーメッセージを送信
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text=event.message.text)
        )
        logger.info(f"Echo message sent: {event.message.text}")

    except LineBotApiError as e:
        # エラー処理（同期処理なので非同期タスクとして実行）
        logger.error(f"LINE Bot API error: {e}")
        # 非同期でエラー解析を実行
        asyncio.create_task(handle_line_bot_error(e))
    except Exception as e:
        logger.error(f"Unexpected error in message handler: {str(e)}")
        asyncio.create_task(handle_line_bot_error(e))


async def health_check_handler(request: Request) -> Response:
    """ヘルスチェックエンドポイント"""
    try:
        health_data = {
            "status": "healthy",
            "line_bot_api": "configured" if line_bot_api else "not configured",
            "webhook_handler": "configured" if handler else "not configured",
            "error_analyzer": "ready",
        }
        return json_response(health_data)
    except Exception as e:
        analysis = await handle_line_bot_error(e)
        error_data = {
            "status": "unhealthy",
            "error": analysis.description,
            "recommended_action": analysis.recommended_action,
        }
        return json_response(error_data, status=500)


async def test_error_analysis_handler(request: Request) -> Response:
    """エラー解析のテスト用エンドポイント"""
    try:
        error_code = int(request.match_info["error_code"])
    except ValueError:
        return json_response({"error": "Invalid error code"}, status=400)

    test_messages = {
        400: "Invalid request body format",
        401: "Invalid channel access token",
        403: "Forbidden operation for this channel",
        404: "The specified resource was not found",
        429: "Rate limit exceeded. Retry after 60 seconds",
        500: "LINE server internal error occurred",
    }

    if error_code not in test_messages:
        return json_response({"error": "Unsupported error code"}, status=400)

    error_message = f"({error_code}) {test_messages[error_code]}"
    analysis = await error_analyzer.analyze(error_message)

    result = {
        "original_error": error_message,
        "analysis": {
            "status_code": analysis.status_code,
            "category": analysis.category.value if analysis.category else None,
            "is_retryable": analysis.is_retryable,
            "description": analysis.description,
            "recommended_action": analysis.recommended_action,
            "retry_after": analysis.retry_after,
        },
    }

    return json_response(result)


async def root_handler(request: Request) -> Response:
    """ルートエンドポイント"""
    info = {
        "message": "LINE Bot Echo Server with Error Analysis (aiohttp)",
        "endpoints": {
            "POST /callback": "LINE Webhook endpoint",
            "GET /health": "Health check",
            "GET /test-error/{code}": "Test error analysis",
        },
    }
    return json_response(info)


async def create_app():
    """aiohttp アプリケーションを作成"""
    app = web.Application()

    # ルートを追加
    app.router.add_get("/", root_handler)
    app.router.add_post("/callback", callback_handler)
    app.router.add_get("/health", health_check_handler)
    app.router.add_get("/test-error/{error_code}", test_error_analysis_handler)

    return app


async def init():
    """アプリケーション初期化"""
    logger.info("=== aiohttp Echo Bot with Error Analysis ===")
    logger.info("")
    logger.info("🔧 設定確認:")
    logger.info(f"  CHANNEL_SECRET: {'✓ 設定済み' if CHANNEL_SECRET else '❌ 未設定'}")
    logger.info(
        f"  CHANNEL_ACCESS_TOKEN: {'✓ 設定済み' if CHANNEL_ACCESS_TOKEN else '❌ 未設定'}"
    )
    logger.info("")

    if not CHANNEL_SECRET or not CHANNEL_ACCESS_TOKEN:
        logger.warning("💡 環境変数の設定例:")
        logger.warning("  export LINE_CHANNEL_SECRET='your_channel_secret'")
        logger.warning("  export LINE_CHANNEL_ACCESS_TOKEN='your_channel_access_token'")
        logger.warning("")
        logger.warning(
            "⚠️  環境変数が未設定でも起動しますが、実際のLINE Botとして動作しません"
        )

    logger.info("🚀 aiohttp server starting...")
    logger.info("  利用可能エンドポイント:")
    logger.info("    POST /callback - LINE Webhook")
    logger.info("    GET  /health   - ヘルスチェック")
    logger.info("    GET  /test-error/{code} - エラー解析テスト")


def main():
    """メイン関数"""
    arg_parser = ArgumentParser(
        usage="Usage: python " + __file__ + " [--port <port>] [--help]"
    )
    arg_parser.add_argument("-p", "--port", type=int, default=8000, help="port")
    arg_parser.add_argument("-H", "--host", default="0.0.0.0", help="host")
    options = arg_parser.parse_args()

    # 初期化を実行
    asyncio.run(init())

    print("")
    print("💡 テスト方法:")
    print(f"  curl http://localhost:{options.port}/health")
    print(f"  curl http://localhost:{options.port}/test-error/401")
    print("")

    # アプリケーションを作成して起動
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    app = loop.run_until_complete(create_app())

    try:
        web.run_app(app, host=options.host, port=options.port)
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    finally:
        loop.close()


if __name__ == "__main__":
    main()
