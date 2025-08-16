"""
LINE Bot エラー分析器 - 非同期版

LINE Messaging API のエラーを非同期で自動分析・分類するクラス。
高パフォーマンスな並行処理とバッチ処理をサポート。
"""

from __future__ import annotations
import asyncio
import json
from typing import Any, Dict, List, Optional, Union, TYPE_CHECKING
from .base_analyzer import BaseLineErrorAnalyzer
from ..models import LineErrorInfo, ErrorCategory
from ..exceptions import AnalyzerError, UnsupportedErrorTypeError, InvalidErrorDataError

if TYPE_CHECKING:
    from ..utils.types import SupportedErrorType


class AsyncLineErrorAnalyzer(BaseLineErrorAnalyzer):
    """
    LINE Bot エラー分析器（非同期版）

    LINE Messaging API のエラーを非同期で自動分析し、詳細な診断情報を提供。
    高パフォーマンスな並行処理とバッチ処理に対応。
    """

    async def analyze(self, error: "SupportedErrorType") -> LineErrorInfo:
        """
        エラーを非同期で分析してLineErrorInfoを返す

        Args:
            error: 分析対象のエラー（SDK例外、辞書、HTTPレスポンス等）

        Returns:
            LineErrorInfo: エラーの詳細分析結果

        Raises:
            UnsupportedErrorTypeError: サポートされていないエラー形式
            AnalyzerError: 分析処理中のエラー
        """
        try:
            # 協調的マルチタスクのための制御権移譲
            await asyncio.sleep(0)

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
            raise
        except Exception as e:
            raise AnalyzerError(f"Failed to analyze error: {str(e)}", e)

            # 非同期版分析メソッド
            return await self.analyze(error)
        except Exception as e:
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
