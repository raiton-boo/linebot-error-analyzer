"""
LINE Bot エラー分析 - エラー情報データクラス

エラー分析結果を表現するLineErrorInfoクラスの定義。
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, TYPE_CHECKING
import json

from .enums import ErrorCategory

if TYPE_CHECKING:
    from ..utils.types import (
        StatusCode,
        ErrorMessage,
        RequestId,
        Headers,
        RawErrorData,
        AnalysisResultDict,
    )


@dataclass
class LineErrorInfo:
    """
    LINE API エラー情報

    Args:
        status_code: HTTPステータスコード
        message: エラーメッセージ
        category: エラーカテゴリ（オプション、APIパターン指定時のみ）
        is_retryable: リトライ可能かどうか（オプション、APIパターン指定時のみ）
        description: エラーの詳細説明
        recommended_action: 推奨対処法
        retry_after: リトライまでの推奨待機時間（秒）
        raw_error: 元のエラーデータ
        request_id: LINE APIリクエストID
        accepted_request_id: 受理されたリクエストID
        headers: レスポンスヘッダー
        details: エラー詳細リスト
        documentation_url: 関連ドキュメントURL
    """

    # 基本情報
    status_code: "StatusCode"
    message: "ErrorMessage"

    # 分析結果（APIパターン指定時のみ設定、未指定時はNone）
    category: Optional[ErrorCategory] = None
    is_retryable: Optional[bool] = None

    # 詳細情報
    description: str = ""
    recommended_action: str = ""
    retry_after: Optional[int] = None  # リトライまでの推奨待機時間（秒）

    # 元データ
    raw_error: "RawErrorData" = field(default_factory=dict)
    request_id: Optional["RequestId"] = None
    accepted_request_id: Optional["RequestId"] = None
    headers: Optional["Headers"] = None

    # 追加情報
    details: Optional[List[Dict[str, Any]]] = None
    documentation_url: Optional[str] = None

    def __post_init__(self) -> None:
        """データクラス初期化後の検証"""
        self._validate_data()

    def _validate_data(self) -> None:
        """データの妥当性を検証"""
        # status_code 0 はエラー分析失敗時の特別な値として許可
        if not isinstance(self.status_code, int) or (
            self.status_code != 0 and not (100 <= self.status_code <= 999)
        ):
            raise ValueError(f"Invalid status_code: {self.status_code}")

        if not isinstance(self.message, str) or not self.message.strip():
            raise ValueError(f"Invalid message: {self.message}")

        if self.category is not None and not isinstance(self.category, ErrorCategory):
            raise TypeError(
                f"category must be ErrorCategory, got {type(self.category)}"
            )

        if self.is_retryable is not None and not isinstance(self.is_retryable, bool):
            raise TypeError(f"is_retryable must be bool, got {type(self.is_retryable)}")

    def to_dict(self) -> "AnalysisResultDict":
        """辞書形式で出力"""
        return {
            "basic": {
                "status_code": self.status_code,
                "message": self.message,
            },
            "analysis": {
                "category": self.category.value if self.category else None,
                "is_retryable": self.is_retryable,
            },
            "guidance": {
                "description": self.description,
                "recommended_action": self.recommended_action,
                "retry_after": self.retry_after,
                "documentation_url": self.documentation_url,
            },
            "raw_data": {
                "request_id": self.request_id,
                "accepted_request_id": self.accepted_request_id,
                "headers": self.headers,
                "details": self.details,
                "raw_error": self.raw_error,
            },
        }

    def to_json(self, indent: int = 2) -> str:
        """JSON形式で出力"""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    def __str__(self) -> str:
        """文字列表現"""
        category_str = self.category.value if self.category else "None"

        return (
            f"LineErrorInfo("
            f"status={self.status_code}, "
            f"message='{self.message[:50]}...', "
            f"category={category_str}, "
            f"retryable={self.is_retryable})"
        )

    def __repr__(self) -> str:
        """開発用文字列表現"""
        return self.__str__()
