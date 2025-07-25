"""
LINE Bot エラー分析器 - 型定義

型ヒント、プロトコル、TypedDictの定義。
"""

from typing import (
    Any,
    Dict,
    List,
    Optional,
    Union,
    TypeVar,
    Protocol,
    runtime_checkable,
)
from typing_extensions import TypedDict, Literal
from abc import ABC, abstractmethod

# 基本的な型エイリアス
StatusCode = int
ErrorMessage = str
RequestId = str
Headers = Dict[str, str]
RawErrorData = Dict[str, Any]

# LINE API エラーの種類を表すリテラル型
ErrorCategoryLiteral = Literal[
    "AUTH_ERROR",
    "INVALID_TOKEN",
    "EXPIRED_TOKEN",
    "INVALID_SIGNATURE",
    "RATE_LIMIT",
    "QUOTA_EXCEEDED",
    "CONCURRENT_LIMIT",
    "INVALID_PARAM",
    "INVALID_REQUEST_BODY",
    "INVALID_JSON",
    "INVALID_CONTENT_TYPE",
    "PAYLOAD_TOO_LARGE",
    "UNSUPPORTED_MEDIA_TYPE",
    "USER_NOT_FOUND",
    "RESOURCE_NOT_FOUND",
    "PROFILE_NOT_ACCESSIBLE",
    "USER_BLOCKED",
    "MESSAGE_SEND_FAILED",
    "INVALID_REPLY_TOKEN",
    "REPLY_TOKEN_EXPIRED",
    "REPLY_TOKEN_USED",
    "FORBIDDEN",
    "ACCESS_DENIED",
    "PLAN_LIMITATION",
    "SERVER_ERROR",
    "NETWORK_ERROR",
    "TIMEOUT_ERROR",
    "CONNECTION_ERROR",
    "RICH_MENU_ERROR",
    "RICH_MENU_SIZE_ERROR",
    "AUDIENCE_ERROR",
    "AUDIENCE_SIZE_ERROR",
    "WEBHOOK_ERROR",
    "CONFLICT",
    "GONE",
    "UNKNOWN",
]

ErrorSeverityLiteral = Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"]


# TypedDict for structured error data
class ErrorDataDict(TypedDict, total=False):
    """エラーデータの構造化された型定義"""

    status_code: StatusCode
    status: StatusCode
    message: ErrorMessage
    error: ErrorMessage
    error_code: Optional[str]
    headers: Optional[Headers]
    request_id: Optional[RequestId]
    accepted_request_id: Optional[RequestId]
    details: Optional[List[Dict[str, Any]]]


class ErrorDetailDict(TypedDict):
    """エラー詳細情報の型定義"""

    message: str
    property: str


class ErrorResponseDict(TypedDict, total=False):
    """LINE API エラーレスポンスの型定義"""

    message: str
    details: List[ErrorDetailDict]


# Protocol for error-like objects
@runtime_checkable
class ErrorLike(Protocol):
    """エラーライクオブジェクトのプロトコル"""

    def __str__(self) -> str:
        """文字列表現を返す"""
        ...


@runtime_checkable
class HttpResponseLike(Protocol):
    """HTTPレスポンスライクオブジェクトのプロトコル"""

    status_code: StatusCode
    text: str
    headers: Headers


@runtime_checkable
class LineBotV3ApiExceptionLike(Protocol):
    """LINE Bot SDK v3 ApiException ライクオブジェクトのプロトコル"""

    __module__: str
    status: StatusCode
    body: Union[str, bytes, Dict[str, Any]]
    headers: Any
    reason: Optional[str]


@runtime_checkable
class LineBotV2ApiErrorLike(Protocol):
    """LINE Bot SDK v2 LineBotApiError ライクオブジェクトのプロトコル"""

    __module__: str
    status_code: StatusCode
    headers: Optional[Headers]
    request_id: Optional[RequestId]
    accepted_request_id: Optional[RequestId]
    error: Any


# Union types for supported error objects
SupportedErrorType = Union[
    ErrorDataDict,
    LineBotV3ApiExceptionLike,
    LineBotV2ApiErrorLike,
    HttpResponseLike,
    ErrorLike,
    Dict[str, Any],
    Any,  # fallback
]

# Generic type variables
T = TypeVar("T")
ErrorT = TypeVar("ErrorT", bound=SupportedErrorType)


# Analysis result types
class AnalysisResultDict(TypedDict):
    """分析結果の辞書型定義"""

    basic: Dict[str, Any]
    analysis: Dict[str, Any]
    guidance: Dict[str, Any]
    raw_data: Dict[str, Any]


# Callback types
from typing import Callable, Awaitable

ErrorAnalysisCallback = Callable[[SupportedErrorType], None]
AsyncErrorAnalysisCallback = Callable[[SupportedErrorType], Awaitable[None]]


# Configuration types
class RetryConfig(TypedDict, total=False):
    """リトライ設定の型定義"""

    max_attempts: int
    base_delay: float
    max_delay: float
    exponential_base: float
    jitter: bool


class AnalyzerConfig(TypedDict, total=False):
    """分析器設定の型定義"""

    enable_caching: bool
    cache_size: int
    retry_config: RetryConfig
    custom_patterns: List[Dict[str, Any]]


# Validation functions
def is_valid_status_code(status_code: Any) -> bool:
    """有効なHTTPステータスコードかチェック"""
    return isinstance(status_code, int) and 100 <= status_code <= 999


def is_valid_error_message(message: Any) -> bool:
    """有効なエラーメッセージかチェック"""
    return isinstance(message, str) and len(message.strip()) > 0


def is_error_data_dict(obj: Any) -> bool:
    """ErrorDataDict型かチェック"""
    if not isinstance(obj, dict):
        return False

    # 必須フィールドのチェック
    has_status = "status_code" in obj or "status" in obj
    has_message = "message" in obj or "error" in obj

    return has_status and has_message


# Type guards
def is_line_bot_v3_exception(error: Any) -> bool:
    """LINE Bot SDK v3 ApiException かチェック"""
    return (
        hasattr(error, "__module__")
        and "linebot.v3" in str(error.__module__)
        and hasattr(error, "status")
        and hasattr(error, "body")
    )


def is_line_bot_v2_error(error: Any) -> bool:
    """LINE Bot SDK v2 LineBotApiError かチェック"""
    return (
        hasattr(error, "__module__")
        and "linebot" in str(error.__module__)
        and "v3" not in str(error.__module__)
        and hasattr(error, "status_code")
        and hasattr(error, "error")
    )


def is_http_response_like(obj: Any) -> bool:
    """HTTPレスポンスライクオブジェクトかチェック"""
    return (
        hasattr(obj, "status_code")
        and hasattr(obj, "text")
        and hasattr(obj, "headers")
        and obj.status_code is not None
        and obj.text is not None
        and obj.headers is not None
    )
