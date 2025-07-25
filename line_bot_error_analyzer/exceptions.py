"""
LINE Bot エラー分析器 - 例外クラス

分析器で使用する例外クラスの定義。
"""


class AnalyzerError(Exception):
    """エラー分析時の例外"""

    def __init__(self, message: str, original_error: Exception = None):
        super().__init__(message)
        self.original_error = original_error

    def __str__(self) -> str:
        if self.original_error:
            return f"{super().__str__()} (Original: {self.original_error})"
        return super().__str__()


class UnsupportedErrorTypeError(AnalyzerError):
    """サポートされていないエラータイプ"""

    pass


class InvalidErrorDataError(AnalyzerError):
    """無効なエラーデータ"""

    pass
