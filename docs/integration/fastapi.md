# 🚀 FastAPI 統合ガイド

LINE Bot Error Analyzer を FastAPI アプリケーションに統合する方法を説明します。

## 基本的な統合

### 依存関係のインストール

```bash
pip install fastapi uvicorn
pip install linebot-error-analyzer
pip install line-bot-sdk  # LINE Bot SDK
```

### 基本的なセットアップ

```python
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from linebot.v3.messaging import ApiClient, Configuration, MessagingApi
from linebot.v3.messaging.exceptions import ApiException
from linebot.v3.exceptions import InvalidSignatureError
from linebot_error_analyzer import LineErrorAnalyzer

app = FastAPI(title="LINE Bot with Error Analysis")
analyzer = LineErrorAnalyzer()

# LINE Bot の設定
configuration = Configuration(access_token='YOUR_CHANNEL_ACCESS_TOKEN')
api_client = ApiClient(configuration)
line_bot_api = MessagingApi(api_client)
```

## 例外ハンドラーの設定

### LINE API 例外ハンドラー

```python
@app.exception_handler(ApiException)
async def line_api_exception_handler(request: Request, exc: ApiException):
    """LINE API例外の統一処理"""

    # エラー分析を実行
    error_info = analyzer.analyze(exc)

    # ログ出力
    print(f"LINE API Error: {error_info.category.value} - {error_info.message}")

    # クライアントレスポンス
    return JSONResponse(
        status_code=error_info.status_code,
        content={
            "error": {
                "type": "line_api_error",
                "category": error_info.category.value,
                "message": error_info.message,
                "error_code": error_info.error_code,
                "guidance": {
                    "description": error_info.description,
                    "recommended_action": error_info.recommended_action,
                    "is_retryable": error_info.is_retryable,
                    "retry_after": error_info.retry_after,
                    "documentation_url": error_info.documentation_url
                },
                "request_id": error_info.request_id
            }
        }
    )

@app.exception_handler(InvalidSignatureError)
async def invalid_signature_handler(request: Request, exc: InvalidSignatureError):
    """署名検証エラーハンドラー"""

    error_info = analyzer.analyze(exc)

    return JSONResponse(
        status_code=401,
        content={
            "error": {
                "type": "signature_error",
                "message": "Invalid webhook signature",
                "guidance": {
                    "description": error_info.description,
                    "recommended_action": error_info.recommended_action
                }
            }
        }
    )
```

### 一般的な例外ハンドラー

```python
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """一般的な例外の処理"""

    # 辞書形式でエラー分析器に渡す
    error_data = {
        "status_code": 500,
        "message": str(exc),
        "error_type": type(exc).__name__
    }

    error_info = analyzer.analyze(error_data)

    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "type": "internal_error",
                "message": "Internal server error",
                "guidance": error_info.recommended_action
            }
        }
    )
```

## 実際の Webhook エンドポイント

### LINE Webhook の実装

```python
from linebot.v3.messaging.models import ReplyMessageRequest, TextMessage
from linebot.v3.webhook import WebhookHandler
from linebot.v3.webhooks.models import MessageEvent, TextMessageContent

webhook_handler = WebhookHandler('YOUR_CHANNEL_SECRET')

@app.post("/webhook")
async def webhook(request: Request):
    """LINE Webhook エンドポイント"""

    # 署名検証
    signature = request.headers.get('x-line-signature')
    body = await request.body()

    try:
        webhook_handler.handle(body.decode('utf-8'), signature)
    except InvalidSignatureError:
        # 署名エラーは例外ハンドラーで処理される
        raise

    return {"status": "ok"}

@webhook_handler.add(MessageEvent, message=TextMessageContent)
def handle_text_message(event):
    """テキストメッセージの処理"""

    try:
        # メッセージの送信
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=f"You said: {event.message.text}")]
            )
        )
    except ApiException as e:
        # API例外は例外ハンドラーで処理される
        raise
```

## 非同期エラー分析

### 非同期分析器の使用

```python
from line_bot_error_detective import AsyncLineErrorAnalyzer

# 非同期分析器の初期化
async_analyzer = AsyncLineErrorAnalyzer()

@app.post("/analyze-errors")
async def analyze_errors(error_data: dict):
    """エラーの非同期分析エンドポイント"""

    try:
        # 非同期でエラー分析
        result = await async_analyzer.analyze(error_data)

        return {
            "analysis": {
                "category": result.category.value,
                "severity": result.severity.value,
                "is_retryable": result.is_retryable,
                "description": result.description,
                "recommended_action": result.recommended_action
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/batch-analyze")
async def batch_analyze_errors(errors: List[dict]):
    """バッチエラー分析エンドポイント"""

    try:
        results = await async_analyzer.analyze_batch(errors, batch_size=20)

        return {
            "total_analyzed": len(results),
            "results": [
                {
                    "category": result.category.value,
                    "severity": result.severity.value,
                    "is_retryable": result.is_retryable
                }
                for result in results
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

## ミドルウェアの実装

### エラー分析ミドルウェア

```python
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import time
import logging

class ErrorAnalysisMiddleware(BaseHTTPMiddleware):
    """エラー分析とログ記録のミドルウェア"""

    def __init__(self, app, analyzer: LineErrorAnalyzer):
        super().__init__(app)
        self.analyzer = analyzer
        self.logger = logging.getLogger(__name__)

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        try:
            response = await call_next(request)

            # レスポンス時間の記録
            process_time = time.time() - start_time
            response.headers["X-Process-Time"] = str(process_time)

            return response

        except ApiException as e:
            # LINE API エラーの分析とログ記録
            error_info = self.analyzer.analyze(e)

            self.logger.error(
                f"LINE API Error - Category: {error_info.category.value}, "
                f"Code: {error_info.error_code}, "
                f"Path: {request.url.path}"
            )

            # エラーレスポンスの生成
            return JSONResponse(
                status_code=error_info.status_code,
                content={
                    "error": {
                        "category": error_info.category.value,
                        "message": error_info.message,
                        "is_retryable": error_info.is_retryable,
                        "recommended_action": error_info.recommended_action
                    }
                }
            )

# ミドルウェアの登録
app.add_middleware(ErrorAnalysisMiddleware, analyzer=analyzer)
```

## 高度な統合パターン

### 依存性注入の活用

```python
from fastapi import Depends

def get_error_analyzer() -> LineErrorAnalyzer:
    """エラー分析器の依存性注入"""
    return analyzer

def get_async_analyzer() -> AsyncLineErrorAnalyzer:
    """非同期エラー分析器の依存性注入"""
    return async_analyzer

@app.post("/send-message")
async def send_message(
    message_data: dict,
    error_analyzer: LineErrorAnalyzer = Depends(get_error_analyzer)
):
    """メッセージ送信とエラー分析"""

    try:
        # メッセージ送信処理
        result = line_bot_api.push_message(...)
        return {"status": "success", "result": result}

    except ApiException as e:
        error_info = error_analyzer.analyze(e)

        if error_info.is_retryable:
            # リトライ可能な場合の処理
            return {
                "status": "retry_needed",
                "error": error_info.category.value,
                "retry_after": error_info.retry_after
            }
        else:
            # リトライ不可能な場合
            raise HTTPException(
                status_code=error_info.status_code,
                detail=error_info.recommended_action
            )
```

### バックグラウンドタスクでの分析

```python
from fastapi import BackgroundTasks

def log_error_analysis(error_info: LineErrorInfo, request_path: str):
    """バックグラウンドでのエラー分析ログ記録"""

    # データベースへの記録
    error_log = {
        "timestamp": datetime.utcnow(),
        "path": request_path,
        "category": error_info.category.value,
        "error_code": error_info.error_code,
        "severity": error_info.severity.value,
        "is_retryable": error_info.is_retryable,
        "request_id": error_info.request_id
    }

    # データベース保存処理
    save_error_log(error_log)

    # 必要に応じてアラート送信
    if error_info.severity.value == "CRITICAL":
        send_alert(error_info)

@app.post("/webhook-with-logging")
async def webhook_with_logging(
    request: Request,
    background_tasks: BackgroundTasks
):
    """ログ記録付きWebhook"""

    try:
        # Webhook処理
        await process_webhook(request)
        return {"status": "ok"}

    except ApiException as e:
        error_info = analyzer.analyze(e)

        # バックグラウンドでエラー分析をログ記録
        background_tasks.add_task(
            log_error_analysis,
            error_info,
            request.url.path
        )

        # エラーレスポンス
        raise HTTPException(
            status_code=error_info.status_code,
            detail=error_info.recommended_action
        )
```

## 設定とベストプラクティス

### 設定ファイル

```python
# config.py
from pydantic import BaseSettings

class Settings(BaseSettings):
    line_channel_access_token: str
    line_channel_secret: str
    log_level: str = "INFO"
    enable_error_analysis: bool = True
    error_analysis_batch_size: int = 20

    class Config:
        env_file = ".env"

settings = Settings()
```

### ログ設定

```python
import logging

# ログ設定
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# エラー分析専用のロガー
error_analysis_logger = logging.getLogger("line_error_analysis")
```

### ヘルスチェックエンドポイント

```python
@app.get("/health")
async def health_check():
    """ヘルスチェック（エラー分析器の状態確認）"""

    try:
        # 簡単なエラー分析テスト
        test_error = {"status_code": 200, "message": "test"}
        result = analyzer.analyze(test_error)

        return {
            "status": "healthy",
            "analyzer": "operational",
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow()
        }
```

## 実行とデプロイ

### 開発環境での実行

```bash
# 開発サーバーの起動
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Docker での実行

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 次のステップ

- [Flask 統合](flask.md) - Flask での統合方法
- [カスタム分析器](custom_analyzer.md) - カスタム分析器の作成
- [パフォーマンス最適化](../performance/optimization.md) - 高速化のテクニック
