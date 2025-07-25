# ベースクラス設計

`BaseLineErrorAnalyzer` の設計と実装について詳しく説明します。

## 設計思想

### なぜベースクラスが必要か？

LINE Bot エラー分析器では、同期処理と非同期処理の両方をサポートしています。しかし、エラー分析の核となるロジックは同じです：

**従来の問題点:**

- 同期・非同期分析器でコードが重複
- 修正時に両方のファイルを更新する必要
- ロジックの一貫性を保つのが困難
- テストも重複して作成する必要

**ベースクラス設計の利点:**

- 共通ロジックを一箇所に集約
- 一度の修正で両方に反映
- 一貫した分析結果を保証
- テストの重複を排除

## クラス階層

```
BaseLineErrorAnalyzer (抽象基底クラス)
├── LineErrorAnalyzer (同期実装)
└── AsyncLineErrorAnalyzer (非同期実装)
```

## BaseLineErrorAnalyzer の実装

### 完全なクラス定義

```python
from abc import ABC
from typing import Any, Dict, Optional, Union
from ..database.error_database import ErrorDatabase
from .models import LineErrorInfo, ErrorCategory, ErrorSeverity

class BaseLineErrorAnalyzer(ABC):
    """LINE Bot エラー分析器の基底クラス

    同期・非同期分析器の共通ロジックを提供し、
    コードの重複を排除して保守性を向上させます。
    """

    def __init__(self):
        self.error_db = ErrorDatabase()

    # === 型判定メソッド ===

    def _is_v3_api_exception(self, error: Any) -> bool:
        """LINE Bot SDK v3 の ApiException かどうかを判定"""
        return hasattr(error, 'status_code') and hasattr(error, 'headers')

    def _is_v3_signature_error(self, error: Any) -> bool:
        """LINE Bot SDK v3 の署名エラーかどうかを判定"""
        error_type = type(error).__name__
        return error_type == 'InvalidSignatureError'

    def _is_v2_api_error(self, error: Any) -> bool:
        """LINE Bot SDK v2 の LineBotApiError かどうかを判定"""
        return hasattr(error, 'status_code') and hasattr(error, 'error')

    def _is_v2_signature_error(self, error: Any) -> bool:
        """LINE Bot SDK v2 の署名エラーかどうかを判定"""
        error_type = type(error).__name__
        return error_type == 'InvalidSignatureError'

    # === 分析メソッド ===

    def _analyze_v3_api_exception(self, error: Any) -> LineErrorInfo:
        """LINE Bot SDK v3 の ApiException を分析"""
        try:
            # error.body から詳細情報を取得
            error_details = getattr(error, 'body', {})
            if isinstance(error_details, str):
                import json
                try:
                    error_details = json.loads(error_details)
                except json.JSONDecodeError:
                    error_details = {}

            status_code = getattr(error, 'status_code', 500)
            headers = getattr(error, 'headers', {})

            # エラーコードとメッセージを抽出
            error_code = error_details.get('details', [{}])[0].get('property') if error_details.get('details') else None
            message = error_details.get('message', str(error))

            return self._create_error_info(
                status_code=status_code,
                error_code=error_code,
                message=message,
                headers=headers,
                error_data=error_details
            )

        except Exception as e:
            # フォールバック: 基本情報のみで分析
            return self._create_error_info(
                status_code=getattr(error, 'status_code', 500),
                message=str(error),
                headers=getattr(error, 'headers', {}),
                error_data={}
            )

    def _analyze_v2_api_error(self, error: Any) -> LineErrorInfo:
        """LINE Bot SDK v2 の LineBotApiError を分析"""
        try:
            status_code = getattr(error, 'status_code', 500)
            error_details = getattr(error, 'error', {})

            # v2 では error.error.details にエラー詳細
            error_code = None
            if hasattr(error_details, 'details') and error_details.details:
                error_code = error_details.details[0].get('property')

            message = getattr(error_details, 'message', str(error))

            return self._create_error_info(
                status_code=status_code,
                error_code=error_code,
                message=message,
                headers={},
                error_data=error_details.__dict__ if hasattr(error_details, '__dict__') else {}
            )

        except Exception:
            return self._create_error_info(
                status_code=getattr(error, 'status_code', 500),
                message=str(error),
                headers={},
                error_data={}
            )

    def _analyze_signature_error(self, error: Any) -> LineErrorInfo:
        """署名検証エラーを分析"""
        return self._create_error_info(
            status_code=401,
            error_code="40004",  # 署名検証エラーのコード
            message="署名検証に失敗しました",
            headers={},
            error_data={"signature_error": str(error)}
        )

    def _analyze_dict_error(self, error_dict: Dict[str, Any]) -> LineErrorInfo:
        """辞書形式のエラーデータを分析"""
        status_code = error_dict.get('status_code', 500)
        error_code = error_dict.get('error_code')
        message = error_dict.get('message', 'Unknown error')
        headers = error_dict.get('headers', {})

        return self._create_error_info(
            status_code=status_code,
            error_code=error_code,
            message=message,
            headers=headers,
            error_data=error_dict
        )

    def _create_error_info(self,
                          status_code: int,
                          message: str,
                          headers: Dict[str, str],
                          error_data: Dict[str, Any],
                          error_code: Optional[str] = None) -> LineErrorInfo:
        """LineErrorInfo オブジェクトを生成"""

        # ErrorDatabase を使用してエラーを分析
        analysis_result = self.error_db.analyze_error(
            status_code=status_code,
            error_code=error_code,
            message=message
        )

        # retry_after ヘッダーの処理
        retry_after = None
        if headers and 'retry-after' in headers:
            try:
                retry_after = int(headers['retry-after'])
            except (ValueError, TypeError):
                retry_after = None

        # リクエストID の取得
        request_id = headers.get('x-line-request-id') if headers else None

        return LineErrorInfo(
            status_code=status_code,
            error_code=error_code,
            message=message,
            category=analysis_result['category'],
            severity=analysis_result['severity'],
            is_retryable=analysis_result['is_retryable'],
            description=analysis_result['description'],
            recommended_action=analysis_result['recommended_action'],
            retry_after=retry_after,
            raw_error=error_data,
            request_id=request_id,
            headers=headers,
            documentation_url=analysis_result.get('documentation_url')
        )
```

## 設計パターンの活用

### 1. Template Method Pattern

基底クラスで処理の流れを定義し、具体的な実装は派生クラスに委譲：

```python
# BaseLineErrorAnalyzer (Template)
def _create_error_info(self, **kwargs):
    # 共通の処理フロー
    analysis_result = self.error_db.analyze_error(...)
    return LineErrorInfo(...)

# LineErrorAnalyzer (Concrete)
def analyze(self, error):
    # 同期処理の具体的な実装
    if self._is_v3_api_exception(error):
        return self._analyze_v3_api_exception(error)
    # ...

# AsyncLineErrorAnalyzer (Concrete)
async def analyze(self, error):
    # 非同期処理の具体的な実装
    if self._is_v3_api_exception(error):
        return self._analyze_v3_api_exception(error)
    # ...
```

### 2. Strategy Pattern

エラーの種類に応じて適切な分析戦略を選択：

```python
def _get_analysis_strategy(self, error):
    """エラータイプに応じた分析戦略を取得"""
    if self._is_v3_api_exception(error):
        return self._analyze_v3_api_exception
    elif self._is_v3_signature_error(error):
        return self._analyze_signature_error
    elif isinstance(error, dict):
        return self._analyze_dict_error
    else:
        return self._analyze_unknown_error
```

### 3. Factory Pattern

LineErrorInfo オブジェクトの生成を統一：

```python
def _create_error_info(self, **kwargs) -> LineErrorInfo:
    """LineErrorInfo ファクトリーメソッド"""
    # 共通の生成ロジック
    # バリデーション、デフォルト値設定、等
    return LineErrorInfo(...)
```

## 継承クラスの実装

### LineErrorAnalyzer (同期版)

```python
class LineErrorAnalyzer(BaseLineErrorAnalyzer):
    """同期処理用のエラー分析器"""

    def analyze(self, error: Union[Exception, Dict[str, Any]]) -> LineErrorInfo:
        """エラーを分析して詳細情報を返す"""

        # 基底クラスのメソッドを活用
        if self._is_v3_api_exception(error):
            return self._analyze_v3_api_exception(error)
        elif self._is_v3_signature_error(error):
            return self._analyze_signature_error(error)
        elif isinstance(error, dict):
            return self._analyze_dict_error(error)

        # その他のエラー処理...
```

### AsyncLineErrorAnalyzer (非同期版)

```python
class AsyncLineErrorAnalyzer(BaseLineErrorAnalyzer):
    """非同期処理用のエラー分析器"""

    async def analyze(self, error: Union[Exception, Dict[str, Any]]) -> LineErrorInfo:
        """エラーを非同期で分析"""

        # 同じロジック（基底クラスのメソッドは同期なのでそのまま使用可能）
        if self._is_v3_api_exception(error):
            return self._analyze_v3_api_exception(error)
        elif self._is_v3_signature_error(error):
            return self._analyze_signature_error(error)
        elif isinstance(error, dict):
            return self._analyze_dict_error(error)

        # 非同期特有の処理...

    async def analyze_batch(self, errors: List[Any], batch_size: int = 10) -> List[LineErrorInfo]:
        """バッチ処理での非同期分析"""
        # バッチ処理の実装...
```

## 利点の詳細

### 1. 保守性の向上

**Before (ベースクラスなし):**

```python
# analyzer.py と async_analyzer.py に同じコードが重複
def _analyze_v3_api_exception(self, error):
    # 同じ処理が2箇所に...
    status_code = getattr(error, 'status_code', 500)
    # ... 100行のコード
```

**After (ベースクラスあり):**

```python
# base_analyzer.py に一度だけ実装
def _analyze_v3_api_exception(self, error):
    # 一箇所にまとめられた処理
    status_code = getattr(error, 'status_code', 500)
    # ... 100行のコード
```

### 2. 一貫性の保証

- 同じメソッドを使用するため、同期・非同期で結果が一致
- バグ修正が両方に確実に反映される
- テストケースも共通化できる

### 3. 拡張性の向上

```python
class CustomLineErrorAnalyzer(BaseLineErrorAnalyzer):
    """カスタム分析器の例"""

    def analyze(self, error):
        # 基底クラスの機能を活用
        if self._is_v3_api_exception(error):
            return super()._analyze_v3_api_exception(error)

        # カスタムロジックを追加
        return self._analyze_custom_error(error)

    def _analyze_custom_error(self, error):
        # 独自の分析ロジック
        return self._create_error_info(
            status_code=500,
            message="Custom error",
            headers={},
            error_data={}
        )
```

## テストの設計

### 基底クラスのテスト

```python
class TestBaseLineErrorAnalyzer(unittest.TestCase):
    """BaseLineErrorAnalyzer のテスト"""

    def setUp(self):
        # テスト用の具象クラスを作成
        class TestableAnalyzer(BaseLineErrorAnalyzer):
            def analyze(self, error):
                return self._analyze_dict_error(error)

        self.analyzer = TestableAnalyzer()

    def test_analyze_v3_api_exception(self):
        """v3 API例外の分析テスト"""
        # テスト実装...

    def test_create_error_info(self):
        """ErrorInfo生成のテスト"""
        # テスト実装...
```

### 継承クラスのテスト

```python
class TestLineErrorAnalyzer(unittest.TestCase):
    """LineErrorAnalyzer のテスト"""

    def test_analyze_integration(self):
        """統合テスト（基底クラスとの連携確認）"""
        # 基底クラスのメソッドが正しく動作することを確認
```

## 次のステップ

- [エラー分析フロー](error_flow.md) - 処理フローの詳細
- [データモデル](data_models.md) - LineErrorInfo の詳細
- [カスタム分析器](../integration/custom_analyzer.md) - カスタム実装の作成方法
