#!/usr/bin/env python3
"""設定・モジュール構造のテストケース"""

import unittest
import sys
import os

# プロジェクトのルートをPATHに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestModuleStructure(unittest.TestCase):
    """モジュール構造・インポートのテスト"""

    def test_main_imports(self):
        """メインモジュールのインポートテスト"""
        try:
            from linebot_error_analyzer import LineErrorAnalyzer
            from linebot_error_analyzer import AsyncLineErrorAnalyzer

            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Main imports failed: {e}")

    def test_models_imports(self):
        """モデルクラスのインポートテスト"""
        try:
            from linebot_error_analyzer.models import (
                ErrorResult,
                ApiPattern,
                ErrorCategory,
            )

            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Models imports failed: {e}")

    def test_log_parser_import(self):
        """LogParserのインポートテスト"""
        try:
            from linebot_error_analyzer.models.log_parser import LogParser

            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"LogParser import failed: {e}")

    def test_exception_imports(self):
        """例外クラスのインポートテスト"""
        try:
            from linebot_error_analyzer.exceptions import AnalyzerError

            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Exception imports failed: {e}")

    def test_enum_completeness(self):
        """列挙型の完全性テスト"""
        from linebot_error_analyzer.models import ApiPattern, ErrorCategory

        # ApiPatternに必要な要素があることを確認
        required_patterns = [
            "MESSAGE_PUSH",
            "MESSAGE_REPLY",
            "USER_PROFILE",
            "RICH_MENU_CREATE",
            "WEBHOOK_SETTINGS",
        ]

        for pattern_name in required_patterns:
            self.assertTrue(
                hasattr(ApiPattern, pattern_name), f"Missing ApiPattern: {pattern_name}"
            )

        # ErrorCategoryに必要な要素があることを確認
        required_categories = [
            "CLIENT_ERROR",
            "SERVER_ERROR",
            "AUTHENTICATION_ERROR",
            "RATE_LIMIT_ERROR",
            "USER_BLOCKED",
        ]

        for category_name in required_categories:
            self.assertTrue(
                hasattr(ErrorCategory, category_name),
                f"Missing ErrorCategory: {category_name}",
            )

    def test_version_availability(self):
        """バージョン情報の取得テスト"""
        try:
            import linebot_error_analyzer

            # __version__ 属性があることを確認
            if hasattr(linebot_error_analyzer, "__version__"):
                version = linebot_error_analyzer.__version__
                self.assertIsInstance(version, str)
                self.assertTrue(len(version) > 0)
        except Exception:
            # バージョン情報がない場合も許容
            pass

    def test_package_structure(self):
        """パッケージ構造の確認"""
        import linebot_error_analyzer

        # パッケージパスの確認
        package_path = linebot_error_analyzer.__file__
        self.assertTrue(package_path.endswith("__init__.py"))

        # 必要なサブモジュールの存在確認
        expected_modules = [
            "linebot_error_analyzer.models",
            "linebot_error_analyzer.core",
            "linebot_error_analyzer.database",
        ]

        for module_name in expected_modules:
            try:
                __import__(module_name)
            except ImportError as e:
                self.fail(f"Missing module: {module_name} - {e}")


class TestConfiguration(unittest.TestCase):
    """設定・環境のテスト"""

    def test_python_version_compatibility(self):
        """Python バージョン互換性テスト"""
        import sys

        # Python 3.7+ を要求
        self.assertGreaterEqual(sys.version_info.major, 3)
        self.assertGreaterEqual(sys.version_info.minor, 7)

    def test_required_dependencies(self):
        """必要な依存関係のテスト"""
        required_modules = [
            "asyncio",  # 非同期処理用
            "re",  # 正規表現用
            "json",  # JSON処理用
            "enum",  # 列挙型用
        ]

        for module in required_modules:
            try:
                __import__(module)
            except ImportError as e:
                self.fail(f"Missing required module: {module} - {e}")

    def test_analyzer_initialization(self):
        """アナライザーの初期化テスト"""
        from linebot_error_analyzer import LineErrorAnalyzer, AsyncLineErrorAnalyzer

        # 同期版アナライザー
        sync_analyzer = LineErrorAnalyzer()
        self.assertIsInstance(sync_analyzer, LineErrorAnalyzer)

        # 非同期版アナライザー
        async_analyzer = AsyncLineErrorAnalyzer()
        self.assertIsInstance(async_analyzer, AsyncLineErrorAnalyzer)

    def test_analyzer_default_behavior(self):
        """アナライザーのデフォルト動作テスト"""
        from linebot_error_analyzer import LineErrorAnalyzer

        analyzer = LineErrorAnalyzer()

        # 基本的なエラー解析
        result = analyzer.analyze(404, "Not Found")

        # 必須フィールドの存在確認
        self.assertTrue(hasattr(result, "status_code"))
        self.assertTrue(hasattr(result, "category"))
        self.assertTrue(hasattr(result, "description"))
        self.assertTrue(hasattr(result, "recommended_action"))
        self.assertTrue(hasattr(result, "is_retryable"))


if __name__ == "__main__":
    unittest.main()
