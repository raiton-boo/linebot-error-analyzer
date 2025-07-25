# 設定ガイド

LINE Bot エラー分析器の詳細な設定方法と設定オプションについて説明します。

## 基本設定

### 1. 基本的な設定方法

```python
from line_bot_error_detective import LineErrorAnalyzer, AsyncLineErrorAnalyzer
from line_bot_error_detective.core.config import AnalyzerConfig
from line_bot_error_detective.core.models import ErrorSeverity

# 基本設定
config = AnalyzerConfig()

# 同期分析器
analyzer = LineErrorAnalyzer(config=config)

# 非同期分析器
async_analyzer = AsyncLineErrorAnalyzer(config=config)
```

### 2. 設定ファイルからの読み込み

```python
import json
import yaml
from pathlib import Path

# JSONファイルからの設定
def load_config_from_json(config_path: str) -> AnalyzerConfig:
    """JSONファイルから設定を読み込み"""

    with open(config_path, 'r', encoding='utf-8') as f:
        config_data = json.load(f)

    return AnalyzerConfig(**config_data)

# YAMLファイルからの設定
def load_config_from_yaml(config_path: str) -> AnalyzerConfig:
    """YAMLファイルから設定を読み込み"""

    with open(config_path, 'r', encoding='utf-8') as f:
        config_data = yaml.safe_load(f)

    return AnalyzerConfig(**config_data)

# 使用例
config = load_config_from_json('config/analyzer_config.json')
analyzer = LineErrorAnalyzer(config=config)
```

## 設定オプション詳細

### 1. 分析設定 (AnalysisConfig)

```python
from dataclasses import dataclass
from typing import Dict, List, Optional

@dataclass
class AnalysisConfig:
    """分析設定クラス"""

    # 基本分析設定
    enable_detailed_analysis: bool = True
    enable_pattern_matching: bool = True
    enable_severity_assessment: bool = True

    # カスタムエラーコードマッピング
    custom_error_codes: Optional[Dict[str, str]] = None

    # 重要度判定設定
    severity_thresholds: Optional[Dict[str, float]] = None

    # 分析対象外エラー
    ignore_error_codes: Optional[List[str]] = None
    ignore_status_codes: Optional[List[int]] = None

    # 分析タイムアウト（秒）
    analysis_timeout: float = 5.0

# 設定例
analysis_config = AnalysisConfig(
    enable_detailed_analysis=True,
    custom_error_codes={
        "CUSTOM_001": "カスタムビジネスエラー",
        "CUSTOM_002": "データ整合性エラー"
    },
    severity_thresholds={
        "critical": 0.9,
        "high": 0.7,
        "medium": 0.4,
        "low": 0.2
    },
    ignore_error_codes=["40010", "40011"],  # 無視するエラーコード
    ignore_status_codes=[418],  # I'm a teapot
    analysis_timeout=10.0
)
```

### 2. キャッシュ設定 (CacheConfig)

```python
@dataclass
class CacheConfig:
    """キャッシュ設定クラス"""

    # キャッシュ有効/無効
    enabled: bool = False

    # キャッシュサイズ（エントリ数）
    max_size: int = 1000

    # キャッシュTTL（秒）
    ttl_seconds: int = 3600

    # キャッシュキー生成方法
    key_strategy: str = "full"  # "full", "minimal", "custom"

    # LRU vs LFU
    eviction_policy: str = "lru"  # "lru", "lfu", "ttl"

    # キャッシュ統計収集
    collect_stats: bool = True

# 設定例
cache_config = CacheConfig(
    enabled=True,
    max_size=5000,
    ttl_seconds=7200,  # 2時間
    key_strategy="minimal",
    eviction_policy="lru",
    collect_stats=True
)
```

### 3. 非同期処理設定 (AsyncConfig)

```python
@dataclass
class AsyncConfig:
    """非同期処理設定クラス"""

    # デフォルトバッチサイズ
    default_batch_size: int = 50

    # 最大バッチサイズ
    max_batch_size: int = 500

    # 同時実行数制限
    max_concurrent: int = 10

    # バッチ処理タイムアウト（秒）
    batch_timeout: float = 30.0

    # リトライ設定
    retry_attempts: int = 3
    retry_delay: float = 1.0
    retry_backoff: float = 2.0

    # セマフォ制御
    use_semaphore: bool = True
    semaphore_limit: int = 100

# 設定例
async_config = AsyncConfig(
    default_batch_size=100,
    max_batch_size=1000,
    max_concurrent=20,
    batch_timeout=60.0,
    retry_attempts=5,
    retry_delay=0.5,
    retry_backoff=1.5,
    use_semaphore=True,
    semaphore_limit=200
)
```

### 4. ログ設定 (LoggingConfig)

```python
@dataclass
class LoggingConfig:
    """ログ設定クラス"""

    # ログレベル
    level: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL

    # ログ形式
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # ログファイル設定
    log_file: Optional[str] = None
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5

    # 構造化ログ
    structured_logging: bool = False

    # 詳細分析ログ
    log_analysis_details: bool = False

    # パフォーマンスログ
    log_performance: bool = False

# 設定例
logging_config = LoggingConfig(
    level="DEBUG",
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    log_file="logs/analyzer.log",
    max_file_size=50 * 1024 * 1024,  # 50MB
    backup_count=10,
    structured_logging=True,
    log_analysis_details=True,
    log_performance=True
)
```

### 5. メトリクス設定 (MetricsConfig)

```python
@dataclass
class MetricsConfig:
    """メトリクス設定クラス"""

    # メトリクス収集有効/無効
    enabled: bool = True

    # 収集間隔（秒）
    collection_interval: float = 60.0

    # メトリクス保持期間（秒）
    retention_period: int = 86400  # 24時間

    # 詳細メトリクス
    detailed_metrics: bool = False

    # エクスポート設定
    export_enabled: bool = False
    export_endpoint: Optional[str] = None
    export_format: str = "prometheus"  # prometheus, json, csv

    # カスタムメトリクス
    custom_metrics: Optional[List[str]] = None

# 設定例
metrics_config = MetricsConfig(
    enabled=True,
    collection_interval=30.0,
    retention_period=7 * 86400,  # 1週間
    detailed_metrics=True,
    export_enabled=True,
    export_endpoint="http://localhost:9090/metrics",
    export_format="prometheus",
    custom_metrics=["business_error_rate", "user_impact_score"]
)
```

## 統合設定クラス

```python
@dataclass
class AnalyzerConfig:
    """統合分析器設定クラス"""

    # 基本設定
    version: str = "2.0.0"
    environment: str = "production"  # development, staging, production

    # 各種設定
    analysis: AnalysisConfig = AnalysisConfig()
    cache: CacheConfig = CacheConfig()
    async_config: AsyncConfig = AsyncConfig()
    logging: LoggingConfig = LoggingConfig()
    metrics: MetricsConfig = MetricsConfig()

    # LINE API設定
    line_api_timeout: float = 10.0
    line_api_retry_attempts: int = 3

    # セキュリティ設定
    mask_sensitive_data: bool = True
    log_raw_errors: bool = False

    # パフォーマンス設定
    enable_performance_monitoring: bool = True
    performance_threshold_ms: float = 1000.0

    def __post_init__(self):
        """設定後の初期化処理"""
        self._validate_config()
        self._apply_environment_overrides()

    def _validate_config(self):
        """設定値の検証"""

        # バッチサイズの検証
        if self.async_config.default_batch_size > self.async_config.max_batch_size:
            raise ValueError("default_batch_size cannot be larger than max_batch_size")

        # キャッシュサイズの検証
        if self.cache.enabled and self.cache.max_size <= 0:
            raise ValueError("cache max_size must be positive when cache is enabled")

        # タイムアウトの検証
        if self.analysis.analysis_timeout <= 0:
            raise ValueError("analysis_timeout must be positive")

    def _apply_environment_overrides(self):
        """環境別設定オーバーライド"""

        if self.environment == "development":
            self.logging.level = "DEBUG"
            self.logging.log_analysis_details = True
            self.metrics.detailed_metrics = True
            self.cache.collect_stats = True

        elif self.environment == "staging":
            self.logging.level = "INFO"
            self.metrics.enabled = True
            self.cache.enabled = True

        elif self.environment == "production":
            self.logging.level = "WARNING"
            self.logging.log_raw_errors = False
            self.mask_sensitive_data = True
            self.enable_performance_monitoring = True

    @classmethod
    def from_file(cls, config_path: str) -> 'AnalyzerConfig':
        """ファイルから設定を読み込み"""

        config_path = Path(config_path)

        if config_path.suffix == '.json':
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
        elif config_path.suffix in ['.yaml', '.yml']:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
        else:
            raise ValueError(f"Unsupported config file format: {config_path.suffix}")

        return cls(**config_data)

    def to_dict(self) -> Dict:
        """設定を辞書形式で取得"""
        from dataclasses import asdict
        return asdict(self)

    def save_to_file(self, config_path: str):
        """設定をファイルに保存"""

        config_path = Path(config_path)
        config_data = self.to_dict()

        config_path.parent.mkdir(parents=True, exist_ok=True)

        if config_path.suffix == '.json':
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
        elif config_path.suffix in ['.yaml', '.yml']:
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True)
        else:
            raise ValueError(f"Unsupported config file format: {config_path.suffix}")
```

## 設定ファイル例

### 1. 本番環境設定 (production.json)

```json
{
  "version": "2.0.0",
  "environment": "production",
  "analysis": {
    "enable_detailed_analysis": true,
    "enable_pattern_matching": true,
    "enable_severity_assessment": true,
    "custom_error_codes": {
      "BUSINESS_001": "ビジネスロジックエラー",
      "BUSINESS_002": "データ検証エラー"
    },
    "severity_thresholds": {
      "critical": 0.9,
      "high": 0.7,
      "medium": 0.4,
      "low": 0.2
    },
    "ignore_error_codes": ["40010"],
    "analysis_timeout": 5.0
  },
  "cache": {
    "enabled": true,
    "max_size": 10000,
    "ttl_seconds": 3600,
    "key_strategy": "minimal",
    "eviction_policy": "lru",
    "collect_stats": true
  },
  "async_config": {
    "default_batch_size": 100,
    "max_batch_size": 500,
    "max_concurrent": 10,
    "batch_timeout": 30.0,
    "retry_attempts": 3,
    "retry_delay": 1.0,
    "retry_backoff": 2.0,
    "use_semaphore": true,
    "semaphore_limit": 100
  },
  "logging": {
    "level": "WARNING",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "log_file": "logs/analyzer_prod.log",
    "max_file_size": 104857600,
    "backup_count": 10,
    "structured_logging": true,
    "log_analysis_details": false,
    "log_performance": true
  },
  "metrics": {
    "enabled": true,
    "collection_interval": 60.0,
    "retention_period": 604800,
    "detailed_metrics": false,
    "export_enabled": true,
    "export_endpoint": "http://prometheus:9090/metrics",
    "export_format": "prometheus"
  },
  "line_api_timeout": 10.0,
  "line_api_retry_attempts": 3,
  "mask_sensitive_data": true,
  "log_raw_errors": false,
  "enable_performance_monitoring": true,
  "performance_threshold_ms": 1000.0
}
```

### 2. 開発環境設定 (development.yaml)

```yaml
version: '2.0.0'
environment: 'development'

analysis:
  enable_detailed_analysis: true
  enable_pattern_matching: true
  enable_severity_assessment: true
  custom_error_codes:
    TEST_001: 'テストエラー1'
    TEST_002: 'テストエラー2'
  severity_thresholds:
    critical: 0.8
    high: 0.6
    medium: 0.3
    low: 0.1
  ignore_error_codes: []
  analysis_timeout: 10.0

cache:
  enabled: true
  max_size: 1000
  ttl_seconds: 1800
  key_strategy: 'full'
  eviction_policy: 'lru'
  collect_stats: true

async_config:
  default_batch_size: 20
  max_batch_size: 100
  max_concurrent: 5
  batch_timeout: 60.0
  retry_attempts: 5
  retry_delay: 0.5
  retry_backoff: 1.5
  use_semaphore: true
  semaphore_limit: 50

logging:
  level: 'DEBUG'
  format: '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
  log_file: 'logs/analyzer_dev.log'
  max_file_size: 10485760
  backup_count: 3
  structured_logging: true
  log_analysis_details: true
  log_performance: true

metrics:
  enabled: true
  collection_interval: 30.0
  retention_period: 86400
  detailed_metrics: true
  export_enabled: false
  custom_metrics:
    - 'dev_error_rate'
    - 'test_success_rate'

line_api_timeout: 15.0
line_api_retry_attempts: 5
mask_sensitive_data: false
log_raw_errors: true
enable_performance_monitoring: true
performance_threshold_ms: 500.0
```

## 動的設定変更

```python
from typing import Dict, Any
import threading
import time

class DynamicConfigManager:
    """動的設定管理クラス"""

    def __init__(self, initial_config: AnalyzerConfig):
        self.config = initial_config
        self._config_lock = threading.RLock()
        self._watchers = []
        self._running = False

    def update_config(self, updates: Dict[str, Any]):
        """設定の動的更新"""

        with self._config_lock:
            # 設定を更新
            for key, value in updates.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)
                else:
                    # ネストした設定の更新
                    self._update_nested_config(key, value)

            # 設定変更通知
            self._notify_watchers(updates)

    def _update_nested_config(self, key: str, value: Any):
        """ネストした設定の更新"""

        if '.' in key:
            parts = key.split('.')
            obj = self.config

            for part in parts[:-1]:
                obj = getattr(obj, part)

            setattr(obj, parts[-1], value)

    def _notify_watchers(self, updates: Dict[str, Any]):
        """設定変更の通知"""

        for watcher in self._watchers:
            try:
                watcher(updates)
            except Exception as e:
                print(f"Config watcher error: {e}")

    def add_watcher(self, callback):
        """設定変更監視の追加"""
        self._watchers.append(callback)

    def remove_watcher(self, callback):
        """設定変更監視の削除"""
        if callback in self._watchers:
            self._watchers.remove(callback)

    def get_config(self) -> AnalyzerConfig:
        """現在の設定を取得"""
        with self._config_lock:
            return self.config

# 使用例
def config_change_handler(updates: Dict[str, Any]):
    """設定変更ハンドラー"""
    print(f"設定が変更されました: {updates}")

# 動的設定管理の初期化
config = AnalyzerConfig()
config_manager = DynamicConfigManager(config)
config_manager.add_watcher(config_change_handler)

# 設定の動的変更
config_manager.update_config({
    "cache.max_size": 5000,
    "logging.level": "DEBUG",
    "async_config.default_batch_size": 150
})
```

## 環境変数による設定オーバーライド

```python
import os
from typing import Optional

class EnvironmentConfigLoader:
    """環境変数による設定ローダー"""

    @staticmethod
    def load_from_environment(base_config: AnalyzerConfig) -> AnalyzerConfig:
        """環境変数から設定をオーバーライド"""

        # 基本設定
        base_config.environment = os.getenv('ANALYZER_ENV', base_config.environment)

        # 分析設定
        if os.getenv('ANALYZER_DETAILED_ANALYSIS'):
            base_config.analysis.enable_detailed_analysis = \
                os.getenv('ANALYZER_DETAILED_ANALYSIS').lower() == 'true'

        if os.getenv('ANALYZER_TIMEOUT'):
            base_config.analysis.analysis_timeout = float(os.getenv('ANALYZER_TIMEOUT'))

        # キャッシュ設定
        if os.getenv('ANALYZER_CACHE_ENABLED'):
            base_config.cache.enabled = \
                os.getenv('ANALYZER_CACHE_ENABLED').lower() == 'true'

        if os.getenv('ANALYZER_CACHE_SIZE'):
            base_config.cache.max_size = int(os.getenv('ANALYZER_CACHE_SIZE'))

        # ログ設定
        if os.getenv('ANALYZER_LOG_LEVEL'):
            base_config.logging.level = os.getenv('ANALYZER_LOG_LEVEL')

        if os.getenv('ANALYZER_LOG_FILE'):
            base_config.logging.log_file = os.getenv('ANALYZER_LOG_FILE')

        # 非同期設定
        if os.getenv('ANALYZER_BATCH_SIZE'):
            base_config.async_config.default_batch_size = \
                int(os.getenv('ANALYZER_BATCH_SIZE'))

        # メトリクス設定
        if os.getenv('ANALYZER_METRICS_ENABLED'):
            base_config.metrics.enabled = \
                os.getenv('ANALYZER_METRICS_ENABLED').lower() == 'true'

        return base_config

# 使用例
# 環境変数設定
os.environ['ANALYZER_ENV'] = 'production'
os.environ['ANALYZER_CACHE_ENABLED'] = 'true'
os.environ['ANALYZER_CACHE_SIZE'] = '10000'
os.environ['ANALYZER_LOG_LEVEL'] = 'WARNING'
os.environ['ANALYZER_BATCH_SIZE'] = '200'

# 基本設定から開始
base_config = AnalyzerConfig()

# 環境変数でオーバーライド
config = EnvironmentConfigLoader.load_from_environment(base_config)

print(f"環境: {config.environment}")
print(f"キャッシュ有効: {config.cache.enabled}")
print(f"キャッシュサイズ: {config.cache.max_size}")
print(f"ログレベル: {config.logging.level}")
print(f"バッチサイズ: {config.async_config.default_batch_size}")
```

## 設定検証ツール

```python
class ConfigValidator:
    """設定検証ツール"""

    @staticmethod
    def validate_config(config: AnalyzerConfig) -> Dict[str, List[str]]:
        """設定の詳細検証"""

        errors = {}
        warnings = {}

        # 分析設定の検証
        analysis_errors = ConfigValidator._validate_analysis_config(config.analysis)
        if analysis_errors:
            errors['analysis'] = analysis_errors

        # キャッシュ設定の検証
        cache_errors = ConfigValidator._validate_cache_config(config.cache)
        if cache_errors:
            errors['cache'] = cache_errors

        # 非同期設定の検証
        async_errors = ConfigValidator._validate_async_config(config.async_config)
        if async_errors:
            errors['async'] = async_errors

        # ログ設定の検証
        logging_errors = ConfigValidator._validate_logging_config(config.logging)
        if logging_errors:
            errors['logging'] = logging_errors

        # パフォーマンス警告
        perf_warnings = ConfigValidator._check_performance_warnings(config)
        if perf_warnings:
            warnings['performance'] = perf_warnings

        return {
            'errors': errors,
            'warnings': warnings,
            'is_valid': len(errors) == 0
        }

    @staticmethod
    def _validate_analysis_config(config: AnalysisConfig) -> List[str]:
        """分析設定の検証"""
        errors = []

        if config.analysis_timeout <= 0:
            errors.append("analysis_timeout must be positive")

        if config.analysis_timeout > 30:
            errors.append("analysis_timeout should not exceed 30 seconds")

        if config.severity_thresholds:
            for severity, threshold in config.severity_thresholds.items():
                if not 0 <= threshold <= 1:
                    errors.append(f"severity_threshold for {severity} must be between 0 and 1")

        return errors

    @staticmethod
    def _validate_cache_config(config: CacheConfig) -> List[str]:
        """キャッシュ設定の検証"""
        errors = []

        if config.enabled:
            if config.max_size <= 0:
                errors.append("cache max_size must be positive when enabled")

            if config.ttl_seconds <= 0:
                errors.append("cache ttl_seconds must be positive")

            if config.key_strategy not in ['full', 'minimal', 'custom']:
                errors.append("cache key_strategy must be 'full', 'minimal', or 'custom'")

            if config.eviction_policy not in ['lru', 'lfu', 'ttl']:
                errors.append("cache eviction_policy must be 'lru', 'lfu', or 'ttl'")

        return errors

    @staticmethod
    def _validate_async_config(config: AsyncConfig) -> List[str]:
        """非同期設定の検証"""
        errors = []

        if config.default_batch_size <= 0:
            errors.append("default_batch_size must be positive")

        if config.max_batch_size <= 0:
            errors.append("max_batch_size must be positive")

        if config.default_batch_size > config.max_batch_size:
            errors.append("default_batch_size cannot exceed max_batch_size")

        if config.max_concurrent <= 0:
            errors.append("max_concurrent must be positive")

        if config.batch_timeout <= 0:
            errors.append("batch_timeout must be positive")

        if config.retry_attempts < 0:
            errors.append("retry_attempts cannot be negative")

        if config.retry_delay < 0:
            errors.append("retry_delay cannot be negative")

        if config.retry_backoff < 1:
            errors.append("retry_backoff must be at least 1")

        return errors

    @staticmethod
    def _validate_logging_config(config: LoggingConfig) -> List[str]:
        """ログ設定の検証"""
        errors = []

        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if config.level not in valid_levels:
            errors.append(f"log level must be one of {valid_levels}")

        if config.max_file_size <= 0:
            errors.append("max_file_size must be positive")

        if config.backup_count < 0:
            errors.append("backup_count cannot be negative")

        return errors

    @staticmethod
    def _check_performance_warnings(config: AnalyzerConfig) -> List[str]:
        """パフォーマンス警告のチェック"""
        warnings = []

        # キャッシュ無効時の警告
        if not config.cache.enabled:
            warnings.append("Cache is disabled - consider enabling for better performance")

        # 大きなバッチサイズの警告
        if config.async_config.default_batch_size > 200:
            warnings.append("Large batch size may consume significant memory")

        # 高い同時実行数の警告
        if config.async_config.max_concurrent > 50:
            warnings.append("High concurrency may impact system resources")

        # デバッグログの警告
        if config.logging.level == 'DEBUG' and config.environment == 'production':
            warnings.append("DEBUG logging in production may impact performance")

        return warnings

# 使用例
config = AnalyzerConfig()
validation_result = ConfigValidator.validate_config(config)

print(f"設定検証結果:")
print(f"有効: {validation_result['is_valid']}")

if validation_result['errors']:
    print(f"エラー:")
    for category, errors in validation_result['errors'].items():
        for error in errors:
            print(f"  {category}: {error}")

if validation_result['warnings']:
    print(f"警告:")
    for category, warnings in validation_result['warnings'].items():
        for warning in warnings:
            print(f"  {category}: {warning}")
```

## まとめ

この設定ガイドでは、LINE Bot エラー分析器の詳細な設定方法を説明しました：

1. **基本設定**: 基本的な設定方法と設定ファイルからの読み込み
2. **詳細オプション**: 分析、キャッシュ、非同期、ログ、メトリクス設定
3. **統合設定**: 全ての設定を統合した設定クラス
4. **設定ファイル**: JSON/YAML 形式での設定例
5. **動的設定**: 実行時の設定変更機能
6. **環境変数**: 環境変数による設定オーバーライド
7. **設定検証**: 設定値の検証とパフォーマンス最適化

適切な設定により、アプリケーションの要件に合わせた最適なエラー分析環境を構築できます。
