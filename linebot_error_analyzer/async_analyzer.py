"""
LINE Bot エラー分析器 - 非同期版

LINE Messaging API のエラーを非同期で自動分析・分類するクラス。
高パフォーマンスな並行処理とバッチ処理をサポート。
"""

from __future__ import annotations
import asyncio
import json
from typing import Any, Dict, List, Optional, Union, TYPE_CHECKING, overload
from .core.base_analyzer import BaseLineErrorAnalyzer
from .models import LineErrorInfo, ErrorCategory, ApiPattern
from .models.log_parser import LogParser
from .exceptions import AnalyzerError, UnsupportedErrorTypeError, InvalidErrorDataError

if TYPE_CHECKING:
    from .utils.types import SupportedErrorType


class AsyncLineErrorAnalyzer(BaseLineErrorAnalyzer):
    """
    LINE Bot エラー分析器（非同期版）

    LINE Messaging API のエラーを非同期で自動分析し、詳細な診断情報を提供。
    高パフォーマンスな並行処理とバッチ処理に対応。

    Issue #1対応: エラーログ文字列の非同期解析にも対応
    """

    @overload
    async def analyze(self, error: "SupportedErrorType") -> LineErrorInfo: ...

    @overload
    async def analyze(
        self, error_log: str, api_pattern: Optional[ApiPattern] = None
    ) -> LineErrorInfo: ...

    async def analyze(
        self,
        error: Union[str, "SupportedErrorType"],
        api_pattern: Optional[ApiPattern] = None,
    ) -> LineErrorInfo:
        """
        エラーを非同期で分析してLineErrorInfoを返す

        Args:
            error: 分析対象のエラー（SDK例外、辞書、HTTPレスポンス、またはエラーログ文字列）
            api_pattern: エラーログ文字列解析時のAPIエンドポイントパターン（オプション）

        Returns:
            LineErrorInfo: エラーの詳細分析結果

        Raises:
            UnsupportedErrorTypeError: サポートされていないエラー形式
            AnalyzerError: 分析処理中のエラー
        """
        try:
            # 協調的マルチタスクのための制御権移譲
            await asyncio.sleep(0)

            # Issue #1: エラーログ文字列の場合の処理
            if isinstance(error, str):
                return await self._analyze_error_log(error, api_pattern)

            # エラータイプ別分析（優先度順）
            if self._is_v3_sig(error):
                return await self._analyze_v3_sig(error)
            elif self._is_v2_sig(error):
                return await self._analyze_v2_sig(error)
            elif self._is_v3(error):
                return await self._analyze_v3(error)
            elif self._is_v2(error):
                return await self._analyze_v2(error)
            elif isinstance(error, dict):
                return await self._analyze_dict(error)
            elif hasattr(error, "status_code") and hasattr(error, "text"):
                return await self._analyze_response(error)
            else:
                raise UnsupportedErrorTypeError(
                    f"Unsupported error type: {type(error)}"
                )

        except UnsupportedErrorTypeError:
            # サポート対象外エラーは上位に委ねる
            raise
        except AnalyzerError:
            # 既にラップされたエラーは再発生
            raise
        except Exception as e:
            # 予期しない例外: フォールバック情報を返す（サービス継続性重視）
            return self._create_info(
                status_code=0,
                message=f"Analysis failed: {str(e)}",
                headers={},
                error_data={},
                category=ErrorCategory.UNKNOWN,
                is_retryable=False,
                raw_error={"original_error": str(error), "analysis_error": str(e)},
            )

    async def _analyze_v3_sig(self, error: Any) -> LineErrorInfo:
        """v3 署名エラーの非同期分析"""
        await asyncio.sleep(0)
        return super()._analyze_v3_sig(error)

    async def _analyze_v2_sig(self, error: Any) -> LineErrorInfo:
        """v2 署名エラーの非同期分析"""
        await asyncio.sleep(0)
        return super()._analyze_v2_sig(error)

    async def _analyze_v3(self, error: Any) -> LineErrorInfo:
        """v3 API例外の非同期分析"""
        await asyncio.sleep(0)

        try:
            status_code = (
                getattr(error, "status", None)
                or getattr(error, "status_code", None)
                or 0
            )

            # statusがMockオブジェクトの場合の処理
            if hasattr(status_code, "_mock_name"):
                status_code = 0

            # headersの安全な取得
            headers = {}
            if hasattr(error, "headers") and error.headers:
                try:
                    if hasattr(error.headers, "items"):
                        headers = dict(error.headers.items())
                    elif hasattr(error.headers, "__iter__"):
                        headers = dict(error.headers)
                    else:
                        headers = {}
                except (TypeError, AttributeError, ValueError):
                    headers = {}

            # bodyからエラー情報を抽出
            error_data = {}
            if hasattr(error, "body") and error.body:
                try:
                    if isinstance(error.body, (str, bytes)):
                        error_data = json.loads(error.body)
                    else:
                        error_data = error.body
                except (json.JSONDecodeError, TypeError):
                    error_data = {"message": str(error.body)}

            message = error_data.get(
                "message", getattr(error, "reason", "Unknown error")
            )

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
            raise AnalyzerError(f"Failed to analyze v3 ApiException: {str(e)}", e)

    async def _analyze_v2(self, error: Any) -> LineErrorInfo:
        """v2系 LineBotApiError の非同期分析"""
        await asyncio.sleep(0)  # 協調的マルチタスク

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

    async def _analyze_dict(self, error: Dict[str, Any]) -> LineErrorInfo:
        """辞書形式のエラーデータを非同期分析"""
        await asyncio.sleep(0)  # 協調的マルチタスク
        return super()._analyze_dict(error)

    async def _analyze_response(self, error: Any) -> LineErrorInfo:
        """HTTPレスポンス類似オブジェクトを非同期分析"""
        await asyncio.sleep(0)  # 協調的マルチタスク
        return super()._analyze_response(error)

    async def _analyze_error_log(
        self, error_log: str, api_pattern: Optional[ApiPattern] = None
    ) -> LineErrorInfo:
        """
        エラーログ文字列を非同期で解析してLineErrorInfoを返す（Issue #1対応）

        Args:
            error_log: エラーログ文字列
            api_pattern: APIエンドポイントパターン（詳細分析用）

        Returns:
            LineErrorInfo: 解析結果

        Raises:
            AnalyzerError: ログ解析中のエラー
        """
        # 協調的マルチタスクのための制御権移譲
        await asyncio.sleep(0)

        try:
            # ログパーサーでログを解析（CPUバウンドなタスク）
            parser = LogParser()
            parse_result = parser.parse(error_log)

            # 非同期で制御権移譲
            await asyncio.sleep(0)

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

            # 非同期で制御権移譲
            await asyncio.sleep(0)

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
