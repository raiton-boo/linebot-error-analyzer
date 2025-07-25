"""
LINE Bot エラー分析器 - 同期版

LINE Messaging API のエラーを自動分析・分類するメインクラス。
LINE Bot SDK v2/v3 例外、辞書形式エラー、HTTPレスポンス等に対応。
"""

from __future__ import annotations
import json
from typing import Any, Dict, List, Optional, Union, TYPE_CHECKING
from .base_analyzer import BaseLineErrorAnalyzer
from .models import LineErrorInfo, ErrorCategory, ErrorSeverity
from ..exceptions import AnalyzerError, UnsupportedErrorTypeError, InvalidErrorDataError

if TYPE_CHECKING:
    from ..utils.types import SupportedErrorType


class LineErrorAnalyzer(BaseLineErrorAnalyzer):
    """
    LINE Bot エラー分析器（同期版）

    LINE Messaging API のエラーを自動分析し、詳細な診断情報を提供。
    SDK例外、辞書形式エラー、HTTPレスポンス等に対応し、
    エラーの分類・重要度判定・対処法提案を行う。
    """

    def analyze(self, error: "SupportedErrorType") -> LineErrorInfo:
        """
        エラーを分析してLineErrorInfoを返す

        Args:
            error: 分析対象のエラー（SDK例外、辞書、HTTPレスポンス等）

        Returns:
            LineErrorInfo: エラーの詳細分析結果

        Raises:
            UnsupportedErrorTypeError: サポートされていないエラー形式
            AnalyzerError: 分析処理中のエラー
        """
        try:
            # エラータイプ別分析（優先度順）
            if self._is_v3_sig(error):
                return self._analyze_v3_sig(error)
            elif self._is_v2_sig(error):
                return self._analyze_v2_sig(error)
            elif self._is_v3(error):
                return self._analyze_v3(error)
            elif self._is_v2(error):
                return self._analyze_v2(error)
            elif isinstance(error, dict):
                return self._analyze_dict(error)
            elif hasattr(error, "status_code") and hasattr(error, "text"):
                return self._analyze_response(error)
            else:
                raise UnsupportedErrorTypeError(
                    f"Unsupported error type: {type(error)}. "
                    f"Supported types: SDK exceptions, dict, HTTP response objects"
                )

        except UnsupportedErrorTypeError:
            # サポート対象外エラーは再発生させて上位に委ねる
            raise
        except Exception as e:
            # 予期しないエラーはAnalyzerErrorでラップして詳細情報を付加
            raise AnalyzerError(
                f"Failed to analyze error: {str(e)}. Error type: {type(error)}", e
            )

    def analyze_multiple(
        self, errors: List["SupportedErrorType"]
    ) -> List[LineErrorInfo]:
        """
        複数エラーの一括分析

        エラーリストを順次分析し、結果をリストで返す。
        個別エラーの分析失敗時も処理を継続（graceful degradation）。

        Args:
            errors: 分析対象のエラーリスト

        Returns:
            List[LineErrorInfo]: 各エラーの分析結果（入力と同サイズ）
        """
        results = []
        for error in errors:
            try:
                result = self.analyze(error)
                results.append(result)
            except Exception as e:
                # 個別分析失敗時のフォールバック処理
                error_info = self._create_info(
                    status_code=0,
                    message=f"Analysis failed: {str(e)}",
                    headers={},
                    error_data={},
                    category=ErrorCategory.UNKNOWN,
                    severity=ErrorSeverity.MEDIUM,
                    is_retryable=False,
                    raw_error={
                        "original_error": str(error),
                        "analysis_error": str(e),
                        "error_type": type(error).__name__,
                    },
                )
                results.append(error_info)
        return results

    # SDK バージョン別分析メソッド

    def _analyze_v3(self, error: Any) -> LineErrorInfo:
        """
        LINE Bot SDK v3 ApiException の分析

        v3 SDK例外からステータスコード、ヘッダー、エラーボディを抽出し、
        構造化されたエラー情報を生成する。

        Args:
            error: LINE Bot SDK v3 ApiException オブジェクト

        Returns:
            LineErrorInfo: v3 API例外の分析結果

        Raises:
            AnalyzerError: 分析処理中のエラー
        """
        try:
            # ステータスコード取得
            status_code = (
                getattr(error, "status", None)
                or getattr(error, "status_code", None)
                or 0
            )

            # テスト環境のMockオブジェクト対応
            if hasattr(status_code, "_mock_name"):
                status_code = 0

            # レスポンスヘッダー取得
            headers = {}
            if hasattr(error, "headers") and error.headers:
                try:
                    if hasattr(error.headers, "items"):
                        headers = dict(error.headers.items())
                    elif hasattr(error.headers, "__iter__"):
                        headers = dict(error.headers)
                except (TypeError, AttributeError, ValueError):
                    headers = {}

            # レスポンスボディからエラー情報抽出
            error_data = {}
            if hasattr(error, "body") and error.body:
                try:
                    if isinstance(error.body, (str, bytes)):
                        error_data = json.loads(error.body)
                    else:
                        error_data = error.body
                except (json.JSONDecodeError, TypeError):
                    error_data = {"message": str(error.body)}

            # エラーメッセージ決定
            message = error_data.get(
                "message", getattr(error, "reason", "Unknown error")
            )

            # 構造化エラー情報生成
            return self._create_info(
                status_code=status_code,
                message=message,
                headers=headers,
                error_data=error_data,
                request_id=headers.get("x-line-request-id")
                or headers.get("X-Line-Request-Id"),
                error_code=error_data.get("error_code"),
                raw_error=error_data,
            )

        except Exception as e:
            raise AnalyzerError(
                f"Failed to analyze v3 ApiException: {str(e)}. "
                f"Error attributes: {[attr for attr in dir(error) if not attr.startswith('_')]}",
                e,
            )

    def _analyze_v2(self, error: Any) -> LineErrorInfo:
        """
        LINE Bot SDK v2 LineBotApiError の分析

        v2 SDK例外からステータスコード、リクエストID、エラー詳細を抽出し、
        構造化されたエラー情報を生成する。

        Args:
            error: LINE Bot SDK v2 LineBotApiError オブジェクト

        Returns:
            LineErrorInfo: v2 API例外の分析結果

        Raises:
            AnalyzerError: 分析処理中のエラー
        """
        try:
            status_code = error.status_code
            headers = self._safe_dict_conversion(error.headers or {})
            request_id = error.request_id
            accepted_request_id = error.accepted_request_id

            # error.error オブジェクトから情報を抽出
            error_obj = error.error
            message = error_obj.message if error_obj else "Unknown error"
            details = (
                error_obj.details if error_obj and hasattr(error_obj, "details") else []
            )

            return self._create_info(
                status_code=status_code,
                message=message,
                headers=headers,
                error_data={"details": details},
                request_id=request_id,
                raw_error={
                    "status_code": status_code,
                    "request_id": request_id,
                    "accepted_request_id": accepted_request_id,
                    "error": {"message": message, "details": details},
                },
            )

        except Exception as e:
            raise AnalyzerError(f"Failed to analyze v2 LineBotApiError: {str(e)}", e)
