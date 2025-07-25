# AsyncLineErrorAnalyzer - 非同期エラー分析器

非同期処理に特化したエラー分析器の完全な API リファレンスです。

## クラス概要

```python
class AsyncLineErrorAnalyzer(BaseLineErrorAnalyzer)
```

**継承**: `BaseLineErrorAnalyzer`  
**用途**: 高パフォーマンスな非同期エラー分析  
**特徴**: バッチ処理、並行処理サポート

## インポート

```python
from line_bot_error_detective import AsyncLineErrorAnalyzer
```

## コンストラクタ

### `__init__()`

```python
analyzer = AsyncLineErrorAnalyzer()
```

**パラメータ**: なし  
**戻り値**: `AsyncLineErrorAnalyzer` インスタンス

## 主要メソッド

### `analyze(error)` (非同期)

単一エラーの非同期分析を実行します。

```python
async def analyze(
    self,
    error: Union[Exception, Dict[str, Any], Any]
) -> LineErrorInfo
```

**パラメータ**:

- `error`: 分析対象のエラー
  - `Exception`: Python 例外オブジェクト
  - `Dict[str, Any]`: エラー情報辞書
  - `Any`: その他のエラーオブジェクト

**戻り値**: `LineErrorInfo` オブジェクト

**例外**: なし（すべてのエラーを分析対象として処理）

#### 使用例

```python
import asyncio
from line_bot_error_detective import AsyncLineErrorAnalyzer

async def analyze_error():
    analyzer = AsyncLineErrorAnalyzer()

    # 辞書形式のエラー
    error_data = {
        "status_code": 429,
        "message": "Too Many Requests",
        "error_code": "42901"
    }

    result = await analyzer.analyze(error_data)

    print(f"カテゴリ: {result.category.value}")
    print(f"リトライ時間: {result.retry_after}秒")

    return result

# 実行
result = asyncio.run(analyze_error())
```

### `analyze_batch(errors, batch_size=100)` (非同期)

複数エラーの一括非同期分析を実行します。

```python
async def analyze_batch(
    self,
    errors: List[Union[Exception, Dict[str, Any], Any]],
    batch_size: int = 100
) -> List[LineErrorInfo]
```

**パラメータ**:

- `errors`: 分析対象のエラーリスト
- `batch_size`: バッチサイズ（デフォルト: 100）

**戻り値**: `LineErrorInfo` オブジェクトのリスト

**パフォーマンス**:

- 並行処理により高速化
- メモリ効率的なバッチ処理
- 大量データ対応（10,000+ エラー）

#### 使用例

```python
async def batch_analysis():
    analyzer = AsyncLineErrorAnalyzer()

    # 大量のエラーデータ
    errors = [
        {"status_code": 400 + i % 100, "message": f"Error {i}"}
        for i in range(1000)
    ]

    # バッチ処理実行
    results = await analyzer.analyze_batch(errors, batch_size=50)

    # 統計情報
    categories = {}
    for result in results:
        category = result.category.value
        categories[category] = categories.get(category, 0) + 1

    print("エラーカテゴリ統計:")
    for category, count in categories.items():
        print(f"  {category}: {count}件")

    return results
```

### `analyze_with_context(error, context)` (非同期)

コンテキスト情報付きでエラー分析を実行します。

```python
async def analyze_with_context(
    self,
    error: Union[Exception, Dict[str, Any], Any],
    context: Dict[str, Any]
) -> LineErrorInfo
```

**パラメータ**:

- `error`: 分析対象のエラー
- `context`: コンテキスト情報
  - `user_id`: ユーザー ID
  - `request_id`: リクエスト ID
  - `timestamp`: タイムスタンプ
  - `api_endpoint`: API エンドポイント

**戻り値**: コンテキスト情報が付加された `LineErrorInfo`

#### 使用例

```python
async def analyze_with_user_context():
    analyzer = AsyncLineErrorAnalyzer()

    error = {"status_code": 401, "message": "Unauthorized"}
    context = {
        "user_id": "U1234567890",
        "request_id": "req_12345",
        "timestamp": "2024-01-01T12:00:00Z",
        "api_endpoint": "/v2/bot/message/reply"
    }

    result = await analyzer.analyze_with_context(error, context)

    # コンテキスト情報の確認
    print(f"ユーザーID: {result.context.get('user_id')}")
    print(f"リクエストID: {result.context.get('request_id')}")

    return result
```

## 高度な機能

### パフォーマンス最適化

#### `set_batch_size(size)`

デフォルトのバッチサイズを設定します。

```python
def set_batch_size(self, size: int) -> None
```

**パラメータ**:

- `size`: バッチサイズ（1-1000）

```python
analyzer = AsyncLineErrorAnalyzer()
analyzer.set_batch_size(200)  # 大きなバッチサイズで高速化
```

#### `enable_caching(cache_size=1000)`

分析結果のキャッシュを有効化します。

```python
def enable_caching(self, cache_size: int = 1000) -> None
```

**パラメータ**:

- `cache_size`: キャッシュサイズ

```python
analyzer = AsyncLineErrorAnalyzer()
analyzer.enable_caching(2000)  # 2000件までキャッシュ

# 同じエラーの再分析は高速化される
result1 = await analyzer.analyze({"status_code": 401})
result2 = await analyzer.analyze({"status_code": 401})  # キャッシュから取得
```

### 統計機能

#### `get_analysis_stats()`

分析統計情報を取得します。

```python
def get_analysis_stats(self) -> Dict[str, Any]
```

**戻り値**: 統計情報辞書

- `total_analyzed`: 総分析数
- `cache_hits`: キャッシュヒット数
- `average_analysis_time`: 平均分析時間
- `error_categories`: カテゴリ別統計

```python
analyzer = AsyncLineErrorAnalyzer()
analyzer.enable_caching()

# 複数の分析実行後
stats = analyzer.get_analysis_stats()

print(f"総分析数: {stats['total_analyzed']}")
print(f"キャッシュヒット率: {stats['cache_hits'] / stats['total_analyzed'] * 100:.1f}%")
print(f"平均分析時間: {stats['average_analysis_time']:.3f}秒")
```

## 実用的なパターン

### 1. エラー監視システム

```python
import asyncio
from datetime import datetime, timedelta
from collections import defaultdict

class AsyncErrorMonitor:
    def __init__(self):
        self.analyzer = AsyncLineErrorAnalyzer()
        self.analyzer.enable_caching(5000)
        self.error_log = []

    async def monitor_errors(self, error_stream):
        """エラーストリームの監視"""

        while True:
            try:
                # エラーの取得（キューやストリームから）
                errors = await self.get_errors_from_stream(error_stream)

                if errors:
                    # バッチ分析
                    results = await self.analyzer.analyze_batch(errors)

                    # ログ記録
                    for result in results:
                        self.error_log.append({
                            "timestamp": datetime.now(),
                            "result": result
                        })

                    # 重要エラーのアラート
                    await self.check_critical_errors(results)

                # 1秒待機
                await asyncio.sleep(1)

            except Exception as e:
                print(f"監視エラー: {e}")
                await asyncio.sleep(5)

    async def check_critical_errors(self, results):
        """重要エラーのチェック"""

        critical_errors = [
            r for r in results
            if r.severity.value == "CRITICAL"
        ]

        if critical_errors:
            await self.send_alert(f"重要エラー {len(critical_errors)}件発生")

    async def get_hourly_stats(self):
        """過去1時間の統計取得"""

        cutoff = datetime.now() - timedelta(hours=1)
        recent_errors = [
            log for log in self.error_log
            if log["timestamp"] > cutoff
        ]

        stats = defaultdict(int)
        for log in recent_errors:
            stats[log["result"].category.value] += 1

        return dict(stats)
```

### 2. 自動復旧システム

```python
class AutoRecoverySystem:
    def __init__(self):
        self.analyzer = AsyncLineErrorAnalyzer()
        self.recovery_actions = {
            "RATE_LIMIT": self.handle_rate_limit,
            "SERVER_ERROR": self.handle_server_error,
            "NETWORK_ERROR": self.handle_network_error
        }

    async def execute_with_recovery(self, operation, *args, **kwargs):
        """自動復旧付きオペレーション実行"""

        max_retries = 3
        base_delay = 1.0

        for attempt in range(max_retries + 1):
            try:
                return await operation(*args, **kwargs)

            except Exception as e:
                error_info = await self.analyzer.analyze(e)

                if attempt == max_retries:
                    raise  # 最後の試行で失敗

                # 復旧アクション実行
                recovery_action = self.recovery_actions.get(error_info.category.value)
                if recovery_action:
                    delay = await recovery_action(error_info, attempt)
                else:
                    delay = base_delay * (2 ** attempt)

                print(f"復旧試行 {attempt + 1}/{max_retries}: {delay}秒待機")
                await asyncio.sleep(delay)

    async def handle_rate_limit(self, error_info, attempt):
        """レート制限の処理"""

        # Retry-After ヘッダーの値を使用
        delay = error_info.retry_after or 60

        print(f"レート制限検出: {delay}秒待機")
        return delay

    async def handle_server_error(self, error_info, attempt):
        """サーバーエラーの処理"""

        # 指数バックオフ
        delay = 2 ** attempt

        print(f"サーバーエラー検出: {delay}秒待機")
        return delay

    async def handle_network_error(self, error_info, attempt):
        """ネットワークエラーの処理"""

        # 短い固定間隔
        delay = 5

        print(f"ネットワークエラー検出: {delay}秒待機")
        return delay
```

### 3. リアルタイム分析ダッシュボード

```python
import json
from datetime import datetime

class RealtimeAnalyticsDashboard:
    def __init__(self):
        self.analyzer = AsyncLineErrorAnalyzer()
        self.analyzer.enable_caching(10000)
        self.live_stats = {
            "total_errors": 0,
            "errors_by_category": defaultdict(int),
            "errors_by_hour": defaultdict(int),
            "recent_errors": []
        }

    async def process_error_stream(self, websocket_connection):
        """WebSocket経由でのリアルタイム処理"""

        while True:
            try:
                # WebSocketからエラーデータ受信
                error_data = await websocket_connection.receive_json()

                # エラー分析
                result = await self.analyzer.analyze(error_data)

                # 統計更新
                await self.update_live_stats(result)

                # クライアントに結果送信
                response = {
                    "type": "error_analysis",
                    "result": {
                        "category": result.category.value,
                        "severity": result.severity.value,
                        "is_retryable": result.is_retryable,
                        "timestamp": datetime.now().isoformat()
                    },
                    "stats": self.live_stats
                }

                await websocket_connection.send_json(response)

            except Exception as e:
                error_result = await self.analyzer.analyze(e)
                print(f"ダッシュボードエラー: {error_result.description}")

    async def update_live_stats(self, result):
        """ライブ統計の更新"""

        self.live_stats["total_errors"] += 1
        self.live_stats["errors_by_category"][result.category.value] += 1

        # 時間別統計
        hour_key = datetime.now().strftime("%Y-%m-%d %H")
        self.live_stats["errors_by_hour"][hour_key] += 1

        # 最近のエラー（最新10件）
        self.live_stats["recent_errors"].append({
            "category": result.category.value,
            "severity": result.severity.value,
            "timestamp": datetime.now().isoformat()
        })

        if len(self.live_stats["recent_errors"]) > 10:
            self.live_stats["recent_errors"].pop(0)
```

## パフォーマンスガイド

### メモリ使用量の最適化

```python
# 大量データ処理時のメモリ効率的な処理
async def memory_efficient_processing(large_error_list):
    analyzer = AsyncLineErrorAnalyzer()

    # 小さなバッチサイズでメモリ使用量を制限
    results = []
    batch_size = 20  # メモリ制限環境では小さく設定

    for i in range(0, len(large_error_list), batch_size):
        batch = large_error_list[i:i + batch_size]
        batch_results = await analyzer.analyze_batch(batch, batch_size=batch_size)
        results.extend(batch_results)

        # バッチ間で少し待機（メモリ解放）
        await asyncio.sleep(0.1)

    return results
```

### 同時実行数の制御

```python
import asyncio

# セマフォを使った同時実行数制御
async def controlled_concurrent_analysis(error_groups):
    analyzer = AsyncLineErrorAnalyzer()

    # 最大10個の並行処理
    semaphore = asyncio.Semaphore(10)

    async def analyze_group(errors):
        async with semaphore:
            return await analyzer.analyze_batch(errors)

    # 並行実行
    tasks = [analyze_group(group) for group in error_groups]
    results = await asyncio.gather(*tasks)

    return results
```

## まとめ

`AsyncLineErrorAnalyzer` は高パフォーマンスな非同期エラー分析を提供します：

- **高速処理**: バッチ処理と並行処理による高速化
- **スケーラビリティ**: 大量データ対応
- **キャッシュ機能**: 重複分析の高速化
- **統計機能**: リアルタイムな分析統計
- **柔軟性**: カスタマイズ可能な処理パターン

次のステップ:

- **[LineErrorAnalyzer](analyzer.md)** - 同期版の API
- **[データモデル](models.md)** - 詳細なデータ構造
- **[実用例](../examples/advanced_usage.md)** - 高度な使用例
