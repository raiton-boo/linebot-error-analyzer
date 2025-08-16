"""
LINE Bot API エラー分析 - 列挙型定義

LINE Messaging API公式ドキュメントに基づいたエラーカテゴリとAPIパターンの定義。
"""

from enum import Enum


class ErrorCategory(Enum):
    """
    エラーカテゴリ

    公式ドキュメント: https://developers.line.biz/en/reference/messaging-api/#status-codes
    """

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


class ApiPattern(Enum):
    """LINE API エンドポイントパターン（公式API構造ベース）"""

    # Message API
    MESSAGE_REPLY = "message_reply"
    MESSAGE_PUSH = "message_push"
    MESSAGE_MULTICAST = "message_multicast"
    MESSAGE_BROADCAST = "message_broadcast"
    MESSAGE_NARROWCAST = "message_narrowcast"

    # User Profile API
    USER_PROFILE = "user_profile"

    # Group/Room API
    GROUP_SUMMARY = "group_summary"
    ROOM_MEMBER = "room_member"

    # Rich Menu API
    RICH_MENU = "rich_menu"

    # Content API
    CONTENT = "content"

    # Webhook API
    WEBHOOK = "webhook"

    # Channel Access Token API
    CHANNEL_ACCESS_TOKEN = "channel_access_token"
