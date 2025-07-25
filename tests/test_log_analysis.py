"""
ログパース機能のテストケース
"""

import unittest
from linebot_error_analyzer.utils.log_parser import LogParser, ParsedLogData
from linebot_error_analyzer import LineErrorAnalyzer, AsyncLineErrorAnalyzer, ErrorCategory, ErrorSeverity
import asyncio


class TestLogParser(unittest.TestCase):
    """LogParser のテストクラス"""

    def setUp(self):
        """テストセットアップ"""
        self.parser = LogParser()

    def test_parse_issue_example_log(self):
        """Issue で提供されたログ例の解析テスト"""
        log_string = """(404)
Reason: Not Found
HTTP response headers: HTTPHeaderDict({'server': 'legy', 'cache-control': 'no-cache, no-store, max-age=0, must-revalidate', 'content-type': 'application/json', 'date': 'Fri, 25 Jul 2025 18:23:24 GMT', 'expires': '0', 'pragma': 'no-cache', 'x-content-type-options': 'nosniff', 'x-frame-options': 'DENY', 'x-line-request-id': 'e40f3c8f-ab14-4042-9194-4c26ee828b80', 'x-xss-protection': '1; mode=block', 'content-length': '23'})
HTTP response body: {"message":"Not found"}"""

        parsed = self.parser.parse(log_string)

        self.assertEqual(parsed.status_code, 404)
        self.assertEqual(parsed.reason, "Not Found")
        self.assertEqual(parsed.message, "Not found")
        self.assertIn("x-line-request-id", parsed.headers)
        self.assertEqual(parsed.request_id, "e40f3c8f-ab14-4042-9194-4c26ee828b80")
        self.assertEqual(parsed.body["message"], "Not found")

    def test_parse_simple_status_code_log(self):
        """シンプルなステータスコードログの解析テスト"""
        log_string = "(401) Unauthorized - Authentication failed"
        
        parsed = self.parser.parse(log_string)
        
        self.assertEqual(parsed.status_code, 401)
        self.assertEqual(parsed.reason, "Unauthorized - Authentication failed")
        self.assertEqual(parsed.message, "Unauthorized - Authentication failed")

    def test_parse_json_body_log(self):
        """JSONボディを含むログの解析テスト"""
        log_string = """Status: 400
Body: {"error": "Invalid request", "details": "Missing required field"}"""
        
        parsed = self.parser.parse(log_string)
        
        self.assertEqual(parsed.status_code, 400)
        self.assertEqual(parsed.body["error"], "Invalid request")
        self.assertEqual(parsed.message, "Invalid request")

    def test_parse_headers_only_log(self):
        """ヘッダーのみのログ解析テスト"""
        log_string = """(429)
Headers: {'retry-after': '60', 'x-line-request-id': 'test-123'}"""
        
        parsed = self.parser.parse(log_string)
        
        self.assertEqual(parsed.status_code, 429)
        self.assertEqual(parsed.headers["retry-after"], "60")
        self.assertEqual(parsed.request_id, "test-123")

    def test_is_parseable_valid_logs(self):
        """有効なログの解析可能性判定テスト"""
        valid_logs = [
            "(404) Not Found",
            "Status: 500",
            "Error: Authentication failed",
            "HTTP 401 Unauthorized",
        ]
        
        for log in valid_logs:
            with self.subTest(log=log):
                self.assertTrue(self.parser.is_parseable(log))

    def test_is_parseable_invalid_logs(self):
        """無効なログの解析可能性判定テスト"""
        invalid_logs = [
            "",
            None,
            "Just a regular message",
            123,
        ]
        
        for log in invalid_logs:
            with self.subTest(log=log):
                self.assertFalse(self.parser.is_parseable(log))


class TestLogAnalyzer(unittest.TestCase):
    """ログ解析機能のテストクラス"""

    def setUp(self):
        """テストセットアップ"""
        self.analyzer = LineErrorAnalyzer()

    def test_analyze_log_string_basic(self):
        """基本的なログ文字列解析テスト"""
        log_string = "(404) Not Found"
        
        result = self.analyzer.analyze_log(log_string)
        
        self.assertEqual(result.status_code, 404)
        self.assertEqual(result.category, ErrorCategory.RESOURCE_NOT_FOUND)
        self.assertEqual(result.severity, ErrorSeverity.MEDIUM)
        self.assertFalse(result.is_retryable)

    def test_analyze_log_with_user_pattern(self):
        """ユーザーパターン指定によるログ解析テスト"""
        log_string = "(404) Not found"
        
        result = self.analyzer.analyze_log(log_string, api_pattern="user.user_profile")
        
        self.assertEqual(result.status_code, 404)
        self.assertEqual(result.category, ErrorCategory.USER_BLOCKED)
        self.assertEqual(result.severity, ErrorSeverity.MEDIUM)
        self.assertFalse(result.is_retryable)

    def test_analyze_log_with_message_pattern(self):
        """メッセージパターン指定によるログ解析テスト"""
        log_string = "(400) Invalid reply token"
        
        result = self.analyzer.analyze_log(log_string, api_pattern="message.message_reply")
        
        self.assertEqual(result.status_code, 400)
        self.assertEqual(result.category, ErrorCategory.INVALID_REPLY_TOKEN)
        self.assertEqual(result.severity, ErrorSeverity.HIGH)
        self.assertFalse(result.is_retryable)

    def test_analyze_log_with_rich_menu_pattern(self):
        """リッチメニューパターン指定によるログ解析テスト"""
        log_string = "(400) Invalid image size"
        
        result = self.analyzer.analyze_log(log_string, api_pattern="rich_menu.rich_menu_create")
        
        self.assertEqual(result.status_code, 400)
        self.assertEqual(result.category, ErrorCategory.RICH_MENU_SIZE_ERROR)
        self.assertEqual(result.severity, ErrorSeverity.MEDIUM)
        self.assertFalse(result.is_retryable)

    def test_analyze_log_issue_example(self):
        """Issue例によるログ解析テスト"""
        log_string = """(404)
Reason: Not Found
HTTP response headers: HTTPHeaderDict({'server': 'legy', 'cache-control': 'no-cache, no-store, max-age=0, must-revalidate', 'content-type': 'application/json', 'date': 'Fri, 25 Jul 2025 18:23:24 GMT', 'expires': '0', 'pragma': 'no-cache', 'x-content-type-options': 'nosniff', 'x-frame-options': 'DENY', 'x-line-request-id': 'e40f3c8f-ab14-4042-9194-4c26ee828b80', 'x-xss-protection': '1; mode=block', 'content-length': '23'})
HTTP response body: {"message":"Not found"}"""
        
        # パターンなしの場合
        result_no_pattern = self.analyzer.analyze_log(log_string)
        self.assertEqual(result_no_pattern.category, ErrorCategory.RESOURCE_NOT_FOUND)
        
        # ユーザープロフィール取得パターンの場合
        result_user_pattern = self.analyzer.analyze_log(log_string, api_pattern="user.user_profile")
        self.assertEqual(result_user_pattern.category, ErrorCategory.USER_BLOCKED)
        self.assertEqual(result_user_pattern.request_id, "e40f3c8f-ab14-4042-9194-4c26ee828b80")

    def test_analyze_string_through_main_analyze(self):
        """メインのanalyzeメソッドでの文字列解析テスト"""
        log_string = "(401) Unauthorized"
        
        result = self.analyzer.analyze(log_string)
        
        self.assertEqual(result.status_code, 401)
        self.assertEqual(result.category, ErrorCategory.AUTH_ERROR)
        self.assertEqual(result.severity, ErrorSeverity.CRITICAL)


class TestAsyncLogAnalyzer(unittest.TestCase):
    """非同期ログ解析機能のテストクラス"""

    def setUp(self):
        """テストセットアップ"""
        self.analyzer = AsyncLineErrorAnalyzer()

    def test_async_analyze_log_string(self):
        """非同期ログ文字列解析テスト"""
        async def run_test():
            log_string = "(404) Not Found"
            
            result = await self.analyzer.analyze_log(log_string)
            
            self.assertEqual(result.status_code, 404)
            self.assertEqual(result.category, ErrorCategory.RESOURCE_NOT_FOUND)
            self.assertEqual(result.severity, ErrorSeverity.MEDIUM)
            self.assertFalse(result.is_retryable)

        asyncio.run(run_test())

    def test_async_analyze_log_with_pattern(self):
        """非同期パターン指定ログ解析テスト"""
        async def run_test():
            log_string = "(400) Invalid reply token expired"
            
            result = await self.analyzer.analyze_log(
                log_string, 
                api_pattern="message.message_reply"
            )
            
            self.assertEqual(result.status_code, 400)
            self.assertEqual(result.category, ErrorCategory.REPLY_TOKEN_EXPIRED)
            self.assertEqual(result.severity, ErrorSeverity.HIGH)

        asyncio.run(run_test())

    def test_async_analyze_string_through_main_analyze(self):
        """非同期メインanalyzeメソッドでの文字列解析テスト"""
        async def run_test():
            log_string = "(429) Too many requests"
            
            result = await self.analyzer.analyze(log_string)
            
            self.assertEqual(result.status_code, 429)
            self.assertEqual(result.category, ErrorCategory.RATE_LIMIT)
            self.assertEqual(result.severity, ErrorSeverity.MEDIUM)
            self.assertTrue(result.is_retryable)

        asyncio.run(run_test())

    def test_async_batch_log_analysis(self):
        """非同期バッチログ解析テスト"""
        async def run_test():
            log_strings = [
                "(404) Not Found",
                "(401) Unauthorized", 
                "(429) Rate limit exceeded"
            ]
            
            results = await self.analyzer.analyze_multiple(log_strings)
            
            self.assertEqual(len(results), 3)
            self.assertEqual(results[0].status_code, 404)
            self.assertEqual(results[1].status_code, 401)
            self.assertEqual(results[2].status_code, 429)

        asyncio.run(run_test())


class TestLogAnalysisPatterns(unittest.TestCase):
    """ログ解析パターンマッチングのテストクラス"""

    def setUp(self):
        """テストセットアップ"""
        self.analyzer = LineErrorAnalyzer()

    def test_user_pattern_analysis(self):
        """ユーザーパターン解析のテストケース"""
        test_cases = [
            # (log_string, api_pattern, expected_category)
            ("(404) User not found", "user.user_profile", ErrorCategory.USER_BLOCKED),
            ("(404) Profile not accessible", "user.user_profile", ErrorCategory.PROFILE_NOT_ACCESSIBLE),
            ("(403) Profile access denied", "user.user_profile", ErrorCategory.PROFILE_NOT_ACCESSIBLE),
            ("(403) Access forbidden", "user.user_followers", ErrorCategory.FORBIDDEN),
        ]
        
        for log_string, api_pattern, expected_category in test_cases:
            with self.subTest(log=log_string, pattern=api_pattern):
                result = self.analyzer.analyze_log(log_string, api_pattern)
                self.assertEqual(result.category, expected_category)

    def test_message_pattern_analysis(self):
        """メッセージパターン解析のテストケース"""
        test_cases = [
            ("(400) Invalid reply token", "message.message_reply", ErrorCategory.INVALID_REPLY_TOKEN),
            ("(400) Reply token expired", "message.message_reply", ErrorCategory.REPLY_TOKEN_EXPIRED),
            ("(400) Reply token already used", "message.message_reply", ErrorCategory.REPLY_TOKEN_USED),
            ("(400) Payload too large", "message.message_push", ErrorCategory.PAYLOAD_TOO_LARGE),
        ]
        
        for log_string, api_pattern, expected_category in test_cases:
            with self.subTest(log=log_string, pattern=api_pattern):
                result = self.analyzer.analyze_log(log_string, api_pattern)
                self.assertEqual(result.category, expected_category)

    def test_rich_menu_pattern_analysis(self):
        """リッチメニューパターン解析のテストケース"""
        test_cases = [
            ("(400) Invalid image size", "rich_menu.rich_menu_create", ErrorCategory.RICH_MENU_SIZE_ERROR),
            ("(400) Rich menu dimension error", "rich_menu.rich_menu_image", ErrorCategory.RICH_MENU_SIZE_ERROR),
            ("(400) Rich menu validation failed", "rich_menu.rich_menu_create", ErrorCategory.RICH_MENU_ERROR),
        ]
        
        for log_string, api_pattern, expected_category in test_cases:
            with self.subTest(log=log_string, pattern=api_pattern):
                result = self.analyzer.analyze_log(log_string, api_pattern)
                self.assertEqual(result.category, expected_category)

    def test_pattern_specificity(self):
        """パターン固有性のテスト（同じエラーでもパターンで結果が変わる）"""
        log_string = "(404) Not found"
        
        # パターンなし
        result_no_pattern = self.analyzer.analyze_log(log_string)
        self.assertEqual(result_no_pattern.category, ErrorCategory.RESOURCE_NOT_FOUND)
        
        # ユーザーパターン
        result_user_pattern = self.analyzer.analyze_log(log_string, "user.user_profile")
        self.assertEqual(result_user_pattern.category, ErrorCategory.USER_BLOCKED)
        
        # その他のパターン（特別な処理なし）
        result_other_pattern = self.analyzer.analyze_log(log_string, "webhook.webhook_settings")
        self.assertEqual(result_other_pattern.category, ErrorCategory.RESOURCE_NOT_FOUND)


if __name__ == "__main__":
    unittest.main()