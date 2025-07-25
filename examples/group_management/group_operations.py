"""
LINE Bot グループ管理エラーハンドリング例

このファイルでは、グループ情報取得、メンバー管理、ルーム管理などの
グループ関連APIでのエラーハンドリングパターンを示します。

注意：このファイル内のerror辞書は、実際のLINE APIで発生する可能性のあるエラーパターンを
示すためのサンプルです。実際のAPIエラーは例外オブジェクトから取得されます。
このファイルは複雑なデモ用実装です。シンプルな実装は simple_group_operations.py を参照してください。
"""

import sys
import os
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import hashlib

# プロジェクトルートを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from linebot_error_analyzer import LineErrorAnalyzer


class GroupManager:
    """LINE グループ管理クラス（エラーハンドリング付き）"""

    def __init__(
        self, channel_access_token: str, analyzer: Optional[LineErrorAnalyzer] = None
    ):
        self.channel_access_token = channel_access_token
        self.analyzer = analyzer or LineErrorAnalyzer()
        self.base_url = "https://api.line.me/v2/bot"
        self.group_cache = {}
        self.member_cache = {}
        self.error_log = []

    def get_group_summary(self, group_id: str) -> Dict[str, Any]:
        """
        グループ情報の取得

        Args:
            group_id: グループID

        Returns:
            Dict: グループ情報と詳細情報
        """

        result = {
            "success": False,
            "operation": "get_group_summary",
            "group_id": group_id,
            "timestamp": datetime.now().isoformat(),
            "errors": [],
        }

        try:
            # 1. グループIDの検証
            validation_result = self._validate_group_id(group_id)
            if not validation_result["valid"]:
                result["errors"].extend(validation_result["errors"])
                return result

            # 2. キャッシュの確認
            cache_key = f"group_summary_{group_id}"
            if cache_key in self.group_cache:
                cached_data = self.group_cache[cache_key]
                # キャッシュの有効期限チェック（例：30分）
                cache_age = (
                    datetime.now() - datetime.fromisoformat(cached_data["timestamp"])
                ).seconds
                if cache_age < 1800:  # 30分以内
                    result["success"] = True
                    result["group_summary"] = cached_data["summary"]
                    result["from_cache"] = True
                    print(f"💾 キャッシュからグループ情報取得: {group_id}")
                    return result

            # 3. API呼び出しのシミュレーション
            api_result = self._simulate_group_summary_api_call(group_id)

            if api_result["success"]:
                result["success"] = True
                result["group_summary"] = api_result["summary"]
                result["from_cache"] = False

                # キャッシュに保存
                self.group_cache[cache_key] = {
                    "summary": api_result["summary"],
                    "timestamp": datetime.now().isoformat(),
                }

                print(f"🏢 グループ情報取得成功: {api_result['summary']['groupName']}")

            else:
                result["errors"].extend(api_result["errors"])
                self.error_log.append(api_result)

            return result

        except Exception as e:
            # 実際のLINE APIで発生する可能性のあるエラーパターン（サンプル）
            error_data = {
                "status_code": 500,
                "message": f"Unexpected error in get group summary: {str(e)}",
                "endpoint": "group.summary",
            }
            analysis = self.analyzer.analyze(error_data)
            result["errors"].append(
                {"type": "予期しないエラー", "message": str(e), "analysis": analysis}
            )
            return result

    def get_group_members_count(self, group_id: str) -> Dict[str, Any]:
        """
        グループメンバー数の取得

        Args:
            group_id: グループID

        Returns:
            Dict: メンバー数情報
        """

        result = {
            "success": False,
            "operation": "get_group_members_count",
            "group_id": group_id,
            "timestamp": datetime.now().isoformat(),
            "errors": [],
        }

        try:
            # 1. グループIDの検証
            validation_result = self._validate_group_id(group_id)
            if not validation_result["valid"]:
                result["errors"].extend(validation_result["errors"])
                return result

            # 2. API呼び出しのシミュレーション
            api_result = self._simulate_members_count_api_call(group_id)

            if api_result["success"]:
                result["success"] = True
                result["count"] = api_result["count"]

                print(f"👥 グループメンバー数取得成功: {api_result['count']}人")

            else:
                result["errors"].extend(api_result["errors"])
                self.error_log.append(api_result)

            return result

        except Exception as e:
            # 実際のLINE APIで発生する可能性のあるエラーパターン（サンプル）
            # 実際のLINE APIで発生する可能性のあるエラーパターン（サンプル）
            error_data = {
                "status_code": 500,
                "message": f"Unexpected error in get group members count: {str(e)}",
                "endpoint": "group.members.count",
            }
            analysis = self.analyzer.analyze(error_data)
            result["errors"].append(
                {"type": "予期しないエラー", "message": str(e), "analysis": analysis}
            )
            return result

    def get_group_members_ids(self, group_id: str, start: str = None) -> Dict[str, Any]:
        """
        グループメンバーIDリストの取得

        Args:
            group_id: グループID
            start: 開始位置（ページネーション用）

        Returns:
            Dict: メンバーIDリストと詳細情報
        """

        result = {
            "success": False,
            "operation": "get_group_members_ids",
            "group_id": group_id,
            "start": start,
            "timestamp": datetime.now().isoformat(),
            "errors": [],
        }

        try:
            # 1. グループIDの検証
            validation_result = self._validate_group_id(group_id)
            if not validation_result["valid"]:
                result["errors"].extend(validation_result["errors"])
                return result

            # 2. startパラメータの検証（指定されている場合）
            if start is not None:
                start_validation = self._validate_continuation_token(start)
                if not start_validation["valid"]:
                    result["errors"].extend(start_validation["errors"])
                    return result

            # 3. API呼び出しのシミュレーション
            api_result = self._simulate_members_ids_api_call(group_id, start)

            if api_result["success"]:
                result["success"] = True
                result["member_ids"] = api_result["member_ids"]
                result["next"] = api_result.get("next")  # 次のページがある場合

                print(
                    f"📋 グループメンバーIDリスト取得成功: {len(api_result['member_ids'])}件"
                )

            else:
                result["errors"].extend(api_result["errors"])
                self.error_log.append(api_result)

            return result

        except Exception as e:
            # 実際のLINE APIで発生する可能性のあるエラーパターン（サンプル）
            # 実際のLINE APIで発生する可能性のあるエラーパターン（サンプル）
            error_data = {
                "status_code": 500,
                "message": f"Unexpected error in get group members ids: {str(e)}",
                "endpoint": "group.members.ids",
            }
            analysis = self.analyzer.analyze(error_data)
            result["errors"].append(
                {"type": "予期しないエラー", "message": str(e), "analysis": analysis}
            )
            return result

    def leave_group(self, group_id: str) -> Dict[str, Any]:
        """
        グループからの退出

        Args:
            group_id: グループID

        Returns:
            Dict: 退出結果と詳細情報
        """

        result = {
            "success": False,
            "operation": "leave_group",
            "group_id": group_id,
            "timestamp": datetime.now().isoformat(),
            "errors": [],
        }

        try:
            # 1. グループIDの検証
            validation_result = self._validate_group_id(group_id)
            if not validation_result["valid"]:
                result["errors"].extend(validation_result["errors"])
                return result

            # 2. 退出前の確認処理
            confirm_result = self._confirm_group_leave_operation(group_id)
            if not confirm_result["allowed"]:
                result["errors"].extend(confirm_result["errors"])
                return result

            # 3. API呼び出しのシミュレーション
            api_result = self._simulate_leave_group_api_call(group_id)

            if api_result["success"]:
                result["success"] = True

                # キャッシュをクリア
                cache_keys_to_remove = [
                    key for key in self.group_cache.keys() if group_id in key
                ]
                for key in cache_keys_to_remove:
                    del self.group_cache[key]

                print(f"🚪 グループ退出成功: {group_id}")

            else:
                result["errors"].extend(api_result["errors"])
                self.error_log.append(api_result)

            return result

        except Exception as e:
            # 実際のLINE APIで発生する可能性のあるエラーパターン（サンプル）
            # 実際のLINE APIで発生する可能性のあるエラーパターン（サンプル）
            error_data = {
                "status_code": 500,
                "message": f"Unexpected error in leave group: {str(e)}",
                "endpoint": "group.leave",
            }
            analysis = self.analyzer.analyze(error_data)
            result["errors"].append(
                {"type": "予期しないエラー", "message": str(e), "analysis": analysis}
            )
            return result

    def get_room_members_count(self, room_id: str) -> Dict[str, Any]:
        """
        ルームメンバー数の取得

        Args:
            room_id: ルームID

        Returns:
            Dict: メンバー数情報
        """

        result = {
            "success": False,
            "operation": "get_room_members_count",
            "room_id": room_id,
            "timestamp": datetime.now().isoformat(),
            "errors": [],
        }

        try:
            # 1. ルームIDの検証
            validation_result = self._validate_room_id(room_id)
            if not validation_result["valid"]:
                result["errors"].extend(validation_result["errors"])
                return result

            # 2. API呼び出しのシミュレーション
            api_result = self._simulate_room_members_count_api_call(room_id)

            if api_result["success"]:
                result["success"] = True
                result["count"] = api_result["count"]

                print(f"🏠 ルームメンバー数取得成功: {api_result['count']}人")

            else:
                result["errors"].extend(api_result["errors"])
                self.error_log.append(api_result)

            return result

        except Exception as e:
            # 実際のLINE APIで発生する可能性のあるエラーパターン（サンプル）
            # 実際のLINE APIで発生する可能性のあるエラーパターン（サンプル）
            error_data = {
                "status_code": 500,
                "message": f"Unexpected error in get room members count: {str(e)}",
                "endpoint": "room.members.count",
            }
            analysis = self.analyzer.analyze(error_data)
            result["errors"].append(
                {"type": "予期しないエラー", "message": str(e), "analysis": analysis}
            )
            return result

    def get_room_members_ids(self, room_id: str, start: str = None) -> Dict[str, Any]:
        """
        ルームメンバーIDリストの取得

        Args:
            room_id: ルームID
            start: 開始位置（ページネーション用）

        Returns:
            Dict: メンバーIDリストと詳細情報
        """

        result = {
            "success": False,
            "operation": "get_room_members_ids",
            "room_id": room_id,
            "start": start,
            "timestamp": datetime.now().isoformat(),
            "errors": [],
        }

        try:
            # 1. ルームIDの検証
            validation_result = self._validate_room_id(room_id)
            if not validation_result["valid"]:
                result["errors"].extend(validation_result["errors"])
                return result

            # 2. startパラメータの検証（指定されている場合）
            if start is not None:
                start_validation = self._validate_continuation_token(start)
                if not start_validation["valid"]:
                    result["errors"].extend(start_validation["errors"])
                    return result

            # 3. API呼び出しのシミュレーション
            api_result = self._simulate_room_members_ids_api_call(room_id, start)

            if api_result["success"]:
                result["success"] = True
                result["member_ids"] = api_result["member_ids"]
                result["next"] = api_result.get("next")

                print(
                    f"📋 ルームメンバーIDリスト取得成功: {len(api_result['member_ids'])}件"
                )

            else:
                result["errors"].extend(api_result["errors"])
                self.error_log.append(api_result)

            return result

        except Exception as e:
            # 実際のLINE APIで発生する可能性のあるエラーパターン（サンプル）
            # 実際のLINE APIで発生する可能性のあるエラーパターン（サンプル）
            error_data = {
                "status_code": 500,
                "message": f"Unexpected error in get room members ids: {str(e)}",
                "endpoint": "room.members.ids",
            }
            analysis = self.analyzer.analyze(error_data)
            result["errors"].append(
                {"type": "予期しないエラー", "message": str(e), "analysis": analysis}
            )
            return result

    def leave_room(self, room_id: str) -> Dict[str, Any]:
        """
        ルームからの退出

        Args:
            room_id: ルームID

        Returns:
            Dict: 退出結果と詳細情報
        """

        result = {
            "success": False,
            "operation": "leave_room",
            "room_id": room_id,
            "timestamp": datetime.now().isoformat(),
            "errors": [],
        }

        try:
            # 1. ルームIDの検証
            validation_result = self._validate_room_id(room_id)
            if not validation_result["valid"]:
                result["errors"].extend(validation_result["errors"])
                return result

            # 2. API呼び出しのシミュレーション
            api_result = self._simulate_leave_room_api_call(room_id)

            if api_result["success"]:
                result["success"] = True

                print(f"🚪 ルーム退出成功: {room_id}")

            else:
                result["errors"].extend(api_result["errors"])
                self.error_log.append(api_result)

            return result

        except Exception as e:
            # 実際のLINE APIで発生する可能性のあるエラーパターン（サンプル）
            # 実際のLINE APIで発生する可能性のあるエラーパターン（サンプル）
            error_data = {
                "status_code": 500,
                "message": f"Unexpected error in leave room: {str(e)}",
                "endpoint": "room.leave",
            }
            analysis = self.analyzer.analyze(error_data)
            result["errors"].append(
                {"type": "予期しないエラー", "message": str(e), "analysis": analysis}
            )
            return result

    def analyze_group_activity(self, group_id: str, days: int = 7) -> Dict[str, Any]:
        """
        グループ活動の分析

        Args:
            group_id: グループID
            days: 分析対象日数

        Returns:
            Dict: 活動分析結果
        """

        result = {
            "success": False,
            "operation": "analyze_group_activity",
            "group_id": group_id,
            "analysis_days": days,
            "timestamp": datetime.now().isoformat(),
            "errors": [],
        }

        try:
            # 1. グループIDの検証
            validation_result = self._validate_group_id(group_id)
            if not validation_result["valid"]:
                result["errors"].extend(validation_result["errors"])
                return result

            # 2. 日数の検証
            if days <= 0 or days > 365:
                # 実際のLINE APIで発生する可能性のあるエラーパターン（サンプル）
                error_data = {
                    "status_code": 400,
                    "message": f"Invalid analysis days: {days}",
                    "endpoint": "group.activity.analysis",
                }
                analysis = self.analyzer.analyze(error_data)
                result["errors"].append(
                    {
                        "type": "分析期間エラー",
                        "message": f"分析期間は1-365日の範囲で指定してください（指定値: {days}日）",
                        "analysis": analysis,
                    }
                )
                return result

            # 3. 活動分析の実行
            activity_data = self._generate_activity_analysis(group_id, days)

            result["success"] = True
            result["analysis"] = activity_data

            print(f"📊 グループ活動分析完了: {group_id} ({days}日間)")

            return result

        except Exception as e:
            # 実際のLINE APIで発生する可能性のあるエラーパターン（サンプル）
            error_data = {
                "status_code": 500,
                "message": f"Unexpected error in analyze group activity: {str(e)}",
                "endpoint": "group.activity.analysis",
            }
            analysis = self.analyzer.analyze(error_data)
            result["errors"].append(
                {"type": "予期しないエラー", "message": str(e), "analysis": analysis}
            )
            return result

    def _validate_group_id(self, group_id: str) -> Dict[str, Any]:
        """グループIDの検証"""

        result = {"valid": False, "errors": []}

        if not group_id:
            # 実際のLINE APIで発生する可能性のあるエラーパターン（サンプル）
            # 実際のLINE APIで発生する可能性のあるエラーパターン（サンプル）
            error_data = {
                "status_code": 400,
                "message": "Group ID is required",
                "endpoint": "group.validation",
            }
            analysis = self.analyzer.analyze(error_data)
            result["errors"].append(
                {
                    "type": "グループIDエラー",
                    "message": "グループIDが指定されていません",
                    "analysis": analysis,
                }
            )
            return result

        # グループIDの形式チェック（C + 32文字）
        if not group_id.startswith("C") or len(group_id) != 33:
            # 実際のLINE APIで発生する可能性のあるエラーパターン（サンプル）
            # 実際のLINE APIで発生する可能性のあるエラーパターン（サンプル）
            error_data = {
                "status_code": 400,
                "message": f"Invalid group ID format: {group_id}",
                "endpoint": "group.validation",
            }
            analysis = self.analyzer.analyze(error_data)
            result["errors"].append(
                {
                    "type": "グループIDフォーマットエラー",
                    "message": f"グループIDのフォーマットが正しくありません: {group_id}",
                    "analysis": analysis,
                    "recommendations": [
                        "グループIDは 'C' + 32文字の形式である必要があります",
                        "例: C1234567890123456789012345678901234567890123456789",
                    ],
                }
            )
            return result

        result["valid"] = True
        return result

    def _validate_room_id(self, room_id: str) -> Dict[str, Any]:
        """ルームIDの検証"""

        result = {"valid": False, "errors": []}

        if not room_id:
            # 実際のLINE APIで発生する可能性のあるエラーパターン（サンプル）
            # 実際のLINE APIで発生する可能性のあるエラーパターン（サンプル）
            error_data = {
                "status_code": 400,
                "message": "Room ID is required",
                "endpoint": "room.validation",
            }
            analysis = self.analyzer.analyze(error_data)
            result["errors"].append(
                {
                    "type": "ルームIDエラー",
                    "message": "ルームIDが指定されていません",
                    "analysis": analysis,
                }
            )
            return result

        # ルームIDの形式チェック（R + 32文字）
        if not room_id.startswith("R") or len(room_id) != 33:
            # 実際のLINE APIで発生する可能性のあるエラーパターン（サンプル）
            # 実際のLINE APIで発生する可能性のあるエラーパターン（サンプル）
            error_data = {
                "status_code": 400,
                "message": f"Invalid room ID format: {room_id}",
                "endpoint": "room.validation",
            }
            analysis = self.analyzer.analyze(error_data)
            result["errors"].append(
                {
                    "type": "ルームIDフォーマットエラー",
                    "message": f"ルームIDのフォーマットが正しくありません: {room_id}",
                    "analysis": analysis,
                    "recommendations": [
                        "ルームIDは 'R' + 32文字の形式である必要があります",
                        "例: R1234567890123456789012345678901234567890123456789",
                    ],
                }
            )
            return result

        result["valid"] = True
        return result

    def _validate_continuation_token(self, token: str) -> Dict[str, Any]:
        """継続トークンの検証"""

        result = {"valid": False, "errors": []}

        if not token:
            result["valid"] = True  # 空は有効（最初のページ）
            return result

        # 継続トークンの基本的な形式チェック
        if len(token) < 10 or len(token) > 500:
            # 実際のLINE APIで発生する可能性のあるエラーパターン（サンプル）
            # 実際のLINE APIで発生する可能性のあるエラーパターン（サンプル）
            error_data = {
                "status_code": 400,
                "message": f"Invalid continuation token format: {token[:50]}...",
                "endpoint": "pagination.validation",
            }
            analysis = self.analyzer.analyze(error_data)
            result["errors"].append(
                {
                    "type": "継続トークンエラー",
                    "message": "継続トークンのフォーマットが正しくありません",
                    "analysis": analysis,
                    "recommendations": [
                        "前回のAPIレスポンスの'next'フィールドの値を使用してください",
                        "継続トークンを手動で編集しないでください",
                    ],
                }
            )
            return result

        result["valid"] = True
        return result

    def _confirm_group_leave_operation(self, group_id: str) -> Dict[str, Any]:
        """グループ退出操作の確認"""

        result = {"allowed": False, "errors": []}

        # 実際の実装では、管理者権限の確認、重要なグループかどうかの判定など
        # ここでは簡易的な例を示す

        # 例: 特定のグループIDパターンは退出を制限
        if "admin" in group_id.lower() or "important" in group_id.lower():
            # 実際のLINE APIで発生する可能性のあるエラーパターン（サンプル）
            # 実際のLINE APIで発生する可能性のあるエラーパターン（サンプル）
            error_data = {
                "status_code": 403,
                "message": "Cannot leave from important group",
                "endpoint": "group.leave.validation",
            }
            analysis = self.analyzer.analyze(error_data)
            result["errors"].append(
                {
                    "type": "退出制限エラー",
                    "message": "このグループからの退出は制限されています",
                    "analysis": analysis,
                    "recommendations": [
                        "管理者に退出の許可を求めてください",
                        "重要なグループからの退出は慎重に検討してください",
                    ],
                }
            )
            return result

        result["allowed"] = True
        return result

    def _simulate_group_summary_api_call(self, group_id: str) -> Dict[str, Any]:
        """グループ情報API呼び出しのシミュレーション"""

        result = {"success": False, "errors": []}

        import random

        # 80%の確率で成功
        if random.random() < 0.8:
            group_hash = hashlib.md5(group_id.encode()).hexdigest()[:8]

            result["success"] = True
            result["summary"] = {
                "groupId": group_id,
                "groupName": f"グループ{group_hash}",
                "pictureUrl": f"https://example.com/group/{group_hash}.jpg",
            }
            return result

        # 20%の確率でエラーをシミュレート
        error_scenarios = [
            {
                "status_code": 403,
                "message": "The bot doesn't have permission to access group information",
                "details": "Bot may not be a member of the group",
            },
            {
                "status_code": 404,
                "message": "The group couldn't be found",
                "details": "Group may have been deleted or bot was removed",
            },
        ]

        error_scenario = random.choice(error_scenarios)

        # 実際のLINE APIで発生する可能性のあるエラーパターン（サンプル）
        error_data = {
            "status_code": error_scenario["status_code"],
            "message": error_scenario["message"],
            "endpoint": "group.summary",
        }

        analysis = self.analyzer.analyze(error_data)

        result["errors"].append(
            {
                "type": "グループ情報取得エラー",
                "message": error_scenario["message"],
                "details": error_scenario["details"],
                "status_code": error_scenario["status_code"],
                "analysis": analysis,
            }
        )

        return result

    def _simulate_members_count_api_call(self, group_id: str) -> Dict[str, Any]:
        """メンバー数API呼び出しのシミュレーション"""

        result = {"success": False, "errors": []}

        import random

        # 85%の確率で成功
        if random.random() < 0.85:
            # グループIDベースの固定値を生成
            random.seed(hash(group_id))
            count = random.randint(3, 500)

            result["success"] = True
            result["count"] = count
            return result

        # 15%の確率でエラーをシミュレート
        error_scenarios = [
            {
                "status_code": 403,
                "message": "The bot doesn't have permission to access member count",
                "details": "Insufficient permissions",
            }
        ]

        error_scenario = random.choice(error_scenarios)

        # 実際のLINE APIで発生する可能性のあるエラーパターン（サンプル）
        error_data = {
            "status_code": error_scenario["status_code"],
            "message": error_scenario["message"],
            "endpoint": "group.members.count",
        }

        analysis = self.analyzer.analyze(error_data)

        result["errors"].append(
            {
                "type": "メンバー数取得エラー",
                "message": error_scenario["message"],
                "details": error_scenario["details"],
                "status_code": error_scenario["status_code"],
                "analysis": analysis,
            }
        )

        return result

    def _simulate_members_ids_api_call(
        self, group_id: str, start: str
    ) -> Dict[str, Any]:
        """メンバーIDリストAPI呼び出しのシミュレーション"""

        result = {"success": False, "errors": []}

        import random

        # 80%の確率で成功
        if random.random() < 0.8:
            # ダミーのユーザーIDリストを生成
            random.seed(hash(f"{group_id}_{start}"))
            member_count = random.randint(5, 20)

            member_ids = []
            for i in range(member_count):
                user_hash = hashlib.md5(f"{group_id}_user_{i}".encode()).hexdigest()
                member_ids.append(f"U{user_hash[:32]}")

            result["success"] = True
            result["member_ids"] = member_ids

            # 次のページがあるかどうか（ランダム）
            if random.random() < 0.3:  # 30%の確率で次のページあり
                result["next"] = f"next_token_{group_id}_{random.randint(1000, 9999)}"

            return result

        # 20%の確率でエラーをシミュレート
        error_scenarios = [
            {
                "status_code": 403,
                "message": "The bot doesn't have permission to access member list",
                "details": "Insufficient permissions",
            }
        ]

        error_scenario = random.choice(error_scenarios)

        # 実際のLINE APIで発生する可能性のあるエラーパターン（サンプル）
        error_data = {
            "status_code": error_scenario["status_code"],
            "message": error_scenario["message"],
            "endpoint": "group.members.ids",
        }

        analysis = self.analyzer.analyze(error_data)

        result["errors"].append(
            {
                "type": "メンバーIDリスト取得エラー",
                "message": error_scenario["message"],
                "details": error_scenario["details"],
                "status_code": error_scenario["status_code"],
                "analysis": analysis,
            }
        )

        return result

    def _simulate_leave_group_api_call(self, group_id: str) -> Dict[str, Any]:
        """グループ退出API呼び出しのシミュレーション"""

        result = {"success": False, "errors": []}

        import random

        # 90%の確率で成功
        if random.random() < 0.9:
            result["success"] = True
            return result

        # 10%の確率でエラーをシミュレート
        error_scenarios = [
            {
                "status_code": 403,
                "message": "The bot is not a member of the group",
                "details": "Cannot leave a group the bot is not a member of",
            }
        ]

        error_scenario = random.choice(error_scenarios)

        # 実際のLINE APIで発生する可能性のあるエラーパターン（サンプル）
        error_data = {
            "status_code": error_scenario["status_code"],
            "message": error_scenario["message"],
            "endpoint": "group.leave",
        }

        analysis = self.analyzer.analyze(error_data)

        result["errors"].append(
            {
                "type": "グループ退出エラー",
                "message": error_scenario["message"],
                "details": error_scenario["details"],
                "status_code": error_scenario["status_code"],
                "analysis": analysis,
            }
        )

        return result

    def _simulate_room_members_count_api_call(self, room_id: str) -> Dict[str, Any]:
        """ルームメンバー数API呼び出しのシミュレーション"""

        result = {"success": False, "errors": []}

        import random

        # 85%の確率で成功
        if random.random() < 0.85:
            random.seed(hash(room_id))
            count = random.randint(2, 20)  # ルームは小規模

            result["success"] = True
            result["count"] = count
            return result

        # 15%の確率でエラーをシミュレート
        error_scenarios = [
            {
                "status_code": 404,
                "message": "The room couldn't be found",
                "details": "Room may have been deleted",
            }
        ]

        error_scenario = random.choice(error_scenarios)

        # 実際のLINE APIで発生する可能性のあるエラーパターン（サンプル）
        error_data = {
            "status_code": error_scenario["status_code"],
            "message": error_scenario["message"],
            "endpoint": "room.members.count",
        }

        analysis = self.analyzer.analyze(error_data)

        result["errors"].append(
            {
                "type": "ルームメンバー数取得エラー",
                "message": error_scenario["message"],
                "details": error_scenario["details"],
                "status_code": error_scenario["status_code"],
                "analysis": analysis,
            }
        )

        return result

    def _simulate_room_members_ids_api_call(
        self, room_id: str, start: str
    ) -> Dict[str, Any]:
        """ルームメンバーIDリストAPI呼び出しのシミュレーション"""

        result = {"success": False, "errors": []}

        import random

        # 80%の確率で成功
        if random.random() < 0.8:
            random.seed(hash(f"{room_id}_{start}"))
            member_count = random.randint(2, 10)  # ルームは小規模

            member_ids = []
            for i in range(member_count):
                user_hash = hashlib.md5(f"{room_id}_user_{i}".encode()).hexdigest()
                member_ids.append(f"U{user_hash[:32]}")

            result["success"] = True
            result["member_ids"] = member_ids
            # ルームは小規模なので、基本的にページネーションなし

            return result

        # 20%の確率でエラーをシミュレート
        error_scenarios = [
            {
                "status_code": 404,
                "message": "The room couldn't be found",
                "details": "Room may have been deleted",
            }
        ]

        error_scenario = random.choice(error_scenarios)

        # 実際のLINE APIで発生する可能性のあるエラーパターン（サンプル）
        error_data = {
            "status_code": error_scenario["status_code"],
            "message": error_scenario["message"],
            "endpoint": "room.members.ids",
        }

        analysis = self.analyzer.analyze(error_data)

        result["errors"].append(
            {
                "type": "ルームメンバーIDリスト取得エラー",
                "message": error_scenario["message"],
                "details": error_scenario["details"],
                "status_code": error_scenario["status_code"],
                "analysis": analysis,
            }
        )

        return result

    def _simulate_leave_room_api_call(self, room_id: str) -> Dict[str, Any]:
        """ルーム退出API呼び出しのシミュレーション"""

        result = {"success": False, "errors": []}

        import random

        # 90%の確率で成功
        if random.random() < 0.9:
            result["success"] = True
            return result

        # 10%の確率でエラーをシミュレート
        error_scenarios = [
            {
                "status_code": 403,
                "message": "The bot is not a member of the room",
                "details": "Cannot leave a room the bot is not a member of",
            }
        ]

        error_scenario = random.choice(error_scenarios)

        # 実際のLINE APIで発生する可能性のあるエラーパターン（サンプル）
        error_data = {
            "status_code": error_scenario["status_code"],
            "message": error_scenario["message"],
            "endpoint": "room.leave",
        }

        analysis = self.analyzer.analyze(error_data)

        result["errors"].append(
            {
                "type": "ルーム退出エラー",
                "message": error_scenario["message"],
                "details": error_scenario["details"],
                "status_code": error_scenario["status_code"],
                "analysis": analysis,
            }
        )

        return result

    def _generate_activity_analysis(self, group_id: str, days: int) -> Dict[str, Any]:
        """グループ活動分析データの生成"""

        import random

        # グループIDベースのシード値で再現可能な結果を生成
        random.seed(hash(f"{group_id}_{days}"))

        analysis = {
            "group_id": group_id,
            "analysis_period_days": days,
            "total_messages": random.randint(days * 5, days * 50),
            "unique_active_members": random.randint(3, 25),
            "peak_activity_hour": f"{random.randint(9, 22):02d}:00-{random.randint(9, 22):02d}:59",
            "most_active_day": [
                "月曜日",
                "火曜日",
                "水曜日",
                "木曜日",
                "金曜日",
                "土曜日",
                "日曜日",
            ][random.randint(0, 6)],
            "message_types": {
                "text": round(random.uniform(0.6, 0.8), 2),
                "sticker": round(random.uniform(0.1, 0.3), 2),
                "image": round(random.uniform(0.05, 0.15), 2),
                "other": round(random.uniform(0.01, 0.05), 2),
            },
            "activity_trend": "increasing" if random.random() > 0.5 else "decreasing",
            "engagement_score": round(random.uniform(0.3, 0.9), 2),
        }

        return analysis


def demo_group_management():
    """グループ管理のデモ実行"""

    print("🚀 LINE Bot グループ管理エラーハンドリングデモ")
    print("=" * 60)

    group_manager = GroupManager("dummy_channel_access_token")

    # テストケース
    test_cases = [
        {
            "name": "正常なグループ情報取得",
            "method": "get_group_summary",
            "args": ["C1234567890123456789012345678901234567890123456789"],
        },
        {
            "name": "無効なグループIDフォーマット",
            "method": "get_group_summary",
            "args": ["invalid-group-id"],
        },
        {"name": "空のグループID", "method": "get_group_summary", "args": [""]},
        {
            "name": "グループメンバー数取得",
            "method": "get_group_members_count",
            "args": ["C1234567890123456789012345678901234567890123456789"],
        },
        {
            "name": "グループメンバーIDリスト取得",
            "method": "get_group_members_ids",
            "args": ["C1234567890123456789012345678901234567890123456789"],
        },
        {
            "name": "ページネーション付きメンバーIDリスト取得",
            "method": "get_group_members_ids",
            "args": [
                "C1234567890123456789012345678901234567890123456789",
                "next_token_example",
            ],
        },
        {
            "name": "ルームメンバー数取得",
            "method": "get_room_members_count",
            "args": ["R1234567890123456789012345678901234567890123456789"],
        },
        {
            "name": "ルームメンバーIDリスト取得",
            "method": "get_room_members_ids",
            "args": ["R1234567890123456789012345678901234567890123456789"],
        },
        {
            "name": "グループ活動分析",
            "method": "analyze_group_activity",
            "args": ["C1234567890123456789012345678901234567890123456789", 7],
        },
        {
            "name": "無効な分析期間",
            "method": "analyze_group_activity",
            "args": ["C1234567890123456789012345678901234567890123456789", 400],
        },
        {
            "name": "グループ退出",
            "method": "leave_group",
            "args": ["C1234567890123456789012345678901234567890123456789"],
        },
        {
            "name": "制限されたグループからの退出",
            "method": "leave_group",
            "args": ["Cadmin567890123456789012345678901234567890123456789"],
        },
        {
            "name": "ルーム退出",
            "method": "leave_room",
            "args": ["R1234567890123456789012345678901234567890123456789"],
        },
    ]

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 テストケース {i}: {test_case['name']}")
        print("-" * 40)

        method = getattr(group_manager, test_case["method"])
        result = method(*test_case["args"])

        print(f"📊 実行結果:")
        print(f"   • 成功: {result['success']}")
        print(f"   • 操作: {result['operation']}")

        if result["success"]:
            print("✅ 操作成功")

            if "group_summary" in result:
                summary = result["group_summary"]
                print(f"   • グループ名: {summary.get('groupName', 'N/A')}")
                if result.get("from_cache"):
                    print("   • データソース: キャッシュ")
                else:
                    print("   • データソース: API")

            if "count" in result:
                print(f"   • メンバー数: {result['count']:,}人")

            if "member_ids" in result:
                print(f"   • 取得IDリスト数: {len(result['member_ids'])}件")
                if result.get("next"):
                    print("   • 次のページ: あり")
                else:
                    print("   • 次のページ: なし")

            if "analysis" in result:
                analysis = result["analysis"]
                print(f"   • 分析期間: {analysis['analysis_period_days']}日間")
                print(f"   • 総メッセージ数: {analysis['total_messages']:,}件")
                print(f"   • アクティブメンバー: {analysis['unique_active_members']}人")
                print(f"   • エンゲージメントスコア: {analysis['engagement_score']}")
                print(f"   • アクティビティトレンド: {analysis['activity_trend']}")

        else:
            print("❌ 操作失敗")
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

    print(f"\n💾 キャッシュ統計:")
    print(f"   • グループキャッシュエントリ数: {len(group_manager.group_cache)}")
    print(f"   • メンバーキャッシュエントリ数: {len(group_manager.member_cache)}")
    print(f"   • エラーログ数: {len(group_manager.error_log)}")

    # キャッシュテスト（同じグループ情報を再度取得）
    print(f"\n🔄 キャッシュテスト:")
    print("同じグループ情報を2回取得してキャッシュ動作を確認")

    group_id = "C1234567890123456789012345678901234567890123456789"

    print("1回目:")
    result1 = group_manager.get_group_summary(group_id)
    if result1["success"]:
        print(
            f"   データソース: {'キャッシュ' if result1.get('from_cache') else 'API'}"
        )

    print("2回目（すぐ後）:")
    result2 = group_manager.get_group_summary(group_id)
    if result2["success"]:
        print(
            f"   データソース: {'キャッシュ' if result2.get('from_cache') else 'API'}"
        )


if __name__ == "__main__":
    demo_group_management()
