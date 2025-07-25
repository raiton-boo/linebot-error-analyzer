# データモデル - LineErrorInfo とエラーカテゴリ

LINE エラー分析器で使用される全データモデルの詳細仕様です。

## LineErrorInfo クラス

エラー分析結果を格納するメインのデータクラスです。

### クラス定義

```python
@dataclass
class LineErrorInfo:
    """LINE API エラー分析結果"""

    # 基本情報
    status_code: int           # HTTPステータスコード
    error_code: Optional[str]  # LINE APIエラーコード
    message: str              # エラーメッセージ

    # 分析結果
    category: ErrorCategory   # エラーカテゴリ
    severity: ErrorSeverity   # 重要度
    is_retryable: bool       # リトライ可能性

    # 詳細情報
    description: str          # エラーの詳細説明
    recommended_action: str   # 推奨対処法
    retry_after: Optional[int] # リトライ推奨時間（秒）

    # メタデータ
    raw_error: Dict[str, Any]         # 元のエラーデータ
    request_id: Optional[str]         # リクエストID
    headers: Optional[Dict[str, str]] # レスポンスヘッダー
    documentation_url: Optional[str]  # 関連ドキュメントURL
    context: Optional[Dict[str, Any]] # コンテキスト情報
```

### 基本情報フィールド

#### `status_code: int`

HTTP ステータスコード

```python
result = analyzer.analyze({"status_code": 401})
print(result.status_code)  # 401
```

**値の範囲**:

- `200-299`: 成功（通常はエラー分析対象外）
- `400-499`: クライアントエラー
- `500-599`: サーバーエラー

#### `error_code: Optional[str]`

LINE API 固有のエラーコード

```python
result = analyzer.analyze({
    "status_code": 400,
    "error_code": "40100"
})
print(result.error_code)  # "40100"
```

**主要エラーコード**:

- `40001`: 無効なチャネルアクセストークン
- `40100`: 無効な返信トークン
- `42901`: レート制限
- `50000`: サーバー内部エラー

#### `message: str`

エラーメッセージ（原文）

```python
result = analyzer.analyze({
    "status_code": 401,
    "message": "Authentication failed"
})
print(result.message)  # "Authentication failed"
```

### 分析結果フィールド

#### `category: ErrorCategory`

自動分類されたエラーカテゴリ

```python
result = analyzer.analyze({"status_code": 401})
print(result.category.value)  # "AUTH_ERROR"
print(result.category)        # ErrorCategory.AUTH_ERROR
```

#### `severity: ErrorSeverity`

エラーの重要度レベル

```python
result = analyzer.analyze({"status_code": 500})
print(result.severity.value)  # "HIGH"
print(result.severity)       # ErrorSeverity.HIGH
```

#### `is_retryable: bool`

自動リトライの推奨可否

```python
result = analyzer.analyze({"status_code": 429})  # レート制限
print(result.is_retryable)  # True

result = analyzer.analyze({"status_code": 401})  # 認証エラー
print(result.is_retryable)  # False
```

### 詳細情報フィールド

#### `description: str`

日本語での詳細な説明

```python
result = analyzer.analyze({"status_code": 401})
print(result.description)
# "認証に失敗しました。チャネルアクセストークンが無効または期限切れです。"
```

#### `recommended_action: str`

推奨される対処法

```python
result = analyzer.analyze({"status_code": 401})
print(result.recommended_action)
# "有効なチャネルアクセストークンを取得して再設定してください。"
```

#### `retry_after: Optional[int]`

リトライ推奨時間（秒）

```python
result = analyzer.analyze({
    "status_code": 429,
    "headers": {"Retry-After": "60"}
})
print(result.retry_after)  # 60
```

### メタデータフィールド

#### `raw_error: Dict[str, Any]`

元のエラーデータ（デバッグ用）

```python
original_error = {"status_code": 401, "custom_field": "value"}
result = analyzer.analyze(original_error)
print(result.raw_error)  # {"status_code": 401, "custom_field": "value"}
```

#### `request_id: Optional[str]`

リクエスト追跡 ID

```python
result = analyzer.analyze({
    "status_code": 500,
    "headers": {"X-Line-Request-Id": "req_123456"}
})
print(result.request_id)  # "req_123456"
```

#### `headers: Optional[Dict[str, str]]`

レスポンスヘッダー情報

```python
result = analyzer.analyze({
    "status_code": 429,
    "headers": {
        "Retry-After": "60",
        "X-RateLimit-Remaining": "0"
    }
})
print(result.headers)  # {"Retry-After": "60", "X-RateLimit-Remaining": "0"}
```

#### `documentation_url: Optional[str]`

関連ドキュメント URL

```python
result = analyzer.analyze({"status_code": 401})
print(result.documentation_url)
# "https://developers.line.biz/ja/docs/basics/channel-access-token/"
```

#### `context: Optional[Dict[str, Any]]`

コンテキスト情報（非同期分析器でのみ設定）

```python
context = {"user_id": "U1234", "endpoint": "/reply"}
result = await async_analyzer.analyze_with_context(error, context)
print(result.context)  # {"user_id": "U1234", "endpoint": "/reply"}
```

## エラーカテゴリ (ErrorCategory)

エラーの分類を表す Enum 型です。

```python
from enum import Enum

class ErrorCategory(Enum):
    # 認証・認可関連
    AUTH_ERROR = "AUTH_ERROR"
    INVALID_TOKEN = "INVALID_TOKEN"
    EXPIRED_TOKEN = "EXPIRED_TOKEN"
    INVALID_SIGNATURE = "INVALID_SIGNATURE"

    # リクエスト関連
    INVALID_PARAM = "INVALID_PARAM"
    INVALID_REQUEST_BODY = "INVALID_REQUEST_BODY"
    INVALID_JSON = "INVALID_JSON"
    PAYLOAD_TOO_LARGE = "PAYLOAD_TOO_LARGE"

    # メッセージ関連
    INVALID_REPLY_TOKEN = "INVALID_REPLY_TOKEN"
    REPLY_TOKEN_EXPIRED = "REPLY_TOKEN_EXPIRED"
    REPLY_TOKEN_USED = "REPLY_TOKEN_USED"
    MESSAGE_SEND_FAILED = "MESSAGE_SEND_FAILED"

    # ユーザー関連
    USER_NOT_FOUND = "USER_NOT_FOUND"
    USER_BLOCKED = "USER_BLOCKED"
    FORBIDDEN = "FORBIDDEN"

    # レート制限・クォータ
    RATE_LIMIT = "RATE_LIMIT"
    QUOTA_EXCEEDED = "QUOTA_EXCEEDED"
    CONCURRENT_LIMIT = "CONCURRENT_LIMIT"

    # サーバー・ネットワーク
    SERVER_ERROR = "SERVER_ERROR"
    NETWORK_ERROR = "NETWORK_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"

    # その他
    UNKNOWN_ERROR = "UNKNOWN_ERROR"
```

### カテゴリ別詳細

#### 認証・認可関連

| カテゴリ            | 説明               | 典型的なステータス | 対処法               |
| ------------------- | ------------------ | ------------------ | -------------------- |
| `AUTH_ERROR`        | 一般的な認証エラー | 401                | 認証情報の確認・更新 |
| `INVALID_TOKEN`     | 無効なトークン     | 401                | 新しいトークンの取得 |
| `EXPIRED_TOKEN`     | 期限切れトークン   | 401                | トークンの更新       |
| `INVALID_SIGNATURE` | 署名検証失敗       | 401                | 署名ロジックの確認   |

#### リクエスト関連

| カテゴリ               | 説明                   | 典型的なステータス | 対処法               |
| ---------------------- | ---------------------- | ------------------ | -------------------- |
| `INVALID_PARAM`        | 無効なパラメータ       | 400                | パラメータの修正     |
| `INVALID_REQUEST_BODY` | 無効なリクエストボディ | 400                | リクエスト形式の修正 |
| `INVALID_JSON`         | JSON 解析エラー        | 400                | JSON 形式の修正      |
| `PAYLOAD_TOO_LARGE`    | リクエストサイズ超過   | 413                | データサイズの削減   |

## エラー重要度 (ErrorSeverity)

エラーの重要度を表す Enum 型です。

```python
class ErrorSeverity(Enum):
    LOW = "LOW"         # 軽微なエラー
    MEDIUM = "MEDIUM"   # 中程度のエラー
    HIGH = "HIGH"       # 重要なエラー
    CRITICAL = "CRITICAL" # 緊急対応が必要
```

### 重要度の判定基準

| 重要度     | 説明             | 例                   | 対応優先度 |
| ---------- | ---------------- | -------------------- | ---------: |
| `LOW`      | サービス継続可能 | バリデーションエラー |          4 |
| `MEDIUM`   | 機能制限あり     | レート制限           |          3 |
| `HIGH`     | サービス影響大   | サーバーエラー       |          2 |
| `CRITICAL` | サービス停止     | 認証エラー           |          1 |

## ユーティリティメソッド

### `to_dict()` メソッド

LineErrorInfo を辞書形式に変換します。

```python
result = analyzer.analyze({"status_code": 401})
error_dict = result.to_dict()

print(error_dict)
# {
#     "status_code": 401,
#     "error_code": None,
#     "message": "Authentication failed",
#     "category": "AUTH_ERROR",
#     "severity": "CRITICAL",
#     "is_retryable": False,
#     "description": "認証に失敗しました...",
#     "recommended_action": "有効なチャネルアクセストークンを...",
#     "retry_after": None,
#     "request_id": None,
#     "documentation_url": "https://developers.line.biz/..."
# }
```

### `to_json()` メソッド

構造化された JSON 形式で出力します。

```python
result = analyzer.analyze({"status_code": 401})
json_output = result.to_json()

print(json_output)
# {
#   "basic": {
#     "status_code": 401,
#     "error_code": null,
#     "message": "Authentication failed"
#   },
#   "analysis": {
#     "category": "AUTH_ERROR",
#     "severity": "CRITICAL",
#     "is_retryable": false
#   },
#   "guidance": {
#     "description": "認証に失敗しました...",
#     "recommended_action": "有効なチャネルアクセストークンを...",
#     "retry_after": null,
#     "documentation_url": "https://developers.line.biz/..."
#   }
# }
```

### `is_client_error()` メソッド

クライアント側のエラーかどうかを判定します。

```python
result = analyzer.analyze({"status_code": 400})
print(result.is_client_error())  # True

result = analyzer.analyze({"status_code": 500})
print(result.is_client_error())  # False
```

### `is_server_error()` メソッド

サーバー側のエラーかどうかを判定します。

```python
result = analyzer.analyze({"status_code": 500})
print(result.is_server_error())  # True

result = analyzer.analyze({"status_code": 400})
print(result.is_server_error())  # False
```

### `requires_immediate_attention()` メソッド

即座の対応が必要かどうかを判定します。

```python
result = analyzer.analyze({"status_code": 401})  # CRITICAL
print(result.requires_immediate_attention())  # True

result = analyzer.analyze({"status_code": 400})  # MEDIUM
print(result.requires_immediate_attention())  # False
```

## 使用例とパターン

### 1. エラー情報の構造化ログ出力

```python
import json
import logging

def log_structured_error(error_info: LineErrorInfo):
    """構造化されたエラーログの出力"""

    log_data = {
        "timestamp": datetime.now().isoformat(),
        "error": {
            "category": error_info.category.value,
            "severity": error_info.severity.value,
            "status_code": error_info.status_code,
            "error_code": error_info.error_code,
            "is_retryable": error_info.is_retryable
        },
        "details": {
            "message": error_info.message,
            "description": error_info.description,
            "recommended_action": error_info.recommended_action
        },
        "metadata": {
            "request_id": error_info.request_id,
            "retry_after": error_info.retry_after,
            "documentation_url": error_info.documentation_url
        }
    }

    # 重要度に応じたログレベル
    if error_info.severity == ErrorSeverity.CRITICAL:
        logging.error(json.dumps(log_data, ensure_ascii=False))
    elif error_info.severity == ErrorSeverity.HIGH:
        logging.warning(json.dumps(log_data, ensure_ascii=False))
    else:
        logging.info(json.dumps(log_data, ensure_ascii=False))
```

### 2. エラー統計の収集

```python
from collections import defaultdict
from typing import List

class ErrorStatistics:
    def __init__(self):
        self.stats = {
            "total_count": 0,
            "by_category": defaultdict(int),
            "by_severity": defaultdict(int),
            "by_status_code": defaultdict(int),
            "retryable_count": 0,
            "with_error_code": 0
        }

    def add_error(self, error_info: LineErrorInfo):
        """エラー統計への追加"""

        self.stats["total_count"] += 1
        self.stats["by_category"][error_info.category.value] += 1
        self.stats["by_severity"][error_info.severity.value] += 1
        self.stats["by_status_code"][error_info.status_code] += 1

        if error_info.is_retryable:
            self.stats["retryable_count"] += 1

        if error_info.error_code:
            self.stats["with_error_code"] += 1

    def get_summary(self) -> dict:
        """統計サマリーの取得"""

        total = self.stats["total_count"]
        if total == 0:
            return {"message": "エラーデータがありません"}

        return {
            "total_errors": total,
            "retryable_percentage": round(self.stats["retryable_count"] / total * 100, 1),
            "error_code_coverage": round(self.stats["with_error_code"] / total * 100, 1),
            "top_categories": dict(sorted(
                self.stats["by_category"].items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]),
            "severity_distribution": dict(self.stats["by_severity"])
        }

# 使用例
stats = ErrorStatistics()

errors = [
    {"status_code": 401, "message": "Auth error"},
    {"status_code": 429, "message": "Rate limit"},
    {"status_code": 500, "message": "Server error"}
]

for error in errors:
    result = analyzer.analyze(error)
    stats.add_error(result)

summary = stats.get_summary()
print(json.dumps(summary, indent=2, ensure_ascii=False))
```

### 3. カスタムフィールドの追加

```python
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

@dataclass
class ExtendedLineErrorInfo(LineErrorInfo):
    """拡張されたエラー情報"""

    # カスタムフィールド
    user_id: Optional[str] = None
    api_endpoint: Optional[str] = None
    response_time_ms: Optional[int] = None
    client_version: Optional[str] = None
    custom_tags: Dict[str, Any] = field(default_factory=dict)

    def add_tag(self, key: str, value: Any):
        """カスタムタグの追加"""
        self.custom_tags[key] = value

    def get_extended_summary(self) -> dict:
        """拡張サマリーの取得"""

        base_summary = self.to_dict()
        base_summary.update({
            "user_id": self.user_id,
            "api_endpoint": self.api_endpoint,
            "response_time_ms": self.response_time_ms,
            "client_version": self.client_version,
            "custom_tags": self.custom_tags
        })

        return base_summary

# カスタム分析器での使用
class ExtendedLineErrorAnalyzer(LineErrorAnalyzer):
    def analyze_extended(self, error, **kwargs) -> ExtendedLineErrorInfo:
        """拡張エラー分析"""

        base_result = super().analyze(error)

        # 基本結果から拡張結果を作成
        extended_result = ExtendedLineErrorInfo(
            status_code=base_result.status_code,
            error_code=base_result.error_code,
            message=base_result.message,
            category=base_result.category,
            severity=base_result.severity,
            is_retryable=base_result.is_retryable,
            description=base_result.description,
            recommended_action=base_result.recommended_action,
            retry_after=base_result.retry_after,
            raw_error=base_result.raw_error,
            request_id=base_result.request_id,
            headers=base_result.headers,
            documentation_url=base_result.documentation_url,
            context=base_result.context
        )

        # 拡張フィールドの設定
        extended_result.user_id = kwargs.get('user_id')
        extended_result.api_endpoint = kwargs.get('api_endpoint')
        extended_result.response_time_ms = kwargs.get('response_time_ms')
        extended_result.client_version = kwargs.get('client_version')

        return extended_result
```

## まとめ

LINE エラー分析器のデータモデルは以下の特徴を持ちます：

- **包括的な情報**: 基本情報から詳細分析まで網羅
- **構造化データ**: JSON/辞書形式での出力サポート
- **拡張可能性**: カスタムフィールドの追加が容易
- **実用的なメソッド**: 判定・分類・出力の便利機能
- **型安全性**: Enum と dataclass による型安全な設計

次のステップ:

- **[LineErrorAnalyzer](analyzer.md)** - 同期分析器の API
- **[AsyncLineErrorAnalyzer](async_analyzer.md)** - 非同期分析器の API
- **[エラーリファレンス](../errors/line_api_codes.md)** - 全エラーコード詳細
