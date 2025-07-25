#!/usr/bin/env python3
"""
ログ解析機能のデモスクリプト

新しく実装されたエラーログ文字列の解析とAPIパターンベースの分析機能をデモします。
"""

import json
from linebot_error_analyzer import LineErrorAnalyzer, AsyncLineErrorAnalyzer
import asyncio


def main():
    """メインデモ関数"""
    print("🤖 LINE Bot Error Analyzer - ログ解析機能デモ\n")
    
    # アナライザーの初期化
    analyzer = LineErrorAnalyzer()
    
    # Issue で提供されたログ例
    issue_log = """(404)
Reason: Not Found
HTTP response headers: HTTPHeaderDict({'server': 'legy', 'cache-control': 'no-cache, no-store, max-age=0, must-revalidate', 'content-type': 'application/json', 'date': 'Fri, 25 Jul 2025 18:23:24 GMT', 'expires': '0', 'pragma': 'no-cache', 'x-content-type-options': 'nosniff', 'x-frame-options': 'DENY', 'x-line-request-id': 'e40f3c8f-ab14-4042-9194-4c26ee828b80', 'x-xss-protection': '1; mode=block', 'content-length': '23'})
HTTP response body: {"message":"Not found"}"""

    print("📝 Issue サンプルログの解析結果")
    print("=" * 50)
    
    # 1. パターンなしでの解析
    print("\n1️⃣ パターンなしでの解析:")
    result_no_pattern = analyzer.analyze_log(issue_log)
    print(f"   カテゴリ: {result_no_pattern.category.value}")
    print(f"   重要度: {result_no_pattern.severity.value}")
    print(f"   推奨対処法: {result_no_pattern.recommended_action}")
    
    # 2. ユーザープロフィール取得パターンでの解析
    print("\n2️⃣ ユーザープロフィール取得パターンでの解析:")
    result_user_pattern = analyzer.analyze_log(issue_log, api_pattern="user.user_profile")
    print(f"   カテゴリ: {result_user_pattern.category.value}")
    print(f"   重要度: {result_user_pattern.severity.value}")
    print(f"   推奨対処法: {result_user_pattern.recommended_action}")
    print(f"   リクエストID: {result_user_pattern.request_id}")
    
    # 3. その他のログパターン例
    print("\n\n📋 その他のログ解析例")
    print("=" * 50)
    
    log_examples = [
        ("(401) Unauthorized", "認証エラー", None),
        ("(400) Invalid reply token", "返信トークンエラー", "message.message_reply"),
        ("(429) Too many requests", "レート制限エラー", None),
        ("(400) Rich menu image size invalid", "リッチメニューエラー", "rich_menu.rich_menu_create"),
    ]
    
    for i, (log, description, pattern) in enumerate(log_examples, 1):
        print(f"\n{i}️⃣ {description}:")
        print(f"   ログ: {log}")
        if pattern:
            print(f"   パターン: {pattern}")
            result = analyzer.analyze_log(log, api_pattern=pattern)
        else:
            result = analyzer.analyze_log(log)
        print(f"   カテゴリ: {result.category.value}")
        print(f"   重要度: {result.severity.value}")
        if result.is_retryable:
            print(f"   リトライ可能: はい ({result.retry_after}秒後)")
        else:
            print("   リトライ可能: いいえ")
    
    # 4. 文字列として直接analyze()メソッドを使用
    print("\n\n🎯 メインanalyze()メソッドでの文字列解析")
    print("=" * 50)
    
    simple_log = "(500) Internal Server Error"
    print(f"ログ: {simple_log}")
    result = analyzer.analyze(simple_log)  # analyze_log()ではなくanalyze()を使用
    print(f"カテゴリ: {result.category.value}")
    print(f"重要度: {result.severity.value}")
    print(f"リトライ可能: {'はい' if result.is_retryable else 'いいえ'}")


async def async_demo():
    """非同期デモ"""
    print("\n\n⚡ 非同期ログ解析デモ")
    print("=" * 50)
    
    async_analyzer = AsyncLineErrorAnalyzer()
    
    # 複数ログの並行解析
    log_batch = [
        "(404) Not Found",
        "(401) Unauthorized", 
        "(429) Rate limit exceeded",
        "(500) Internal Server Error"
    ]
    
    print("複数ログの並行解析:")
    results = await async_analyzer.analyze_multiple(log_batch)
    
    for i, result in enumerate(results, 1):
        print(f"{i}. {result.message} → {result.category.value}")


def detailed_analysis_demo():
    """詳細分析結果のデモ"""
    print("\n\n🔍 詳細分析結果のデモ")
    print("=" * 50)
    
    analyzer = LineErrorAnalyzer()
    
    # Issue のログ例で詳細分析
    issue_log = """(404)
Reason: Not Found
HTTP response headers: HTTPHeaderDict({'server': 'legy', 'cache-control': 'no-cache, no-store, max-age=0, must-revalidate', 'content-type': 'application/json', 'date': 'Fri, 25 Jul 2025 18:23:24 GMT', 'expires': '0', 'pragma': 'no-cache', 'x-content-type-options': 'nosniff', 'x-frame-options': 'DENY', 'x-line-request-id': 'e40f3c8f-ab14-4042-9194-4c26ee828b80', 'x-xss-protection': '1; mode=block', 'content-length': '23'})
HTTP response body: {"message":"Not found"}"""
    
    result = analyzer.analyze_log(issue_log, api_pattern="user.user_profile")
    
    print("📊 分析結果の詳細:")
    print(f"   ステータスコード: {result.status_code}")
    print(f"   メッセージ: {result.message}")
    print(f"   カテゴリ: {result.category.value}")
    print(f"   重要度: {result.severity.value}")
    print(f"   リトライ可能: {result.is_retryable}")
    print(f"   リクエストID: {result.request_id}")
    
    print("\n📝 JSON形式での出力:")
    result_json = result.to_json()
    parsed_json = json.loads(result_json)
    print(json.dumps(parsed_json, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        # 同期デモ
        main()
        
        # 詳細分析デモ
        detailed_analysis_demo()
        
        # 非同期デモ
        asyncio.run(async_demo())
        
        print("\n✅ デモ完了!")
        print("\n💡 新機能のポイント:")
        print("   • エラーログ文字列の直接解析が可能")
        print("   • APIパターン指定による文脈に応じた分析")
        print("   • 同じエラーでもパターンにより異なる解釈")
        print("   • 既存機能との完全な後方互換性")
        
    except Exception as e:
        print(f"❌ デモ実行エラー: {e}")
        import traceback
        traceback.print_exc()