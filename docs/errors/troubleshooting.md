# 🛠️ トラブルシューティングガイド

LINE Bot エラー分析器の使用時によくある問題と解決方法を説明します。

## 🔧 よくある問題と解決方法

### 1. インポートエラー

#### 問題: `ImportError: No module named 'line_bot_error_analyzer'`

**症状**:

```python
>>> from line_bot_error_analyzer import LineErrorAnalyzer
ImportError: No module named 'line_bot_error_analyzer'
```

**原因と解決方法**:

1. **Python パスの問題**

   ```bash
   # 現在のディレクトリを確認
   pwd

   # line-api-error-python ディレクトリにいることを確認
   ls -la
   # line_bot_error_analyzer/ ディレクトリが存在することを確認

   # Pythonパスに追加
   export PYTHONPATH="${PYTHONPATH}:$(pwd)"
   ```

2. **ディレクトリ構造の確認**

   ```bash
   # 正しい構造かチェック
   tree line_bot_error_analyzer/
   # 📁 line_bot_error_analyzer/
   # ├── __init__.py
   # ├── analyzer.py
   # ├── async_analyzer.py
   # ├── ...
   ```

3. **Python 実行場所の確認**
   ```bash
   # プロジェクトルートで実行していることを確認
   cd /path/to/line-api-error-python
   python -c "from line_bot_error_analyzer import LineErrorAnalyzer; print('OK')"
   ```

#### 問題: `ImportError: attempted relative import with no known parent package`

**症状**:

```python
ImportError: attempted relative import with no known parent package
```

**解決方法**:

```bash
# モジュールとして実行
python -m line_bot_error_detective.analyzer

# または、プロジェクトルートから実行
cd /path/to/line-api-error-python
python your_script.py
```

### 2. 分析結果の異常

#### 問題: すべてのエラーが `UNKNOWN_ERROR` に分類される

**症状**:

```python
result = analyzer.analyze({"status_code": 401})
print(result.category.value)  # "UNKNOWN_ERROR" になってしまう
```

**原因と解決方法**:

1. **エラーデータ形式の確認**

   ```python
   # ❌ 間違った形式
   error = 401  # 数値のみ

   # ✅ 正しい形式
   error = {"status_code": 401}
   error = {"status_code": 401, "message": "Unauthorized"}
   ```

2. **必要フィールドの確認**

   ```python
   # 最小構成
   error = {"status_code": 401}

   # 推奨構成
   error = {
       "status_code": 401,
       "message": "Authentication failed",
       "error_code": "40001"  # LINE APIエラーコード
   }
   ```

3. **デバッグ用の詳細出力**

   ```python
   result = analyzer.analyze(error)

   # デバッグ情報を確認
   print(f"元のエラー: {result.raw_error}")
   print(f"分析情報: {result.to_dict()}")
   ```

#### 問題: LINE API エラーコードが認識されない

**症状**:

```python
error = {"status_code": 400, "error_code": "40100"}
result = analyzer.analyze(error)
print(result.error_code)  # None になってしまう
```

**解決方法**:

1. **フィールド名の確認**

   ```python
   # ✅ 正しいフィールド名
   error = {"status_code": 400, "error_code": "40100"}

   # ❌ 間違ったフィールド名
   error = {"status_code": 400, "errorCode": "40100"}  # camelCase
   error = {"status_code": 400, "code": "40100"}       # 短縮形
   ```

2. **LINE Bot SDK 例外の確認**

   ```python
   from linebot.v3.exceptions import ApiException

   try:
       # LINE API呼び出し
       pass
   except ApiException as e:
       # SDK例外は自動で適切に分析される
       result = analyzer.analyze(e)
       print(f"エラーコード: {result.error_code}")
   ```

### 3. パフォーマンス問題

#### 問題: 分析処理が遅い

**症状**:

```python
# 大量のエラー処理に時間がかかる
errors = [{"status_code": 400}] * 10000
# 処理に数分かかってしまう
```

**解決方法**:

1. **非同期処理の使用**

   ```python
   import asyncio
   from line_bot_error_detective import AsyncLineErrorAnalyzer

   async def fast_analysis():
       analyzer = AsyncLineErrorAnalyzer()

       # バッチ処理で高速化
       results = await analyzer.analyze_batch(errors, batch_size=100)
       return results

   results = asyncio.run(fast_analysis())
   ```

2. **キャッシュの有効化**

   ```python
   analyzer = AsyncLineErrorAnalyzer()
   analyzer.enable_caching(5000)  # 5000件までキャッシュ

   # 同じエラーの繰り返し分析が高速化される
   ```

3. **バッチサイズの調整**

   ```python
   # メモリ使用量を抑えたい場合
   results = await analyzer.analyze_batch(errors, batch_size=50)

   # 処理速度を重視する場合
   results = await analyzer.analyze_batch(errors, batch_size=200)
   ```

#### 問題: メモリ使用量が多い

**症状**:

```python
# 大量エラー処理でメモリ不足
MemoryError: Unable to allocate array
```

**解決方法**:

1. **小さなバッチでの処理**

   ```python
   async def memory_efficient_processing(errors):
       analyzer = AsyncLineErrorAnalyzer()
       results = []

       # 小さなバッチに分割
       batch_size = 20
       for i in range(0, len(errors), batch_size):
           batch = errors[i:i + batch_size]
           batch_results = await analyzer.analyze_batch(batch)
           results.extend(batch_results)

           # バッチ間で少し待機（メモリ解放）
           await asyncio.sleep(0.1)

       return results
   ```

2. **ジェネレータの使用**

   ```python
   async def process_errors_generator(error_generator):
       analyzer = AsyncLineErrorAnalyzer()

       async for error_batch in error_generator:
           results = await analyzer.analyze_batch(error_batch)
           yield results
   ```

### 4. LINE Bot SDK 統合問題

#### 問題: LINE Bot SDK v3 の例外が正しく分析されない

**症状**:

```python
from linebot.v3.exceptions import ApiException

try:
    # LINE API呼び出し
    pass
except ApiException as e:
    result = analyzer.analyze(e)
    print(result.error_code)  # None または不正確
```

**解決方法**:

1. **例外属性の確認**

   ```python
   try:
       # LINE API呼び出し
       pass
   except ApiException as e:
       # 例外の詳細を確認
       print(f"Status Code: {e.status_code}")
       print(f"Detail: {e.detail}")
       print(f"Has error_code: {hasattr(e.detail, 'error_code')}")

       # 手動でエラー情報を構築
       error_data = {
           "status_code": e.status_code,
           "message": str(e),
           "error_code": getattr(e.detail, 'error_code', None)
       }

       result = analyzer.analyze(error_data)
   ```

2. **SDK バージョンの確認**

   ```python
   import linebot
   print(f"LINE Bot SDK version: {linebot.__version__}")

   # v3.0.0以降を推奨
   # pip install --upgrade line-bot-sdk
   ```

#### 問題: Webhook での署名検証エラー

**症状**:

```python
from linebot.v3.exceptions import InvalidSignatureError

try:
    handler.handle(body, signature)
except InvalidSignatureError as e:
    result = analyzer.analyze(e)
    # 適切に分析されない
```

**解決方法**:

```python
try:
    handler.handle(body, signature)
except InvalidSignatureError as e:
    # 署名検証エラーの詳細分析
    error_data = {
        "status_code": 401,
        "message": "Invalid signature",
        "error_type": "signature_validation",
        "webhook_body_length": len(body),
        "signature": signature[:10] + "..."  # セキュリティのため一部のみ
    }

    result = analyzer.analyze(error_data)
    print(f"署名検証エラー: {result.description}")
```

### 5. デバッグとログ設定

#### デバッグモードの有効化

```python
import logging

# デバッグログの有効化
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('line_bot_error_detective')

# カスタムログハンドラーの追加
class ErrorAnalysisHandler(logging.Handler):
    def emit(self, record):
        print(f"[DEBUG] {record.getMessage()}")

logger.addHandler(ErrorAnalysisHandler())
```

#### 詳細な分析ログ

```python
def debug_analyze(analyzer, error):
    """デバッグ用の詳細分析"""

    print("=== エラー分析デバッグ ===")
    print(f"入力エラー: {error}")
    print(f"エラータイプ: {type(error)}")

    result = analyzer.analyze(error)

    print(f"分析結果:")
    print(f"  - カテゴリ: {result.category.value}")
    print(f"  - ステータス: {result.status_code}")
    print(f"  - エラーコード: {result.error_code}")
    print(f"  - 重要度: {result.severity.value}")
    print(f"  - リトライ可能: {result.is_retryable}")
    print(f"  - 説明: {result.description}")
    print(f"  - 対処法: {result.recommended_action}")
    print(f"  - 元データ: {result.raw_error}")

    return result

# 使用例
error = {"status_code": 401, "message": "Auth failed"}
result = debug_analyze(analyzer, error)
```

### 6. テスト環境での問題

#### 問題: テストでのモック作成

**症状**:

```python
# LINE API例外のモックが難しい
mock_exception = Mock(spec=ApiException)
# 適切にモックできない
```

**解決方法**:

1. **完全なモック作成**

   ```python
   from unittest.mock import Mock, MagicMock
   from linebot.v3.exceptions import ApiException

   def create_mock_api_exception(status_code=401, error_code=None):
       """LINE API例外のモック作成"""

       mock_exception = Mock(spec=ApiException)
       mock_exception.status_code = status_code

       # detail属性のモック
       mock_detail = MagicMock()
       if error_code:
           mock_detail.error_code = error_code
       else:
           del mock_detail.error_code  # 属性を削除

       mock_exception.detail = mock_detail

       return mock_exception

   # 使用例
   mock_error = create_mock_api_exception(401, "40001")
   result = analyzer.analyze(mock_error)
   ```

2. **テスト用のヘルパークラス**

   ```python
   class TestErrorGenerator:
       """テスト用エラー生成器"""

       @staticmethod
       def auth_error():
           return {"status_code": 401, "message": "Unauthorized"}

       @staticmethod
       def rate_limit_error():
           return {
               "status_code": 429,
               "message": "Too Many Requests",
               "error_code": "42901",
               "headers": {"Retry-After": "60"}
           }

       @staticmethod
       def server_error():
           return {"status_code": 500, "message": "Internal Server Error"}

   # テストでの使用
   def test_auth_error_analysis():
       error = TestErrorGenerator.auth_error()
       result = analyzer.analyze(error)
       assert result.category.value == "AUTH_ERROR"
   ```

### 7. パフォーマンス診断ツール

```python
import time
import psutil
import asyncio
from typing import List, Dict, Any

class PerformanceDiagnostics:
    """パフォーマンス診断ツール"""

    def __init__(self):
        self.analyzer = AsyncLineErrorAnalyzer()
        self.metrics = []

    async def diagnose_performance(self, test_errors: List[dict]) -> Dict[str, Any]:
        """パフォーマンス診断の実行"""

        print("🔍 パフォーマンス診断を開始...")

        # メモリ使用量（開始時）
        process = psutil.Process()
        start_memory = process.memory_info().rss / 1024 / 1024  # MB

        # 1. 単一エラー分析のテスト
        single_start = time.time()
        single_result = await self.analyzer.analyze(test_errors[0])
        single_time = time.time() - single_start

        # 2. バッチ分析のテスト
        batch_sizes = [10, 50, 100, 500]
        batch_results = {}

        for batch_size in batch_sizes:
            if len(test_errors) >= batch_size:
                batch = test_errors[:batch_size]

                batch_start = time.time()
                results = await self.analyzer.analyze_batch(batch, batch_size=batch_size)
                batch_time = time.time() - batch_start

                batch_results[batch_size] = {
                    "time_seconds": batch_time,
                    "errors_per_second": batch_size / batch_time if batch_time > 0 else 0,
                    "average_latency_ms": batch_time / batch_size * 1000
                }

        # 3. キャッシュ効果のテスト
        cache_start = time.time()
        self.analyzer.enable_caching(1000)

        # 同じエラーを複数回分析
        duplicate_errors = [test_errors[0]] * 100
        await self.analyzer.analyze_batch(duplicate_errors)
        cache_time = time.time() - cache_start

        # メモリ使用量（終了時）
        end_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = end_memory - start_memory

        # 分析器統計の取得
        analyzer_stats = self.analyzer.get_analysis_stats()

        diagnosis = {
            "memory_usage": {
                "start_mb": round(start_memory, 2),
                "end_mb": round(end_memory, 2),
                "increase_mb": round(memory_increase, 2)
            },
            "single_analysis": {
                "time_ms": round(single_time * 1000, 3),
                "category": single_result.category.value
            },
            "batch_analysis": batch_results,
            "cache_performance": {
                "time_for_100_duplicates_ms": round(cache_time * 1000, 2),
                "cache_hit_rate": analyzer_stats.get("cache_hits", 0) / analyzer_stats.get("total_analyzed", 1) * 100
            },
            "recommendations": self.generate_recommendations(batch_results, memory_increase)
        }

        return diagnosis

    def generate_recommendations(self, batch_results: Dict, memory_increase: float) -> List[str]:
        """パフォーマンス推奨事項の生成"""

        recommendations = []

        # バッチサイズの推奨
        best_batch_size = None
        best_throughput = 0

        for batch_size, metrics in batch_results.items():
            if metrics["errors_per_second"] > best_throughput:
                best_throughput = metrics["errors_per_second"]
                best_batch_size = batch_size

        if best_batch_size:
            recommendations.append(f"最適なバッチサイズ: {best_batch_size}")

        # メモリ使用量の推奨
        if memory_increase > 100:  # 100MB以上の増加
            recommendations.append("メモリ使用量が多いです。バッチサイズを小さくすることを検討してください。")

        # 処理速度の推奨
        if best_throughput < 100:  # 100 errors/sec未満
            recommendations.append("処理速度が低いです。非同期処理とキャッシュの使用を検討してください。")

        return recommendations

# 診断実行例
async def run_performance_diagnosis():
    """パフォーマンス診断の実行例"""

    # テストデータ生成
    test_errors = []
    error_templates = [
        {"status_code": 401, "message": "Auth error"},
        {"status_code": 429, "message": "Rate limit", "error_code": "42901"},
        {"status_code": 500, "message": "Server error"},
        {"status_code": 400, "message": "Bad request", "error_code": "40010"}
    ]

    for i in range(1000):
        template = error_templates[i % len(error_templates)]
        error = template.copy()
        error["request_id"] = f"req_{i}"
        test_errors.append(error)

    # 診断実行
    diagnostics = PerformanceDiagnostics()
    diagnosis = await diagnostics.diagnose_performance(test_errors)

    # 結果出力
    print("\n📊 パフォーマンス診断結果:")
    print("=" * 50)

    print(f"\n💾 メモリ使用量:")
    memory = diagnosis["memory_usage"]
    print(f"  開始時: {memory['start_mb']} MB")
    print(f"  終了時: {memory['end_mb']} MB")
    print(f"  増加量: {memory['increase_mb']} MB")

    print(f"\n⚡ 単一分析:")
    single = diagnosis["single_analysis"]
    print(f"  処理時間: {single['time_ms']} ms")
    print(f"  分析結果: {single['category']}")

    print(f"\n📦 バッチ分析:")
    for batch_size, metrics in diagnosis["batch_analysis"].items():
        print(f"  バッチサイズ {batch_size}: {metrics['errors_per_second']:.1f} errors/sec")

    print(f"\n🔄 キャッシュ性能:")
    cache = diagnosis["cache_performance"]
    print(f"  重複100件処理: {cache['time_for_100_duplicates_ms']} ms")
    print(f"  キャッシュヒット率: {cache['cache_hit_rate']:.1f}%")

    print(f"\n💡 推奨事項:")
    for rec in diagnosis["recommendations"]:
        print(f"  • {rec}")

# 実行
if __name__ == "__main__":
    asyncio.run(run_performance_diagnosis())
```

## よくある質問（FAQ）

### Q: 分析結果が期待と異なる場合はどうすれば良いですか？

A: 以下の手順で確認してください：

1. **エラーデータの確認**: `result.raw_error` で元データを確認
2. **デバッグ分析**: 上記の `debug_analyze` 関数を使用
3. **ログレベル調整**: `logging.DEBUG` でより詳細な情報を取得

### Q: カスタムエラーカテゴリを追加できますか？

A: はい、ベースクラスを継承してカスタム分析器を作成できます：

```python
from line_bot_error_detective.core import BaseLineErrorAnalyzer
from line_bot_error_detective.core.models import LineErrorInfo, ErrorCategory

class CustomErrorCategory(ErrorCategory):
    CUSTOM_ERROR = "CUSTOM_ERROR"

class CustomAnalyzer(BaseLineErrorAnalyzer):
    def analyze(self, error):
        # カスタムロジック
        if self.is_custom_error(error):
            return self.create_custom_error_info(error)

        # デフォルト分析
        return super().analyze(error)
```

### Q: 本番環境でのログ設定はどうすれば良いですか？

A: 構造化ログの使用を推奨します：

```python
import json
import logging
from datetime import datetime

class StructuredErrorLogger:
    def __init__(self):
        self.logger = logging.getLogger('line_bot_error_detective')
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(message)s'))
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    def log_error_analysis(self, error_info, context=None):
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": error_info.severity.value,
            "category": error_info.category.value,
            "status_code": error_info.status_code,
            "error_code": error_info.error_code,
            "description": error_info.description,
            "context": context or {}
        }

        self.logger.info(json.dumps(log_entry, ensure_ascii=False))
```

## サポートとヘルプ

問題が解決しない場合は：

1. **[GitHub Issues](https://github.com/raiton-boo/line-api-error-python/issues)** - バグ報告
2. **[ディスカッション](https://github.com/raiton-boo/line-api-error-python/discussions)** - 質問・相談
3. **[API リファレンス](../api/)** - 詳細な仕様確認

問題報告時は以下の情報を含めてください：

- Python バージョン
- LINE Bot SDK バージョン（使用している場合）
- エラーメッセージ（完全なスタックトレース）
- 問題を再現する最小コード
- 期待する結果と実際の結果
