# 📚 基本的な使用例

LINE Bot エラー分析器の基本的な使用方法を実際のコード例で説明します。

## 🔍 目次

1. [最初のエラー分析](#最初のエラー分析)
2. [LINE Bot SDK との統合](#line-bot-sdk-との統合)
3. [様々なエラー形式の処理](#様々なエラー形式の処理)
4. [エラー情報の活用](#エラー情報の活用)
5. [非同期処理の基本](#非同期処理の基本)

## ⚡ 最初のエラー分析

### 簡単なエラー分析

```python
from linebot_error_analyzer import LineErrorAnalyzer

# 分析器を作成
analyzer = LineErrorAnalyzer()

# 辞書形式のエラーデータを分析
error_data = {
    "status_code": 401,
    "message": "Authentication failed",
    "error_code": "40001"  # LINE API エラーコード
}

# エラーを分析
result = analyzer.analyze(error_data)

# 結果を表示
print(f"カテゴリ: {result.category.value}")
print(f"重要度: {result.severity.value}")
print(f"エラーコード: {result.error_code}")
print(f"説明: {result.description}")
print(f"対処法: {result.recommended_action}")
print(f"リトライ可能: {result.is_retryable}")
```

**出力例:**

```
カテゴリ: INVALID_TOKEN
重要度: CRITICAL
エラーコード: 40001
説明: 認証に失敗しました。チャネルアクセストークンが無効または期限切れです。
対処法: 有効なチャネルアクセストークンを取得して再設定してください。
リトライ可能: False
```

### ステータスコードのみでの分析

```python
# エラーコードがない場合でも分析可能
simple_error = {
    "status_code": 429,
    "message": "Too many requests"
}

result = analyzer.analyze(simple_error)

print(f"カテゴリ: {result.category.value}")      # RATE_LIMIT
print(f"リトライ時間: {result.retry_after}秒")    # 60
print(f"対処法: {result.recommended_action}")
```

## 🔗 LINE Bot SDK との統合

### LINE Bot SDK v3 との統合

```python
from linebot.v3.messaging import ApiClient, Configuration, MessagingApi
from linebot.v3.messaging.exceptions import ApiException
from linebot.v3.messaging.models import ReplyMessageRequest, TextMessage
from linebot_error_analyzer import LineErrorAnalyzer

# LINE Bot の設定
configuration = Configuration(access_token='YOUR_CHANNEL_ACCESS_TOKEN')
api_client = ApiClient(configuration)
line_bot_api = MessagingApi(api_client)

# エラー分析器
analyzer = LineErrorAnalyzer()

def send_reply_message(reply_token: str, text: str):
    """返信メッセージの送信（エラー処理付き）"""

    try:
        # メッセージを送信
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=reply_token,
                messages=[TextMessage(text=text)]
            )
        )
        print("メッセージ送信成功")

    except ApiException as e:
        # LINE API例外を分析
        error_info = analyzer.analyze(e)

        print(f"エラーカテゴリ: {error_info.category.value}")
        print(f"エラーコード: {error_info.error_code}")
        print(f"対処法: {error_info.recommended_action}")

        # エラーの種類に応じた処理
        if error_info.category.value == "INVALID_REPLY_TOKEN":
            print("無効なreplyToken - 新しいイベントから取得してください")
        elif error_info.category.value == "RATE_LIMIT":
            print(f"レート制限 - {error_info.retry_after}秒後にリトライ")
        elif error_info.is_retryable:
            print("リトライ可能なエラー")
        else:
            print("修正が必要なエラー")

# 使用例
send_reply_message("invalid_token", "Hello!")
```

###署名検証エラーの処理

```python
from linebot.v3.exceptions import InvalidSignatureError

def verify_webhook_signature(body: bytes, signature: str):
    """Webhook署名の検証"""

    try:
        # 署名検証のロジック
        webhook_handler.handle(body.decode('utf-8'), signature)
        return True

    except InvalidSignatureError as e:
        # 署名エラーを分析
        error_info = analyzer.analyze(e)

        print(f"署名検証エラー: {error_info.description}")
        print(f"対処法: {error_info.recommended_action}")
        return False
```

## 🔄 様々なエラー形式の処理

### HTTP レスポンスオブジェクトの分析

```python
import requests

def call_line_api_with_requests():
    """requests ライブラリでのAPI呼び出し"""

    url = "https://api.line.me/v2/bot/message/reply"
    headers = {"Authorization": "Bearer YOUR_TOKEN"}
    data = {"replyToken": "invalid", "messages": []}

    response = requests.post(url, json=data, headers=headers)

    if response.status_code != 200:
        # レスポンスオブジェクトから分析用データを作成
        error_data = {
            "status_code": response.status_code,
            "message": response.text,
            "headers": dict(response.headers)
        }

        # JSON レスポンスからエラーコードを抽出
        try:
            json_data = response.json()
            if "details" in json_data and json_data["details"]:
                error_data["error_code"] = json_data["details"][0].get("property")
        except:
            pass

        # エラー分析
        result = analyzer.analyze(error_data)
        print(f"API呼び出しエラー: {result.category.value}")
        print(f"対処法: {result.recommended_action}")
```

### 例外オブジェクトの分析

```python
def handle_various_exceptions():
    """様々な例外の処理例"""

    try:
        # 何らかの処理
        raise Exception("Network error occurred")

    except Exception as e:
        # 例外を辞書形式に変換して分析
        error_data = {
            "status_code": 500,
            "message": str(e),
            "error_type": type(e).__name__
        }

        result = analyzer.analyze(error_data)
        print(f"例外分析結果: {result.category.value}")
```

## 📊 エラー情報の活用

### 詳細な情報の取得

```python
def detailed_error_handling(error):
    """詳細なエラー処理の例"""

    result = analyzer.analyze(error)

    # 基本情報
    print("=== エラー基本情報 ===")
    print(f"ステータスコード: {result.status_code}")
    print(f"エラーコード: {result.error_code}")
    print(f"メッセージ: {result.message}")

    # 分析結果
    print("\n=== 分析結果 ===")
    print(f"カテゴリ: {result.category.value}")
    print(f"重要度: {result.severity.value}")
    print(f"説明: {result.description}")

    # 対処方法
    print("\n=== 対処方法 ===")
    print(f"推奨対処法: {result.recommended_action}")
    print(f"リトライ可能: {result.is_retryable}")
    if result.retry_after:
        print(f"推奨待機時間: {result.retry_after}秒")

    # メタ情報
    print("\n=== メタ情報 ===")
    if result.request_id:
        print(f"リクエストID: {result.request_id}")
    if result.documentation_url:
        print(f"関連ドキュメント: {result.documentation_url}")

    # 元のエラーデータ
    print(f"\n=== 元データ ===")
    print(f"生データ: {result.raw_error}")
```

### JSON 出力での活用

```python
import json

def export_error_analysis(error):
    """エラー分析結果のJSON出力"""

    result = analyzer.analyze(error)

    # JSON形式で出力
    json_output = result.to_json()
    print("JSON出力:")
    print(json.dumps(json.loads(json_output), indent=2, ensure_ascii=False))

    # ファイルに保存
    with open("error_analysis.json", "w", encoding="utf-8") as f:
        f.write(json_output)
```

### エラー分類による処理分岐

```python
def handle_by_category(error):
    """エラーカテゴリに応じた処理分岐"""

    result = analyzer.analyze(error)
    category = result.category.value

    if category == "INVALID_TOKEN":
        # トークンエラー -> 再認証
        print("トークンを再取得してください")
        refresh_access_token()

    elif category == "RATE_LIMIT":
        # レート制限 -> 待機
        wait_time = result.retry_after or 60
        print(f"{wait_time}秒待機します")
        time.sleep(wait_time)

    elif category == "INVALID_REPLY_TOKEN":
        # リプライトークンエラー -> ログのみ
        print("無効なreplyToken（処理をスキップ）")

    elif category == "SERVER_ERROR":
        # サーバーエラー -> リトライ
        if result.is_retryable:
            print("サーバーエラー - リトライします")
            return retry_request()

    else:
        print(f"未処理のエラーカテゴリ: {category}")
        print(f"対処法: {result.recommended_action}")

def refresh_access_token():
    """アクセストークンの再取得"""
    print("アクセストークンを再取得中...")

def retry_request():
    """リクエストのリトライ"""
    print("リクエストをリトライ中...")
```

## ⚡ 非同期処理の基本

### 基本的な非同期分析

```python
import asyncio
from linebot_error_analyzer import AsyncLineErrorAnalyzer

async def basic_async_analysis():
    """基本的な非同期エラー分析"""

    analyzer = AsyncLineErrorAnalyzer()

    error_data = {
        "status_code": 429,
        "message": "Rate limit exceeded",
        "error_code": "42901"
    }

    # 非同期でエラー分析
    result = await analyzer.analyze(error_data)

    print(f"非同期分析結果: {result.category.value}")
    print(f"リトライ時間: {result.retry_after}秒")

# 実行
asyncio.run(basic_async_analysis())
```

### 複数エラーの並行分析

```python
async def parallel_error_analysis():
    """複数エラーの並行分析"""

    analyzer = AsyncLineErrorAnalyzer()

    # 複数のエラー
    errors = [
        {"status_code": 401, "message": "Invalid token", "error_code": "40001"},
        {"status_code": 400, "message": "Bad request", "error_code": "40010"},
        {"status_code": 429, "message": "Rate limit", "error_code": "42901"},
        {"status_code": 500, "message": "Server error", "error_code": "50000"}
    ]

    # 並行して分析
    tasks = [analyzer.analyze(error) for error in errors]
    results = await asyncio.gather(*tasks)

    # 結果の表示
    for i, result in enumerate(results):
        print(f"エラー{i+1}: {result.category.value} ({result.severity.value})")

asyncio.run(parallel_error_analysis())
```

### バッチ処理での高速分析

```python
async def batch_processing_example():
    """バッチ処理での高速分析"""

    analyzer = AsyncLineErrorAnalyzer()

    # 大量のエラーデータ
    errors = []
    for i in range(100):
        errors.append({
            "status_code": 400 + (i % 5),
            "message": f"Error message {i}",
            "error_code": f"4000{i % 10}"
        })

    # バッチ処理で分析（デフォルト: batch_size=10）
    print("バッチ処理開始...")
    start_time = time.time()

    results = await analyzer.analyze_batch(errors, batch_size=20)

    end_time = time.time()
    print(f"100個のエラーを {end_time - start_time:.2f}秒で処理完了")

    # 結果の統計
    categories = {}
    for result in results:
        category = result.category.value
        categories[category] = categories.get(category, 0) + 1

    print("カテゴリ別集計:")
    for category, count in categories.items():
        print(f"  {category}: {count}件")

asyncio.run(batch_processing_example())
```

## 🌟 実用的な統合例

### Webhook 処理での活用

```python
from flask import Flask, request, abort

app = Flask(__name__)
analyzer = LineErrorAnalyzer()

@app.route("/webhook", methods=['POST'])
def webhook():
    """LINE Webhook エンドポイント"""

    try:
        # Webhook処理
        signature = request.headers.get('X-Line-Signature')
        body = request.get_data(as_text=True)

        # 署名検証
        webhook_handler.handle(body, signature)

        return 'OK'

    except InvalidSignatureError as e:
        # 署名エラーを分析
        error_info = analyzer.analyze(e)
        print(f"署名検証エラー: {error_info.recommended_action}")
        abort(400)

    except ApiException as e:
        # API エラーを分析
        error_info = analyzer.analyze(e)

        if error_info.is_retryable:
            print(f"リトライ可能なエラー: {error_info.category.value}")
            # リトライ処理を実装
        else:
            print(f"修正が必要: {error_info.recommended_action}")

        abort(error_info.status_code)
```

### エラーログの構造化

```python
import logging
import json

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def structured_error_logging(error):
    """構造化されたエラーログ"""

    result = analyzer.analyze(error)

    # 構造化ログデータ
    log_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "error_analysis": {
            "category": result.category.value,
            "severity": result.severity.value,
            "error_code": result.error_code,
            "status_code": result.status_code,
            "is_retryable": result.is_retryable,
            "request_id": result.request_id
        },
        "action": {
            "recommended": result.recommended_action,
            "retry_after": result.retry_after
        },
        "raw_error": result.raw_error
    }

    # JSON形式でログ出力
    logger.error(json.dumps(log_data, ensure_ascii=False))
```

## 🚀 次のステップ

- [高度な使用例](advanced_usage.md) - より複雑な使用例
- [統合ガイド](../integration/) - フレームワーク別の詳細な統合方法
- [API リファレンス](../api/) - 詳細な API ドキュメント
