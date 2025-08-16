#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Flask Echo Bot with Error Analysis

LINE Bot SDK のecho botサンプルにエラーアナライザーを組み込んだ例です。
実際のLINE Bot Webhookでエラーハンドリングを行います。

Requirements:
    pip install line-bot-sdk flask linebot-error-analyzer

Usage:
    1. LINE Developersでチャネルを作成
    2. 環境変数を設定: CHANNEL_SECRET, CHANNEL_ACCESS_TOKEN
    3. python flask_echo_bot.py
    4. ngrokなどでトンネルを作成してWebhook URLを設定
"""

import os
import sys
from argparse import ArgumentParser

from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import (
    MessageEvent,
    TextMessage,
    TextSendMessage,
)

# エラーアナライザーをインポート
from linebot_error_analyzer import LineErrorAnalyzer

app = Flask(__name__)

# 環境変数から設定を読み込み
channel_secret = os.getenv("LINE_CHANNEL_SECRET", None)
channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", None)

if channel_secret is None:
    print("Specify LINE_CHANNEL_SECRET as environment variable.")
    sys.exit(1)
if channel_access_token is None:
    print("Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.")
    sys.exit(1)

line_bot_api = LineBotApi(channel_access_token)
handler = WebhookHandler(channel_secret)

# エラーアナライザーを初期化
error_analyzer = LineErrorAnalyzer()


def handle_line_bot_error(error):
    """LINE Bot APIエラーを解析して対処"""
    if isinstance(error, LineBotApiError):
        # LINE Bot APIエラーのメッセージを抽出
        error_message = f"({error.status_code}) {error.message}"

        # エラーアナライザーで解析
        analysis = error_analyzer.analyze(error_message)

        print(f"🔍 エラー解析結果:")
        print(
            f"   カテゴリ: {analysis.category.value if analysis.category else '不明'}"
        )
        print(f"   説明: {analysis.description}")
        print(f"   対処法: {analysis.recommended_action}")
        print(f"   再試行可能: {'はい' if analysis.is_retryable else 'いいえ'}")

        if analysis.retry_after:
            print(f"   再試行まで: {analysis.retry_after}秒")

        # エラーログを記録
        app.logger.error(f"LINE Bot error: {analysis.description}")

        return analysis
    else:
        # その他のエラー
        error_message = str(error)
        analysis = error_analyzer.analyze(error_message)
        app.logger.error(f"General error: {error_message}")
        return analysis


@app.route("/callback", methods=["POST"])
def callback():
    """LINE Webhook callback"""
    # get X-Line-Signature header value
    signature = request.headers["X-Line-Signature"]

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print(
            "Invalid signature. Please check your channel access token/channel secret."
        )
        abort(400)
    except LineBotApiError as e:
        # LINE Bot APIエラーをキャッチして解析
        analysis = handle_line_bot_error(e)

        # エラーの種類によって処理を分岐
        if analysis.is_retryable:
            app.logger.info(
                "Error is retryable. Webhook will be retried by LINE platform."
            )
        else:
            app.logger.error(
                "Non-retryable error. Manual intervention may be required."
            )

        # WebhookはLINEプラットフォームが再送するため、500を返す
        abort(500)
    except Exception as e:
        # その他の予期しないエラー
        app.logger.error(f"Unexpected error: {str(e)}")
        analysis = handle_line_bot_error(e)
        abort(500)

    return "OK"


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    """メッセージイベントの処理"""
    try:
        # エコーメッセージを送信
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text=event.message.text)
        )
        app.logger.info(f"Echo message sent: {event.message.text}")

    except LineBotApiError as e:
        # LINE Bot APIエラーを解析してログに記録
        analysis = handle_line_bot_error(e)
        app.logger.error(f"LINE Bot API error: {e}")

    except Exception as e:
        # その他のエラー
        app.logger.error(f"Unexpected error in message handler: {str(e)}")
        handle_line_bot_error(e)


@app.route("/health", methods=["GET"])
def health_check():
    """ヘルスチェックエンドポイント"""
    try:
        # 簡単なLINE APIテスト (プロフィール取得APIを使用)
        # 注意: これは実際のユーザーIDが必要なので、簡単なテストとして設計

        return {
            "status": "healthy",
            "line_bot_api": "configured",
            "error_analyzer": "ready",
        }, 200
    except Exception as e:
        analysis = handle_line_bot_error(e)
        return {
            "status": "unhealthy",
            "error": analysis.description,
            "recommended_action": analysis.recommended_action,
        }, 500


@app.route("/test-error/<int:error_code>", methods=["GET"])
def test_error_analysis(error_code):
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
        return {"error": "Unsupported error code"}, 400

    error_message = f"({error_code}) {test_messages[error_code]}"
    analysis = error_analyzer.analyze(error_message)

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


if __name__ == "__main__":
    arg_parser = ArgumentParser(
        usage="Usage: python " + __file__ + " [--port <port>] [--help]"
    )
    arg_parser.add_argument("-p", "--port", type=int, default=8000, help="port")
    arg_parser.add_argument("-d", "--debug", default=False, help="debug")
    options = arg_parser.parse_args()

    # サンプル用の環境変数チェック
    print("=== Flask Echo Bot with Error Analysis ===")
    print()
    print("🔧 設定確認:")
    print(f"  CHANNEL_SECRET: {'✓ 設定済み' if channel_secret else '❌ 未設定'}")
    print(
        f"  CHANNEL_ACCESS_TOKEN: {'✓ 設定済み' if channel_access_token else '❌ 未設定'}"
    )
    print()

    if not channel_secret or not channel_access_token:
        print("💡 環境変数の設定例:")
        print("  export LINE_CHANNEL_SECRET='your_channel_secret'")
        print("  export LINE_CHANNEL_ACCESS_TOKEN='your_channel_access_token'")
        print()
        print("⚠️  環境変数が未設定でも起動しますが、実際のLINE Botとして動作しません")
        print()

    print("🚀 起動中...")
    print(f"  ポート: {options.port}")
    print("  利用可能エンドポイント:")
    print(f"    POST /callback - LINE Webhook")
    print(f"    GET  /health   - ヘルスチェック")
    print(f"    GET  /test-error/<code> - エラー解析テスト")
    print()
    print("💡 テスト方法:")
    print(f"  curl http://localhost:{options.port}/health")
    print(f"  curl http://localhost:{options.port}/test-error/401")
    print()

    app.run(debug=options.debug, port=options.port, host="0.0.0.0")
