# LineErrorAnalyzer API リファレンス

同期処理用のエラー分析器 `LineErrorAnalyzer` の詳細な API ドキュメントです。

## クラス概要

```python
class LineErrorAnalyzer(BaseLineErrorAnalyzer):
    """LINE Bot エラー分析器（同期版）

    LINE Messaging API のエラーを同期的に分析し、
    詳細なエラー情報と推奨対処法を提供します。
    """
```

## 継承関係

```
BaseLineErrorAnalyzer
└── LineErrorAnalyzer
```

## コンストラクタ

### `__init__()`

```python
def __init__(self) -> None:
    """LineErrorAnalyzer を初期化

    エラーデータベースを初期化し、分析の準備を行います。

    Examples:
        >>> analyzer = LineErrorAnalyzer()
    """
```

**パラメータ:**

- なし

**戻り値:**

- なし

## メソッド

### `analyze(error)`

主要なエラー分析メソッドです。様々な形式のエラーを受け取り、詳細な分析結果を返します。

```python
def analyze(self, error: Union[Exception, Dict[str, Any]]) -> LineErrorInfo:
    """エラーを分析して詳細情報を返す

    LINE Bot SDK の例外、辞書形式のエラーデータ、
    HTTP レスポンスオブジェクト等を分析し、
    カテゴリ、重要度、対処法等の詳細情報を提供します。

    Args:
        error: 分析対象のエラー
            - linebot.v3.messaging.exceptions.ApiException
            - linebot.v3.exceptions.InvalidSignatureError
            - linebot.exceptions.LineBotApiError (v2)
            - linebot.exceptions.InvalidSignatureError (v2)
            - Dict[str, Any]: 辞書形式のエラーデータ
            - その他の例外オブジェクト

    Returns:
        LineErrorInfo: 分析結果の詳細情報
            - category: エラーカテゴリ
            - severity: 重要度
            - is_retryable: リトライ可能性
            - recommended_action: 推奨対処法
            - retry_after: 推奨待機時間
            - その他詳細情報

    Examples:
        >>> # LINE Bot SDK v3 例外の分析
        >>> try:
        ...     line_bot_api.reply_message(...)
        ... except ApiException as e:
        ...     result = analyzer.analyze(e)
        ...     print(f"カテゴリ: {result.category.value}")

        >>> # 辞書形式エラーの分析
        >>> error_data = {
        ...     "status_code": 401,
        ...     "message": "Authentication failed",
        ...     "error_code": "40001"
        ... }
        >>> result = analyzer.analyze(error_data)
        >>> print(f"重要度: {result.severity.value}")

        >>> # HTTP レスポンスの分析
        >>> response = requests.post(url, data=data)
        >>> if response.status_code != 200:
        ...     error_data = {
        ...         "status_code": response.status_code,
        ...         "message": response.text,
        ...         "headers": dict(response.headers)
        ...     }
        ...     result = analyzer.analyze(error_data)

    Raises:
        ValueError: 無効な入力形式の場合
        TypeError: サポートされていない型の場合
    """
```

**パラメータ詳細:**

| パラメータ | 型                                 | 説明             | 必須 |
| ---------- | ---------------------------------- | ---------------- | ---- |
| `error`    | `Union[Exception, Dict[str, Any]]` | 分析対象のエラー | ✓    |

**対応エラー形式:**

1. **LINE Bot SDK v3 例外:**

   ```python
   from linebot.v3.messaging.exceptions import ApiException
   from linebot.v3.exceptions import InvalidSignatureError
   ```

2. **LINE Bot SDK v2 例外:**

   ```python
   from linebot.exceptions import LineBotApiError, InvalidSignatureError
   ```

3. **辞書形式エラー:**
   ```python
   {
       "status_code": 400,
       "message": "Error message",
       "error_code": "40100",  # オプション
       "headers": {...}        # オプション
   }
   ```

**戻り値詳細:**

`LineErrorInfo` オブジェクトには以下の属性が含まれます：

| 属性                 | 型                         | 説明                  |
| -------------------- | -------------------------- | --------------------- |
| `status_code`        | `int`                      | HTTP ステータスコード |
| `error_code`         | `Optional[str]`            | LINE API エラーコード |
| `message`            | `str`                      | エラーメッセージ      |
| `category`           | `ErrorCategory`            | エラーカテゴリ        |
| `severity`           | `ErrorSeverity`            | 重要度                |
| `is_retryable`       | `bool`                     | リトライ可能性        |
| `description`        | `str`                      | 詳細説明              |
| `recommended_action` | `str`                      | 推奨対処法            |
| `retry_after`        | `Optional[int]`            | 推奨待機時間（秒）    |
| `raw_error`          | `Dict[str, Any]`           | 元のエラーデータ      |
| `request_id`         | `Optional[str]`            | リクエスト ID         |
| `headers`            | `Optional[Dict[str, str]]` | レスポンスヘッダー    |
| `documentation_url`  | `Optional[str]`            | 関連ドキュメント URL  |

## 使用例

### 基本的な使用方法

```python
from line_bot_error_detective import LineErrorAnalyzer

# 分析器を初期化
analyzer = LineErrorAnalyzer()

# LINE Bot SDK v3 での使用
try:
    line_bot_api.reply_message(...)
except ApiException as e:
    result = analyzer.analyze(e)

    print(f"エラーカテゴリ: {result.category.value}")
    print(f"エラーコード: {result.error_code}")
    print(f"重要度: {result.severity.value}")
    print(f"リトライ可能: {result.is_retryable}")
    print(f"対処法: {result.recommended_action}")

    if result.retry_after:
        print(f"推奨待機時間: {result.retry_after}秒")
```

### エラーカテゴリ別の処理

```python
def handle_line_error(error):
    """エラーカテゴリに応じた処理"""

    result = analyzer.analyze(error)
    category = result.category.value

    if category == "INVALID_TOKEN":
        # トークンエラー -> 認証処理
        refresh_access_token()

    elif category == "RATE_LIMIT":
        # レート制限 -> 待機
        time.sleep(result.retry_after or 60)

    elif category == "INVALID_REPLY_TOKEN":
        # リプライトークンエラー -> ログ記録
        log_reply_token_error(result)

    elif result.is_retryable:
        # その他のリトライ可能エラー
        retry_with_backoff(error)

    else:
        # 修正が必要なエラー
        handle_critical_error(result)
```

### 詳細情報の活用

```python
def detailed_error_handling(error):
    """詳細なエラー情報の活用"""

    result = analyzer.analyze(error)

    # ログ記録
    logger.error(
        f"LINE API Error - Category: {result.category.value}, "
        f"Code: {result.error_code}, "
        f"Status: {result.status_code}, "
        f"Request ID: {result.request_id}"
    )

    # 重要度に応じたアラート
    if result.severity.value == "CRITICAL":
        send_critical_alert(result)
    elif result.severity.value == "HIGH":
        send_warning_alert(result)

    # ドキュメント URL の提供
    if result.documentation_url:
        print(f"詳細情報: {result.documentation_url}")

    # JSON 形式での保存
    with open("error_log.json", "a") as f:
        f.write(result.to_json() + "\n")
```

### HTTP リクエストでの使用

```python
import requests

def api_request_with_error_analysis(url, data):
    """HTTP リクエストでのエラー分析"""

    response = requests.post(url, json=data)

    if response.status_code != 200:
        # レスポンスからエラーデータを構築
        error_data = {
            "status_code": response.status_code,
            "message": response.text,
            "headers": dict(response.headers)
        }

        # JSON レスポンスからエラーコードを抽出
        try:
            json_response = response.json()
            if "details" in json_response and json_response["details"]:
                error_data["error_code"] = json_response["details"][0].get("property")
        except:
            pass

        # エラー分析
        result = analyzer.analyze(error_data)

        if result.is_retryable and result.retry_after:
            print(f"リトライします（{result.retry_after}秒後）")
            time.sleep(result.retry_after)
            return api_request_with_error_analysis(url, data)  # リトライ
        else:
            raise Exception(f"API Error: {result.recommended_action}")

    return response
```

## パフォーマンス特性

### 処理速度

- **単一エラー分析**: ~0.1-0.5ms
- **大量エラー処理**: ~2,000-3,000 errors/sec
- **メモリ使用量**: ~1KB/error

### 最適化のヒント

```python
# 分析器の再利用（推奨）
analyzer = LineErrorAnalyzer()  # 一度だけ初期化

# 大量処理時は非同期版を使用
from line_bot_error_detective import AsyncLineErrorAnalyzer
async_analyzer = AsyncLineErrorAnalyzer()
```

## エラーハンドリング

### 分析失敗時の動作

```python
try:
    result = analyzer.analyze(malformed_error)
except ValueError as e:
    print(f"分析エラー: {e}")
    # フォールバック処理
except TypeError as e:
    print(f"型エラー: {e}")
    # デフォルト処理
```

### 未知のエラー形式

未知の形式のエラーが渡された場合、以下の動作をします：

1. 可能な限り情報を抽出
2. デフォルトカテゴリ（`UNKNOWN_ERROR`）を設定
3. 基本的な推奨対処法を提供

## スレッドセーフティ

`LineErrorAnalyzer` はスレッドセーフです：

```python
import threading

# 複数スレッドで同じ分析器を使用可能
analyzer = LineErrorAnalyzer()

def worker_thread(errors):
    for error in errors:
        result = analyzer.analyze(error)
        process_result(result)

# 複数スレッドで並行実行
threads = []
for error_batch in error_batches:
    thread = threading.Thread(target=worker_thread, args=(error_batch,))
    threads.append(thread)
    thread.start()
```

## 継承とカスタマイズ

### カスタム分析器の作成

```python
class CustomLineErrorAnalyzer(LineErrorAnalyzer):
    """カスタム分析器の例"""

    def analyze(self, error):
        # 基本分析を実行
        result = super().analyze(error)

        # カスタムロジックを追加
        if result.category.value == "UNKNOWN_ERROR":
            # 独自の分析ロジック
            custom_result = self._analyze_custom_error(error)
            if custom_result:
                return custom_result

        return result

    def _analyze_custom_error(self, error):
        """独自のエラー分析ロジック"""
        # カスタム実装
        pass
```

## 関連クラス

- [AsyncLineErrorAnalyzer](async_analyzer.md) - 非同期版
- [BaseLineErrorAnalyzer](base_analyzer.md) - 基底クラス
- [LineErrorInfo](models.md#lineerrorinfo) - 結果データ
- [ErrorDatabase](error_database.md) - エラー分類

## 次のステップ

- [非同期分析器](async_analyzer.md) - 高性能な非同期処理
- [統合ガイド](../integration/line_sdk.md) - LINE Bot SDK との統合
- [使用例](../examples/basic_usage.md) - 実際の使用例
