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
from .models import LineErrorInfo, ErrorCategory, ErrorSeverity
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

    async def analyze_multiple(
        self, errors: List["SupportedErrorType"]
    ) -> List[LineErrorInfo]:
        """
        複数エラーの非同期一括分析

        エラーリストを並行処理で分析し、結果をリストで返す。
        個別エラーの分析失敗時も処理を継続（graceful degradation）。

        Args:
            errors: 分析対象のエラーリスト

        Returns:
            List[LineErrorInfo]: 各エラーの分析結果（入力と同サイズ）
        """
        tasks = []
        for error in errors:
            task = self._analyze_single_with_fallback(error)
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 例外をキャッチしてUNKNOWNエラーに変換
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                error_info = self._create_info(
                    status_code=0,
                    message=f"Analysis failed: {str(result)}",
                    headers={},
                    error_data={},
                    category=ErrorCategory.UNKNOWN,
                    severity=ErrorSeverity.MEDIUM,
                    is_retryable=False,
                    raw_error={
                        "original_error": str(errors[i]),
                        "analysis_error": str(result),
                    },
                )
                final_results.append(error_info)
            else:
                final_results.append(result)

        return final_results

    async def analyze_batch(
        self,
        errors: List["SupportedErrorType"],
        batch_size: int = 10,
        max_workers: int = None,
    ) -> List[LineErrorInfo]:
        """
        大量エラーのバッチ処理による非同期分析

        メモリ使用量を抑制しつつ大量のエラーを効率的に処理。

        Args:
            errors: 分析対象のエラーリスト
            batch_size: バッチサイズ（デフォルト: 10）
            max_workers: 最大ワーカー数（互換性のため保持、未使用）

        Returns:
            List[LineErrorInfo]: 全エラーの分析結果
        """
        results: List[LineErrorInfo] = []

        # バッチごとに処理
        for i in range(0, len(errors), batch_size):
            batch = errors[i : i + batch_size]
            batch_results = await self.analyze_multiple(batch)
            results.extend(batch_results)
            await asyncio.sleep(0.001)  # バッチ間の協調的制御権移譲

        return results

    # 非同期版分析メソッド

    async def _analyze_single_with_fallback(
        self, error: "SupportedErrorType"
    ) -> LineErrorInfo:
        """エラー分析のフォールバック付きラッパー"""
        try:
            return await self.analyze(error)
        except Exception as e:
            return self._create_info(
                status_code=0,
                message=f"Analysis failed: {str(e)}",
                headers={},
                error_data={},
                category=ErrorCategory.UNKNOWN,
                severity=ErrorSeverity.MEDIUM,
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
                error_code=error_data.get("error_code"),
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
