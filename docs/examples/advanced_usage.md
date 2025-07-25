# 🚀 高度な使用例

実際のプロダクション環境での高度な使用パターンと最適化手法を紹介します。

## 🏢 エンタープライズレベルのエラー監視システム

### 1. マルチサービス対応エラーハブ

複数の LINE Bot サービスのエラーを一元管理するシステムです。

```python
import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from collections import defaultdict
from linebot_error_analyzer import AsyncLineErrorAnalyzer

@dataclass
class ServiceConfig:
    """サービス設定"""
    service_id: str
    service_name: str
    channel_access_token: str
    alert_threshold: int = 100  # 1時間あたりのエラー閾値
    critical_categories: List[str] = field(default_factory=lambda: ["AUTH_ERROR", "SERVER_ERROR"])

class EnterpriseErrorHub:
    """エンタープライズエラー監視ハブ"""

    def __init__(self, services: List[ServiceConfig]):
        self.services = {s.service_id: s for s in services}
        self.analyzer = AsyncLineErrorAnalyzer()
        self.analyzer.enable_caching(50000)  # 大容量キャッシュ

        # 統計データストレージ
        self.error_storage = defaultdict(lambda: defaultdict(list))
        self.service_stats = defaultdict(lambda: {
            "total_errors": 0,
            "critical_errors": 0,
            "last_alert": None
        })

        # アラート管理
        self.alert_cooldown = timedelta(minutes=15)  # アラート間隔

        # ログ設定
        self.setup_logging()

    def setup_logging(self):
        """構造化ログの設定"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('enterprise_errors.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('enterprise_error_hub')

    async def process_error_batch(self, service_id: str, errors: List[dict]) -> List[dict]:
        """エラーバッチの処理"""

        if service_id not in self.services:
            self.logger.warning(f"Unknown service: {service_id}")
            return []

        service = self.services[service_id]

        # バッチ分析実行
        results = await self.analyzer.analyze_batch(errors, batch_size=100)

        processed_results = []
        critical_count = 0

        for error, result in zip(errors, results):
            # エラー情報の拡張
            enriched_result = {
                "service_id": service_id,
                "service_name": service.service_name,
                "timestamp": datetime.now().isoformat(),
                "analysis": result.to_dict(),
                "original_error": error
            }

            processed_results.append(enriched_result)

            # 統計更新
            await self.update_service_stats(service_id, result)

            # 重要エラーのカウント
            if result.category.value in service.critical_categories:
                critical_count += 1

            # ストレージに保存
            hour_key = datetime.now().strftime("%Y-%m-%d-%H")
            self.error_storage[service_id][hour_key].append(enriched_result)

        # アラートチェック
        if critical_count > 0:
            await self.check_and_send_alerts(service_id, critical_count)

        return processed_results

    async def update_service_stats(self, service_id: str, result):
        """サービス統計の更新"""

        stats = self.service_stats[service_id]
        stats["total_errors"] += 1

        if result.severity.value in ["CRITICAL", "HIGH"]:
            stats["critical_errors"] += 1

    async def check_and_send_alerts(self, service_id: str, critical_count: int):
        """アラート条件チェックと送信"""

        service = self.services[service_id]
        stats = self.service_stats[service_id]

        # 前回アラートからの時間チェック
        if stats["last_alert"] and datetime.now() - stats["last_alert"] < self.alert_cooldown:
            return

        # 1時間以内のエラー数チェック
        hour_key = datetime.now().strftime("%Y-%m-%d-%H")
        recent_errors = len(self.error_storage[service_id][hour_key])

        if recent_errors >= service.alert_threshold:
            await self.send_critical_alert(
                service_id,
                f"高頻度エラー検出: {recent_errors}件/時間 (閾値: {service.alert_threshold})"
            )
            stats["last_alert"] = datetime.now()

        if critical_count >= 10:  # 重要エラーが10件以上
            await self.send_critical_alert(
                service_id,
                f"重要エラー多発: {critical_count}件の重要エラー"
            )

    async def send_critical_alert(self, service_id: str, message: str):
        """重要アラートの送信"""

        service = self.services[service_id]

        alert_data = {
            "timestamp": datetime.now().isoformat(),
            "service_id": service_id,
            "service_name": service.service_name,
            "alert_type": "CRITICAL",
            "message": message,
            "stats": self.get_service_summary(service_id)
        }

        # ログ出力
        self.logger.critical(json.dumps(alert_data, ensure_ascii=False))

        # 実際の実装では Slack、メール、PagerDuty等に送信
        print(f"🚨 CRITICAL ALERT: {message}")

        # Webhook通知の例
        await self.notify_webhook(alert_data)

    async def notify_webhook(self, alert_data: dict):
        """Webhook通知の送信"""

        # 実装例：Slack Webhook
        import aiohttp

        webhook_url = "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"

        slack_message = {
            "text": f"🚨 LINE Bot Error Alert",
            "attachments": [{
                "color": "danger",
                "fields": [
                    {"title": "Service", "value": alert_data["service_name"], "short": True},
                    {"title": "Alert Type", "value": alert_data["alert_type"], "short": True},
                    {"title": "Message", "value": alert_data["message"], "short": False}
                ]
            }]
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=slack_message) as response:
                    if response.status == 200:
                        self.logger.info("Slack notification sent successfully")
                    else:
                        self.logger.error(f"Failed to send Slack notification: {response.status}")
        except Exception as e:
            self.logger.error(f"Webhook notification error: {e}")

    def get_service_summary(self, service_id: str) -> dict:
        """サービス統計サマリー"""

        stats = self.service_stats[service_id]

        # 過去24時間のエラー統計
        now = datetime.now()
        recent_errors = []

        for i in range(24):
            hour_key = (now - timedelta(hours=i)).strftime("%Y-%m-%d-%H")
            hour_errors = self.error_storage[service_id][hour_key]
            recent_errors.extend(hour_errors)

        # カテゴリ別統計
        category_stats = defaultdict(int)
        for error in recent_errors:
            category = error["analysis"]["category"]
            category_stats[category] += 1

        return {
            "total_errors_24h": len(recent_errors),
            "critical_errors_24h": stats["critical_errors"],
            "category_breakdown": dict(category_stats),
            "last_alert": stats["last_alert"].isoformat() if stats["last_alert"] else None
        }

    async def get_dashboard_data(self) -> dict:
        """ダッシュボード用データの取得"""

        dashboard_data = {
            "timestamp": datetime.now().isoformat(),
            "services": {}
        }

        for service_id, service in self.services.items():
            dashboard_data["services"][service_id] = {
                "service_name": service.service_name,
                "summary": self.get_service_summary(service_id),
                "analyzer_stats": self.analyzer.get_analysis_stats()
            }

        return dashboard_data

# 使用例
async def setup_enterprise_monitoring():
    """エンタープライズ監視の設定"""

    services = [
        ServiceConfig(
            service_id="customer_support_bot",
            service_name="カスタマーサポートBot",
            channel_access_token="token1",
            alert_threshold=50
        ),
        ServiceConfig(
            service_id="marketing_bot",
            service_name="マーケティングBot",
            channel_access_token="token2",
            alert_threshold=100
        ),
        ServiceConfig(
            service_id="internal_bot",
            service_name="内部通知Bot",
            channel_access_token="token3",
            alert_threshold=20
        )
    ]

    hub = EnterpriseErrorHub(services)

    # エラーストリームの処理（実際の実装では外部キューから取得）
    while True:
        try:
            # 各サービスからのエラーを処理
            for service_id in hub.services.keys():
                errors = await get_errors_from_service(service_id)  # 実装依存

                if errors:
                    results = await hub.process_error_batch(service_id, errors)
                    print(f"Processed {len(results)} errors for {service_id}")

            # ダッシュボードデータの更新
            dashboard_data = await hub.get_dashboard_data()
            await update_dashboard(dashboard_data)  # 実装依存

            await asyncio.sleep(30)  # 30秒間隔

        except Exception as e:
            logging.error(f"Monitoring loop error: {e}")
            await asyncio.sleep(60)
```

### 2. 自動復旧とフォールバック システム

```python
import asyncio
from typing import Callable, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

class RecoveryStrategy(Enum):
    """復旧戦略"""
    RETRY = "retry"
    FALLBACK = "fallback"
    CIRCUIT_BREAKER = "circuit_breaker"
    BACKOFF = "exponential_backoff"

@dataclass
class RecoveryConfig:
    """復旧設定"""
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    backoff_multiplier: float = 2.0
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: float = 300.0  # 5分

class SmartRecoverySystem:
    """スマート自動復旧システム"""

    def __init__(self, config: RecoveryConfig):
        self.config = config
        self.analyzer = AsyncLineErrorAnalyzer()

        # サーキットブレーカー状態管理
        self.circuit_states = {}
        self.failure_counts = defaultdict(int)
        self.last_failure_times = {}

        # 復旧戦略マッピング
        self.recovery_strategies = {
            "RATE_LIMIT": RecoveryStrategy.BACKOFF,
            "SERVER_ERROR": RecoveryStrategy.RETRY,
            "NETWORK_ERROR": RecoveryStrategy.CIRCUIT_BREAKER,
            "AUTH_ERROR": RecoveryStrategy.FALLBACK
        }

    async def execute_with_recovery(
        self,
        operation: Callable,
        fallback_operation: Optional[Callable] = None,
        operation_id: str = "default",
        *args,
        **kwargs
    ) -> Any:
        """復旧機能付きオペレーション実行"""

        # サーキットブレーカーチェック
        if self.is_circuit_open(operation_id):
            if fallback_operation:
                return await self.execute_fallback(fallback_operation, *args, **kwargs)
            else:
                raise Exception(f"Circuit breaker open for {operation_id}")

        for attempt in range(self.config.max_retries + 1):
            try:
                result = await operation(*args, **kwargs)

                # 成功時は失敗カウントをリセット
                self.reset_failure_count(operation_id)
                return result

            except Exception as e:
                error_info = await self.analyzer.analyze(e)

                # 最後の試行または非復旧可能エラー
                if attempt == self.config.max_retries or not error_info.is_retryable:
                    self.record_failure(operation_id)

                    # フォールバック戦略
                    if fallback_operation and self.should_use_fallback(error_info):
                        return await self.execute_fallback(fallback_operation, *args, **kwargs)

                    raise

                # 復旧戦略の実行
                await self.execute_recovery_strategy(error_info, attempt, operation_id)

        return None

    def is_circuit_open(self, operation_id: str) -> bool:
        """サーキットブレーカーの状態確認"""

        if operation_id not in self.circuit_states:
            return False

        failure_count = self.failure_counts[operation_id]
        last_failure = self.last_failure_times.get(operation_id)

        if failure_count >= self.config.circuit_breaker_threshold:
            if last_failure and datetime.now() - last_failure < timedelta(seconds=self.config.circuit_breaker_timeout):
                return True
            else:
                # タイムアウト後はリセット
                self.reset_failure_count(operation_id)
                return False

        return False

    def record_failure(self, operation_id: str):
        """失敗の記録"""
        self.failure_counts[operation_id] += 1
        self.last_failure_times[operation_id] = datetime.now()

    def reset_failure_count(self, operation_id: str):
        """失敗カウントのリセット"""
        self.failure_counts[operation_id] = 0
        if operation_id in self.last_failure_times:
            del self.last_failure_times[operation_id]

    async def execute_recovery_strategy(self, error_info, attempt: int, operation_id: str):
        """復旧戦略の実行"""

        strategy = self.recovery_strategies.get(
            error_info.category.value,
            RecoveryStrategy.RETRY
        )

        if strategy == RecoveryStrategy.BACKOFF:
            delay = min(
                self.config.base_delay * (self.config.backoff_multiplier ** attempt),
                self.config.max_delay
            )

            # Retry-Afterヘッダーがある場合はそれを優先
            if error_info.retry_after:
                delay = min(error_info.retry_after, self.config.max_delay)

            print(f"Exponential backoff: {delay}秒待機 (試行 {attempt + 1})")
            await asyncio.sleep(delay)

        elif strategy == RecoveryStrategy.RETRY:
            delay = self.config.base_delay * (attempt + 1)
            print(f"Simple retry: {delay}秒待機 (試行 {attempt + 1})")
            await asyncio.sleep(delay)

        elif strategy == RecoveryStrategy.CIRCUIT_BREAKER:
            # サーキットブレーカー状態を記録
            self.record_failure(operation_id)
            print(f"Circuit breaker activated for {operation_id}")

            # 短い待機後にサーキットブレーカーをチェック
            await asyncio.sleep(1.0)

    def should_use_fallback(self, error_info) -> bool:
        """フォールバック使用の判定"""

        fallback_categories = [
            "AUTH_ERROR",
            "INVALID_TOKEN",
            "SERVER_ERROR",
            "SERVICE_UNAVAILABLE"
        ]

        return error_info.category.value in fallback_categories

    async def execute_fallback(self, fallback_operation: Callable, *args, **kwargs) -> Any:
        """フォールバック操作の実行"""

        print("🔄 Executing fallback operation")

        try:
            result = await fallback_operation(*args, **kwargs)
            print("✅ Fallback operation succeeded")
            return result
        except Exception as e:
            print(f"❌ Fallback operation failed: {e}")
            raise

# LINE Bot での使用例
class ResilientLineBotService:
    """復旧機能付きLINE Botサービス"""

    def __init__(self, access_token: str, backup_token: str = None):
        self.access_token = access_token
        self.backup_token = backup_token

        self.recovery_system = SmartRecoverySystem(RecoveryConfig(
            max_retries=3,
            base_delay=1.0,
            backoff_multiplier=2.0,
            circuit_breaker_threshold=5
        ))

        # プライマリとバックアップのAPIクライアント
        self.primary_api = self.create_api_client(access_token)
        self.backup_api = self.create_api_client(backup_token) if backup_token else None

    def create_api_client(self, token: str):
        """APIクライアントの作成"""
        from linebot.v3.messaging import Configuration, ApiClient, MessagingApi

        if not token:
            return None

        configuration = Configuration(access_token=token)
        api_client = ApiClient(configuration)
        return MessagingApi(api_client)

    async def send_message_resilient(self, reply_token: str, message: str) -> bool:
        """復旧機能付きメッセージ送信"""

        async def primary_send():
            """プライマリAPIでの送信"""
            return await self.primary_api.reply_message_async(
                ReplyMessageRequest(
                    reply_token=reply_token,
                    messages=[TextMessage(text=message)]
                )
            )

        async def fallback_send():
            """バックアップAPIでの送信"""
            if not self.backup_api:
                raise Exception("Backup API not available")

            return await self.backup_api.reply_message_async(
                ReplyMessageRequest(
                    reply_token=reply_token,
                    messages=[TextMessage(text=f"[BACKUP] {message}")]
                )
            )

        try:
            await self.recovery_system.execute_with_recovery(
                primary_send,
                fallback_send,
                "message_send"
            )
            return True

        except Exception as e:
            print(f"All message send attempts failed: {e}")
            return False

    async def get_profile_resilient(self, user_id: str) -> Optional[dict]:
        """復旧機能付きプロフィール取得"""

        async def primary_get_profile():
            """プライマリAPIでのプロフィール取得"""
            profile = await self.primary_api.get_profile_async(user_id)
            return {
                "display_name": profile.display_name,
                "user_id": profile.user_id,
                "picture_url": profile.picture_url,
                "status_message": profile.status_message
            }

        async def fallback_get_profile():
            """フォールバック：キャッシュまたはデフォルト値"""
            # 実際の実装ではキャッシュやDBから取得
            return {
                "display_name": "ユーザー",
                "user_id": user_id,
                "picture_url": None,
                "status_message": None
            }

        try:
            return await self.recovery_system.execute_with_recovery(
                primary_get_profile,
                fallback_get_profile,
                "profile_get"
            )

        except Exception as e:
            print(f"Profile retrieval failed: {e}")
            return None

# 使用例
async def demonstrate_resilient_service():
    """復旧機能の実演"""

    service = ResilientLineBotService(
        access_token="primary_token",
        backup_token="backup_token"
    )

    # メッセージ送信のテスト
    success = await service.send_message_resilient(
        "reply_token_123",
        "Hello, World!"
    )

    if success:
        print("✅ Message sent successfully")
    else:
        print("❌ Message sending failed")

    # プロフィール取得のテスト
    profile = await service.get_profile_resilient("user_123")

    if profile:
        print(f"✅ Profile retrieved: {profile['display_name']}")
    else:
        print("❌ Profile retrieval failed")
```

### 3. パフォーマンス最適化とスケーリング

```python
import asyncio
import time
from typing import Dict, List, Any
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor

@dataclass
class PerformanceMetrics:
    """パフォーマンス指標"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    average_response_time: float = 0.0
    peak_response_time: float = 0.0
    requests_per_second: float = 0.0
    memory_usage_mb: float = 0.0

class HighPerformanceErrorProcessor:
    """高性能エラー処理システム"""

    def __init__(self, max_workers: int = 10, batch_size: int = 1000):
        self.max_workers = max_workers
        self.batch_size = batch_size

        # 複数の分析器でロードバランシング
        self.analyzers = [AsyncLineErrorAnalyzer() for _ in range(max_workers)]
        for analyzer in self.analyzers:
            analyzer.enable_caching(10000)

        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.metrics = PerformanceMetrics()
        self.response_times = []

        # ロードバランサー
        self.current_analyzer = 0

    def get_next_analyzer(self) -> AsyncLineErrorAnalyzer:
        """ラウンドロビンで分析器を取得"""
        analyzer = self.analyzers[self.current_analyzer]
        self.current_analyzer = (self.current_analyzer + 1) % len(self.analyzers)
        return analyzer

    async def process_high_volume_errors(self, errors: List[dict]) -> List[dict]:
        """大量エラーの高速処理"""

        start_time = time.time()

        # エラーをバッチに分割
        batches = [
            errors[i:i + self.batch_size]
            for i in range(0, len(errors), self.batch_size)
        ]

        # 並行処理でバッチを処理
        tasks = []
        for batch in batches:
            analyzer = self.get_next_analyzer()
            task = asyncio.create_task(
                self.process_batch_with_metrics(analyzer, batch)
            )
            tasks.append(task)

        # 全バッチの完了を待機
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)

        # 結果をマージ
        all_results = []
        for result in batch_results:
            if isinstance(result, Exception):
                print(f"Batch processing error: {result}")
                continue
            all_results.extend(result)

        # メトリクス更新
        end_time = time.time()
        processing_time = end_time - start_time

        self.update_performance_metrics(len(errors), len(all_results), processing_time)

        return all_results

    async def process_batch_with_metrics(
        self,
        analyzer: AsyncLineErrorAnalyzer,
        batch: List[dict]
    ) -> List[dict]:
        """メトリクス付きバッチ処理"""

        batch_start = time.time()

        try:
            # バッチ分析実行
            results = await analyzer.analyze_batch(batch, batch_size=len(batch))

            # 結果を辞書形式に変換
            processed_results = []
            for error, result in zip(batch, results):
                processed_results.append({
                    "original_error": error,
                    "analysis": result.to_dict(),
                    "processing_time_ms": (time.time() - batch_start) * 1000,
                    "analyzer_id": id(analyzer)
                })

            return processed_results

        except Exception as e:
            print(f"Batch processing error: {e}")
            return []

    def update_performance_metrics(
        self,
        total_errors: int,
        successful_errors: int,
        processing_time: float
    ):
        """パフォーマンスメトリクスの更新"""

        self.metrics.total_requests += total_errors
        self.metrics.successful_requests += successful_errors
        self.metrics.failed_requests += (total_errors - successful_errors)

        # レスポンス時間の記録
        self.response_times.append(processing_time)
        if len(self.response_times) > 1000:  # 最新1000件のみ保持
            self.response_times.pop(0)

        # 平均レスポンス時間
        self.metrics.average_response_time = sum(self.response_times) / len(self.response_times)

        # ピークレスポンス時間
        self.metrics.peak_response_time = max(self.response_times)

        # 1秒あたりのリクエスト数
        if processing_time > 0:
            self.metrics.requests_per_second = total_errors / processing_time

    def get_performance_report(self) -> dict:
        """パフォーマンスレポートの生成"""

        success_rate = 0
        if self.metrics.total_requests > 0:
            success_rate = (self.metrics.successful_requests / self.metrics.total_requests) * 100

        # 分析器ごとの統計
        analyzer_stats = []
        for i, analyzer in enumerate(self.analyzers):
            stats = analyzer.get_analysis_stats()
            analyzer_stats.append({
                "analyzer_id": i,
                "total_analyzed": stats.get("total_analyzed", 0),
                "cache_hits": stats.get("cache_hits", 0),
                "cache_hit_rate": (
                    stats.get("cache_hits", 0) / stats.get("total_analyzed", 1) * 100
                )
            })

        return {
            "overall_metrics": {
                "total_requests": self.metrics.total_requests,
                "success_rate": round(success_rate, 2),
                "average_response_time_ms": round(self.metrics.average_response_time * 1000, 2),
                "peak_response_time_ms": round(self.metrics.peak_response_time * 1000, 2),
                "requests_per_second": round(self.metrics.requests_per_second, 2)
            },
            "analyzer_details": analyzer_stats,
            "configuration": {
                "max_workers": self.max_workers,
                "batch_size": self.batch_size,
                "active_analyzers": len(self.analyzers)
            }
        }

    async def adaptive_batch_sizing(self, errors: List[dict]) -> List[dict]:
        """適応的バッチサイズ調整"""

        # 小さなバッチでテスト実行
        test_batch_size = min(100, len(errors))
        test_batch = errors[:test_batch_size]

        start_time = time.time()
        test_results = await self.process_high_volume_errors(test_batch)
        test_time = time.time() - start_time

        # パフォーマンスに基づいてバッチサイズを調整
        if test_time > 0:
            optimal_batch_size = int(test_batch_size / test_time * 0.5)  # 0.5秒目標
            optimal_batch_size = max(50, min(2000, optimal_batch_size))  # 範囲制限

            print(f"Adaptive batch size: {optimal_batch_size} (based on test performance)")

            # バッチサイズを更新
            original_batch_size = self.batch_size
            self.batch_size = optimal_batch_size

            try:
                # 残りのエラーを処理
                remaining_errors = errors[test_batch_size:]
                remaining_results = await self.process_high_volume_errors(remaining_errors)

                # 結果をマージ
                all_results = test_results + remaining_results
                return all_results

            finally:
                # バッチサイズを復元
                self.batch_size = original_batch_size

        # フォールバック：通常処理
        return await self.process_high_volume_errors(errors[test_batch_size:])

# ベンチマークツール
class ErrorProcessingBenchmark:
    """エラー処理性能ベンチマーク"""

    def __init__(self):
        self.processor = HighPerformanceErrorProcessor(max_workers=8, batch_size=500)

    def generate_test_errors(self, count: int) -> List[dict]:
        """テスト用エラーデータの生成"""

        error_templates = [
            {"status_code": 401, "message": "Authentication failed"},
            {"status_code": 400, "message": "Bad request", "error_code": "40010"},
            {"status_code": 429, "message": "Rate limit exceeded", "error_code": "42901"},
            {"status_code": 500, "message": "Internal server error"},
            {"status_code": 403, "message": "Forbidden"},
        ]

        errors = []
        for i in range(count):
            template = error_templates[i % len(error_templates)]
            error = template.copy()
            error["request_id"] = f"req_{i}"
            error["timestamp"] = time.time()
            errors.append(error)

        return errors

    async def run_benchmark(self, error_counts: List[int]) -> dict:
        """ベンチマーク実行"""

        benchmark_results = {}

        for count in error_counts:
            print(f"\n🧪 Testing with {count:,} errors...")

            # テストデータ生成
            test_errors = self.generate_test_errors(count)

            # ベンチマーク実行
            start_time = time.time()
            results = await self.processor.process_high_volume_errors(test_errors)
            end_time = time.time()

            # 結果記録
            processing_time = end_time - start_time
            errors_per_second = count / processing_time if processing_time > 0 else 0

            benchmark_results[count] = {
                "processing_time_seconds": round(processing_time, 3),
                "errors_per_second": round(errors_per_second, 1),
                "success_rate": len(results) / count * 100,
                "average_latency_ms": round(processing_time / count * 1000, 3)
            }

            print(f"✅ Processed {len(results):,} errors in {processing_time:.3f}s")
            print(f"📊 {errors_per_second:.1f} errors/sec")

        return benchmark_results

# 使用例とベンチマーク実行
async def demonstrate_high_performance():
    """高性能処理の実演"""

    benchmark = ErrorProcessingBenchmark()

    # 段階的な負荷テスト
    test_sizes = [100, 1000, 5000, 10000, 50000]

    print("🚀 Starting performance benchmark...")
    results = await benchmark.run_benchmark(test_sizes)

    print("\n📊 Benchmark Results:")
    print("=" * 80)
    print(f"{'Errors':<10} {'Time(s)':<10} {'Errors/sec':<12} {'Success%':<10} {'Latency(ms)':<12}")
    print("=" * 80)

    for count, metrics in results.items():
        print(f"{count:<10,} {metrics['processing_time_seconds']:<10} "
              f"{metrics['errors_per_second']:<12} {metrics['success_rate']:<10.1f} "
              f"{metrics['average_latency_ms']:<12}")

    # パフォーマンスレポート
    performance_report = benchmark.processor.get_performance_report()
    print(f"\n📈 Performance Summary:")
    print(json.dumps(performance_report, indent=2))

# 実行
if __name__ == "__main__":
    asyncio.run(demonstrate_high_performance())
```

## まとめ

これらの高度な使用例では以下の実践的なパターンを示しました：

### 1. エンタープライズレベルの監視

- **マルチサービス対応**: 複数の LINE Bot サービスの一元管理
- **アラートシステム**: 閾値ベースの自動アラート
- **統計とダッシュボード**: リアルタイムな監視データ

### 2. 自動復旧システム

- **復旧戦略**: エラータイプ別の適応的な復旧
- **サーキットブレーカー**: 障害の連鎖を防ぐ保護機能
- **フォールバック**: バックアップシステムへの自動切り替え

### 3. パフォーマンス最適化

- **並行処理**: マルチワーカーによる高速化
- **適応的バッチサイズ**: パフォーマンスに基づく自動調整
- **詳細メトリクス**: 性能監視と最適化指標

これらのパターンを組み合わせることで、本格的なプロダクション環境で使用できる堅牢で高性能な LINE Bot システムを構築できます。

次のステップ:

- **[実際のプロジェクト例](real_world.md)** - 具体的な実装例
- **[トラブルシューティング](../errors/troubleshooting.md)** - 問題解決ガイド
- **[パフォーマンスチューニング](performance_tuning.md)** - さらなる最適化手法
