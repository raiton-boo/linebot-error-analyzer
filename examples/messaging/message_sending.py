"""
LINE Bot メッセージ送信エラーハンドリング例

このファイルでは、Reply API、Push API、Multicast APIを使った
メッセージ送信時のエラーハンドリングパターンを示します。

注意：このファイル内のerror辞書は、実際のLINE APIで発生する可能性のあるエラーパターンを
示すためのサンプルです。実際のAPIエラーは例外オブジェクトから取得されます。
このファイルは複雑なデモ用実装です。シンプルな実装は simple_message_sending.py を参照してください。
"""

import sys
import os
import json
import time
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import hashlib
import hmac
import base64

# プロジェクトルートを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from linebot_error_analyzer import LineErrorAnalyzer


class MessageSender:
    """LINE メッセージ送信クラス（エラーハンドリング付き）"""

    def __init__(
        self, channel_access_token: str, analyzer: Optional[LineErrorAnalyzer] = None
    ):
        self.channel_access_token = channel_access_token
        self.analyzer = analyzer or LineErrorAnalyzer()
        self.base_url = "https://api.line.me/v2/bot"
        self.send_history = []
        self.error_log = []

    def reply_message(
        self, reply_token: str, messages: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Reply APIを使用したメッセージ送信

        Args:
            reply_token: リプライトークン
            messages: 送信するメッセージのリスト

        Returns:
            Dict[str, Any]: 送信結果とエラー情報
        """
        result = {"success": False, "errors": [], "reply_token": reply_token}

        try:
            # 1. reply_tokenの検証
            if not reply_token:
                # 実際のLINE APIで発生する可能性のあるエラーパターン（サンプル）
                error_data = {
                    "status_code": 400,
                    "message": "Invalid reply token: empty or None",
                    "endpoint": "reply",
                }
                analysis = self.analyzer.analyze(error_data)
                result["errors"].append(
                    {
                        "type": "リプライトークンエラー",
                        "message": "リプライトークンが指定されていません",
                        "analysis": analysis,
                        "recommendations": [
                            "Webhookから正しくreply_tokenを取得してください",
                            "トークンが空文字列やNoneでないことを確認してください",
                        ],
                    }
                )
                return result

            # 2. 基本的なメッセージ検証
            validation_result = self._validate_messages(messages)
            if not validation_result["valid"]:
                result["errors"].extend(validation_result["errors"])
                return result

            # 3. Reply API制限のチェック
            if len(messages) > 5:
                # 実際のLINE APIで発生する可能性のあるエラーパターン（サンプル）
                error_data = {
                    "status_code": 400,
                    "message": f"Reply API allows maximum 5 messages, got {len(messages)}",
                    "endpoint": "reply",
                }
                analysis = self.analyzer.analyze(error_data)
                result["errors"].append(
                    {
                        "type": "メッセージ数制限エラー",
                        "message": f"Reply APIは最大5件までのメッセージ送信が可能です（送信しようとした件数: {len(messages)}）",
                        "analysis": analysis,
                        "recommendations": [
                            "メッセージを5件以下に分割してください",
                            "大量送信が必要な場合は、Push APIの使用を検討してください",
                        ],
                    }
                )
                return result

            # 4. reply_tokenの有効期限チェック（シミュレーション）
            if self._simulate_expired_reply_token(reply_token):
                # 実際のLINE APIで発生する可能性のあるエラーパターン（サンプル）
                error_data = {
                    "status_code": 400,
                    "message": "Reply token has expired",
                    "endpoint": "reply",
                }
                analysis = self.analyzer.analyze(error_data)
                result["errors"].append(
                    {
                        "type": "トークン有効期限エラー",
                        "message": "リプライトークンの有効期限が切れています",
                        "analysis": analysis,
                        "recommendations": [
                            "Webhookイベント受信後、1分以内にReply APIを呼び出してください",
                            "遅延処理が必要な場合は、Push APIの使用を検討してください",
                        ],
                    }
                )
                return result

            # 5. アクセストークンの検証
            if not self._validate_access_token():
                # 実際のLINE APIで発生する可能性のあるエラーパターン（サンプル）
                error_data = {
                    "status_code": 401,
                    "message": "Invalid channel access token",
                    "endpoint": "reply",
                }
                analysis = self.analyzer.analyze(error_data)
                result["errors"].append(
                    {
                        "type": "認証エラー",
                        "message": "無効なチャンネルアクセストークンです",
                        "analysis": analysis,
                        "recommendations": [
                            "LINE Developers Consoleでトークンを確認してください",
                            "トークンが正しく設定されているか確認してください",
                        ],
                    }
                )
                return result

            # 6. 実際の送信処理をシミュレート
            send_result = self._simulate_reply_api_call(reply_token, messages)
            if not send_result["success"]:
                result["errors"].extend(send_result["errors"])
                return result

            result["success"] = True
            result["message"] = "メッセージを正常に送信しました"
            self._log_send_history("reply", reply_token, messages, result)

        except Exception as e:
            # 実際のLINE APIで発生する可能性のあるエラーパターン（サンプル）
            error_data = {
                "status_code": 500,
                "message": str(e),
                "endpoint": "reply",
            }
            analysis = self.analyzer.analyze(error_data)
            result["errors"].append(
                {
                    "type": "予期しないエラー",
                    "message": f"予期しないエラーが発生しました: {str(e)}",
                    "analysis": analysis,
                    "recommendations": [
                        "エラーログを確認してください",
                        "一時的な問題の可能性があります。しばらく待ってから再試行してください",
                    ],
                }
            )

        return result

    def push_message(self, to: str, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Push APIを使用したメッセージ送信

        Args:
            to: 送信先ユーザーID、グループID、ルームID
            messages: 送信するメッセージのリスト

        Returns:
            Dict[str, Any]: 送信結果とエラー情報
        """
        result = {"success": False, "errors": [], "to": to}

        try:
            # 1. 送信先の検証
            if not to:
                # 実際のLINE APIで発生する可能性のあるエラーパターン（サンプル）
                error_data = {
                    "status_code": 400,
                    "message": "Missing 'to' parameter",
                    "endpoint": "push",
                }
                analysis = self.analyzer.analyze(error_data)
                result["errors"].append(
                    {
                        "type": "送信先エラー",
                        "message": "送信先が指定されていません",
                        "analysis": analysis,
                        "recommendations": [
                            "有効なユーザーID、グループID、またはルームIDを指定してください",
                        ],
                    }
                )
                return result

            # 2. 基本的なメッセージ検証
            validation_result = self._validate_messages(messages)
            if not validation_result["valid"]:
                result["errors"].extend(validation_result["errors"])
                return result

            # 3. Push API制限のチェック
            if len(messages) > 5:
                # 実際のLINE APIで発生する可能性のあるエラーパターン（サンプル）
                error_data = {
                    "status_code": 400,
                    "message": f"Push API allows maximum 5 messages, got {len(messages)}",
                    "endpoint": "push",
                }
                analysis = self.analyzer.analyze(error_data)
                result["errors"].append(
                    {
                        "type": "メッセージ数制限エラー",
                        "message": f"Push APIは最大5件までのメッセージ送信が可能です（送信しようとした件数: {len(messages)}）",
                        "analysis": analysis,
                        "recommendations": [
                            "メッセージを5件以下に分割してください",
                            "大量送信が必要な場合は、Multicast APIの使用を検討してください",
                        ],
                    }
                )
                return result

            # 4. レート制限のチェック
            if self._check_rate_limit("push"):
                # 実際のLINE APIで発生する可能性のあるエラーパターン（サンプル）
                error_data = {
                    "status_code": 429,
                    "message": "Rate limit exceeded",
                    "endpoint": "push",
                }
                analysis = self.analyzer.analyze(error_data)
                result["errors"].append(
                    {
                        "type": "レート制限エラー",
                        "message": "APIの呼び出し制限に達しました",
                        "analysis": analysis,
                        "recommendations": [
                            "しばらく待ってから再試行してください",
                            "送信頻度を調整してください",
                        ],
                    }
                )
                return result

            # 5. ユーザーの状態確認
            user_status = self._check_user_status(to)
            if not user_status["can_receive"]:
                # 実際のLINE APIで発生する可能性のあるエラーパターン（サンプル）
                error_data = {
                    "status_code": 403,
                    "message": f"User blocked the bot or left the group: {to}",
                    "endpoint": "push",
                }
                analysis = self.analyzer.analyze(error_data)
                result["errors"].append(
                    {
                        "type": "送信先状態エラー",
                        "message": user_status["reason"],
                        "analysis": analysis,
                        "recommendations": [
                            "ユーザーがブロックを解除するまで送信できません",
                            "グループから退出した場合は、再参加が必要です",
                        ],
                    }
                )
                return result

            # 6. 実際の送信処理をシミュレート
            send_result = self._simulate_push_api_call(to, messages)
            if not send_result["success"]:
                result["errors"].extend(send_result["errors"])
                return result

            result["success"] = True
            result["message"] = "メッセージを正常に送信しました"
            self._log_send_history("push", to, messages, result)

        except Exception as e:
            # 実際のLINE APIで発生する可能性のあるエラーパターン（サンプル）
            error_data = {
                "status_code": 500,
                "message": str(e),
                "endpoint": "push",
            }
            analysis = self.analyzer.analyze(error_data)
            result["errors"].append(
                {
                    "type": "予期しないエラー",
                    "message": f"予期しないエラーが発生しました: {str(e)}",
                    "analysis": analysis,
                    "recommendations": [
                        "エラーログを確認してください",
                        "一時的な問題の可能性があります。しばらく待ってから再試行してください",
                    ],
                }
            )

        return result

    def multicast_message(
        self, to: List[str], messages: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Multicast APIを使用したメッセージ送信

        Args:
            to: 送信先ユーザーIDのリスト
            messages: 送信するメッセージのリスト

        Returns:
            Dict[str, Any]: 送信結果とエラー情報
        """
        result = {"success": False, "errors": [], "to": to}

        try:
            # 1. 送信先リストの検証
            if not to or not isinstance(to, list):
                # 実際のLINE APIで発生する可能性のあるエラーパターン（サンプル）
                error_data = {
                    "status_code": 400,
                    "message": "Invalid 'to' parameter: must be a non-empty list",
                    "endpoint": "multicast",
                }
                analysis = self.analyzer.analyze(error_data)
                result["errors"].append(
                    {
                        "type": "送信先エラー",
                        "message": "送信先リストが無効です",
                        "analysis": analysis,
                        "recommendations": [
                            "送信先は空でないリストで指定してください",
                            "各要素は有効なユーザーIDである必要があります",
                        ],
                    }
                )
                return result

            # 2. 送信先数の制限チェック
            if len(to) > 500:
                # 実際のLINE APIで発生する可能性のあるエラーパターン（サンプル）
                error_data = {
                    "status_code": 400,
                    "message": f"Multicast API allows maximum 500 recipients, got {len(to)}",
                    "endpoint": "multicast",
                }
                analysis = self.analyzer.analyze(error_data)
                result["errors"].append(
                    {
                        "type": "送信先数制限エラー",
                        "message": f"Multicast APIは最大500人までの送信が可能です（送信しようとした人数: {len(to)}）",
                        "analysis": analysis,
                        "recommendations": [
                            "送信先を500人以下に分割してください",
                            "複数回に分けて送信してください",
                        ],
                    }
                )
                return result

            # 3. 基本的なメッセージ検証
            validation_result = self._validate_messages(messages)
            if not validation_result["valid"]:
                result["errors"].extend(validation_result["errors"])
                return result

            # 4. Multicast API制限のチェック
            if len(messages) > 5:
                # 実際のLINE APIで発生する可能性のあるエラーパターン（サンプル）
                error_data = {
                    "status_code": 400,
                    "message": f"Multicast API allows maximum 5 messages, got {len(messages)}",
                    "endpoint": "multicast",
                }
                analysis = self.analyzer.analyze(error_data)
                result["errors"].append(
                    {
                        "type": "メッセージ数制限エラー",
                        "message": f"Multicast APIは最大5件までのメッセージ送信が可能です（送信しようとした件数: {len(messages)}）",
                        "analysis": analysis,
                        "recommendations": [
                            "メッセージを5件以下に分割してください",
                        ],
                    }
                )
                return result

            # 5. 各送信先の検証
            invalid_recipients = []
            blocked_recipients = []
            for user_id in to:
                if not user_id or not isinstance(user_id, str):
                    invalid_recipients.append(user_id)
                    continue

                user_status = self._check_user_status(user_id)
                if not user_status["can_receive"]:
                    blocked_recipients.append(
                        {"user_id": user_id, "reason": user_status["reason"]}
                    )

            if invalid_recipients:
                # 実際のLINE APIで発生する可能性のあるエラーパターン（サンプル）
                error_data = {
                    "status_code": 400,
                    "message": f"Invalid user IDs found: {invalid_recipients}",
                    "endpoint": "multicast",
                }
                analysis = self.analyzer.analyze(error_data)
                result["errors"].append(
                    {
                        "type": "無効な送信先エラー",
                        "message": f"無効なユーザーIDが含まれています: {invalid_recipients}",
                        "analysis": analysis,
                        "recommendations": [
                            "全ての送信先が有効なユーザーIDであることを確認してください",
                        ],
                    }
                )

            if blocked_recipients:
                # 実際のLINE APIで発生する可能性のあるエラーパターン（サンプル）
                error_data = {
                    "status_code": 200,  # Multicastは部分成功でも200を返す
                    "message": f"Some recipients cannot receive messages: {len(blocked_recipients)} users",
                    "endpoint": "multicast",
                }
                analysis = self.analyzer.analyze(error_data)
                result["errors"].append(
                    {
                        "type": "送信先状態警告",
                        "message": f"{len(blocked_recipients)}人のユーザーに送信できませんでした",
                        "analysis": analysis,
                        "blocked_users": blocked_recipients,
                        "recommendations": [
                            "ブロックされたユーザーへの送信は失敗します",
                            "有効なユーザーのみに送信されます",
                        ],
                    }
                )

            # 6. 実際の送信処理をシミュレート
            send_result = self._simulate_multicast_api_call(to, messages)
            if not send_result["success"]:
                result["errors"].extend(send_result["errors"])
                return result

            result["success"] = True
            result["message"] = "メッセージを正常に送信しました"
            result["sent_count"] = len(to) - len(blocked_recipients)
            result["failed_count"] = len(blocked_recipients)
            self._log_send_history("multicast", to, messages, result)

        except Exception as e:
            # 実際のLINE APIで発生する可能性のあるエラーパターン（サンプル）
            error_data = {
                "status_code": 500,
                "message": str(e),
                "endpoint": "multicast",
            }
            analysis = self.analyzer.analyze(error_data)
            result["errors"].append(
                {
                    "type": "予期しないエラー",
                    "message": f"予期しないエラーが発生しました: {str(e)}",
                    "analysis": analysis,
                    "recommendations": [
                        "エラーログを確認してください",
                        "一時的な問題の可能性があります。しばらく待ってから再試行してください",
                    ],
                }
            )

        return result

    def _validate_messages(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        メッセージの基本検証

        Args:
            messages: 検証するメッセージのリスト

        Returns:
            Dict[str, Any]: 検証結果
        """
        result = {"valid": True, "errors": []}

        if not messages:
            # 実際のLINE APIで発生する可能性のあるエラーパターン（サンプル）
            error_data = {
                "status_code": 400,
                "message": "Messages cannot be empty",
                "endpoint": "validation",
            }
            analysis = self.analyzer.analyze(error_data)
            result["errors"].append(
                {
                    "type": "メッセージ空エラー",
                    "message": "送信するメッセージが指定されていません",
                    "analysis": analysis,
                    "recommendations": ["最低1つのメッセージを指定してください"],
                }
            )
            result["valid"] = False
            return result

        for i, message in enumerate(messages):
            if not isinstance(message, dict):
                # 実際のLINE APIで発生する可能性のあるエラーパターン（サンプル）
                error_data = {
                    "status_code": 400,
                    "message": f"Message at index {i} is not a dictionary",
                    "endpoint": "validation",
                }
                analysis = self.analyzer.analyze(error_data)
                result["errors"].append(
                    {
                        "type": "メッセージ形式エラー",
                        "message": f"メッセージ{i+1}の形式が正しくありません",
                        "analysis": analysis,
                        "recommendations": ["メッセージは辞書形式で指定してください"],
                    }
                )
                result["valid"] = False
                continue

            if "type" not in message:
                # 実際のLINE APIで発生する可能性のあるエラーパターン（サンプル）
                error_data = {
                    "status_code": 400,
                    "message": f"Message at index {i} missing 'type' field",
                    "endpoint": "validation",
                }
                analysis = self.analyzer.analyze(error_data)
                result["errors"].append(
                    {
                        "type": "メッセージタイプエラー",
                        "message": f"メッセージ{i+1}にtypeが指定されていません",
                        "analysis": analysis,
                        "recommendations": [
                            "メッセージタイプ（text, image, video等）を指定してください"
                        ],
                    }
                )
                result["valid"] = False
                continue

            # テキストメッセージの詳細検証
            if message.get("type") == "text":
                text_content = message.get("text", "")
                if len(text_content) > 5000:
                    # 実際のLINE APIで発生する可能性のあるエラーパターン（サンプル）
                    error_data = {
                        "status_code": 400,
                        "message": f"Text message at index {i} exceeds 5000 characters: {len(text_content)}",
                        "endpoint": "validation",
                    }
                    analysis = self.analyzer.analyze(error_data)
                    result["errors"].append(
                        {
                            "type": "テキスト長制限エラー",
                            "message": f"メッセージ{i+1}のテキストが長すぎます（{len(text_content)}文字）",
                            "analysis": analysis,
                            "recommendations": [
                                "テキストメッセージは5000文字以内にしてください",
                                "長い文章は複数のメッセージに分割してください",
                            ],
                        }
                    )
                    result["valid"] = False

        return result

    def _simulate_expired_reply_token(self, reply_token: str) -> bool:
        """
        リプライトークンの有効期限をシミュレート

        Args:
            reply_token: リプライトークン

        Returns:
            bool: 有効期限切れかどうか
        """
        # シミュレーション: 特定の文字列パターンで有効期限切れをシミュレート
        return reply_token.endswith("_expired")

    def _validate_access_token(self) -> bool:
        """
        アクセストークンの有効性を検証

        Returns:
            bool: トークンが有効かどうか
        """
        # シミュレーション: 基本的な形式チェック
        if not self.channel_access_token:
            return False
        if len(self.channel_access_token) < 100:  # 実際のトークンはもっと長い
            return False
        return True

    def _check_rate_limit(self, api_type: str) -> bool:
        """
        レート制限をチェック

        Args:
            api_type: API種別（reply, push, multicast）

        Returns:
            bool: レート制限に達しているかどうか
        """
        # シミュレーション: 実際の実装では、送信履歴から判定
        recent_sends = [
            entry
            for entry in self.send_history
            if entry["api_type"] == api_type
            and (datetime.now() - entry["timestamp"]).seconds < 60
        ]

        # API種別ごとの制限（例：1分間に10回まで）
        limits = {"reply": 10, "push": 10, "multicast": 5}
        return len(recent_sends) >= limits.get(api_type, 10)

    def _check_user_status(self, user_id: str) -> Dict[str, Any]:
        """
        ユーザーの状態をチェック

        Args:
            user_id: ユーザーID

        Returns:
            Dict[str, Any]: ユーザー状態情報
        """
        # シミュレーション: 特定の文字列パターンで状態をシミュレート
        if user_id.endswith("_blocked"):
            return {
                "can_receive": False,
                "reason": "ユーザーがボットをブロックしています",
            }
        elif user_id.endswith("_left"):
            return {
                "can_receive": False,
                "reason": "ユーザーがグループから退出しています",
            }
        else:
            return {"can_receive": True, "reason": "正常"}

    def _simulate_reply_api_call(
        self, reply_token: str, messages: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Reply API呼び出しをシミュレート

        Args:
            reply_token: リプライトークン
            messages: メッセージリスト

        Returns:
            Dict[str, Any]: API呼び出し結果
        """
        # シミュレーション: 実際の実装ではHTTPリクエストを送信
        result = {"success": True, "errors": []}

        # ネットワークエラーのシミュレーション
        if reply_token.endswith("_network_error"):
            # 実際のLINE APIで発生する可能性のあるエラーパターン（サンプル）
            error_data = {
                "status_code": 500,
                "message": "Network timeout",
                "endpoint": "reply",
            }
            analysis = self.analyzer.analyze(error_data)
            result["errors"].append(
                {
                    "type": "ネットワークエラー",
                    "message": "ネットワークタイムアウトが発生しました",
                    "analysis": analysis,
                    "recommendations": [
                        "しばらく待ってから再試行してください",
                        "ネットワーク接続を確認してください",
                    ],
                }
            )
            result["success"] = False

        return result

    def _simulate_push_api_call(
        self, to: str, messages: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Push API呼び出しをシミュレート

        Args:
            to: 送信先
            messages: メッセージリスト

        Returns:
            Dict[str, Any]: API呼び出し結果
        """
        result = {"success": True, "errors": []}

        # クォータ制限のシミュレーション
        if to.endswith("_quota_exceeded"):
            # 実際のLINE APIで発生する可能性のあるエラーパターン（サンプル）
            error_data = {
                "status_code": 429,
                "message": "Monthly quota exceeded",
                "endpoint": "push",
            }
            analysis = self.analyzer.analyze(error_data)
            result["errors"].append(
                {
                    "type": "クォータ制限エラー",
                    "message": "月間送信制限に達しました",
                    "analysis": analysis,
                    "recommendations": [
                        "翌月まで待つか、追加クォータの購入を検討してください",
                        "送信対象を絞り込んでください",
                    ],
                }
            )
            result["success"] = False

        return result

    def _simulate_multicast_api_call(
        self, to: List[str], messages: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Multicast API呼び出しをシミュレート

        Args:
            to: 送信先リスト
            messages: メッセージリスト

        Returns:
            Dict[str, Any]: API呼び出し結果
        """
        result = {"success": True, "errors": []}

        # 部分失敗のシミュレーション
        failed_count = len([user_id for user_id in to if user_id.endswith("_blocked")])
        if failed_count > 0:
            # 実際のLINE APIで発生する可能性のあるエラーパターン（サンプル）
            error_data = {
                "status_code": 200,  # Multicastは部分成功でも200
                "message": f"Partial success: {failed_count} recipients failed",
                "endpoint": "multicast",
            }
            analysis = self.analyzer.analyze(error_data)
            result["errors"].append(
                {
                    "type": "部分送信エラー",
                    "message": f"{failed_count}人への送信に失敗しました",
                    "analysis": analysis,
                    "recommendations": [
                        "失敗した送信先を確認してください",
                        "有効な送信先のみに送信されました",
                    ],
                }
            )

        return result

    def _log_send_history(
        self,
        api_type: str,
        target: Union[str, List[str]],
        messages: List[Dict[str, Any]],
        result: Dict[str, Any],
    ):
        """
        送信履歴をログに記録

        Args:
            api_type: API種別
            target: 送信先
            messages: 送信したメッセージ
            result: 送信結果
        """
        history_entry = {
            "timestamp": datetime.now(),
            "api_type": api_type,
            "target": target,
            "message_count": len(messages),
            "success": result["success"],
            "error_count": len(result["errors"]),
        }
        self.send_history.append(history_entry)

        # エラーログも保存
        if result["errors"]:
            for error in result["errors"]:
                error_entry = {
                    "timestamp": datetime.now(),
                    "api_type": api_type,
                    "target": target,
                    "error_type": error["type"],
                    "error_message": error["message"],
                }
                self.error_log.append(error_entry)

    def get_send_statistics(self) -> Dict[str, Any]:
        """
        送信統計を取得

        Returns:
            Dict[str, Any]: 送信統計情報
        """
        stats = {
            "total_sends": len(self.send_history),
            "successful_sends": len([h for h in self.send_history if h["success"]]),
            "failed_sends": len([h for h in self.send_history if not h["success"]]),
            "total_errors": len(self.error_log),
            "api_usage": {},
            "error_types": {},
        }

        # API種別ごとの使用状況
        for entry in self.send_history:
            api_type = entry["api_type"]
            if api_type not in stats["api_usage"]:
                stats["api_usage"][api_type] = {"count": 0, "success": 0, "failed": 0}

            stats["api_usage"][api_type]["count"] += 1
            if entry["success"]:
                stats["api_usage"][api_type]["success"] += 1
            else:
                stats["api_usage"][api_type]["failed"] += 1

        # エラータイプごとの集計
        for error in self.error_log:
            error_type = error["error_type"]
            if error_type not in stats["error_types"]:
                stats["error_types"][error_type] = 0
            stats["error_types"][error_type] += 1

        return stats


def demonstrate_message_sending():
    """メッセージ送信のデモンストレーション"""
    print("LINE Bot メッセージ送信エラーハンドリングのデモンストレーション")
    print("=" * 70)

    # アナライザーを初期化
    analyzer = LineErrorAnalyzer()

    # メッセージ送信クラスを初期化
    sender = MessageSender("dummy_channel_access_token", analyzer)

    # テストメッセージ
    test_messages = [
        {"type": "text", "text": "こんにちは！"},
        {"type": "text", "text": "これはテストメッセージです。"},
    ]

    print("\n1. Reply API テスト")
    print("-" * 30)

    # 正常なケース
    result = sender.reply_message("valid_reply_token", test_messages)
    print(f"正常ケース: {'成功' if result['success'] else '失敗'}")
    if result["errors"]:
        print(f"エラー数: {len(result['errors'])}")

    # エラーケース（有効期限切れ）
    result = sender.reply_message("expired_reply_token_expired", test_messages)
    print(f"有効期限切れケース: {'成功' if result['success'] else '失敗'}")
    if result["errors"]:
        print(f"エラー: {result['errors'][0]['message']}")

    print("\n2. Push API テスト")
    print("-" * 30)

    # 正常なケース
    result = sender.push_message("user123", test_messages)
    print(f"正常ケース: {'成功' if result['success'] else '失敗'}")

    # エラーケース（ユーザーブロック）
    result = sender.push_message("user123_blocked", test_messages)
    print(f"ブロックケース: {'成功' if result['success'] else '失敗'}")
    if result["errors"]:
        print(f"エラー: {result['errors'][0]['message']}")

    print("\n3. Multicast API テスト")
    print("-" * 30)

    # 正常なケース
    result = sender.multicast_message(["user1", "user2", "user3"], test_messages)
    print(f"正常ケース: {'成功' if result['success'] else '失敗'}")

    # 部分失敗ケース
    result = sender.multicast_message(
        ["user1", "user2_blocked", "user3_left"], test_messages
    )
    print(f"部分失敗ケース: {'成功' if result['success'] else '失敗'}")
    if "sent_count" in result:
        print(f"送信成功: {result['sent_count']}人, 失敗: {result['failed_count']}人")

    print("\n4. 送信統計")
    print("-" * 30)
    stats = sender.get_send_statistics()
    print(f"総送信回数: {stats['total_sends']}")
    print(f"成功回数: {stats['successful_sends']}")
    print(f"失敗回数: {stats['failed_sends']}")
    print(f"総エラー数: {stats['total_errors']}")

    print("\nAPI使用状況:")
    for api_type, usage in stats["api_usage"].items():
        print(
            f"  {api_type}: {usage['count']}回 (成功: {usage['success']}, 失敗: {usage['failed']})"
        )

    if stats["error_types"]:
        print("\nエラータイプ別集計:")
        for error_type, count in stats["error_types"].items():
            print(f"  {error_type}: {count}回")


if __name__ == "__main__":
    demonstrate_message_sending()
