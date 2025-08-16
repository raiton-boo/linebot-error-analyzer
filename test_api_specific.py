#!/usr/bin/env python3
"""APIパターン特有のエラー判定テスト"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from linebot_error_analyzer import LineErrorAnalyzer
from linebot_error_analyzer.models import ApiPattern


def test_user_profile_scenarios():
    """ユーザープロフィール取得の様々なシナリオをテスト"""

    analyzer = LineErrorAnalyzer()

    # シナリオ1: ユーザーブロック（実際のケース）
    blocked_log = """(404)
Reason: Not Found
HTTP response headers: HTTPHeaderDict({'server': 'legy', 'x-line-request-id': 'abc123'})
HTTP response body: {"message":"Not found"}"""

    print("🔍 シナリオ1: ユーザーブロック状態でのプロフィール取得")
    result1 = analyzer.analyze(blocked_log, ApiPattern.USER_PROFILE)
    print(f"✅ カテゴリ: {result1.category}")
    print(f"✅ 説明: {result1.description}")
    print(f"✅ 推奨対処: {result1.recommended_action}")

    # シナリオ2: 存在しないユーザー
    not_found_log = """(404)
Reason: User not found
HTTP response headers: HTTPHeaderDict({'server': 'legy', 'x-line-request-id': 'def456'})
HTTP response body: {"message":"User not found"}"""

    print(f"\n🔍 シナリオ2: 存在しないユーザーのプロフィール取得")
    result2 = analyzer.analyze(not_found_log, ApiPattern.USER_PROFILE)
    print(f"✅ カテゴリ: {result2.category}")
    print(f"✅ 説明: {result2.description}")

    # シナリオ3: メッセージ送信での404（ブロック）
    message_blocked_log = """(404)
Reason: Not Found
HTTP response headers: HTTPHeaderDict({'server': 'legy'})
HTTP response body: {"message":"Not found"}"""

    print(f"\n🔍 シナリオ3: メッセージ送信でのブロック状態")
    result3 = analyzer.analyze(message_blocked_log, ApiPattern.MESSAGE_PUSH)
    print(f"✅ カテゴリ: {result3.category}")
    print(f"✅ 説明: {result3.description}")

    # シナリオ4: 一般的な404（パターン指定なし）
    general_log = """(404)
Reason: Not Found
HTTP response body: {"message":"Not found"}"""

    print(f"\n🔍 シナリオ4: 一般的な404エラー（パターンなし）")
    result4 = analyzer.analyze(general_log)
    print(f"✅ カテゴリ: {result4.category}")
    print(f"✅ 説明: {result4.description}")


if __name__ == "__main__":
    test_user_profile_scenarios()
