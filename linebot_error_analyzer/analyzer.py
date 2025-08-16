"""
LINE Bot エラー分析器 - 同期版

LINE Messaging API のエラーを自動分析・分類するメインクラス。
LINE Bot SDK v2/v3 例外、辞書形式エラー、HTTPレスポンス等に対応。
"""

from __future__ import annotations
import json
from typing import Any, Dict, List, Optional, Union, TYPE_CHECKING, overload
from .core.base_analyzer import BaseLineErrorAnalyzer
from .models import LineErrorInfo, ErrorCategory, ApiPattern
from .models.log_parser import LogParser
from .exceptions import AnalyzerError, UnsupportedErrorTypeError, InvalidErrorDataError

if TYPE_CHECKING:
    from .utils.types import SupportedErrorType


class LineErrorAnalyzer(BaseLineErrorAnalyzer):
    """
    LINE Bot エラー分析器（同期版）

    LINE Messaging API のエラーを自動分析し、詳細な診断情報を提供。
    SDK例外、辞書形式エラー、HTTPレスポンス等に対応し、
    エラーの分類・重要度判定・対処法提案を行う。

    Issue #1対応: エラーログ文字列の解析にも対応
    """

    @overload
    def analyze(self, error: "SupportedErrorType") -> LineErrorInfo: ...

    @overload
    def analyze(
        self, error_log: str, api_pattern: Optional[ApiPattern] = None
    ) -> LineErrorInfo: ...

    def analyze(
        self,
        error: Union[str, "SupportedErrorType"],
        api_pattern: Optional[ApiPattern] = None,
    ) -> LineErrorInfo:
        """
        エラーを分析してLineErrorInfoを返す

        Args:
            error: 分析対象のエラー（SDK例外、辞書、HTTPレスポンス、またはエラーログ文字列）
            api_pattern: エラーログ文字列解析時のAPIエンドポイントパターン（オプション）

        Returns:
            LineErrorInfo: エラーの詳細分析結果

        Raises:
            UnsupportedErrorTypeError: サポートされていないエラー形式
            AnalyzerError: 分析処理中のエラー

        Examples:
            # 従来の使い方
            result = analyzer.analyze(line_bot_api_error)

            # 新機能: エラーログ文字列の解析
            result = analyzer.analyze("Request failed with status code (400): Invalid request")

            # エンドポイント指定での詳細分析
            result = analyzer.analyze(error_log, ApiPattern.USER_PROFILE)
        """
        try:
            # Issue #1: エラーログ文字列の場合の処理
            if isinstance(error, str):
                return self._analyze_error_log(error, api_pattern)
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

    def _analyze_error_log(
        self, error_log: str, api_pattern: Optional[ApiPattern] = None
    ) -> LineErrorInfo:
        """
        エラーログ文字列を解析してLineErrorInfoを返す（Issue #1対応）

        Args:
            error_log: エラーログ文字列
            api_pattern: APIエンドポイントパターン（詳細分析用）

        Returns:
            LineErrorInfo: 解析結果

        Raises:
            AnalyzerError: ログ解析中のエラー
        """
        try:
            # ログパーサーでログを解析
            parser = LogParser()
            parse_result = parser.parse(error_log)

            if not parse_result.parse_success:
                # パースに失敗した場合、基本的な分析のみ実行
                return LineErrorInfo(
                    status_code=0,
                    message=error_log,
                    category=ErrorCategory.UNKNOWN,
                    is_retryable=False,
                    description="エラーログの解析に失敗しました",
                    recommended_action="エラーログの形式を確認してください",
                    raw_error={"error_log": error_log},
                )

            # パース成功 - データベースで詳細分析
            status_code = parse_result.status_code or 0
            message = parse_result.message or "Unknown error"

            # エンドポイント指定がある場合はそれも使用
            endpoint = api_pattern.value if api_pattern else None

            # データベースで分析
            category, _, is_retryable = self.db.analyze_error(
                status_code=status_code, message=message, endpoint=endpoint
            )

            # エラーカテゴリの詳細情報を取得
            error_details = self.db.get_error_details(category)

            # エンドポイント固有の詳細情報があるか確認
            endpoint_details = None
            if endpoint and status_code:
                endpoint_details = self.db.get_endpoint_error_details(
                    endpoint, status_code
                )

            return LineErrorInfo(
                status_code=status_code,
                message=message,
                category=category,
                is_retryable=is_retryable,
                description=(
                    endpoint_details.get("description", error_details["description"])
                    if endpoint_details
                    else error_details["description"]
                ),
                recommended_action=(
                    endpoint_details.get("action", error_details["action"])
                    if endpoint_details
                    else error_details["action"]
                ),
                documentation_url=(
                    endpoint_details.get("doc_url", error_details["doc_url"])
                    if endpoint_details
                    else error_details["doc_url"]
                ),
                request_id=parse_result.request_id,
                headers=parse_result.headers,
                details=(
                    endpoint_details.get("solutions", []) if endpoint_details else []
                ),
                raw_error={
                    "error_log": error_log,
                    "parse_result": parse_result.__dict__,
                },
            )

        except Exception as e:
            raise AnalyzerError(f"Failed to analyze error log: {str(e)}", e)
