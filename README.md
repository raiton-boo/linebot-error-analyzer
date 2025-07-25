# 🤖 LINE Bot Error Analyzer

[![PyPI version](https://badge.fury.io/py/linebot-error-analyzer.svg)](https://badge.fury.io/py/linebot-error-analyzer)
[![Python](https://img.shields.io/pypi/pyversions/linebot-error-analyzer.svg)](https://pypi.org/project/linebot-error-analyzer/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

LINE Bot のエラーを自動分析・診断する Python ライブラリです。

エラーの原因を特定して、具体的な解決策を提案する「エラー分析器」があなたの LINE Bot 開発をサポートします。

## 📋 要件

- **Python**: 3.9 以上（3.9, 3.10, 3.11, 3.12 でテスト済み）
- **LINE Bot SDK**: v2/v3 系に対応（オプション）
- **依存関係**: 標準ライブラリのみ（`typing_extensions`のみ追加）

## 特徴

- **自動分析**: LINE API のエラーを自動で分類・診断
- **詳細対処法**: 各エラーに対する具体的な解決策を提案
- **同期・非同期対応**: 同期/非同期処理の両方をサポート
- **SDK 両対応**: LINE Bot SDK v2/v3 系の両方に対応
- **フレームワーク対応**: Flask、FastAPI 等で使用可能

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

## 基本的な使用方法

```python
from linebot_error_analyzer import LineErrorAnalyzer

analyzer = LineErrorAnalyzer()

# エラーデータを分析
error_data = {
    "status_code": 401,
    "message": "Authentication failed",
    "error_code": "40001"
}

result = analyzer.analyze(error_data)

print(f"カテゴリ: {result.category.value}")  # AUTH_ERROR
print(f"対処法: {result.recommended_action}")
print(f"リトライ可能: {result.is_retryable}")  # False
```

## LINE Bot SDK との統合

```python
from linebot.v3.messaging import ApiClient, MessagingApi
from linebot.v3.messaging.exceptions import ApiException
from linebot_error_analyzer import LineErrorAnalyzer

analyzer = LineErrorAnalyzer()

try:
    # LINE API呼び出し
    line_bot_api.reply_message(...)
except ApiException as e:
    error_info = analyzer.analyze(e)

    if error_info.category.value == "RATE_LIMIT":
        print(f"レート制限: {error_info.retry_after}秒待機")
    elif error_info.is_retryable:
        print("リトライ可能なエラー")
    else:
        print(f"対処法: {error_info.recommended_action}")
```

## 非同期処理

```python
import asyncio
from linebot_error_analyzer import AsyncLineErrorAnalyzer

async def analyze_errors():
    analyzer = AsyncLineErrorAnalyzer()

    # 単一エラーの分析
    result = await analyzer.analyze(error_data)

    # 複数エラーの一括分析
    errors = [error1, error2, error3]
    results = await analyzer.analyze_batch(errors, batch_size=10)

asyncio.run(analyze_errors())
```

## 📚 ドキュメント

### 詳細ガイド

- **[📖 インストールガイド](docs/installation.md)** - 詳細なセットアップ手順
- **[🚀 クイックスタート](docs/quickstart.md)** - すぐに始められるガイド
- **[🎯 使用例集](docs/examples/)** - 実際のプロジェクトでの活用例
- **[🔧 統合ガイド](docs/integration/)** - FastAPI、Flask との統合
- **[🐛 エラーリファレンス](docs/errors/)** - 全エラーコード詳細とトラブルシューティング

### 実装例

本ライブラリには、実際の LINE Bot 開発で使用できる実装例を含んでいます：

- **[📁 Simple Examples](examples/)** - 実用的なシンプル実装例
  - 署名検証、メッセージ送信、ユーザー管理、グループ操作
  - 本番環境での使用を想定した実装
- **[📁 Complex Examples](examples/)** - 学習・研究用の詳細実装例
  - エラーハンドリングパターンの包括的なデモンストレーション
  - エラー分析器との統合例
  - **注意**: 複雑版の `error_data` 辞書は、実際の LINE API で発生する可能性のあるエラーパターンを示すサンプルです

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

## フレームワーク統合

### FastAPI

```python
from fastapi import FastAPI
from fastapi.responses import JSONResponse
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
            "action": error_info.recommended_action
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
