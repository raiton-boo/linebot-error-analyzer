#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
FastAPI Echo Bot with Error Analysis

LINE Bot SDK のFastAPI echo botサンプルにエラーアナライザーを組み込んだ例です。
非同期処理でエラーハンドリングを行います。

Requirements:
    pip install line-bot-sdk fastapi uvicorn linebot-error-analyzer

Usage:
    1. LINE Developersでチャネルを作成
    2. 環境変数を設定: CHANNEL_SECRET, CHANNEL_ACCESS_TOKEN
    3. uvicorn fastapi_echo_bot:app --host 0.0.0.0 --port 8000 --reload
    4. ngrokなどでトンネルを作成してWebhook URLを設定
"""

import os
import sys
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import uvicorn
import logging

from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

# エラーアナライザーをインポート
from linebot_error_analyzer import AsyncLineErrorAnalyzer

# FastAPIアプリケーションを初期化
app = FastAPI(
    title="LINE Bot Echo Server with Error Analysis",
    description="LINE Bot echo server with integrated error analysis",
    version="1.0.0",
)

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


@app.post("/callback")
async def callback(request: Request, background_tasks: BackgroundTasks):
    """LINE Webhook callback"""
    if not handler:
        raise HTTPException(status_code=500, detail="Webhook handler not configured")

    signature = request.headers["X-Line-Signature"]
    body = await request.body()
    body_str = body.decode("utf-8")

    logger.info(f"Request body: {body_str}")

    try:
        handler.handle(body_str, signature)
    except InvalidSignatureError:
        logger.error(
            "Invalid signature. Please check your channel access token/channel secret."
        )
        raise HTTPException(status_code=400, detail="Invalid signature")
    except LineBotApiError as e:
        # バックグラウンドタスクでエラー解析を実行
        background_tasks.add_task(handle_line_bot_error, e)

        # エラーの種類によって適切なHTTPステータスを返す
        if e.status_code >= 500:
            # サーバーエラーの場合は500を返してLINEプラットフォームに再送させる
            raise HTTPException(status_code=500, detail="LINE server error")
        else:
            # クライアントエラーの場合は400を返す
            raise HTTPException(status_code=400, detail="Client error")
    except Exception as e:
        # その他の予期しないエラー
        logger.error(f"Unexpected error: {str(e)}")
        background_tasks.add_task(handle_line_bot_error, e)
        raise HTTPException(status_code=500, detail="Internal server error")

    return {"status": "ok"}


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
        # エラー処理は非同期で実行される
        logger.error(f"LINE Bot API error: {e}")
        # ここではraise しない（WebhookハンドラーがLineBotApiErrorを適切に処理）
    except Exception as e:
        logger.error(f"Unexpected error in message handler: {str(e)}")


@app.get("/health")
async def health_check():
    """ヘルスチェックエンドポイント"""
    try:
        return {
            "status": "healthy",
            "line_bot_api": "configured" if line_bot_api else "not configured",
            "webhook_handler": "configured" if handler else "not configured",
            "error_analyzer": "ready",
        }
    except Exception as e:
        analysis = await handle_line_bot_error(e)
        raise HTTPException(
            status_code=500,
            detail={
                "status": "unhealthy",
                "error": analysis.description,
                "recommended_action": analysis.recommended_action,
            },
        )


@app.get("/test-error/{error_code}")
async def test_error_analysis(error_code: int):
    """エラー解析のテスト用エンドポイント"""
    test_messages = {
        400: "Invalid request body format",
        401: "Invalid channel access token",
        403: "Forbidden operation for this channel",
        404: "The specified resource was not found",
        429: "Rate limit exceeded. Retry after 60 seconds",
        500: "LINE server internal error occurred",
    }

    if error_code not in test_messages:
        raise HTTPException(status_code=400, detail="Unsupported error code")

    error_message = f"({error_code}) {test_messages[error_code]}"
    analysis = await error_analyzer.analyze(error_message)

    return {
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


@app.get("/")
async def root():
    """ルートエンドポイント"""
    return {
        "message": "LINE Bot Echo Server with Error Analysis",
        "endpoints": {
            "POST /callback": "LINE Webhook endpoint",
            "GET /health": "Health check",
            "GET /test-error/{code}": "Test error analysis",
            "GET /docs": "API documentation",
        },
    }


# アプリケーション起動時の処理
@app.on_event("startup")
async def startup_event():
    logger.info("=== FastAPI Echo Bot with Error Analysis ===")
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

    logger.info("🚀 FastAPI server started")
    logger.info("  利用可能エンドポイント:")
    logger.info("    POST /callback - LINE Webhook")
    logger.info("    GET  /health   - ヘルスチェック")
    logger.info("    GET  /test-error/{code} - エラー解析テスト")
    logger.info("    GET  /docs     - API仕様書")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="FastAPI Echo Bot with Error Analysis")
    parser.add_argument("--host", default="0.0.0.0", help="Host address")
    parser.add_argument("--port", type=int, default=8000, help="Port number")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")

    args = parser.parse_args()

    print("💡 テスト方法:")
    print(f"  curl http://localhost:{args.port}/health")
    print(f"  curl http://localhost:{args.port}/test-error/401")
    print(f"  http://localhost:{args.port}/docs (API仕様書)")
    print()

    uvicorn.run(
        "fastapi_echo_bot:app", host=args.host, port=args.port, reload=args.reload
    )
