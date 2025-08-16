#!/usr/bin/env python3
"""全テストを実行するランナースクリプト"""

import unittest
import sys
import os

# プロジェクトのルートをPATHに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def run_all_tests():
    """全テストを実行"""
    # テストディスカバリー
    loader = unittest.TestLoader()
    start_dir = os.path.dirname(os.path.abspath(__file__))
    suite = loader.discover(start_dir, pattern="test_*.py")

    # テスト実行
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 結果サマリー
    print(f"\n{'='*60}")
    print(f"テスト実行結果:")
    print(f"実行数: {result.testsRun}")
    print(f"失敗: {len(result.failures)}")
    print(f"エラー: {len(result.errors)}")
    print(f"スキップ: {len(result.skipped) if hasattr(result, 'skipped') else 0}")

    if result.failures:
        print(f"\n失敗したテスト:")
        for test, traceback in result.failures:
            print(f"  - {test}")

    if result.errors:
        print(f"\nエラーが発生したテスト:")
        for test, traceback in result.errors:
            print(f"  - {test}")

    print(f"{'='*60}")

    return result.wasSuccessful()


def run_specific_test(test_module):
    """特定のテストモジュールを実行"""
    suite = unittest.TestLoader().loadTestsFromName(test_module)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


def run_manual_tests():
    """manualフォルダのテストを実行"""
    manual_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "manual")

    if not os.path.exists(manual_dir):
        print("manual テストディレクトリが見つかりません")
        return

    print("Manual validation tests を実行中...")

    for filename in os.listdir(manual_dir):
        if filename.endswith(".py") and filename.startswith("test_"):
            filepath = os.path.join(manual_dir, filename)
            print(f"\n実行中: {filename}")
            try:
                exec(open(filepath).read())
            except Exception as e:
                print(f"エラー in {filename}: {e}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="テスト実行スクリプト")
    parser.add_argument("--module", "-m", help="特定のテストモジュールを実行")
    parser.add_argument("--manual", action="store_true", help="manual テストを実行")
    parser.add_argument(
        "--all", action="store_true", help="全てのテストを実行 (デフォルト)"
    )

    args = parser.parse_args()

    success = True

    if args.manual:
        run_manual_tests()
    elif args.module:
        success = run_specific_test(args.module)
    else:
        success = run_all_tests()

    sys.exit(0 if success else 1)
