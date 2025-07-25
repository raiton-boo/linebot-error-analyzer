# ⚡ クイックスタート

LINE Bot Error Analyzer の基本的な使い方を説明します。

## インストール

```bash
# PyPI からインストール
pip install line-bot-error-analyzer

# または GitHub からクローン
git clone https://github.com/raiton-boo/line-bot-error-analyzer.git
```

## 基本的な使用方法

### 1. 同期処理でのエラー分析

```python
from line_bot_error_analyzer import LineErrorAnalyzer

# 分析器を初期化
analyzer = LineErrorAnalyzer()

# エラーデータを分析
error_data = {
    "status_code": 401,
    "message": "Authentication failed",
    "error_code": "40001"  # LINE API エラーコード
}

result = analyzer.analyze(error_data)

# 結果を表示
print(f"カテゴリ: {result.category.value}")      # AUTH_ERROR
print(f"重要度: {result.severity.value}")        # CRITICAL
print(f"推奨対処法: {result.recommended_action}")
```

### 2. 非同期処理でのエラー分析

```python
import asyncio
from line_bot_error_analyzer import AsyncLineErrorAnalyzer

async def analyze_error():
    analyzer = AsyncLineErrorAnalyzer()

    error_data = {
        "status_code": 429,
        "message": "Too many requests",
        "error_code": "42901"
    }

    result = await analyzer.analyze(error_data)
    print(f"カテゴリ: {result.category.value}")     # RATE_LIMIT
    print(f"リトライ時間: {result.retry_after}秒")

# 実行
asyncio.run(analyze_error())
```

### 3. LINE Bot SDK との統合

```python
from linebot.v3.messaging.exceptions import ApiException
from line_bot_error_analyzer import LineErrorAnalyzer

analyzer = LineErrorAnalyzer()

try:
    # LINE API呼び出し
    line_bot_api.reply_message(...)
except ApiException as e:
    error_info = analyzer.analyze(e)

    if error_info.is_retryable:
        print(f"リトライ可能: {error_info.retry_after}秒後")
    else:
        print(f"対処法: {error_info.recommended_action}")
```

## 次のステップ

- [🎯 実用例集](examples/) - 実際のプロジェクトでの活用方法
- [🚀 FastAPI 統合](integration/fastapi.md) - FastAPI での使用方法
- [📡 LINE Bot SDK 統合](integration/line_sdk.md) - SDK との統合
- [🐛 エラーリファレンス](errors/line_api_codes.md) - 全エラーコード詳細

## よくある質問

**Q: エラーコードがない場合はどうなりますか？**
A: ステータスコードとメッセージパターンから分析を行います。

**Q: 非同期処理の利点は？**
A: 大量のエラーをバッチ処理で高速に分析できます。

**Q: 対応している SDK バージョンは？**
A: LINE Bot SDK v2/v3 系の両方に対応しています。

### Q: カスタム分析器は作成できますか？

A: はい、BaseLineErrorAnalyzer を継承してカスタム分析器を作成できます。
