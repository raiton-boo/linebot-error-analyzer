# LINE Bot Error Analyzer Examples

LINE Bot Error Analyzer の使用例集です。実際のプロジェクトでコピペして使えるように設計されています。

## 📁 ファイル一覧

### 基本的な使用例

- **`simple_usage.py`** - 最もシンプルな使用例

### Web フレームワーク統合

- **`flask_echo_bot.py`** - Flask での LINE Bot (LINE SDK 風)
- **`fastapi_echo_bot.py`** - FastAPI での LINE Bot (非同期)
- **`aiohttp_echo_bot.py`** - aiohttp での完全非同期実装

## 🚀 クイックスタート

### 1. 最もシンプルな例

```bash
python simple_usage.py
```

### 2. Flask Echo Bot

```bash
# 環境変数を設定
export LINE_CHANNEL_SECRET="your_channel_secret"
export LINE_CHANNEL_ACCESS_TOKEN="your_channel_access_token"

# Flask Echo Botを起動
python flask_echo_bot.py --port 8000
```

### 3. FastAPI Echo Bot

```bash
# 依存関係をインストール
pip install fastapi uvicorn

# FastAPI Echo Botを起動
python fastapi_echo_bot.py --port 8000 --reload
```

### 4. aiohttp Echo Bot

```bash
# 依存関係をインストール
pip install aiohttp

# aiohttp Echo Botを起動
python aiohttp_echo_bot.py --port 8000
```

## 🔧 設定

### LINE Bot 設定

LINE Developers コンソールで Bot を作成後：

1. **Channel Secret** と **Channel Access Token** を取得
2. 環境変数に設定：
   ```bash
   export LINE_CHANNEL_SECRET="your_channel_secret"
   export LINE_CHANNEL_ACCESS_TOKEN="your_channel_access_token"
   ```

### ngrok でテスト

```bash
# ngrokをインストール
# https://ngrok.com/

# サーバーを起動（例：Flask）
python flask_echo_bot.py --port 8000

# 別ターミナルでngrokを起動
ngrok http 8000

# 表示されたURLをLINE Developersのwebhook URLに設定
# 例: https://abc123.ngrok.io/callback
```

## 📊 使用例

### 基本的なエラー解析

```python
from linebot_error_analyzer import LineErrorAnalyzer

analyzer = LineErrorAnalyzer()
result = analyzer.analyze("(401) Invalid channel access token")

print(f"説明: {result.description}")
print(f"対処法: {result.recommended_action}")
print(f"再試行可能: {result.is_retryable}")
```

### 非同期での解析

```python
import asyncio
from linebot_error_analyzer import AsyncLineErrorAnalyzer

async def analyze_errors():
    analyzer = AsyncLineErrorAnalyzer()
    result = await analyzer.analyze("(429) Rate limit exceeded")
    return result

result = asyncio.run(analyze_errors())
```

### Webhook エラーハンドリング

```python
from linebot.exceptions import LineBotApiError
from linebot_error_analyzer import LineErrorAnalyzer

analyzer = LineErrorAnalyzer()

try:
    line_bot_api.reply_message(reply_token, message)
except LineBotApiError as e:
    # エラーを解析
    error_msg = f"({e.status_code}) {e.message}"
    analysis = analyzer.analyze(error_msg)

    # 分析結果に基づいて処理分岐
    if analysis.is_retryable:
        # 再試行ロジック
        print(f"再試行します: {analysis.recommended_action}")
    else:
        # エラー通知
        print(f"手動対応が必要: {analysis.description}")
```

## 🧪 テスト用エンドポイント

各 Web 統合例には、テスト用のエンドポイントが含まれています：

### ヘルスチェック

```bash
curl http://localhost:8000/health
```

### エラー解析テスト

```bash
# 401エラーをテスト
curl http://localhost:8000/test-error/401

# 429エラーをテスト
curl http://localhost:8000/test-error/429
```

## 実装のヒント

### 1. エラーレート監視

```python
# 1分間のエラー数を監視
recent_errors = [e for e in error_history
                if now - e.timestamp <= timedelta(minutes=1)]
if len(recent_errors) > 10:
    send_alert("高いエラー率を検出")
```

### 2. 再試行ロジック

```python
if analysis.is_retryable:
    retry_after = analysis.retry_after or 60
    schedule_retry(task, delay=retry_after)
```

## 📚 関連リンク

- [LINE Bot SDK Examples](https://github.com/line/line-bot-sdk-python/tree/master/examples)
- [LINE Developers](https://developers.line.biz/)
- [ngrok](https://ngrok.com/)
