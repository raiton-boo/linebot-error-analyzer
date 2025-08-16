"""
LINE Bot API エラー分析 - 列挙型定義

LINE Messaging API公式ドキュメントに基づいたエラーカテゴリとAPIパターンの定義。
"""

from enum import Enum


class ErrorCategory(Enum):
    """
    エラーカテゴリ（LINE Messaging API公式ステータスコードベース）

    公式ドキュメント: https://developers.line.biz/en/reference/messaging-api/#status-codes
    """

    # 200系 - 成功
    SUCCESS = "SUCCESS"

    # 400系 - クライアントエラー
    BAD_REQUEST = "BAD_REQUEST"  # 400 - リクエストに問題
    UNAUTHORIZED = "UNAUTHORIZED"  # 401 - 認証エラー
    FORBIDDEN = "FORBIDDEN"  # 403 - アクセス権限なし
    NOT_FOUND = "NOT_FOUND"  # 404 - リソースが見つからない
    CONFLICT = "CONFLICT"  # 409 - 競合状態
    GONE = "GONE"  # 410 - リソースが削除済み
    PAYLOAD_TOO_LARGE = "PAYLOAD_TOO_LARGE"  # 413 - リクエストサイズ超過
    UNSUPPORTED_MEDIA_TYPE = "UNSUPPORTED_MEDIA_TYPE"  # 415 - 非サポートメディア
    TOO_MANY_REQUESTS = "TOO_MANY_REQUESTS"  # 429 - レート制限

    # 500系 - サーバーエラー
    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"  # 500 - サーバー内部エラー

    # その他
    UNKNOWN = "UNKNOWN"  # 不明なエラー


class ApiPattern(Enum):
    """LINE API エンドポイントパターン（公式API構造ベース）"""

    # Message API
    REPLY_MESSAGE = "reply_message"
    PUSH_MESSAGE = "push_message"
    MULTICAST_MESSAGE = "multicast_message"
    BROADCAST_MESSAGE = "broadcast_message"
    NARROWCAST_MESSAGE = "narrowcast_message"

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


from enum import Enum


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


class ApiPattern(Enum):
    """LINE API パターン定義（階層構造）"""

    # 1. message (メッセージ配信)
    MESSAGE_REPLY = "message.message_reply"  # 応答メッセージ
    MESSAGE_PUSH = "message.message_push"  # プッシュメッセージ
    MESSAGE_MULTICAST = "message.message_multicast"  # マルチキャスト
    MESSAGE_NARROWCAST = "message.message_narrowcast"  # ナローキャスト
    MESSAGE_BROADCAST = "message.message_broadcast"  # ブロードキャスト
    MESSAGE_DELIVERY_PROGRESS = "message.message_delivery_progress"  # 配信進捗
    MESSAGE_QUOTA = "message.message_quota"  # 配信制限
    MESSAGE_VALIDATION = "message.message_validation"  # メッセージ検証
    MESSAGE_LOADING = "message.message_loading"  # ローディング表示

    # 2. audience (オーディエンス管理)
    AUDIENCE_CREATE = "audience.audience_create"  # オーディエンスグループ作成
    AUDIENCE_UPDATE = "audience.audience_update"  # オーディエンスグループ更新
    AUDIENCE_GET = "audience.audience_get"  # オーディエンス情報取得
    AUDIENCE_DELETE = "audience.audience_delete"  # オーディエンス削除

    # 3. insights (分析・統計)
    INSIGHTS_MESSAGE_DELIVERY = (
        "insights.insights_message_delivery"  # メッセージ配信統計
    )
    INSIGHTS_FOLLOWERS = "insights.insights_followers"  # フォロワー統計
    INSIGHTS_DEMOGRAPHIC = "insights.insights_demographic"  # 人口統計
    INSIGHTS_NARROWCAST = "insights.insights_narrowcast"  # ナローキャスト統計

    # 4. user (ユーザー管理)
    USER_PROFILE = "user.user_profile"  # ユーザープロフィール
    USER_FOLLOWERS = "user.user_followers"  # フォロワーID取得
    USER_MEMBERSHIP = "user.membership"  # メンバーシップ管理

    # 5. rich_menu (リッチメニュー管理)
    RICH_MENU_CREATE = "rich_menu.rich_menu_create"  # リッチメニュー作成
    RICH_MENU_IMAGE = "rich_menu.rich_menu_image"  # リッチメニュー画像
    RICH_MENU_LINK = "rich_menu.rich_menu_link"  # リッチメニュー設定・解除
    RICH_MENU_DELETE = "rich_menu.rich_menu_delete"  # リッチメニュー削除
    RICH_MENU_ALIAS = "rich_menu.rich_menu_alias"  # リッチメニューエイリアス

    # 6. webhook (Webhook設定)
    WEBHOOK_SETTINGS = "webhook.webhook_settings"  # Webhook設定

    # 7. content (コンテンツ管理)
    CONTENT_RETRIEVAL = "content.content_retrieval"  # コンテンツ取得

    # 8. channel (チャネル管理)
    CHANNEL_ACCESS_TOKENS = "channel.channel_access_tokens"  # チャネルアクセストークン
