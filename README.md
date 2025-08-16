# 🤖 LINE Bot Error Analyzer

[![PyPI version](https://badge.fury.io/py/linebot-error-analyzer.svg)](https://badge.fury.io/py/linebot-error-analyzer)
[![Python](https://img.shields.io/pypi/pyversions/linebot-error-analyzer.svg)](https://pypi.org/project/linebot-error-analyzer/)
![GitHub Repo stars](https://img.shields.io/github/stars/raiton-boo/linebot-error-analyzer?style=social)
![GitHub issues](https://img.shields.io/github/issues/raiton-boo/linebot-error-analyzer)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/linebot-error-analyzer)](https://pepy.tech/project/linebot-error-analyzer)

LINE Bot 開発で発生するエラーを自動分析・診断する Python ライブラリです。

LINE Bot API のエラーレスポンス、例外、ログメッセージを解析し、エラーの種類を特定して具体的な解決策を提案します。開発者の生産性向上と LINE Bot の安定運用をサポートします。

**🚀 このライブラリは共同開発者・コントリビューターを募集中です！ご興味のある方は [Discord](https://discord.gg/6qYHH9HY) までご連絡ください。**

## 📋 要件

- **Python**: 3.9 以上（3.9, 3.10, 3.11, 3.12 でテスト済み）
- **LINE Bot SDK**: v2/v3 系に対応（オプション）
- **依存関係**: 標準ライブラリのみ（`typing_extensions`のみ追加）

## ✨ 特徴

- **🔍 自動エラー解析**: LINE Bot API のエラーレスポンス、例外、ログを自動で分類・診断
- **💡 具体的な対処法**: 各エラーに対する実用的な解決策とベストプラクティスを提案
- **⚡ 同期・非同期対応**: 同期処理と非同期処理の両方をサポート
- **🔄 SDK バージョン対応**: LINE Bot SDK v2/v3 系の両方に対応
- **🌐 フレームワーク統合**: Flask、FastAPI、aiohttp などと簡単に統合
- **📊 リトライ判定**: エラーのリトライ可否を自動判定
- **🏷️ エラー分類**: エラーを意味のあるカテゴリに自動分類

## インストール

### 基本インストール

```bash
pip install linebot-error-analyzer
```

### 開発環境用（テスト依存関係含む）

```bash
pip install linebot-error-analyzer[dev]
```

### LINE Bot SDK と一緒にインストール

```bash
# LINE Bot SDK v3 と一緒に
pip install linebot-error-analyzer linebot-sdk

# または全依存関係込み
pip install linebot-error-analyzer[all]
```

### 対応環境

- Python 3.9+
- Windows, macOS, Linux
- LINE Bot SDK v2/v3（オプション）

## 🚀 基本的な使用方法

```python
from linebot_error_analyzer import LineErrorAnalyzer

# アナライザーを初期化
analyzer = LineErrorAnalyzer()

# エラーメッセージ（ログメッセージから）を分析
error_message = "(401) Invalid channel access token"
result = analyzer.analyze(error_message)

print(f"エラーカテゴリ: {result.category.value}")  # AUTH_ERROR
print(f"対処法: {result.recommended_action}")
print(f"リトライ可能: {result.is_retryable}")  # False

# 辞書形式のエラーデータも分析可能
error_data = {
    "status_code": 429,
    "message": "Rate limit exceeded"
}
result2 = analyzer.analyze(error_data)
print(f"カテゴリ: {result2.category.value}")  # RATE_LIMIT
```

### 📝 サポートされる入力パターン

このライブラリは以下の形式のエラーを分析できます：

1. **エラーログメッセージ（文字列）**

   ```python
   analyzer.analyze("(401) Invalid channel access token")
   analyzer.analyze("429 Rate limit exceeded")
   ```

2. **辞書形式のエラーデータ**

   ```python
   analyzer.analyze({
       "status_code": 400,
       "message": "Bad Request"
   })
   ```

3. **LINE Bot SDK 例外（v2/v3）**

   ```python
   # SDK例外を直接渡すことが可能
   try:
       line_bot_api.reply_message(...)
   except LineBotApiError as e:
       analyzer.analyze(e)  # 例外オブジェクトを直接分析
   ```

4. **HTTP レスポンスオブジェクト**
   ```python
   # requests.Response オブジェクトなど
   response = requests.post(...)
   if not response.ok:
       analyzer.analyze(response)
   ```

## 🔗 LINE Bot SDK との統合

```python
from linebot.v3.messaging import ApiClient, MessagingApi
from linebot.v3.messaging.exceptions import ApiException
from linebot_error_analyzer import LineErrorAnalyzer

analyzer = LineErrorAnalyzer()

try:
    # LINE Bot API を呼び出し
    line_bot_api.reply_message(...)
except ApiException as e:
    # 例外を直接解析
    error_info = analyzer.analyze(e)

    if error_info.category.value == "RATE_LIMIT":
        wait_time = error_info.retry_after or 60
        print(f"レート制限エラー: {wait_time}秒後にリトライしてください")
    elif error_info.is_retryable:
        print("一時的なエラー - リトライを推奨")
    else:
        print(f"対処法: {error_info.recommended_action}")
```

## ⚡ 非同期処理

```python
import asyncio
from linebot_error_analyzer import AsyncLineErrorAnalyzer

async def analyze_errors():
    analyzer = AsyncLineErrorAnalyzer()

    # 単一エラーの非同期分析
    result = await analyzer.analyze("(401) Authentication failed")

    # 複数エラーの一括分析（バッチ処理）
    error_messages = [
        "(401) Invalid channel access token",
        "(429) Rate limit exceeded",
        "(400) Bad Request"
    ]
    results = await analyzer.analyze_batch(error_messages, batch_size=10)

    for result in results:
        print(f"エラー: {result.category.value} - {result.recommended_action}")

asyncio.run(analyze_errors())
```

## 📚 ドキュメント

### 詳細ガイド

- **[📖 インストールガイド](docs/installation.md)** - 詳細なセットアップ手順
- **[🚀 クイックスタート](docs/quickstart.md)** - すぐに始められるガイド
- **[🎯 使用例集](docs/examples/)** - 実際のプロジェクトでの活用例
- **[🔧 統合ガイド](docs/integration/)** - FastAPI、Flask との統合
- **[🐛 エラーリファレンス](docs/errors/)** - 全エラーコード詳細とトラブルシューティング

### 💻 実装例

本ライブラリには、実際の LINE Bot 開発で使用できる実装例を含んでいます：

- **[📁 Examples Collection](examples/)** - 実用的な LINE Bot 実装例
  - **`simple_usage.py`** - 基本的な使用方法のデモ
  - **`flask_echo_bot.py`** - Flask を使用したエコー Bot（エラー処理付き）
  - **`fastapi_echo_bot.py`** - FastAPI を使用した非同期エコー Bot
  - **`aiohttp_echo_bot.py`** - aiohttp を使用したフル非同期実装

これらの例は LINE Bot SDK の公式スタイルに準拠し、コピー&ペーストで実際のプロジェクトに使用できるよう設計されています。

詳細は [📖 Examples Guide](examples/README.md) をご覧ください。

## 主要エラーカテゴリ

| カテゴリ              | 説明               | 例                   |
| --------------------- | ------------------ | -------------------- |
| `AUTH_ERROR`          | 認証エラー         | 無効なトークン       |
| `RATE_LIMIT`          | API 呼び出し制限   | 429 エラー           |
| `INVALID_REPLY_TOKEN` | 無効な返信トークン | 期限切れトークン     |
| `USER_NOT_FOUND`      | ユーザー未発見     | 削除されたアカウント |
| `SERVER_ERROR`        | サーバーエラー     | 5xx 系エラー         |

詳細なエラーコード対応表は [📖 エラーリファレンス](docs/errors/line_api_codes.md) をご覧ください。

## 🔧 フレームワーク統合

### FastAPI との統合例

```python
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from linebot.v3.messaging.exceptions import ApiException
from linebot_error_analyzer import LineErrorAnalyzer

app = FastAPI()
analyzer = LineErrorAnalyzer()

@app.exception_handler(ApiException)
async def line_api_exception_handler(request, exc):
    error_info = analyzer.analyze(exc)
    return JSONResponse(
        status_code=error_info.status_code,
        content={
            "error": error_info.category.value,
            "message": error_info.message,
            "action": error_info.recommended_action,
            "retryable": error_info.is_retryable
        }
    )
```

## テスト実行

```bash
# 基本テスト実行
python -m pytest tests/ -v

# テスト用依存関係のインストール
pip install pytest pytest-asyncio
```

## ライセンス

MIT License

## 免責事項

このライブラリは**サードパーティ製**です。LINE 株式会社とは関係ありません。

## 参考リンク

- [LINE Messaging API リファレンス](https://developers.line.biz/ja/reference/messaging-api/)
- [LINE Bot SDK for Python](https://github.com/line/linebot-sdk-python)
- [LINE Developers](https://developers.line.biz/ja/)
