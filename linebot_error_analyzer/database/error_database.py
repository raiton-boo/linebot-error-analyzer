# LINE Bot Error Detective - エラーデータベース
"""
LINE Bot Error Detective - 階層化エラーデータベース

LINE Messaging APIのエラー分析および解決策提案システム。
階層構造によるエンドポイント別詳細エラー管理を提供。

階層構造:
1. message (メッセージ配信)
   - message.message_reply (応答メッセージ)
   - message.message_push (プッシュメッセージ)
   - message.message_multicast (マルチキャスト)
   - message.message_narrowcast (ナローキャスト)
   - message.message_broadcast (ブロードキャスト)
   - message.message_delivery_progress (配信進捗)
   - message.message_quota (配信制限)
   - message.message_validation (メッセージ検証)
   - message.message_loading (ローディング表示)

2. audience (オーディエンス管理)
   - audience.audience_create (オーディエンスグループ作成)
   - audience.audience_update (オーディエンスグループ更新)
   - audience.audience_get (オーディエンス情報取得)
   - audience.audience_delete (オーディエンス削除)

3. insights (分析・統計)
   - insights.insights_message_delivery (メッセージ配信統計)
   - insights.insights_followers (フォロワー統計)
   - insights.insights_demographic (人口統計)
   - insights.insights_narrowcast (ナローキャスト統計)

4. user (ユーザー管理)
   - user.user_profile (ユーザープロフィール)
   - user.user_followers (フォロワーID取得)
   - user.membership (メンバーシップ管理)

5. rich_menu (リッチメニュー管理)
   - rich_menu.rich_menu_create (リッチメニュー作成)
   - rich_menu.rich_menu_image (リッチメニュー画像)
   - rich_menu.rich_menu_link (リッチメニュー設定・解除)
   - rich_menu.rich_menu_delete (リッチメニュー削除)
   - rich_menu.rich_menu_alias (リッチメニューエイリアス)

6. webhook (Webhook設定)
   - webhook.webhook_settings (Webhook設定)

7. content (コンテンツ管理)
   - content.content_retrieval (コンテンツ取得)

8. channel (チャネル管理)
   - channel.channel_access_tokens (チャネルアクセストークン)

使用例:
    analyzer = ErrorAnalyzer()
    result = analyzer.analyze_error(
        status_code=400,
        message="Invalid push token",
        endpoint="message.message_push"
    )
"""

import re
from typing import Dict, List, Optional, Tuple
from enum import Enum

from ..models.enums import ErrorCategory


class ErrorDatabase:
    """
    LINE Bot Error Detective - エラーデータベース

    階層構造によるエンドポイント別詳細エラー管理システム。
    各エンドポイントの詳細なエラーハンドリング情報と具体的な対処法を提供。
    """

    def __init__(self):
        """データベース初期化: 各種マッピング情報を構築"""
        self._init_status_code_mappings()
        self._init_message_patterns()
        self._init_error_details()

    def _init_status_code_mappings(self):
        """
        HTTPステータスコード基本マッピング + エンドポイント別階層構造初期化

        基本的なHTTPステータスコードとエラーカテゴリの対応に加え、
        階層構造によるエンドポイント固有の詳細エラー情報を管理。
        """
        # 基本HTTPステータスコードマッピング
        self.status_code_mappings = {
            400: (ErrorCategory.INVALID_PARAM, False),
            401: (ErrorCategory.AUTH_ERROR, False),
            403: (ErrorCategory.ACCESS_DENIED, False),
            404: (ErrorCategory.RESOURCE_NOT_FOUND, False),
            409: (ErrorCategory.CONFLICT, False),
            410: (ErrorCategory.GONE, False),
            413: (ErrorCategory.PAYLOAD_TOO_LARGE, False),
            415: (ErrorCategory.UNSUPPORTED_MEDIA_TYPE, False),
            422: (ErrorCategory.INVALID_PARAM, False),
            426: (ErrorCategory.PLAN_LIMITATION, False),
            429: (ErrorCategory.RATE_LIMIT, True),
            500: (ErrorCategory.SERVER_ERROR, True),
            502: (ErrorCategory.SERVER_ERROR, True),
            503: (ErrorCategory.SERVER_ERROR, True),
            504: (ErrorCategory.TIMEOUT_ERROR, True),
        }

        # エンドポイント別ステータスコードマッピング（階層構造）
        self.endpoint_status_mappings = {
            # 1. メッセージ配信
            "message": {
                "message_reply": {
                    400: {
                        "category": ErrorCategory.INVALID_REPLY_TOKEN,
                        "description": "応答メッセージの送信に失敗しました",
                        "action": "応答トークンの有効性、メッセージオブジェクトの形式を確認してください",
                        "retry": False,
                        "code": "REPLY_MESSAGE_ERROR",
                        "doc_url": "https://developers.line.biz/ja/reference/messaging-api/#reply-message",
                        "solutions": [
                            "応答トークンの有効性確認（1回のみ使用、30秒以内）",
                            "メッセージオブジェクトの形式確認",
                            "応答制限時間（30秒）の確認",
                            "メッセージ数制限（5件まで）の確認",
                        ],
                    },
                    404: {
                        "category": ErrorCategory.RESOURCE_NOT_FOUND,
                        "description": "応答可能なイベントが見つかりません",
                        "action": "有効な応答トークンを使用しているか確認してください",
                        "retry": False,
                        "code": "REPLY_EVENT_NOT_FOUND",
                        "doc_url": "https://developers.line.biz/ja/reference/messaging-api/#reply-message",
                        "solutions": [
                            "Webhookイベントの確認",
                            "応答トークンの取得元確認",
                        ],
                    },
                },
                "message_push": {
                    400: {
                        "category": ErrorCategory.MESSAGE_SEND_FAILED,
                        "description": "プッシュメッセージの送信に失敗しました",
                        "action": "ユーザーID、メッセージオブジェクトの形式を確認してください",
                        "retry": False,
                        "code": "PUSH_MESSAGE_ERROR",
                        "doc_url": "https://developers.line.biz/ja/reference/messaging-api/#send-push-message",
                        "solutions": [
                            "ユーザーIDの形式確認",
                            "メッセージオブジェクトの形式確認",
                            "友だち関係の確認",
                            "メッセージ数制限（5件まで）の確認",
                        ],
                    },
                    403: {
                        "category": ErrorCategory.ACCESS_DENIED,
                        "description": "ユーザーがボットをブロックしているか、友だちではありません",
                        "action": "ユーザーとの友だち関係を確認してください",
                        "retry": False,
                        "code": "PUSH_ACCESS_DENIED",
                        "doc_url": "https://developers.line.biz/ja/reference/messaging-api/#send-push-message",
                        "solutions": [
                            "ユーザーのブロック状態確認",
                            "友だち追加状態の確認",
                        ],
                    },
                    429: {
                        "category": ErrorCategory.RATE_LIMIT,
                        "description": "プッシュメッセージのレート制限を超過しました",
                        "action": "送信間隔を調整するか、プランのアップグレードを検討してください",
                        "retry": True,
                        "code": "PUSH_RATE_LIMIT",
                        "doc_url": "https://developers.line.biz/ja/reference/messaging-api/#rate-limits",
                        "solutions": [
                            "送信間隔の調整",
                            "月間制限の確認",
                            "プランのアップグレード",
                        ],
                    },
                },
                "message_narrowcast": {
                    403: {
                        "category": ErrorCategory.PLAN_LIMITATION,
                        "description": "ナローキャスト送信に必要な条件を満たしていません",
                        "action": "ターゲット数、アカウント種別、プランを確認してください",
                        "retry": False,
                        "code": "NARROWCAST_INSUFFICIENT_TARGET",
                        "doc_url": "https://developers.line.biz/ja/reference/messaging-api/#send-narrowcast-message",
                        "solutions": [
                            "友だち数の確認（最低100人以上推奨）",
                            "プランのアップグレード",
                            "オーディエンス設定の見直し",
                        ],
                    },
                },
            },
            # 2. オーディエンス管理
            "audience": {
                "audience_create": {
                    400: {
                        "category": ErrorCategory.AUDIENCE_ERROR,
                        "description": "オーディエンスグループの作成に失敗しました",
                        "action": "オーディエンス名（120文字以内）、説明、ユーザーIDリストを確認してください",
                        "retry": False,
                        "code": "AUDIENCE_CREATE_ERROR",
                        "doc_url": "https://developers.line.biz/ja/reference/messaging-api/#create-upload-audience-group",
                        "solutions": [
                            "オーディエンス名の文字数確認（120文字以内）",
                            "説明文の文字数確認（120文字以内）",
                            "ユーザーIDの形式確認",
                            "重複ユーザーIDの除去",
                        ],
                    },
                },
                "audience_get": {
                    404: {
                        "category": ErrorCategory.RESOURCE_NOT_FOUND,
                        "description": "オーディエンス情報が見つかりません",
                        "action": "正しいオーディエンスIDを指定してください",
                        "retry": False,
                        "code": "AUDIENCE_GET_NOT_FOUND",
                        "doc_url": "https://developers.line.biz/ja/reference/messaging-api/#get-audience-groups",
                        "solutions": [
                            "オーディエンスIDの確認",
                            "オーディエンスの存在確認",
                            "権限の確認",
                        ],
                    },
                },
            },
            # 3. 分析・統計
            "insights": {
                "insights_demographic": {
                    403: {
                        "category": ErrorCategory.PLAN_LIMITATION,
                        "description": "人口統計情報の利用権限がありません",
                        "action": "認証済アカウントまたはプレミアムアカウントが必要です",
                        "retry": False,
                        "code": "DEMOGRAPHIC_INSIGHTS_PERMISSION",
                        "doc_url": "https://developers.line.biz/ja/reference/messaging-api/#get-demographic",
                        "solutions": [
                            "アカウント認証の確認",
                            "最小フォロワー数の確認（通常1000人以上）",
                        ],
                    },
                },
            },
            # 4. リッチメニュー管理
            "rich_menu": {
                "rich_menu_image": {
                    413: {
                        "category": ErrorCategory.RICH_MENU_SIZE_ERROR,
                        "description": "リッチメニュー画像のサイズが大きすぎます",
                        "action": "画像ファイルサイズを1MB以下に圧縮してください",
                        "retry": False,
                        "code": "RICH_MENU_IMAGE_SIZE_EXCEEDED",
                        "doc_url": "https://developers.line.biz/ja/reference/messaging-api/#upload-rich-menu-image",
                        "solutions": ["画像サイズの圧縮", "推奨サイズへの調整"],
                    },
                },
                "rich_menu_link": {
                    400: {
                        "category": ErrorCategory.RICH_MENU_ERROR,
                        "description": "リッチメニューの設定・解除に失敗しました",
                        "action": "ユーザーID、リッチメニューIDを確認してください",
                        "retry": False,
                        "code": "RICH_MENU_LINK_ERROR",
                        "doc_url": "https://developers.line.biz/ja/reference/messaging-api/#link-rich-menu-to-user",
                        "solutions": [
                            "ユーザーIDの形式確認",
                            "リッチメニューIDの確認",
                            "リッチメニューの存在確認",
                        ],
                    },
                },
            },
            # 5. Webhook設定
            "webhook": {
                "webhook_settings": {
                    400: {
                        "category": ErrorCategory.WEBHOOK_ERROR,
                        "description": "無効なWebhook URLが指定されています",
                        "action": "HTTPS URLの形式、有効なドメイン、ポート443の使用、有効なSSL証明書を確認してください",
                        "retry": False,
                        "code": "INVALID_WEBHOOK_URL",
                        "doc_url": "https://developers.line.biz/ja/reference/messaging-api/#set-webhook-endpoint-url",
                        "solutions": [
                            "HTTPSスキームの使用",
                            "有効なドメイン名の確認",
                            "SSL証明書の有効性確認",
                            "ポート443での接続確認",
                        ],
                    },
                    404: {
                        "category": ErrorCategory.WEBHOOK_ERROR,
                        "description": "Webhook設定が見つかりません",
                        "action": "Webhook URLが設定されているか、チャネルが存在するかを確認してください",
                        "retry": False,
                        "code": "WEBHOOK_NOT_FOUND",
                        "doc_url": "https://developers.line.biz/ja/reference/messaging-api/#get-webhook-endpoint-information",
                        "solutions": [
                            "Webhook URLの設定確認",
                            "チャネルの存在確認",
                            "設定権限の確認",
                        ],
                    },
                },
            },
        }

    def _init_message_patterns(self):
        """エラーメッセージパターンマッピング初期化"""
        self.message_patterns = [
            (
                r"invalid reply token|reply token is invalid",
                ErrorCategory.INVALID_REPLY_TOKEN,
                False,
            ),
            (
                r"invalid signature",
                ErrorCategory.INVALID_SIGNATURE,
                False,
            ),
            (
                r"invalid token|invalid access token",
                ErrorCategory.INVALID_TOKEN,
                False,
            ),
            (r"monthly limit", ErrorCategory.QUOTA_EXCEEDED, False),
            (
                r"request body error",
                ErrorCategory.INVALID_REQUEST_BODY,
                False,
            ),
            (
                r"plan subscription required|subscription required|plan limitation",
                ErrorCategory.PLAN_LIMITATION,
                False,
            ),
            (
                r"not authorized|unauthorized|invalid channel access token",
                ErrorCategory.AUTH_ERROR,
                False,
            ),
            (
                r"too many requests|rate limit exceeded",
                ErrorCategory.RATE_LIMIT,
                True,
            ),
            (
                r"quota exceeded",
                ErrorCategory.QUOTA_EXCEEDED,
                False,
            ),
            (
                r"invalid user id|user not found",
                ErrorCategory.USER_NOT_FOUND,
                False,
            ),
            (
                r"invalid message|message format|invalid json",
                ErrorCategory.INVALID_JSON,
                False,
            ),
            (
                r"invalid webhook|webhook url",
                ErrorCategory.WEBHOOK_ERROR,
                False,
            ),
            (
                r"feature not available|not supported",
                ErrorCategory.PLAN_LIMITATION,
                False,
            ),
        ]

    def _init_error_details(self):
        """エラーカテゴリ別詳細情報初期化"""
        self.error_details = {
            ErrorCategory.AUTH_ERROR: {
                "description": "認証に失敗しました。チャネルアクセストークンが無効または期限切れです。",
                "action": "有効なチャネルアクセストークンを取得して再設定してください。",
                "doc_url": "https://developers.line.biz/ja/docs/basics/channel-access-token/",
            },
            ErrorCategory.INVALID_TOKEN: {
                "description": "指定されたトークンが無効です。",
                "action": "正しいトークンを使用するか、新しいトークンを発行してください。",
                "doc_url": "https://developers.line.biz/ja/docs/basics/channel-access-token/",
            },
            ErrorCategory.INVALID_REPLY_TOKEN: {
                "description": "返信トークンが無効です。",
                "action": "正しい返信トークンを使用してください。返信トークンは1回限り有効です。",
                "doc_url": "https://developers.line.biz/ja/reference/messaging-api/#reply-message",
            },
            ErrorCategory.MESSAGE_SEND_FAILED: {
                "description": "メッセージの送信に失敗しました。",
                "action": "送信先の確認やメッセージ内容の見直しを行ってください。",
                "doc_url": "https://developers.line.biz/ja/docs/messaging-api/sending-messages/",
            },
            ErrorCategory.WEBHOOK_ERROR: {
                "description": "Webhook処理でエラーが発生しました。",
                "action": "WebhookエンドポイントとHTTPS設定を確認してください。",
                "doc_url": "https://developers.line.biz/ja/reference/messaging-api/#webhook",
            },
            ErrorCategory.RATE_LIMIT: {
                "description": "APIの呼び出し回数が制限を超えました。",
                "action": "レート制限の回復を待ってから再試行してください。",
                "doc_url": "https://developers.line.biz/ja/reference/messaging-api/#rate-limits",
            },
            ErrorCategory.SERVER_ERROR: {
                "description": "LINEサーバーで内部エラーが発生しました。",
                "action": "しばらく時間をおいてから再試行してください。",
                "doc_url": "https://developers.line.biz/ja/support/",
            },
            ErrorCategory.ACCESS_DENIED: {
                "description": "アクセスが拒否されました。",
                "action": "適切な権限を取得してから再試行してください。",
                "doc_url": "https://developers.line.biz/ja/docs/line-developers-console/",
            },
            ErrorCategory.USER_BLOCKED: {
                "description": "ユーザーにブロックされているため、プロフィール情報にアクセスできません。",
                "action": "ブロックされたユーザーの情報は取得できません。他のユーザーで再試行してください。",
                "doc_url": "https://developers.line.biz/ja/reference/messaging-api/#get-profile",
            },
            ErrorCategory.PLAN_LIMITATION: {
                "description": "現在のプランでは利用できない機能です。",
                "action": "プランのアップグレードまたは代替手段を検討してください。",
                "doc_url": "https://www.lycbiz.com/jp/service/line-official-account/plan/",
            },
            ErrorCategory.RESOURCE_NOT_FOUND: {
                "description": "指定されたリソースが見つかりません。",
                "action": "正しいリソースIDを指定してください。",
                "doc_url": "https://developers.line.biz/ja/reference/messaging-api/",
            },
            ErrorCategory.AUDIENCE_ERROR: {
                "description": "オーディエンス処理でエラーが発生しました。",
                "action": "オーディエンスの設定を確認してください。",
                "doc_url": "https://developers.line.biz/ja/reference/messaging-api/#audience-management",
            },
            ErrorCategory.RICH_MENU_ERROR: {
                "description": "リッチメニューの処理でエラーが発生しました。",
                "action": "リッチメニューの設定内容を確認してください。",
                "doc_url": "https://developers.line.biz/ja/docs/messaging-api/using-rich-menus/",
            },
            ErrorCategory.RICH_MENU_SIZE_ERROR: {
                "description": "リッチメニューのサイズまたは形式に問題があります。",
                "action": "リッチメニューの画像サイズと形式を確認してください。",
                "doc_url": "https://developers.line.biz/ja/docs/messaging-api/using-rich-menus/#uploading-rich-menu-images",
            },
            ErrorCategory.PAYLOAD_TOO_LARGE: {
                "description": "リクエストのサイズが上限を超えています。",
                "action": "リクエストサイズを2MB以下に削減してください。",
                "doc_url": "https://developers.line.biz/ja/reference/messaging-api/#common-specifications",
            },
            ErrorCategory.UNKNOWN: {
                "description": "不明なエラーが発生しました。",
                "action": "エラー詳細を確認し、必要に応じてサポートに連絡してください。",
                "doc_url": "https://developers.line.biz/ja/support/",
            },
        }

    def get_endpoint_error_info(
        self, endpoint: str, status_code: int
    ) -> Optional[Tuple[ErrorCategory, None, bool]]:
        """
        階層構造エンドポイント別エラー情報取得

        Args:
            endpoint: エンドポイント（例: "message.message_push" または "message_push"）
            status_code: HTTPステータスコード

        Returns:
            (ErrorCategory, None, is_retryable) または None
        """
        # 階層構造での検索（例: "message.message_push"）
        if "." in endpoint:
            parent, child = endpoint.split(".", 1)
            mapping = self.endpoint_status_mappings.get(parent, {}).get(child, {})
        else:
            # 後方互換性: フラット構造での検索
            for parent_mapping in self.endpoint_status_mappings.values():
                for child_key, child_mapping in parent_mapping.items():
                    if child_key == endpoint:
                        mapping = child_mapping
                        break
                else:
                    continue
                break
            else:
                return None

        error_info = mapping.get(status_code)
        if error_info:
            return (error_info["category"], None, error_info["retry"])
        return None

    def get_endpoint_error_details(
        self, endpoint: str, status_code: int
    ) -> Optional[Dict]:
        """
        階層構造エンドポイント別詳細エラー情報取得

        Args:
            endpoint: エンドポイント（例: "message.message_push"）
            status_code: HTTPステータスコード

        Returns:
            詳細エラー情報辞書 または None
        """
        # 階層構造での検索
        if "." in endpoint:
            parent, child = endpoint.split(".", 1)
            mapping = self.endpoint_status_mappings.get(parent, {}).get(child, {})
        else:
            # 後方互換性: フラット構造での検索
            for parent_mapping in self.endpoint_status_mappings.values():
                for child_key, child_mapping in parent_mapping.items():
                    if child_key == endpoint:
                        mapping = child_mapping
                        break
                else:
                    continue
                break
            else:
                return None

        return mapping.get(status_code)

    def analyze_error(
        self,
        status_code: int,
        message: str,
        endpoint: Optional[str] = None,
    ) -> Tuple[ErrorCategory, None, bool]:
        """
        エラーを分析してカテゴリ、重要度、リトライ可能性を返す

        Args:
            status_code: HTTPステータスコード
            message: エラーメッセージ
            endpoint: エンドポイント種別

        Returns:
            (ErrorCategory, None, is_retryable)
        """
        # 1. エンドポイント固有の詳細情報
        if endpoint:
            endpoint_result = self.get_endpoint_error_info(endpoint, status_code)
            if endpoint_result:
                return endpoint_result

        # 1.5. APIパターン特有のエラー判定
        if endpoint and status_code and message:
            api_specific_result = self._analyze_api_specific_error(
                endpoint, status_code, message
            )
            if api_specific_result:
                return api_specific_result

        # 2. 基本HTTPステータスコード
        status_result = self.status_code_mappings.get(
            status_code, (ErrorCategory.UNKNOWN, False)
        )

        # 4. エラーメッセージパターンマッチング
        if message:
            for pattern, category, retryable in self.message_patterns:
                if re.search(pattern, message.lower()):
                    # ステータスコードでリトライ可能性を上書き
                    final_retryable = retryable or status_result[1]
                    return (category, None, final_retryable)

        return (status_result[0], None, status_result[1])

    def _analyze_api_specific_error(
        self, endpoint: str, status_code: int, message: str
    ) -> Optional[Tuple[ErrorCategory, None, bool]]:
        """APIパターン特有のエラー分析"""

        # ユーザープロフィール取得の場合
        if "user" in endpoint and "profile" in endpoint:
            if status_code == 404:
                # より具体的なエラーメッセージがある場合
                if "user not found" in message.lower():
                    return (ErrorCategory.USER_NOT_FOUND, None, False)
                # "Not found"メッセージの場合、ブロックされている可能性が高い
                elif "not found" in message.lower():
                    return (ErrorCategory.USER_BLOCKED, None, False)

        # メッセージ送信の場合
        elif "message" in endpoint:
            if status_code == 404:
                # より具体的なメッセージを優先
                if "user not found" in message.lower():
                    return (ErrorCategory.USER_NOT_FOUND, None, False)
                # メッセージ送信での404は通常ユーザーブロックの可能性
                elif "not found" in message.lower():
                    return (ErrorCategory.USER_BLOCKED, None, False)

        # Webhook設定の場合
        elif "webhook" in endpoint:
            if status_code == 404:
                if "not found" in message.lower():
                    return (ErrorCategory.WEBHOOK_ERROR, None, False)

        return None

    def get_error_details(self, category: ErrorCategory) -> Dict[str, str]:
        """エラーカテゴリの詳細情報を取得"""
        return self.error_details.get(
            category, self.error_details[ErrorCategory.UNKNOWN]
        )

    def get_error_info_by_status(
        self, status_code: int
    ) -> Tuple[ErrorCategory, None, bool]:
        """HTTPステータスコードによるエラー情報取得"""
        category, is_retryable = self.status_code_mappings.get(
            status_code, (ErrorCategory.UNKNOWN, False)
        )
        return (category, None, is_retryable)

    def get_error_info_by_message(
        self, message: str
    ) -> Optional[Tuple[ErrorCategory, None, bool]]:
        """エラーメッセージパターンによるエラー情報取得"""
        if not message:
            return None

        for pattern, category, retryable in self.message_patterns:
            if re.search(pattern, message.lower()):
                return (category, None, retryable)

        return None
