#!/usr/bin/env python3
"""シンプルなテスト"""

import sys
import os

# プロジェクトのルートをPATHに追加
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

print("Testing real error log...")

real_error_log = """(404)
Reason: Not Found
HTTP response headers: HTTPHeaderDict({'server': 'legy', 'x-line-request-id': 'e40f3c8f-ab14-4042-9194-4c26ee828b80'})
HTTP response body: {"message":"Not found"}"""

try:
    from linebot_error_analyzer import LineErrorAnalyzer
    from linebot_error_analyzer.models import ApiPattern

    print("✅ Analyzer imported")

    analyzer = LineErrorAnalyzer()
    print("✅ Analyzer created")

    result = analyzer.analyze(real_error_log, api_pattern=ApiPattern.USER_PROFILE)
    print("✅ Analysis completed")

    print(result.status_code)

    print(f"Category: {result.category}")
    print(f"Retryable: {result.is_retryable}")
    print(f"Description: {result.description}")
    print(f"Request ID: {result.request_id}")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback

    traceback.print_exc()

print("Test completed!")
