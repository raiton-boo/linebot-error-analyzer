"""
LINE Bot Webhookイベント処理エラーハンドリング例

このファイルでは、LINE Webhookで受信するイベントの処理において
よく発生するエラーとその適切なハンドリング方法を示します。

注意：このファイル内のerror辞書は、実際のLINE APIで発生する可能性のあるエラーパターンを
示すためのサンプルです。実際のAPIエラーは例外オブジェクトから取得されます。
このファイルは複雑なデモ用実装です。シンプルな実装は simple_event_processing.py を参照してください。
"""

import sys
import os
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

# プロジェクトルートを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from line_bot_error_analyzer import LineErrorAnalyzer


class WebhookEventProcessor:
    """LINE Webhook イベント処理クラス（エラーハンドリング付き）"""

    def __init__(self, analyzer: Optional[LineErrorAnalyzer] = None):
        self.analyzer = analyzer or LineErrorAnalyzer()
        self.processed_events = []
        self.error_log = []

    def process_webhook_request(self, request_data: str) -> Dict[str, Any]:
        """
        Webhookリクエスト全体の処理

        Args:
            request_data: JSONリクエストボディ

        Returns:
            Dict: 処理結果と詳細情報
        """

        result = {
            "success": False,
            "processed_events": 0,
            "failed_events": 0,
            "errors": [],
            "recommendations": [],
        }

        try:
            # 1. JSON解析
            try:
                webhook_data = json.loads(request_data)
            except json.JSONDecodeError as e:
                # 予期しないエラー用のサンプルエラーデータ
                error_data = {
                    "status_code": 400,
                    "message": f"Invalid JSON format: {str(e)}",
                    "endpoint": "webhook.json_parsing",
                }
                analysis = self.analyzer.analyze(error_data)
                result["errors"].append(
                    {
                        "type": "JSON解析エラー",
                        "message": str(e),
                        "analysis": analysis,
                        "recommendations": [
                            "リクエストボディが有効なJSON形式か確認してください",
                            "文字エンコーディングがUTF-8か確認してください",
                            "Content-Typeヘッダーにapplication/jsonが設定されているか確認してください",
                        ],
                    }
                )
                return result

            # 2. 必須フィールドの確認
            if "events" not in webhook_data:
                # 予期しないエラー用のサンプルエラーデータ
                error_data = {
                    "status_code": 400,
                    "message": "Missing 'events' field in webhook data",
                    "endpoint": "webhook.field_validation",
                }
                analysis = self.analyzer.analyze(error_data)
                result["errors"].append(
                    {
                        "type": "必須フィールドエラー",
                        "message": "'events'フィールドが存在しません",
                        "analysis": analysis,
                        "recommendations": [
                            "LINE Platform からの正規のWebhookリクエストか確認してください",
                            "リクエストボディの構造を確認してください",
                        ],
                    }
                )
                return result

            # 3. イベント処理
            events = webhook_data.get("events", [])

            for event in events:
                event_result = self.process_single_event(event)

                if event_result["success"]:
                    result["processed_events"] += 1
                    self.processed_events.append(event_result)
                else:
                    result["failed_events"] += 1
                    result["errors"].extend(event_result["errors"])
                    self.error_log.append(event_result)

            # 4. 全体結果の判定
            if result["failed_events"] == 0:
                result["success"] = True

            return result

        except Exception as e:
            # 予期しないエラー用のサンプルエラーデータ
            # 実際のLINE APIで発生する可能性のあるエラーパターン（サンプル）
            error_data = {
                "status_code": 500,
                "message": f"Unexpected error in webhook processing: {str(e)}",
                "endpoint": "webhook.processing",
            }
            analysis = self.analyzer.analyze(error_data)
            result["errors"].append(
                {
                    "type": "予期しないエラー",
                    "message": str(e),
                    "analysis": analysis,
                    "recommendations": [
                        "アプリケーションログを詳しく確認してください",
                        "サーバーの状態とリソースを確認してください",
                    ],
                }
            )
            return result

    def process_single_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        単一イベントの処理

        Args:
            event: イベントデータ

        Returns:
            Dict: 処理結果
        """

        result = {
            "success": False,
            "event_type": event.get("type", "unknown"),
            "timestamp": datetime.now().isoformat(),
            "errors": [],
        }

        try:
            # 1. イベントタイプの確認
            event_type = event.get("type")
            if not event_type:
                # 予期しないエラー用のサンプルエラーデータ
                error_data = {
                    "status_code": 400,
                    "message": "Missing event type",
                    "endpoint": "webhook.event_validation",
                }
                analysis = self.analyzer.analyze(error_data)
                result["errors"].append(
                    {
                        "type": "イベントタイプエラー",
                        "message": "イベントタイプが指定されていません",
                        "analysis": analysis,
                    }
                )
                return result

            # 2. イベントタイプ別処理
            if event_type == "message":
                return self._process_message_event(event)
            elif event_type == "follow":
                return self._process_follow_event(event)
            elif event_type == "unfollow":
                return self._process_unfollow_event(event)
            elif event_type == "join":
                return self._process_join_event(event)
            elif event_type == "leave":
                return self._process_leave_event(event)
            elif event_type == "memberJoined":
                return self._process_member_joined_event(event)
            elif event_type == "memberLeft":
                return self._process_member_left_event(event)
            elif event_type == "postback":
                return self._process_postback_event(event)
            elif event_type == "beacon":
                return self._process_beacon_event(event)
            else:
                # 未対応のイベントタイプ
                result["success"] = True  # エラーではないが処理はスキップ
                result["message"] = f"未対応のイベントタイプ: {event_type}"
                return result

        except Exception as e:
            # 予期しないエラー用のサンプルエラーデータ
            # 実際のLINE APIで発生する可能性のあるエラーパターン（サンプル）
            error_data = {
                "status_code": 500,
                "message": f"Error processing {event_type} event: {str(e)}",
                "endpoint": f"webhook.event_{event_type}",
            }
            analysis = self.analyzer.analyze(error_data)
            result["errors"].append(
                {"type": "イベント処理エラー", "message": str(e), "analysis": analysis}
            )
            return result

    def _process_message_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """メッセージイベントの処理"""

        result = {
            "success": False,
            "event_type": "message",
            "timestamp": datetime.now().isoformat(),
            "errors": [],
        }

        try:
            # 必須フィールドチェック
            required_fields = ["replyToken", "source", "message"]
            for field in required_fields:
                if field not in event:
                    # 予期しないエラー用のサンプルエラーデータ
                    error_data = {
                        "status_code": 400,
                        "message": f"Missing required field: {field}",
                        "endpoint": "webhook.message_event",
                    }
                    analysis = self.analyzer.analyze(error_data)
                    result["errors"].append(
                        {
                            "type": "必須フィールドエラー",
                            "message": f"メッセージイベントに{field}フィールドがありません",
                            "analysis": analysis,
                        }
                    )
                    return result

            # リプライトークンの検証
            reply_token = event.get("replyToken")
            if not reply_token or reply_token == "00000000000000000000000000000000":
                # テストWebhookまたは無効なリプライトークン
                result["success"] = True
                result["message"] = (
                    "テストWebhookまたは無効なリプライトークンをスキップ"
                )
                return result

            # メッセージ内容の取得
            message = event.get("message", {})
            message_type = message.get("type")

            if not message_type:
                # 予期しないエラー用のサンプルエラーデータ
                error_data = {
                    "status_code": 400,
                    "message": "Missing message type",
                    "endpoint": "webhook.message_event",
                }
                analysis = self.analyzer.analyze(error_data)
                result["errors"].append(
                    {
                        "type": "メッセージタイプエラー",
                        "message": "メッセージタイプが指定されていません",
                        "analysis": analysis,
                    }
                )
                return result

            # ここで実際のメッセージ処理ロジックを実行
            # 例: テキストメッセージの処理
            if message_type == "text":
                text = message.get("text", "")
                print(f"📝 テキストメッセージ受信: {text}")

                # Echo機能の例
                result["response_message"] = f"受信しました: {text}"

            elif message_type == "image":
                print("🖼️ 画像メッセージ受信")
                result["response_message"] = "画像を受信しました"

            elif message_type == "sticker":
                print("😀 スタンプメッセージ受信")
                result["response_message"] = "スタンプありがとうございます！"

            else:
                print(f"❓ 未対応のメッセージタイプ: {message_type}")
                result["response_message"] = "未対応のメッセージタイプです"

            result["success"] = True
            result["reply_token"] = reply_token
            result["message_type"] = message_type

            return result

        except Exception as e:
            # 予期しないエラー用のサンプルエラーデータ
            # 実際のLINE APIで発生する可能性のあるエラーパターン（サンプル）
            error_data = {
                "status_code": 500,
                "message": f"Error in message event processing: {str(e)}",
                "endpoint": "webhook.message_event",
            }
            analysis = self.analyzer.analyze(error_data)
            result["errors"].append(
                {
                    "type": "メッセージ処理エラー",
                    "message": str(e),
                    "analysis": analysis,
                }
            )
            return result

    def _process_follow_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """フォローイベントの処理"""

        result = {
            "success": True,
            "event_type": "follow",
            "timestamp": datetime.now().isoformat(),
            "message": "新規フォローイベントを処理しました",
        }

        user_id = event.get("source", {}).get("userId")
        if user_id:
            print(f"👤 新規フォロー: {user_id}")
            result["user_id"] = user_id
            result["response_message"] = "フォローありがとうございます！"

        return result

    def _process_unfollow_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """アンフォローイベントの処理"""

        result = {
            "success": True,
            "event_type": "unfollow",
            "timestamp": datetime.now().isoformat(),
            "message": "アンフォローイベントを処理しました",
        }

        user_id = event.get("source", {}).get("userId")
        if user_id:
            print(f"👋 アンフォロー: {user_id}")
            result["user_id"] = user_id

        return result

    def _process_join_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """グループ参加イベントの処理"""

        result = {
            "success": True,
            "event_type": "join",
            "timestamp": datetime.now().isoformat(),
            "message": "グループ参加イベントを処理しました",
        }

        source = event.get("source", {})
        if source.get("type") == "group":
            group_id = source.get("groupId")
            print(f"🏢 グループ参加: {group_id}")
            result["group_id"] = group_id
            result["response_message"] = (
                "グループに参加しました！よろしくお願いします。"
            )

        return result

    def _process_leave_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """グループ退出イベントの処理"""

        result = {
            "success": True,
            "event_type": "leave",
            "timestamp": datetime.now().isoformat(),
            "message": "グループ退出イベントを処理しました",
        }

        source = event.get("source", {})
        if source.get("type") == "group":
            group_id = source.get("groupId")
            print(f"🚪 グループ退出: {group_id}")
            result["group_id"] = group_id

        return result

    def _process_member_joined_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """メンバー参加イベントの処理"""

        result = {
            "success": True,
            "event_type": "memberJoined",
            "timestamp": datetime.now().isoformat(),
            "message": "メンバー参加イベントを処理しました",
        }

        joined_members = event.get("joined", {}).get("members", [])
        user_ids = [member.get("userId") for member in joined_members]

        print(f"👥 メンバー参加: {len(user_ids)}人")
        result["joined_user_ids"] = user_ids
        result["response_message"] = f"{len(user_ids)}人のメンバーが参加しました！"

        return result

    def _process_member_left_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """メンバー退出イベントの処理"""

        result = {
            "success": True,
            "event_type": "memberLeft",
            "timestamp": datetime.now().isoformat(),
            "message": "メンバー退出イベントを処理しました",
        }

        left_members = event.get("left", {}).get("members", [])
        user_ids = [member.get("userId") for member in left_members]

        print(f"👋 メンバー退出: {len(user_ids)}人")
        result["left_user_ids"] = user_ids

        return result

    def _process_postback_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """ポストバックイベントの処理"""

        result = {
            "success": True,
            "event_type": "postback",
            "timestamp": datetime.now().isoformat(),
            "message": "ポストバックイベントを処理しました",
        }

        postback_data = event.get("postback", {}).get("data")
        if postback_data:
            print(f"🔄 ポストバック: {postback_data}")
            result["postback_data"] = postback_data
            result["response_message"] = f"ポストバック受信: {postback_data}"

        return result

    def _process_beacon_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """ビーコンイベントの処理"""

        result = {
            "success": True,
            "event_type": "beacon",
            "timestamp": datetime.now().isoformat(),
            "message": "ビーコンイベントを処理しました",
        }

        beacon = event.get("beacon", {})
        hwid = beacon.get("hwid")
        beacon_type = beacon.get("type")

        if hwid:
            print(f"📡 ビーコン検出: {hwid} (type: {beacon_type})")
            result["beacon_hwid"] = hwid
            result["beacon_type"] = beacon_type
            result["response_message"] = "ビーコンを検出しました"

        return result


def demo_webhook_processing():
    """Webhookイベント処理のデモ実行"""

    print("🚀 LINE Bot Webhookイベント処理デモ")
    print("=" * 60)

    processor = WebhookEventProcessor()

    # テストケース
    test_cases = [
        {
            "name": "正常なメッセージイベント",
            "data": json.dumps(
                {
                    "events": [
                        {
                            "type": "message",
                            "replyToken": "test-reply-token-123",
                            "source": {"type": "user", "userId": "test-user-123"},
                            "message": {"type": "text", "text": "Hello, Bot!"},
                        }
                    ]
                }
            ),
        },
        {"name": "不正なJSON", "data": "invalid json data"},
        {"name": "eventsフィールドなし", "data": json.dumps({"destination": "test"})},
        {
            "name": "必須フィールド不足",
            "data": json.dumps(
                {
                    "events": [
                        {
                            "type": "message",
                            # replyTokenなし
                            "source": {"type": "user", "userId": "test-user-123"},
                        }
                    ]
                }
            ),
        },
        {
            "name": "複数イベント（成功・失敗混在）",
            "data": json.dumps(
                {
                    "events": [
                        {
                            "type": "message",
                            "replyToken": "test-reply-token-1",
                            "source": {"type": "user", "userId": "test-user-1"},
                            "message": {"type": "text", "text": "正常メッセージ"},
                        },
                        {
                            "type": "follow",
                            "source": {"type": "user", "userId": "test-user-2"},
                        },
                        {
                            "type": "message",
                            # messageフィールドなし（エラー）
                            "replyToken": "test-reply-token-3",
                            "source": {"type": "user", "userId": "test-user-3"},
                        },
                    ]
                }
            ),
        },
    ]

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 テストケース {i}: {test_case['name']}")
        print("-" * 40)

        result = processor.process_webhook_request(test_case["data"])

        print(f"📊 処理結果:")
        print(f"   • 成功: {result['success']}")
        print(f"   • 処理済みイベント: {result['processed_events']}")
        print(f"   • 失敗イベント: {result['failed_events']}")

        if result["errors"]:
            print(f"❌ エラー詳細:")
            for error in result["errors"]:
                print(f"   • {error['type']}: {error['message']}")
                if error.get("analysis"):
                    analysis = error["analysis"]
                    print(f"     - カテゴリ: {analysis.category.value}")
                    print(f"     - 推奨アクション: {analysis.recommended_action}")

                if error.get("recommendations"):
                    print(f"     - 対処法:")
                    for rec in error["recommendations"]:
                        print(f"       • {rec}")

    print(f"\n📈 全体統計:")
    print(f"   • 処理済みイベント総数: {len(processor.processed_events)}")
    print(f"   • エラーログ総数: {len(processor.error_log)}")


if __name__ == "__main__":
    demo_webhook_processing()
