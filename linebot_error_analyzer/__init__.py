"""
LINE Bot Error Analyzer

LINE Bot SDK のエラーを自動分析・診断するライブラリ。
同期・非同期処理対応、LINE Bot SDK v2/v3 両対応。
"""

__version__ = "2.0.3"
__author__ = "らいとん"
__email__ = "raitosongwe@gmail.com"
__license__ = "MIT"

from .core import (
    LineErrorAnalyzer,
    AsyncLineErrorAnalyzer,
    LineErrorInfo,
    ErrorCategory,
    ErrorSeverity,
)
from .exceptions import AnalyzerError

__all__ = [
    "LineErrorAnalyzer",
    "AsyncLineErrorAnalyzer",
    "LineErrorInfo",
    "ErrorCategory",
    "ErrorSeverity",
    "AnalyzerError",
]
