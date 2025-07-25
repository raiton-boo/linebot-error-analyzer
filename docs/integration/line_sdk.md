# 📡 LINE Bot SDK 統合ガイド

LINE Bot SDK v2/v3 系との詳細な統合方法と実践的な使用例を説明します。

## 概要

LINE Bot Error Analyzer は、LINE Bot SDK の各バージョンとシームレスに統合できます：

- **LINE Bot SDK v3**: 推奨。最新の API と統合
- **LINE Bot SDK v2**: レガシーサポート

## LINE Bot SDK v3 との統合

### 基本セットアップ

```bash
# 必要なパッケージのインストール
pip install line-bot-sdk
pip install linebot-error-analyzer
```

```python
from linebot.v3 import LineBotApi
from linebot.v3.messaging import Configuration, ApiClient, MessagingApi
from linebot.v3.messaging.exceptions import ApiException
from linebot.v3.messaging.models import ReplyMessageRequest, TextMessage
from linebot_error_analyzer import LineErrorAnalyzer

# 設定
configuration = Configuration(access_token='YOUR_CHANNEL_ACCESS_TOKEN')
api_client = ApiClient(configuration)
line_bot_api = MessagingApi(api_client)
analyzer = LineErrorAnalyzer()
```

### 基本的なエラー処理

```python
def send_reply_with_error_handling(reply_token: str, message: str):
    """エラー処理を含む返信送信"""

    try:
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=reply_token,
                messages=[TextMessage(text=message)]
            )
        )
        return True

    except ApiException as e:
        # エラー分析
        error_info = analyzer.analyze(e)

        # ログ出力
        print(f"送信エラー: {error_info.category.value}")
        print(f"ステータス: {error_info.status_code}")
        print(f"エラーコード: {error_info.error_code}")
        print(f"対処法: {error_info.recommended_action}")

        # エラータイプ別の処理
        if error_info.category.value == "INVALID_REPLY_TOKEN":
            print("⚠️ 返信トークンが無効です")
            return False

        elif error_info.category.value == "RATE_LIMIT":
            retry_after = error_info.retry_after or 60
            print(f"⏰ レート制限: {retry_after}秒待機")
            # 実際のアプリでは再試行処理を実装
            return False

        elif error_info.is_retryable:
            print("🔄 リトライ可能なエラー")
            # 実際のアプリでは再試行処理を実装
            return False

        else:
            print("❌ 修正が必要なエラー")
            return False
```

### ユーザープロフィール取得との統合

```python
def get_user_profile_with_error_handling(user_id: str):
    """エラー処理を含むユーザープロフィール取得"""

    try:
        # プロフィール取得
        profile = line_bot_api.get_profile(user_id)
        return {
            "success": True,
            "profile": {
                "display_name": profile.display_name,
                "user_id": profile.user_id,
                "status_message": profile.status_message,
                "picture_url": profile.picture_url
            }
        }

    except ApiException as e:
        error_info = analyzer.analyze(e)

        # エラーコード別の詳細処理
        if error_info.error_code == "40400":
            return {
                "success": False,
                "error": "USER_NOT_FOUND",
                "message": "ユーザーが見つかりません",
                "user_message": "申し訳ございませんが、ユーザー情報を取得できませんでした。"
            }

        elif error_info.error_code == "40402":
            return {
                "success": False,
                "error": "USER_BLOCKED",
                "message": "ユーザーにブロックされています",
                "user_message": "プロフィール情報の取得ができませんが、引き続きサービスをご利用いただけます。"
            }

        else:
            return {
                "success": False,
                "error": error_info.category.value,
                "message": error_info.description,
                "user_message": "一時的な問題が発生しました。しばらく待ってから再度お試しください。",
                "retry_after": error_info.retry_after
            }
```

### Webhook ハンドラーでの統合

```python
from flask import Flask, request, abort
from linebot.v3.webhook import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.webhooks import MessageEvent, TextMessageContent

app = Flask(__name__)
handler = WebhookHandler('YOUR_CHANNEL_SECRET')

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    except Exception as e:
        # 予期しないエラーも分析
        error_info = analyzer.analyze({
            "status_code": 500,
            "message": str(e),
            "error_type": type(e).__name__
        })
        print(f"Webhook エラー: {error_info.description}")
        abort(500)

    return 'OK'

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    """メッセージイベントハンドラー"""

    user_message = event.message.text

    if user_message == "プロフィール":
        # プロフィール取得とエラー処理
        profile_result = get_user_profile_with_error_handling(event.source.user_id)

        if profile_result["success"]:
            reply_text = f"こんにちは、{profile_result['profile']['display_name']}さん！"
        else:
            reply_text = profile_result["user_message"]

        # 返信送信
        send_reply_with_error_handling(event.reply_token, reply_text)

    else:
        # 通常の返信
        send_reply_with_error_handling(
            event.reply_token,
            f"あなたのメッセージ: {user_message}"
        )
```

### 非同期処理での統合

```python
import asyncio
from linebot.v3.aio import AsyncLineBotApi
from line_bot_error_detective import AsyncLineErrorAnalyzer

class AsyncLineBotHandler:
    def __init__(self, access_token: str):
        configuration = Configuration(access_token=access_token)
        api_client = ApiClient(configuration)
        self.line_bot_api = AsyncLineBotApi(api_client)
        self.analyzer = AsyncLineErrorAnalyzer()

    async def send_reply_async(self, reply_token: str, message: str):
        """非同期での返信送信"""

        try:
            await self.line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=reply_token,
                    messages=[TextMessage(text=message)]
                )
            )
            return True

        except ApiException as e:
            error_info = await self.analyzer.analyze(e)

            print(f"非同期送信エラー: {error_info.category.value}")

            if error_info.is_retryable and error_info.retry_after:
                # 非同期での待機とリトライ
                await asyncio.sleep(error_info.retry_after)
                # 実際のアプリではリトライロジックを実装

            return False

    async def get_profile_async(self, user_id: str):
        """非同期でのプロフィール取得"""

        try:
            profile = await self.line_bot_api.get_profile(user_id)
            return {"success": True, "profile": profile}

        except ApiException as e:
            error_info = await self.analyzer.analyze(e)

            return {
                "success": False,
                "error": error_info.category.value,
                "description": error_info.description
            }
```

## LINE Bot SDK v2 との統合

### レガシーサポート

```python
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import LineBotApiError, InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from line_bot_error_detective import LineErrorAnalyzer

# 設定
line_bot_api = LineBotApi('YOUR_CHANNEL_ACCESS_TOKEN')
handler = WebhookHandler('YOUR_CHANNEL_SECRET')
analyzer = LineErrorAnalyzer()

def send_message_v2(reply_token: str, message: str):
    """LINE Bot SDK v2 でのメッセージ送信"""

    try:
        line_bot_api.reply_message(
            reply_token,
            TextSendMessage(text=message)
        )
        return True

    except LineBotApiError as e:
        # v2 例外の分析
        error_info = analyzer.analyze({
            "status_code": e.status_code,
            "message": e.message,
            "error_details": e.error.details if hasattr(e.error, 'details') else None
        })

        print(f"v2 送信エラー: {error_info.category.value}")
        return False
```

## 高度な統合パターン

### エラー統計とモニタリング

```python
from collections import defaultdict
from datetime import datetime, timedelta
import json

class LineErrorMonitor:
    """LINE API エラーの統計とモニタリング"""

    def __init__(self):
        self.analyzer = LineErrorAnalyzer()
        self.error_stats = defaultdict(int)
        self.error_history = []

    def analyze_and_track(self, error):
        """エラー分析と統計記録"""

        error_info = self.analyzer.analyze(error)

        # 統計更新
        self.error_stats[error_info.category.value] += 1

        # 履歴記録
        self.error_history.append({
            "timestamp": datetime.now().isoformat(),
            "category": error_info.category.value,
            "status_code": error_info.status_code,
            "error_code": error_info.error_code,
            "severity": error_info.severity.value,
            "is_retryable": error_info.is_retryable
        })

        # アラート判定
        self._check_alerts(error_info)

        return error_info

    def _check_alerts(self, error_info):
        """アラート条件のチェック"""

        # 重要度の高いエラー
        if error_info.severity.value == "CRITICAL":
            self._send_alert(f"重要エラー発生: {error_info.category.value}")

        # エラー頻度チェック（過去1時間）
        recent_errors = [
            e for e in self.error_history
            if datetime.fromisoformat(e["timestamp"]) > datetime.now() - timedelta(hours=1)
        ]

        if len(recent_errors) > 100:  # 閾値
            self._send_alert(f"エラー頻度が高いです: {len(recent_errors)}件/時間")

    def _send_alert(self, message):
        """アラート送信（実装例）"""
        print(f"🚨 アラート: {message}")
        # 実際の実装では Slack、メール等に送信

    def get_stats(self):
        """エラー統計の取得"""
        return {
            "total_errors": len(self.error_history),
            "error_by_category": dict(self.error_stats),
            "recent_errors": self.error_history[-10:]  # 最近の10件
        }

# 使用例
monitor = LineErrorMonitor()

def monitored_api_call(func, *args, **kwargs):
    """モニタリング付き API 呼び出し"""
    try:
        return func(*args, **kwargs)
    except ApiException as e:
        error_info = monitor.analyze_and_track(e)

        # エラー情報をログに記録
        print(f"API エラー: {error_info.description}")

        raise  # 必要に応じて再発生
```

### 自動リトライ機能

```python
import asyncio
from functools import wraps
from typing import Callable, Any

def line_api_retry(max_retries: int = 3, base_delay: float = 1.0):
    """LINE API 自動リトライデコレータ"""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            analyzer = AsyncLineErrorAnalyzer()

            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)

                except ApiException as e:
                    error_info = await analyzer.analyze(e)

                    if attempt == max_retries or not error_info.is_retryable:
                        # 最後の試行または非リトライエラー
                        raise

                    # リトライ待機時間の計算
                    delay = error_info.retry_after or (base_delay * (2 ** attempt))

                    print(f"リトライ {attempt + 1}/{max_retries}: {delay}秒待機")
                    await asyncio.sleep(delay)

            return None

        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            analyzer = LineErrorAnalyzer()

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)

                except ApiException as e:
                    error_info = analyzer.analyze(e)

                    if attempt == max_retries or not error_info.is_retryable:
                        raise

                    delay = error_info.retry_after or (base_delay * (2 ** attempt))

                    print(f"リトライ {attempt + 1}/{max_retries}: {delay}秒待機")
                    import time
                    time.sleep(delay)

            return None

        # 非同期関数かどうかで分岐
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator

# 使用例
@line_api_retry(max_retries=3, base_delay=1.0)
def reliable_reply_message(reply_token: str, message: str):
    """自動リトライ付きメッセージ送信"""
    line_bot_api.reply_message(
        ReplyMessageRequest(
            reply_token=reply_token,
            messages=[TextMessage(text=message)]
        )
    )

@line_api_retry(max_retries=2, base_delay=0.5)
async def reliable_get_profile_async(user_id: str):
    """自動リトライ付きプロフィール取得（非同期）"""
    return await async_line_bot_api.get_profile(user_id)
```

## ベストプラクティス

### 1. エラーレスポンスの設計

```python
def create_user_friendly_response(error_info):
    """ユーザーフレンドリーなエラーレスポンス作成"""

    user_messages = {
        "INVALID_REPLY_TOKEN": "申し訳ございません。もう一度最初からお試しください。",
        "RATE_LIMIT": "現在アクセスが集中しております。少し時間をおいてから再度お試しください。",
        "USER_NOT_FOUND": "申し訳ございませんが、ユーザー情報を取得できませんでした。",
        "USER_BLOCKED": "プロフィール情報の取得ができませんが、引き続きサービスをご利用いただけます。",
        "SERVER_ERROR": "一時的な問題が発生しました。しばらく待ってから再度お試しください。",
        "AUTH_ERROR": "認証に問題があります。管理者にお問い合わせください。"
    }

    return user_messages.get(
        error_info.category.value,
        "申し訳ございませんが、エラーが発生しました。"
    )
```

### 2. ログ記録の標準化

```python
import logging
import json

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('line_bot_errors')

def log_line_error(error_info, context=None):
    """LINE エラーの構造化ログ記録"""

    log_data = {
        "error_category": error_info.category.value,
        "status_code": error_info.status_code,
        "error_code": error_info.error_code,
        "severity": error_info.severity.value,
        "is_retryable": error_info.is_retryable,
        "retry_after": error_info.retry_after,
        "description": error_info.description,
        "recommended_action": error_info.recommended_action
    }

    if context:
        log_data["context"] = context

    if error_info.severity.value == "CRITICAL":
        logger.error(json.dumps(log_data, ensure_ascii=False))
    elif error_info.severity.value == "HIGH":
        logger.warning(json.dumps(log_data, ensure_ascii=False))
    else:
        logger.info(json.dumps(log_data, ensure_ascii=False))
```

### 3. テスト戦略

```python
import pytest
from unittest.mock import Mock, patch
from linebot.v3.exceptions import ApiException

@pytest.fixture
def mock_api_exception():
    """ApiException のモック"""
    exception = Mock(spec=ApiException)
    exception.status_code = 401
    exception.detail = Mock()
    exception.detail.error_code = "40001"
    return exception

def test_error_handling_integration(mock_api_exception):
    """エラー処理統合テスト"""

    analyzer = LineErrorAnalyzer()

    with patch.object(line_bot_api, 'reply_message', side_effect=mock_api_exception):
        result = send_reply_with_error_handling("test_token", "test_message")

        assert result is False  # エラーのため送信失敗

    # エラー分析結果の確認
    error_info = analyzer.analyze(mock_api_exception)
    assert error_info.category.value == "INVALID_TOKEN"
    assert error_info.status_code == 401
```

## まとめ

LINE Bot SDK との統合により、堅牢で信頼性の高い LINE Bot アプリケーションを構築できます：

- **自動エラー分析**: 詳細なエラー情報による適切な対応
- **ユーザーフレンドリー**: エラー時も適切なメッセージを表示
- **モニタリング**: エラー統計による品質向上
- **自動リトライ**: 一時的な問題の自動解決

次のステップ：

- **[FastAPI 統合](fastapi.md)** - Web フレームワークとの統合
- **[実用例](../examples/)** - より複雑な使用例
- **[API リファレンス](../api/)** - 詳細な API 仕様
