# ベースアナライザ API リファレンス

LINE Bot エラー分析器の基盤となる `BaseLineErrorAnalyzer` クラスと関連コンポーネントの詳細な API リファレンスです。

## BaseLineErrorAnalyzer クラス

```python
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union, Type
from line_bot_error_detective.core.models import LineErrorInfo, ErrorCategory, ErrorSeverity

class BaseLineErrorAnalyzer(ABC):
    """LINE エラー分析器の基底クラス

    すべてのエラー分析器の基盤となる抽象クラスです。
    カスタム分析器を作成する際は、このクラスを継承してください。
    """

    def __init__(self, config: Optional['AnalyzerConfig'] = None):
        """分析器の初期化

        Args:
            config: 分析器設定オブジェクト
        """
        self.config = config or self._get_default_config()
        self._analysis_stats = {
            "total_analyzed": 0,
            "successful_analyses": 0,
            "failed_analyses": 0,
            "cache_hits": 0,
            "analysis_times": []
        }
        self._error_patterns = {}
        self._custom_handlers = {}

    @abstractmethod
    def analyze(self, error: Union[Dict, Exception, Any]) -> LineErrorInfo:
        """エラーの分析を実行

        Args:
            error: 分析対象のエラー
                - Dict: エラー情報を含む辞書
                - Exception: Python例外オブジェクト
                - Any: その他のエラー表現

        Returns:
            LineErrorInfo: 分析結果

        Raises:
            AnalysisError: 分析に失敗した場合
        """
        pass

    def analyze_batch(self, errors: List[Union[Dict, Exception, Any]]) -> List[LineErrorInfo]:
        """複数エラーのバッチ分析

        Args:
            errors: 分析対象のエラーリスト

        Returns:
            List[LineErrorInfo]: 分析結果のリスト
        """
        results = []

        for error in errors:
            try:
                result = self.analyze(error)
                results.append(result)
            except Exception as e:
                # エラー分析に失敗した場合のフォールバック
                fallback_result = self._create_fallback_result(error, e)
                results.append(fallback_result)

        return results

    def register_custom_handler(self,
                              error_type: Union[Type, str],
                              handler: callable) -> None:
        """カスタムエラーハンドラーの登録

        Args:
            error_type: エラータイプまたは識別子
            handler: エラーハンドラー関数
        """
        self._custom_handlers[error_type] = handler

    def get_analysis_stats(self) -> Dict[str, Any]:
        """分析統計情報の取得

        Returns:
            Dict: 統計情報
        """
        stats = self._analysis_stats.copy()

        if stats["analysis_times"]:
            stats["average_analysis_time"] = sum(stats["analysis_times"]) / len(stats["analysis_times"])
            stats["min_analysis_time"] = min(stats["analysis_times"])
            stats["max_analysis_time"] = max(stats["analysis_times"])

        return stats

    def reset_stats(self) -> None:
        """統計情報のリセット"""
        self._analysis_stats = {
            "total_analyzed": 0,
            "successful_analyses": 0,
            "failed_analyses": 0,
            "cache_hits": 0,
            "analysis_times": []
        }

    # Protected methods (継承クラスで使用)

    def _update_stats(self, success: bool, analysis_time: float, cache_hit: bool = False):
        """統計情報の更新"""
        self._analysis_stats["total_analyzed"] += 1

        if success:
            self._analysis_stats["successful_analyses"] += 1
        else:
            self._analysis_stats["failed_analyses"] += 1

        if cache_hit:
            self._analysis_stats["cache_hits"] += 1

        self._analysis_stats["analysis_times"].append(analysis_time)

        # メモリ使用量を制限するため、古い分析時間を削除
        if len(self._analysis_stats["analysis_times"]) > 1000:
            self._analysis_stats["analysis_times"] = self._analysis_stats["analysis_times"][-500:]

    def _extract_error_info(self, error: Any) -> Dict[str, Any]:
        """エラー情報の抽出

        Args:
            error: エラーオブジェクト

        Returns:
            Dict: 抽出されたエラー情報
        """
        if isinstance(error, dict):
            return error.copy()
        elif isinstance(error, Exception):
            return self._extract_from_exception(error)
        else:
            return {"raw_error": str(error), "error_type": type(error).__name__}

    def _extract_from_exception(self, exception: Exception) -> Dict[str, Any]:
        """例外オブジェクトからの情報抽出"""
        error_info = {
            "exception_type": type(exception).__name__,
            "message": str(exception),
            "args": exception.args
        }

        # LINE Bot SDK例外の特別処理
        if hasattr(exception, 'status_code'):
            error_info["status_code"] = exception.status_code

        if hasattr(exception, 'detail'):
            detail = exception.detail
            if hasattr(detail, 'error_code'):
                error_info["error_code"] = detail.error_code
            if hasattr(detail, 'message'):
                error_info["detail_message"] = detail.message

        # HTTPエラーの処理
        if hasattr(exception, 'response'):
            response = exception.response
            if hasattr(response, 'status_code'):
                error_info["status_code"] = response.status_code
            if hasattr(response, 'text'):
                error_info["response_text"] = response.text

        return error_info

    def _determine_category(self, error_info: Dict[str, Any]) -> ErrorCategory:
        """エラーカテゴリの判定

        Args:
            error_info: エラー情報辞書

        Returns:
            ErrorCategory: 判定されたカテゴリ
        """
        status_code = error_info.get("status_code")
        error_code = error_info.get("error_code")
        message = error_info.get("message", "").lower()

        # カスタムハンドラーをチェック
        for error_type, handler in self._custom_handlers.items():
            if self._matches_error_type(error_info, error_type):
                try:
                    category = handler(error_info)
                    if category:
                        return category
                except Exception:
                    continue

        # ステータスコードベースの判定
        if status_code:
            if status_code == 401:
                return ErrorCategory.AUTH_ERROR
            elif status_code == 403:
                return ErrorCategory.PERMISSION_ERROR
            elif status_code == 429:
                return ErrorCategory.RATE_LIMIT_ERROR
            elif 400 <= status_code < 500:
                return ErrorCategory.VALIDATION_ERROR
            elif 500 <= status_code < 600:
                return ErrorCategory.SERVER_ERROR

        # エラーコードベースの判定
        if error_code:
            if error_code.startswith("401"):
                return ErrorCategory.AUTH_ERROR
            elif error_code.startswith("403"):
                return ErrorCategory.PERMISSION_ERROR
            elif error_code.startswith("429"):
                return ErrorCategory.RATE_LIMIT_ERROR
            elif error_code.startswith("4"):
                return ErrorCategory.VALIDATION_ERROR
            elif error_code.startswith("5"):
                return ErrorCategory.SERVER_ERROR

        # メッセージベースの判定
        if "auth" in message or "token" in message:
            return ErrorCategory.AUTH_ERROR
        elif "rate" in message or "limit" in message:
            return ErrorCategory.RATE_LIMIT_ERROR
        elif "timeout" in message or "network" in message:
            return ErrorCategory.NETWORK_ERROR

        return ErrorCategory.UNKNOWN_ERROR

    def _determine_severity(self, error_info: Dict[str, Any], category: ErrorCategory) -> ErrorSeverity:
        """エラー重要度の判定

        Args:
            error_info: エラー情報辞書
            category: エラーカテゴリ

        Returns:
            ErrorSeverity: 判定された重要度
        """
        status_code = error_info.get("status_code")

        # 設定された閾値を使用
        if self.config and self.config.analysis.severity_thresholds:
            thresholds = self.config.analysis.severity_thresholds
            severity_score = self._calculate_severity_score(error_info, category)

            if severity_score >= thresholds.get("critical", 0.9):
                return ErrorSeverity.CRITICAL
            elif severity_score >= thresholds.get("high", 0.7):
                return ErrorSeverity.HIGH
            elif severity_score >= thresholds.get("medium", 0.4):
                return ErrorSeverity.MEDIUM
            else:
                return ErrorSeverity.LOW

        # デフォルトの判定ロジック
        if category == ErrorCategory.SERVER_ERROR:
            return ErrorSeverity.HIGH
        elif category == ErrorCategory.AUTH_ERROR:
            return ErrorSeverity.HIGH
        elif category == ErrorCategory.RATE_LIMIT_ERROR:
            return ErrorSeverity.MEDIUM
        elif category == ErrorCategory.VALIDATION_ERROR:
            return ErrorSeverity.LOW
        else:
            return ErrorSeverity.MEDIUM

    def _calculate_severity_score(self, error_info: Dict[str, Any], category: ErrorCategory) -> float:
        """重要度スコアの計算"""
        score = 0.5  # ベーススコア

        # カテゴリによる重み付け
        category_weights = {
            ErrorCategory.CRITICAL_ERROR: 1.0,
            ErrorCategory.SERVER_ERROR: 0.8,
            ErrorCategory.AUTH_ERROR: 0.8,
            ErrorCategory.PERMISSION_ERROR: 0.7,
            ErrorCategory.RATE_LIMIT_ERROR: 0.6,
            ErrorCategory.NETWORK_ERROR: 0.5,
            ErrorCategory.VALIDATION_ERROR: 0.3,
            ErrorCategory.UNKNOWN_ERROR: 0.4
        }

        score *= category_weights.get(category, 0.5)

        # ステータスコードによる調整
        status_code = error_info.get("status_code")
        if status_code:
            if status_code >= 500:
                score += 0.3
            elif status_code == 429:
                score += 0.2
            elif status_code in [401, 403]:
                score += 0.3

        return min(1.0, score)

    def _is_retryable(self, error_info: Dict[str, Any], category: ErrorCategory) -> bool:
        """リトライ可能性の判定

        Args:
            error_info: エラー情報辞書
            category: エラーカテゴリ

        Returns:
            bool: リトライ可能かどうか
        """
        status_code = error_info.get("status_code")

        # リトライ不可能なエラー
        non_retryable_codes = [400, 401, 403, 404, 422]
        if status_code in non_retryable_codes:
            return False

        # カテゴリベースの判定
        retryable_categories = [
            ErrorCategory.RATE_LIMIT_ERROR,
            ErrorCategory.NETWORK_ERROR,
            ErrorCategory.SERVER_ERROR
        ]

        return category in retryable_categories

    def _generate_description(self, error_info: Dict[str, Any], category: ErrorCategory) -> str:
        """エラー説明文の生成"""
        status_code = error_info.get("status_code")
        error_code = error_info.get("error_code")
        message = error_info.get("message", "")

        if category == ErrorCategory.AUTH_ERROR:
            return f"認証エラーが発生しました。アクセストークンを確認してください。({status_code})"
        elif category == ErrorCategory.RATE_LIMIT_ERROR:
            return f"レート制限に達しました。しばらく待ってから再試行してください。({status_code})"
        elif category == ErrorCategory.SERVER_ERROR:
            return f"LINE APIサーバーエラーが発生しました。({status_code})"
        elif category == ErrorCategory.VALIDATION_ERROR:
            return f"リクエストの形式が不正です。パラメータを確認してください。({status_code})"
        elif category == ErrorCategory.NETWORK_ERROR:
            return "ネットワークエラーが発生しました。接続を確認してください。"
        else:
            return f"不明なエラーが発生しました。{message} ({status_code})"

    def _generate_recommended_action(self, error_info: Dict[str, Any], category: ErrorCategory) -> str:
        """推奨対処法の生成"""
        if category == ErrorCategory.AUTH_ERROR:
            return "アクセストークンの有効性を確認し、必要に応じて再取得してください。"
        elif category == ErrorCategory.RATE_LIMIT_ERROR:
            return "リクエスト頻度を下げ、指数バックオフを使用して再試行してください。"
        elif category == ErrorCategory.SERVER_ERROR:
            return "しばらく待ってから再試行し、問題が続く場合はLINE APIの状況を確認してください。"
        elif category == ErrorCategory.VALIDATION_ERROR:
            return "リクエストパラメータの形式と必須項目を確認してください。"
        elif category == ErrorCategory.NETWORK_ERROR:
            return "ネットワーク接続を確認し、タイムアウト設定を調整してください。"
        else:
            return "エラーの詳細を確認し、必要に応じてサポートに連絡してください。"

    def _matches_error_type(self, error_info: Dict[str, Any], error_type: Union[Type, str]) -> bool:
        """エラータイプのマッチング判定"""
        if isinstance(error_type, str):
            return error_info.get("exception_type") == error_type
        elif isinstance(error_type, type):
            return error_info.get("exception_type") == error_type.__name__
        return False

    def _create_fallback_result(self, original_error: Any, analysis_error: Exception) -> LineErrorInfo:
        """分析失敗時のフォールバック結果作成"""
        return LineErrorInfo(
            category=ErrorCategory.UNKNOWN_ERROR,
            severity=ErrorSeverity.MEDIUM,
            status_code=None,
            error_code=None,
            message=f"Analysis failed: {str(analysis_error)}",
            description="エラー分析に失敗しました。",
            recommended_action="エラーの内容を手動で確認してください。",
            is_retryable=False,
            raw_error=original_error,
            timestamp=None
        )

    def _get_default_config(self) -> 'AnalyzerConfig':
        """デフォルト設定の取得"""
        from line_bot_error_detective.core.config import AnalyzerConfig
        return AnalyzerConfig()


# 同期分析器の具体実装

class LineErrorAnalyzer(BaseLineErrorAnalyzer):
    """同期 LINE エラー分析器

    基本的な同期エラー分析機能を提供します。
    """

    def __init__(self, config: Optional['AnalyzerConfig'] = None):
        """分析器の初期化

        Args:
            config: 分析器設定
        """
        super().__init__(config)
        self._cache = {}
        self._cache_stats = {"hits": 0, "misses": 0}

    def analyze(self, error: Union[Dict, Exception, Any]) -> LineErrorInfo:
        """エラーの分析を実行

        Args:
            error: 分析対象のエラー

        Returns:
            LineErrorInfo: 分析結果

        Example:
            >>> analyzer = LineErrorAnalyzer()
            >>> error = {"status_code": 401, "message": "Unauthorized"}
            >>> result = analyzer.analyze(error)
            >>> print(result.category.value)
            'AUTH_ERROR'
        """
        import time
        start_time = time.time()

        try:
            # キャッシュチェック
            if self.config.cache.enabled:
                cache_key = self._generate_cache_key(error)
                if cache_key in self._cache:
                    self._cache_stats["hits"] += 1
                    self._update_stats(True, time.time() - start_time, cache_hit=True)
                    return self._cache[cache_key]
                else:
                    self._cache_stats["misses"] += 1

            # エラー情報抽出
            error_info = self._extract_error_info(error)

            # 設定による無視チェック
            if self._should_ignore_error(error_info):
                result = self._create_ignored_result(error_info)
            else:
                # 分析実行
                result = self._perform_analysis(error_info)

            # キャッシュに保存
            if self.config.cache.enabled:
                self._cache[cache_key] = result
                self._cleanup_cache()

            analysis_time = time.time() - start_time
            self._update_stats(True, analysis_time)

            return result

        except Exception as e:
            analysis_time = time.time() - start_time
            self._update_stats(False, analysis_time)
            raise AnalysisError(f"Error analysis failed: {str(e)}") from e

    def _perform_analysis(self, error_info: Dict[str, Any]) -> LineErrorInfo:
        """実際の分析処理"""

        # カテゴリ判定
        category = self._determine_category(error_info)

        # 重要度判定
        severity = self._determine_severity(error_info, category)

        # その他の情報生成
        is_retryable = self._is_retryable(error_info, category)
        description = self._generate_description(error_info, category)
        recommended_action = self._generate_recommended_action(error_info, category)

        return LineErrorInfo(
            category=category,
            severity=severity,
            status_code=error_info.get("status_code"),
            error_code=error_info.get("error_code"),
            message=error_info.get("message"),
            description=description,
            recommended_action=recommended_action,
            is_retryable=is_retryable,
            raw_error=error_info,
            timestamp=error_info.get("timestamp")
        )

    def _should_ignore_error(self, error_info: Dict[str, Any]) -> bool:
        """エラーを無視すべきかの判定"""
        if not self.config.analysis:
            return False

        # 無視するエラーコード
        error_code = error_info.get("error_code")
        if (error_code and
            self.config.analysis.ignore_error_codes and
            error_code in self.config.analysis.ignore_error_codes):
            return True

        # 無視するステータスコード
        status_code = error_info.get("status_code")
        if (status_code and
            self.config.analysis.ignore_status_codes and
            status_code in self.config.analysis.ignore_status_codes):
            return True

        return False

    def _create_ignored_result(self, error_info: Dict[str, Any]) -> LineErrorInfo:
        """無視されたエラーの結果作成"""
        return LineErrorInfo(
            category=ErrorCategory.IGNORED,
            severity=ErrorSeverity.LOW,
            status_code=error_info.get("status_code"),
            error_code=error_info.get("error_code"),
            message=error_info.get("message"),
            description="このエラーは設定により無視されました。",
            recommended_action="特に対処は不要です。",
            is_retryable=False,
            raw_error=error_info,
            timestamp=error_info.get("timestamp")
        )

    def _generate_cache_key(self, error: Any) -> str:
        """キャッシュキーの生成"""
        import hashlib

        if self.config.cache.key_strategy == "minimal":
            # 最小限の情報でキー生成
            key_data = {
                "status_code": getattr(error, 'status_code', None) if hasattr(error, 'status_code') else error.get("status_code") if isinstance(error, dict) else None,
                "error_code": getattr(error, 'error_code', None) if hasattr(error, 'error_code') else error.get("error_code") if isinstance(error, dict) else None
            }
        else:
            # 完全な情報でキー生成
            key_data = str(error)

        return hashlib.md5(str(key_data).encode()).hexdigest()

    def _cleanup_cache(self):
        """キャッシュのクリーンアップ"""
        if len(self._cache) > self.config.cache.max_size:
            # LRU的な削除（簡単な実装）
            items_to_remove = len(self._cache) - self.config.cache.max_size + 1
            keys_to_remove = list(self._cache.keys())[:items_to_remove]

            for key in keys_to_remove:
                del self._cache[key]

    def get_cache_stats(self) -> Dict[str, Any]:
        """キャッシュ統計の取得"""
        total_requests = self._cache_stats["hits"] + self._cache_stats["misses"]
        hit_rate = self._cache_stats["hits"] / total_requests if total_requests > 0 else 0

        return {
            "hits": self._cache_stats["hits"],
            "misses": self._cache_stats["misses"],
            "hit_rate": hit_rate,
            "cache_size": len(self._cache),
            "max_size": self.config.cache.max_size if self.config.cache.enabled else 0
        }

    def clear_cache(self):
        """キャッシュのクリア"""
        self._cache.clear()
        self._cache_stats = {"hits": 0, "misses": 0}


# 例外クラス

class AnalysisError(Exception):
    """分析エラー例外"""

    def __init__(self, message: str, original_error: Optional[Exception] = None):
        """
        Args:
            message: エラーメッセージ
            original_error: 元の例外（あれば）
        """
        super().__init__(message)
        self.original_error = original_error


class ConfigurationError(Exception):
    """設定エラー例外"""
    pass


# ユーティリティ関数

def create_analyzer(analyzer_type: str = "sync", config: Optional['AnalyzerConfig'] = None) -> BaseLineErrorAnalyzer:
    """分析器のファクトリ関数

    Args:
        analyzer_type: 分析器タイプ ("sync" または "async")
        config: 設定オブジェクト

    Returns:
        BaseLineErrorAnalyzer: 作成された分析器

    Example:
        >>> analyzer = create_analyzer("sync")
        >>> async_analyzer = create_analyzer("async")
    """
    if analyzer_type == "sync":
        return LineErrorAnalyzer(config)
    elif analyzer_type == "async":
        from line_bot_error_detective import AsyncLineErrorAnalyzer
        return AsyncLineErrorAnalyzer(config)
    else:
        raise ValueError(f"Unknown analyzer type: {analyzer_type}")


def analyze_single_error(error: Union[Dict, Exception, Any],
                        config: Optional['AnalyzerConfig'] = None) -> LineErrorInfo:
    """単一エラーの簡単分析

    Args:
        error: 分析対象のエラー
        config: 設定（オプション）

    Returns:
        LineErrorInfo: 分析結果

    Example:
        >>> error = {"status_code": 429, "message": "Too Many Requests"}
        >>> result = analyze_single_error(error)
        >>> print(result.category.value)
        'RATE_LIMIT_ERROR'
    """
    analyzer = LineErrorAnalyzer(config)
    return analyzer.analyze(error)


# 使用例とデモンストレーション

def demo_base_analyzer():
    """ベースアナライザのデモンストレーション"""

    print("🔍 ベースアナライザ デモンストレーション")
    print("=" * 50)

    # 基本的な使用例
    analyzer = LineErrorAnalyzer()

    # テストエラー
    test_errors = [
        {"status_code": 401, "message": "Unauthorized"},
        {"status_code": 429, "error_code": "42901", "message": "Too Many Requests"},
        {"status_code": 500, "message": "Internal Server Error"},
        {"status_code": 400, "error_code": "40010", "message": "Invalid request"}
    ]

    print("\n📊 単一エラー分析:")
    for i, error in enumerate(test_errors, 1):
        result = analyzer.analyze(error)

        print(f"\nエラー #{i}: {error}")
        print(f"  カテゴリ: {result.category.value}")
        print(f"  重要度: {result.severity.value}")
        print(f"  リトライ可能: {result.is_retryable}")
        print(f"  説明: {result.description}")

    # バッチ分析
    print("\n📦 バッチ分析:")
    batch_results = analyzer.analyze_batch(test_errors)
    print(f"分析数: {len(batch_results)}")

    categories = {}
    for result in batch_results:
        category = result.category.value
        categories[category] = categories.get(category, 0) + 1

    print("カテゴリ別集計:")
    for category, count in categories.items():
        print(f"  {category}: {count}件")

    # 統計情報
    print("\n📈 分析統計:")
    stats = analyzer.get_analysis_stats()
    for key, value in stats.items():
        if key != "analysis_times":  # 長いリストは除外
            print(f"  {key}: {value}")

    # キャッシュ統計
    print("\n💾 キャッシュ統計:")
    cache_stats = analyzer.get_cache_stats()
    for key, value in cache_stats.items():
        print(f"  {key}: {value}")

    # カスタムハンドラーのテスト
    print("\n🛠️ カスタムハンドラー:")

    def custom_business_error_handler(error_info):
        """カスタムビジネスエラーハンドラー"""
        if error_info.get("error_code") == "BUSINESS_001":
            return ErrorCategory.VALIDATION_ERROR
        return None

    analyzer.register_custom_handler("BUSINESS_001", custom_business_error_handler)

    custom_error = {"error_code": "BUSINESS_001", "message": "Business logic error"}
    custom_result = analyzer.analyze(custom_error)
    print(f"カスタムエラー: {custom_error}")
    print(f"  判定カテゴリ: {custom_result.category.value}")

if __name__ == "__main__":
    demo_base_analyzer()
```

## カスタム分析器の作成

```python
class CustomLineErrorAnalyzer(BaseLineErrorAnalyzer):
    """カスタム LINE エラー分析器の例"""

    def __init__(self, config: Optional['AnalyzerConfig'] = None):
        super().__init__(config)
        self.business_rules = {}
        self.context_analyzers = []

    def analyze(self, error: Union[Dict, Exception, Any]) -> LineErrorInfo:
        """カスタム分析ロジック"""

        # 基本的な情報抽出
        error_info = self._extract_error_info(error)

        # ビジネスルールの適用
        business_category = self._apply_business_rules(error_info)
        if business_category:
            category = business_category
        else:
            # デフォルトの判定
            category = self._determine_category(error_info)

        # コンテキスト分析
        context_info = self._analyze_context(error_info)

        # 重要度の動的調整
        base_severity = self._determine_severity(error_info, category)
        adjusted_severity = self._adjust_severity_by_context(base_severity, context_info)

        # カスタム結果作成
        return LineErrorInfo(
            category=category,
            severity=adjusted_severity,
            status_code=error_info.get("status_code"),
            error_code=error_info.get("error_code"),
            message=error_info.get("message"),
            description=self._generate_custom_description(error_info, category, context_info),
            recommended_action=self._generate_custom_action(error_info, category, context_info),
            is_retryable=self._determine_custom_retryable(error_info, category, context_info),
            raw_error=error_info,
            timestamp=error_info.get("timestamp"),
            additional_info=context_info  # カスタム情報
        )

    def add_business_rule(self, rule_name: str, condition_func: callable, action_func: callable):
        """ビジネスルールの追加"""
        self.business_rules[rule_name] = {
            "condition": condition_func,
            "action": action_func
        }

    def add_context_analyzer(self, analyzer_func: callable):
        """コンテキスト分析器の追加"""
        self.context_analyzers.append(analyzer_func)

    def _apply_business_rules(self, error_info: Dict[str, Any]) -> Optional[ErrorCategory]:
        """ビジネスルールの適用"""

        for rule_name, rule in self.business_rules.items():
            try:
                if rule["condition"](error_info):
                    return rule["action"](error_info)
            except Exception as e:
                self.logger.warning(f"Business rule {rule_name} failed: {e}")

        return None

    def _analyze_context(self, error_info: Dict[str, Any]) -> Dict[str, Any]:
        """コンテキスト分析"""

        context = {}

        for analyzer in self.context_analyzers:
            try:
                result = analyzer(error_info)
                if isinstance(result, dict):
                    context.update(result)
            except Exception as e:
                self.logger.warning(f"Context analyzer failed: {e}")

        return context

    def _adjust_severity_by_context(self, base_severity: ErrorSeverity, context: Dict[str, Any]) -> ErrorSeverity:
        """コンテキストによる重要度調整"""

        # 例: ピーク時間中は重要度を上げる
        if context.get("is_peak_time"):
            severity_levels = [ErrorSeverity.LOW, ErrorSeverity.MEDIUM, ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]
            current_index = severity_levels.index(base_severity)
            if current_index < len(severity_levels) - 1:
                return severity_levels[current_index + 1]

        return base_severity

    def _generate_custom_description(self, error_info: Dict[str, Any],
                                   category: ErrorCategory,
                                   context: Dict[str, Any]) -> str:
        """カスタム説明文の生成"""

        base_description = self._generate_description(error_info, category)

        # コンテキスト情報を追加
        if context.get("user_impact_level"):
            base_description += f" (ユーザー影響レベル: {context['user_impact_level']})"

        if context.get("system_load"):
            base_description += f" (システム負荷: {context['system_load']})"

        return base_description

    def _generate_custom_action(self, error_info: Dict[str, Any],
                               category: ErrorCategory,
                               context: Dict[str, Any]) -> str:
        """カスタム対処法の生成"""

        base_action = self._generate_recommended_action(error_info, category)

        # コンテキストに応じた追加アクション
        if context.get("is_peak_time"):
            base_action += " ピーク時間中のため、負荷分散を検討してください。"

        if context.get("repeated_failure"):
            base_action += " 繰り返し発生しているため、根本原因の調査が必要です。"

        return base_action

    def _determine_custom_retryable(self, error_info: Dict[str, Any],
                                   category: ErrorCategory,
                                   context: Dict[str, Any]) -> bool:
        """カスタムリトライ可能性判定"""

        base_retryable = self._is_retryable(error_info, category)

        # コンテキストによる調整
        if context.get("system_overload"):
            return False  # システム過負荷時はリトライしない

        if context.get("circuit_breaker_open"):
            return False  # サーキットブレーカーが開いている場合はリトライしない

        return base_retryable

# カスタム分析器の使用例
def demo_custom_analyzer():
    """カスタム分析器のデモ"""

    analyzer = CustomLineErrorAnalyzer()

    # ビジネスルールの追加
    def is_payment_error(error_info):
        return error_info.get("error_code", "").startswith("PAY")

    def handle_payment_error(error_info):
        return ErrorCategory.VALIDATION_ERROR

    analyzer.add_business_rule("payment_error", is_payment_error, handle_payment_error)

    # コンテキスト分析器の追加
    def analyze_time_context(error_info):
        from datetime import datetime
        now = datetime.now()
        is_peak = 9 <= now.hour <= 18  # 9-18時をピーク時間とする
        return {"is_peak_time": is_peak}

    def analyze_load_context(error_info):
        # 実際の実装では外部システムから負荷情報を取得
        return {"system_load": "normal"}

    analyzer.add_context_analyzer(analyze_time_context)
    analyzer.add_context_analyzer(analyze_load_context)

    # テスト
    payment_error = {"error_code": "PAY001", "message": "Payment failed"}
    result = analyzer.analyze(payment_error)

    print(f"カスタム分析結果:")
    print(f"  カテゴリ: {result.category.value}")
    print(f"  説明: {result.description}")
    print(f"  追加情報: {result.additional_info}")

if __name__ == "__main__":
    demo_custom_analyzer()
```

このベースアナライザ API リファレンスは、LINE Bot エラー分析器の中核となる機能を詳細に説明し、カスタム分析器の作成方法も提供しています。継承とカスタマイズにより、特定のビジネス要件に合わせた分析機能を構築できます。
