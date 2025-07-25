#!/usr/bin/env python3
"""
LINE Bot Error Analyzer - ログ解析機能の実践例

実際の運用環境でのログ解析活用例を示します。
"""

from linebot_error_analyzer import LineErrorAnalyzer, AsyncLineErrorAnalyzer
import asyncio
from datetime import datetime
import json


def basic_log_analysis_example():
    """基本的なログ解析の例"""
    print("=== 基本的なログ解析の例 ===")
    
    analyzer = LineErrorAnalyzer()
    
    # 実際のログ例（Issue から）
    real_log = """(404)
Reason: Not Found
HTTP response headers: HTTPHeaderDict({'server': 'legy', 'cache-control': 'no-cache, no-store, max-age=0, must-revalidate', 'content-type': 'application/json', 'date': 'Fri, 25 Jul 2025 18:23:24 GMT', 'expires': '0', 'pragma': 'no-cache', 'x-content-type-options': 'nosniff', 'x-frame-options': 'DENY', 'x-line-request-id': 'e40f3c8f-ab14-4042-9194-4c26ee828b80', 'x-xss-protection': '1; mode=block', 'content-length': '23'})
HTTP response body: {"message":"Not found"}"""

    result = analyzer.analyze_log(real_log, api_pattern="user.user_profile")
    
    print(f"ステータス: {result.status_code}")
    print(f"カテゴリ: {result.category.value}")
    print(f"重要度: {result.severity.value}")
    print(f"対処法: {result.recommended_action}")
    print(f"リクエストID: {result.request_id}")


def pattern_based_analysis_example():
    """パターンベース解析の例"""
    print("\n=== パターンベース解析の例 ===")
    
    analyzer = LineErrorAnalyzer()
    
    # 同じエラーコードでも異なるパターンで解析
    log = "(404) Not found"
    
    patterns = [
        (None, "パターンなし"),
        ("user.user_profile", "ユーザープロフィール"),
        ("message.message_push", "メッセージ送信"),
        ("rich_menu.rich_menu_create", "リッチメニュー作成")
    ]
    
    for pattern, description in patterns:
        result = analyzer.analyze_log(log, api_pattern=pattern)
        print(f"{description}: {result.category.value}")


def monitoring_system_example():
    """ログ監視システムでの活用例"""
    print("\n=== ログ監視システムでの活用例 ===")
    
    analyzer = LineErrorAnalyzer()
    
    # 模擬ログエントリ
    log_entries = [
        {"timestamp": "2025-01-25 10:15:30", "endpoint": "user.user_profile", 
         "log": "(403) Profile access forbidden"},
        {"timestamp": "2025-01-25 10:16:45", "endpoint": "message.message_reply", 
         "log": "(400) Invalid reply token expired"},
        {"timestamp": "2025-01-25 10:17:12", "endpoint": "rich_menu.rich_menu_create", 
         "log": "(400) Image size too large"},
        {"timestamp": "2025-01-25 10:18:33", "endpoint": None, 
         "log": "(429) Rate limit exceeded"}
    ]
    
    alerts = []
    
    for entry in log_entries:
        result = analyzer.analyze_log(entry["log"], api_pattern=entry["endpoint"])
        
        # 重要度が高い場合はアラート
        if result.severity.value in ['CRITICAL', 'HIGH']:
            alerts.append({
                "timestamp": entry["timestamp"],
                "category": result.category.value,
                "severity": result.severity.value,
                "message": result.message,
                "action": result.recommended_action,
                "endpoint": entry["endpoint"]
            })
    
    print(f"検出されたアラート: {len(alerts)}件")
    for alert in alerts:
        print(f"- {alert['timestamp']}: {alert['category']} ({alert['severity']})")


async def async_batch_processing_example():
    """非同期バッチ処理の例"""
    print("\n=== 非同期バッチ処理の例 ===")
    
    analyzer = AsyncLineErrorAnalyzer()
    
    # 大量ログの模擬データ
    logs = [
        "(404) User not found",
        "(401) Invalid access token",
        "(429) Rate limit exceeded",
        "(500) Internal server error",
        "(400) Invalid reply token",
        "(403) Access denied",
        "(400) Rich menu size invalid"
    ]
    
    # 並行処理で高速解析
    start_time = datetime.now()
    results = await analyzer.analyze_multiple(logs)
    end_time = datetime.now()
    
    # 結果の集計
    category_count = {}
    severity_count = {}
    
    for result in results:
        category = result.category.value
        severity = result.severity.value
        
        category_count[category] = category_count.get(category, 0) + 1
        severity_count[severity] = severity_count.get(severity, 0) + 1
    
    print(f"処理時間: {(end_time - start_time).total_seconds():.3f}秒")
    print(f"処理件数: {len(results)}件")
    print("カテゴリ別集計:")
    for category, count in category_count.items():
        print(f"  {category}: {count}件")
    print("重要度別集計:")
    for severity, count in severity_count.items():
        print(f"  {severity}: {count}件")


def error_reporting_example():
    """エラーレポート生成の例"""
    print("\n=== エラーレポート生成の例 ===")
    
    analyzer = LineErrorAnalyzer()
    
    # エラーログとメタデータ
    error_log = """(400)
Reason: Bad Request
HTTP response headers: HTTPHeaderDict({'x-line-request-id': 'req-12345-67890'})
HTTP response body: {"message": "Invalid reply token", "details": "Token has expired"}"""
    
    result = analyzer.analyze_log(error_log, api_pattern="message.message_reply")
    
    # 詳細レポートの生成
    report = {
        "error_id": f"ERR-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        "timestamp": datetime.now().isoformat(),
        "analysis": {
            "status_code": result.status_code,
            "category": result.category.value,
            "severity": result.severity.value,
            "message": result.message,
            "is_retryable": result.is_retryable,
            "request_id": result.request_id
        },
        "guidance": {
            "description": result.description,
            "recommended_action": result.recommended_action,
            "documentation_url": result.documentation_url
        },
        "raw_data": {
            "original_log": error_log,
            "api_pattern": "message.message_reply"
        }
    }
    
    print("生成されたエラーレポート:")
    print(json.dumps(report, ensure_ascii=False, indent=2))


def integration_example():
    """他システムとの連携例"""
    print("\n=== 他システムとの連携例 ===")
    
    analyzer = LineErrorAnalyzer()
    
    def process_webhook_error(webhook_payload):
        """Webhookエラーの処理例"""
        error_log = webhook_payload.get("error_log")
        endpoint = webhook_payload.get("endpoint")
        
        if not error_log:
            return {"status": "no_error_log"}
        
        try:
            result = analyzer.analyze_log(error_log, api_pattern=endpoint)
            
            return {
                "status": "analyzed",
                "category": result.category.value,
                "severity": result.severity.value,
                "retryable": result.is_retryable,
                "action": result.recommended_action,
                "request_id": result.request_id
            }
        except Exception as e:
            return {
                "status": "analysis_failed",
                "error": str(e)
            }
    
    # 模擬Webhookペイロード
    webhook_data = {
        "timestamp": "2025-01-25T10:30:00Z",
        "endpoint": "user.user_profile",
        "error_log": "(404) User profile not accessible"
    }
    
    response = process_webhook_error(webhook_data)
    print(f"Webhook処理結果: {response}")


def main():
    """メイン実行関数"""
    print("LINE Bot Error Analyzer - ログ解析機能実践例\n")
    
    # 基本例
    basic_log_analysis_example()
    
    # パターン解析例
    pattern_based_analysis_example()
    
    # 監視システム例
    monitoring_system_example()
    
    # エラーレポート例
    error_reporting_example()
    
    # システム連携例
    integration_example()
    
    # 非同期例
    asyncio.run(async_batch_processing_example())
    
    print("\n✅ 全ての例が完了しました!")


if __name__ == "__main__":
    main()