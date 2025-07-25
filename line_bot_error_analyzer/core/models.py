"""
LINE Bot エラー分析 - データモデル

エラー分析結果を表現するデータクラスと列挙型の定義。
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, Any, List, Union, TYPE_CHECKING
import json

if TYPE_CHECKING:
    from ..utils.types import (
        StatusCode,
        ErrorMessage,
        RequestId,
        Headers,
        RawErrorData,
        AnalysisResultDict,
    )


class ErrorCategory(Enum):
    """エラーカテゴリ"""

    # 認証・トークン関連
    AUTH_ERROR = "AUTH_ERROR"
    INVALID_TOKEN = "INVALID_TOKEN"
    EXPIRED_TOKEN = "EXPIRED_TOKEN"
    INVALID_SIGNATURE = "INVALID_SIGNATURE"

    # レート制限・制約関連
    RATE_LIMIT = "RATE_LIMIT"
    QUOTA_EXCEEDED = "QUOTA_EXCEEDED"
    CONCURRENT_LIMIT = "CONCURRENT_LIMIT"

    # リクエスト関連
    INVALID_PARAM = "INVALID_PARAM"
    INVALID_REQUEST_BODY = "INVALID_REQUEST_BODY"
    INVALID_JSON = "INVALID_JSON"
    INVALID_CONTENT_TYPE = "INVALID_CONTENT_TYPE"
    PAYLOAD_TOO_LARGE = "PAYLOAD_TOO_LARGE"
    UNSUPPORTED_MEDIA_TYPE = "UNSUPPORTED_MEDIA_TYPE"

    # ユーザー・リソース関連
    USER_NOT_FOUND = "USER_NOT_FOUND"
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    PROFILE_NOT_ACCESSIBLE = "PROFILE_NOT_ACCESSIBLE"
    USER_BLOCKED = "USER_BLOCKED"

    # メッセージ送信関連
    MESSAGE_SEND_FAILED = "MESSAGE_SEND_FAILED"
    INVALID_REPLY_TOKEN = "INVALID_REPLY_TOKEN"
    REPLY_TOKEN_EXPIRED = "REPLY_TOKEN_EXPIRED"
    REPLY_TOKEN_USED = "REPLY_TOKEN_USED"

    # 権限・アクセス関連
    FORBIDDEN = "FORBIDDEN"
    ACCESS_DENIED = "ACCESS_DENIED"
    PLAN_LIMITATION = "PLAN_LIMITATION"

    # システム・ネットワーク関連
    SERVER_ERROR = "SERVER_ERROR"
    NETWORK_ERROR = "NETWORK_ERROR"
    TIMEOUT_ERROR = "TIMEOUT_ERROR"
    CONNECTION_ERROR = "CONNECTION_ERROR"

    # リッチメニュー関連
    RICH_MENU_ERROR = "RICH_MENU_ERROR"
    RICH_MENU_SIZE_ERROR = "RICH_MENU_SIZE_ERROR"

    # オーディエンス関連
    AUDIENCE_ERROR = "AUDIENCE_ERROR"
    AUDIENCE_SIZE_ERROR = "AUDIENCE_SIZE_ERROR"

    # Webhook関連
    WEBHOOK_ERROR = "WEBHOOK_ERROR"

    # その他・不明
    CONFLICT = "CONFLICT"
    GONE = "GONE"
    UNKNOWN = "UNKNOWN"


class ErrorSeverity(Enum):
    """エラーの重要度"""

    CRITICAL = "CRITICAL"  # サービス停止レベル
    HIGH = "HIGH"  # 機能が使えない
    MEDIUM = "MEDIUM"  # 一部機能に影響
    LOW = "LOW"  # 軽微な問題


@dataclass
class LineErrorInfo:
    """
    LINE API エラー情報

    Args:
        status_code: HTTPステータスコード
        error_code: LINEエラーコード（オプション）
        message: エラーメッセージ
        category: エラーカテゴリ
        severity: エラーの重要度
        is_retryable: リトライ可能かどうか
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
    error_code: Optional[str]
    message: "ErrorMessage"

    # 分析結果
    category: ErrorCategory
    severity: ErrorSeverity
    is_retryable: bool

    # 詳細情報
    description: str
    recommended_action: str
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

        if not isinstance(self.category, ErrorCategory):
            raise TypeError(
                f"category must be ErrorCategory, got {type(self.category)}"
            )

        if not isinstance(self.severity, ErrorSeverity):
            raise TypeError(
                f"severity must be ErrorSeverity, got {type(self.severity)}"
            )

        if not isinstance(self.is_retryable, bool):
            raise TypeError(f"is_retryable must be bool, got {type(self.is_retryable)}")

    def to_dict(self) -> "AnalysisResultDict":
        """辞書形式で出力"""
        return {
            "basic": {
                "status_code": self.status_code,
                "error_code": self.error_code,
                "message": self.message,
            },
            "analysis": {
                "category": self.category.value,
                "severity": self.severity.value,
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
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)

    def __str__(self) -> str:
        """文字列表現"""
        return (
            f"LineErrorInfo(\n"
            f"  Category: {self.category.value}\n"
            f"  Severity: {self.severity.value}\n"
            f"  Status: {self.status_code}\n"
            f"  Message: {self.message}\n"
            f"  Retryable: {self.is_retryable}\n"
            f"  Action: {self.recommended_action}\n"
            f")"
        )
