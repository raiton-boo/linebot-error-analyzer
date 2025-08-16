#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Simple Usage Example

LINE Bot Error Analyzerの基本的な使い方を示すシンプルな例です。
コピペしてすぐに使えます。

Requirements:
    pip install linebot-error-analyzer
"""

from linebot_error_analyzer import LineErrorAnalyzer


def main():
    """基本的な使用例"""
    # アナライザーを初期化
    analyzer = LineErrorAnalyzer()

    # よくあるLINE Botのエラーログ（以下のログメッセージかなり省略してます）
    error_logs = [
        "(401) Invalid channel access token",
        "(429) Rate limit exceeded",
        "(400) Bad Request",
        "(500) Internal Server Error",
    ]

    print("=== LINE Bot Error Analyzer - 基本的な使い方 ===\n")

    for log in error_logs:
        # エラーログを解析
        result = analyzer.analyze(log)

        # 結果を表示
        print(f"エラー: {log}")
        print(f"  説明: {result.description}")
        print(f"  対処法: {result.recommended_action}")
        print(f"  再試行可能: {'はい' if result.is_retryable else 'いいえ'}")
        print()


if __name__ == "__main__":
    main()
