"""
LINE Bot ユーザー管理エラーハンドリング例

このファイルでは、ユーザープロフィール取得、フォロワー管理などの
ユーザー関連APIでのエラーハンドリングパターンを示します。

注意：このファイル内のerror辞書は、実際のLINE APIで発生する可能性のあるエラーパターンを
示すためのサンプルです。実際のAPIエラーは例外オブジェクトから取得されます。
このファイルは複雑なデモ用実装です。シンプルな実装は simple_user_profile.py を参照してください。
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


class UserManager:
    """LINE ユーザー管理クラス（エラーハンドリング付き）"""

    def __init__(
        self, channel_access_token: str, analyzer: Optional[LineErrorAnalyzer] = None
    ):
        self.channel_access_token = channel_access_token
        self.analyzer = analyzer or LineErrorAnalyzer()
        self.base_url = "https://api.line.me/v2/bot"
        self.user_cache = {}
        self.error_log = []

    def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """
        ユーザープロフィール情報の取得

        Args:
            user_id: ユーザーID

        Returns:
            Dict: プロフィール情報と詳細情報
        """

        result = {
            "success": False,
            "operation": "get_user_profile",
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
            "errors": [],
        }

        try:
            # 1. ユーザーIDの検証
            validation_result = self._validate_user_id(user_id)
            if not validation_result["valid"]:
                result["errors"].extend(validation_result["errors"])
                return result

            # 2. キャッシュの確認
            cache_key = f"profile_{user_id}"
            if cache_key in self.user_cache:
                cached_data = self.user_cache[cache_key]
                # キャッシュの有効期限チェック（例：1時間）
                cache_age = (
                    datetime.now() - datetime.fromisoformat(cached_data["timestamp"])
                ).seconds
                if cache_age < 3600:  # 1時間以内
                    result["success"] = True
                    result["profile"] = cached_data["profile"]
                    result["from_cache"] = True
                    print(f"💾 キャッシュからプロフィール取得: {user_id}")
                    return result

            # 3. API呼び出しのシミュレーション
            api_result = self._simulate_profile_api_call(user_id)

            if api_result["success"]:
                result["success"] = True
                result["profile"] = api_result["profile"]
                result["from_cache"] = False

                # キャッシュに保存
                self.user_cache[cache_key] = {
                    "profile": api_result["profile"],
                    "timestamp": datetime.now().isoformat(),
                }

                print(
                    f"👤 プロフィール取得成功: {api_result['profile']['displayName']}"
                )

            else:
                result["errors"].extend(api_result["errors"])
                self.error_log.append(api_result)

            return result

        except Exception as e:
            # 予期しないエラー用のサンプルエラーデータ
            # 予期しないエラー用のサンプルエラーデータ
            # 実際のLINE APIで発生する可能性のあるエラーパターン（サンプル）
            error_data = {
                "status_code": 500,
                "message": f"Unexpected error in get user profile: {str(e)}",
                "endpoint": "profile",
            }
            analysis = self.analyzer.analyze(error_data)
            result["errors"].append(
                {"type": "予期しないエラー", "message": str(e), "analysis": analysis}
            )
            return result

    def get_group_member_profile(self, group_id: str, user_id: str) -> Dict[str, Any]:
        """
        グループメンバーのプロフィール情報取得

        Args:
            group_id: グループID
            user_id: ユーザーID

        Returns:
            Dict: メンバープロフィール情報
        """

        result = {
            "success": False,
            "operation": "get_group_member_profile",
            "group_id": group_id,
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
            "errors": [],
        }

        try:
            # 1. グループIDの検証
            group_validation = self._validate_group_id(group_id)
            if not group_validation["valid"]:
                result["errors"].extend(group_validation["errors"])
                return result

            # 2. ユーザーIDの検証
            user_validation = self._validate_user_id(user_id)
            if not user_validation["valid"]:
                result["errors"].extend(user_validation["errors"])
                return result

            # 3. キャッシュの確認
            cache_key = f"group_member_{group_id}_{user_id}"
            if cache_key in self.user_cache:
                cached_data = self.user_cache[cache_key]
                cache_age = (
                    datetime.now() - datetime.fromisoformat(cached_data["timestamp"])
                ).seconds
                if cache_age < 1800:  # 30分以内
                    result["success"] = True
                    result["profile"] = cached_data["profile"]
                    result["from_cache"] = True
                    print(
                        f"💾 キャッシュからグループメンバープロフィール取得: {user_id}"
                    )
                    return result

            # 4. API呼び出しのシミュレーション
            api_result = self._simulate_group_member_api_call(group_id, user_id)

            if api_result["success"]:
                result["success"] = True
                result["profile"] = api_result["profile"]
                result["from_cache"] = False

                # キャッシュに保存
                self.user_cache[cache_key] = {
                    "profile": api_result["profile"],
                    "timestamp": datetime.now().isoformat(),
                }

                print(
                    f"👥 グループメンバープロフィール取得成功: {api_result['profile']['displayName']}"
                )

            else:
                result["errors"].extend(api_result["errors"])
                self.error_log.append(api_result)

            return result

        except Exception as e:
            # 予期しないエラー用のサンプルエラーデータ
            # 予期しないエラー用のサンプルエラーデータ
            # 実際のLINE APIで発生する可能性のあるエラーパターン（サンプル）
            error_data = {
                "status_code": 500,
                "message": f"Unexpected error in get group member profile: {str(e)}",
                "endpoint": "group.member.profile",
            }
            analysis = self.analyzer.analyze(error_data)
            result["errors"].append(
                {"type": "予期しないエラー", "message": str(e), "analysis": analysis}
            )
            return result

    def get_room_member_profile(self, room_id: str, user_id: str) -> Dict[str, Any]:
        """
        ルームメンバーのプロフィール情報取得

        Args:
            room_id: ルームID
            user_id: ユーザーID

        Returns:
            Dict: メンバープロフィール情報
        """

        result = {
            "success": False,
            "operation": "get_room_member_profile",
            "room_id": room_id,
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
            "errors": [],
        }

        try:
            # 1. ルームIDの検証
            room_validation = self._validate_room_id(room_id)
            if not room_validation["valid"]:
                result["errors"].extend(room_validation["errors"])
                return result

            # 2. ユーザーIDの検証
            user_validation = self._validate_user_id(user_id)
            if not user_validation["valid"]:
                result["errors"].extend(user_validation["errors"])
                return result

            # 3. API呼び出しのシミュレーション
            api_result = self._simulate_room_member_api_call(room_id, user_id)

            if api_result["success"]:
                result["success"] = True
                result["profile"] = api_result["profile"]

                print(
                    f"🏠 ルームメンバープロフィール取得成功: {api_result['profile']['displayName']}"
                )

            else:
                result["errors"].extend(api_result["errors"])
                self.error_log.append(api_result)

            return result

        except Exception as e:
            # 予期しないエラー用のサンプルエラーデータ
            # 予期しないエラー用のサンプルエラーデータ
            # 実際のLINE APIで発生する可能性のあるエラーパターン（サンプル）
            error_data = {
                "status_code": 500,
                "message": f"Unexpected error in get room member profile: {str(e)}",
                "endpoint": "room.member.profile",
            }
            analysis = self.analyzer.analyze(error_data)
            result["errors"].append(
                {"type": "予期しないエラー", "message": str(e), "analysis": analysis}
            )
            return result

    def get_followers_count(self, date: str = None) -> Dict[str, Any]:
        """
        フォロワー数の取得

        Args:
            date: 取得日付（YYYYMMDD形式、指定しない場合は最新）

        Returns:
            Dict: フォロワー数情報
        """

        result = {
            "success": False,
            "operation": "get_followers_count",
            "date": date,
            "timestamp": datetime.now().isoformat(),
            "errors": [],
        }

        try:
            # 1. 日付フォーマットの検証
            if date:
                date_validation = self._validate_date_format(date)
                if not date_validation["valid"]:
                    result["errors"].extend(date_validation["errors"])
                    return result

            # 2. API呼び出しのシミュレーション
            api_result = self._simulate_followers_api_call(date)

            if api_result["success"]:
                result["success"] = True
                result["followers"] = api_result["followers"]
                result["targetedReaches"] = api_result["targetedReaches"]
                result["blocks"] = api_result["blocks"]

                print(f"📊 フォロワー数取得成功: {api_result['followers']}人")

            else:
                result["errors"].extend(api_result["errors"])
                self.error_log.append(api_result)

            return result

        except Exception as e:
            # 予期しないエラー用のサンプルエラーデータ
            # 予期しないエラー用のサンプルエラーデータ
            # 実際のLINE APIで発生する可能性のあるエラーパターン（サンプル）
            error_data = {
                "status_code": 500,
                "message": f"Unexpected error in get followers count: {str(e)}",
                "endpoint": "insight.followers",
            }
            analysis = self.analyzer.analyze(error_data)
            result["errors"].append(
                {"type": "予期しないエラー", "message": str(e), "analysis": analysis}
            )
            return result

    def get_user_interaction_stats(self, user_id: str) -> Dict[str, Any]:
        """
        ユーザーとのインタラクション統計の取得

        Args:
            user_id: ユーザーID

        Returns:
            Dict: インタラクション統計情報
        """

        result = {
            "success": False,
            "operation": "get_user_interaction_stats",
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
            "errors": [],
        }

        try:
            # 1. ユーザーIDの検証
            validation_result = self._validate_user_id(user_id)
            if not validation_result["valid"]:
                result["errors"].extend(validation_result["errors"])
                return result

            # 2. 統計情報の生成（実際の実装では、データベースから取得）
            stats = self._generate_interaction_stats(user_id)

            result["success"] = True
            result["stats"] = stats

            print(f"📈 インタラクション統計取得成功: {user_id}")

            return result

        except Exception as e:
            # 予期しないエラー用のサンプルエラーデータ
            # 実際のLINE APIで発生する可能性のあるエラーパターン（サンプル）
            error_data = {
                "status_code": 500,
                "message": f"Unexpected error in get interaction stats: {str(e)}",
                "endpoint": "user.stats",
            }
            analysis = self.analyzer.analyze(error_data)
            result["errors"].append(
                {"type": "予期しないエラー", "message": str(e), "analysis": analysis}
            )
            return result

    def _validate_user_id(self, user_id: str) -> Dict[str, Any]:
        """ユーザーIDの検証"""

        result = {"valid": False, "errors": []}

        if not user_id:
            # 予期しないエラー用のサンプルエラーデータ
            # 実際のLINE APIで発生する可能性のあるエラーパターン（サンプル）
            error_data = {
                "status_code": 400,
                "message": "User ID is required",
                "endpoint": "user.validation",
            }
            analysis = self.analyzer.analyze(error_data)
            result["errors"].append(
                {
                    "type": "ユーザーIDエラー",
                    "message": "ユーザーIDが指定されていません",
                    "analysis": analysis,
                }
            )
            return result

        # ユーザーIDの形式チェック（U + 32文字）
        if not user_id.startswith("U") or len(user_id) != 33:
            # 予期しないエラー用のサンプルエラーデータ
            # 実際のLINE APIで発生する可能性のあるエラーパターン（サンプル）
            error_data = {
                "status_code": 400,
                "message": f"Invalid user ID format: {user_id}",
                "endpoint": "user.validation",
            }
            analysis = self.analyzer.analyze(error_data)
            result["errors"].append(
                {
                    "type": "ユーザーIDフォーマットエラー",
                    "message": f"ユーザーIDのフォーマットが正しくありません: {user_id}",
                    "analysis": analysis,
                    "recommendations": [
                        "ユーザーIDは 'U' + 32文字の形式である必要があります",
                        "例: U1234567890123456789012345678901234567890123456789",
                    ],
                }
            )
            return result

        result["valid"] = True
        return result

    def _validate_group_id(self, group_id: str) -> Dict[str, Any]:
        """グループIDの検証"""

        result = {"valid": False, "errors": []}

        if not group_id:
            # 予期しないエラー用のサンプルエラーデータ
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
            # 予期しないエラー用のサンプルエラーデータ
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
                        "グループIDは 'C' + 32文字の形式である必要があります"
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
            # 予期しないエラー用のサンプルエラーデータ
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
            # 予期しないエラー用のサンプルエラーデータ
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
                        "ルームIDは 'R' + 32文字の形式である必要があります"
                    ],
                }
            )
            return result

        result["valid"] = True
        return result

    def _validate_date_format(self, date: str) -> Dict[str, Any]:
        """日付フォーマットの検証"""

        result = {"valid": False, "errors": []}

        if not date:
            result["valid"] = True  # 日付は任意
            return result

        # YYYYMMDD形式のチェック
        if len(date) != 8 or not date.isdigit():
            # 予期しないエラー用のサンプルエラーデータ
            # 実際のLINE APIで発生する可能性のあるエラーパターン（サンプル）
            error_data = {
                "status_code": 400,
                "message": f"Invalid date format: {date}",
                "endpoint": "date.validation",
            }
            analysis = self.analyzer.analyze(error_data)
            result["errors"].append(
                {
                    "type": "日付フォーマットエラー",
                    "message": f"日付のフォーマットが正しくありません: {date}",
                    "analysis": analysis,
                    "recommendations": [
                        "日付はYYYYMMDD形式で指定してください",
                        "例: 20241201",
                    ],
                }
            )
            return result

        # 日付の妥当性チェック
        try:
            year = int(date[:4])
            month = int(date[4:6])
            day = int(date[6:8])

            if month < 1 or month > 12:
                raise ValueError("Invalid month")
            if day < 1 or day > 31:
                raise ValueError("Invalid day")

        except ValueError as e:
            # 予期しないエラー用のサンプルエラーデータ
            # 実際のLINE APIで発生する可能性のあるエラーパターン（サンプル）
            error_data = {
                "status_code": 400,
                "message": f"Invalid date value: {date}",
                "endpoint": "date.validation",
            }
            analysis = self.analyzer.analyze(error_data)
            result["errors"].append(
                {
                    "type": "日付値エラー",
                    "message": f"日付の値が正しくありません: {date}",
                    "analysis": analysis,
                }
            )
            return result

        result["valid"] = True
        return result

    def _simulate_profile_api_call(self, user_id: str) -> Dict[str, Any]:
        """プロフィールAPI呼び出しのシミュレーション"""

        result = {"success": False, "errors": []}

        import random

        # 80%の確率で成功
        if random.random() < 0.8:
            # ユーザーIDの末尾数字でダミーデータを生成
            user_hash = hashlib.md5(user_id.encode()).hexdigest()[:8]

            result["success"] = True
            result["profile"] = {
                "userId": user_id,
                "displayName": f"ユーザー{user_hash}",
                "pictureUrl": f"https://example.com/profile/{user_hash}.jpg",
                "statusMessage": f"よろしくお願いします！ #{user_hash}",
            }
            return result

        # 20%の確率でエラーをシミュレート（実際のLINE APIで発生するエラーパターンのサンプル）
        error_scenarios = [
            {
                "status_code": 403,
                "message": "The user hasn't agreed to the Official Accounts Terms of Use",
                "details": "User has not consented to data access",
            },
            {
                "status_code": 404,
                "message": "The user couldn't be found",
                "details": "User may have deleted their account or blocked the bot",
            },
            {
                "status_code": 401,
                "message": "Invalid channel access token",
                "details": "The provided access token is invalid or expired",
            },
        ]

        error_scenario = random.choice(error_scenarios)

        # 実際のLINE APIで発生する可能性のあるエラーパターン（サンプル）
        error_data = {
            "status_code": error_scenario["status_code"],
            "message": error_scenario["message"],
            "endpoint": "profile",
        }

        analysis = self.analyzer.analyze(error_data)

        result["errors"].append(
            {
                "type": "プロフィール取得エラー",
                "message": error_scenario["message"],
                "details": error_scenario["details"],
                "status_code": error_scenario["status_code"],
                "analysis": analysis,
            }
        )

        return result

    def _simulate_group_member_api_call(
        self, group_id: str, user_id: str
    ) -> Dict[str, Any]:
        """グループメンバープロフィールAPI呼び出しのシミュレーション"""

        result = {"success": False, "errors": []}

        import random

        # 75%の確率で成功
        if random.random() < 0.75:
            user_hash = hashlib.md5(f"{group_id}_{user_id}".encode()).hexdigest()[:8]

            result["success"] = True
            result["profile"] = {
                "userId": user_id,
                "displayName": f"グループメンバー{user_hash}",
                "pictureUrl": f"https://example.com/group_profile/{user_hash}.jpg",
            }
            return result

        # 25%の確率でエラーをシミュレート
        error_scenarios = [
            {
                "status_code": 403,
                "message": "The bot doesn't have permission to access group member information",
                "details": "Bot may not be admin or group settings prevent access",
            },
            {
                "status_code": 404,
                "message": "The user is not a member of the group",
                "details": "User may have left the group",
            },
        ]

        error_scenario = random.choice(error_scenarios)

        # 実際のLINE APIで発生する可能性のあるエラーパターン（サンプル）
        error_data = {
            "status_code": error_scenario["status_code"],
            "message": error_scenario["message"],
            "endpoint": "group.member.profile",
        }

        analysis = self.analyzer.analyze(error_data)

        result["errors"].append(
            {
                "type": "グループメンバープロフィール取得エラー",
                "message": error_scenario["message"],
                "details": error_scenario["details"],
                "status_code": error_scenario["status_code"],
                "analysis": analysis,
            }
        )

        return result

    def _simulate_room_member_api_call(
        self, room_id: str, user_id: str
    ) -> Dict[str, Any]:
        """ルームメンバープロフィールAPI呼び出しのシミュレーション"""

        result = {"success": False, "errors": []}

        import random

        # 75%の確率で成功
        if random.random() < 0.75:
            user_hash = hashlib.md5(f"{room_id}_{user_id}".encode()).hexdigest()[:8]

            result["success"] = True
            result["profile"] = {
                "userId": user_id,
                "displayName": f"ルームメンバー{user_hash}",
                "pictureUrl": f"https://example.com/room_profile/{user_hash}.jpg",
            }
            return result

        # 25%の確率でエラーをシミュレート
        error_scenarios = [
            {
                "status_code": 404,
                "message": "The user is not a member of the room",
                "details": "User may have left the room",
            }
        ]

        error_scenario = random.choice(error_scenarios)

        # 実際のLINE APIで発生する可能性のあるエラーパターン（サンプル）
        error_data = {
            "status_code": error_scenario["status_code"],
            "message": error_scenario["message"],
            "endpoint": "room.member.profile",
        }

        analysis = self.analyzer.analyze(error_data)

        result["errors"].append(
            {
                "type": "ルームメンバープロフィール取得エラー",
                "message": error_scenario["message"],
                "details": error_scenario["details"],
                "status_code": error_scenario["status_code"],
                "analysis": analysis,
            }
        )

        return result

    def _simulate_followers_api_call(self, date: str) -> Dict[str, Any]:
        """フォロワー数API呼び出しのシミュレーション"""

        result = {"success": False, "errors": []}

        import random

        # 85%の確率で成功
        if random.random() < 0.85:
            base_count = 1000
            variation = random.randint(-100, 200)

            result["success"] = True
            result["followers"] = base_count + variation
            result["targetedReaches"] = (base_count + variation) * random.uniform(
                0.3, 0.8
            )
            result["blocks"] = random.randint(5, 20)
            return result

        # 15%の確率でエラーをシミュレート
        error_scenarios = [
            {
                "status_code": 403,
                "message": "Statistics are not available for your account type",
                "details": "Only verified or premium accounts can access statistics",
            },
            {
                "status_code": 400,
                "message": "Statistics for the specified date are not available",
                "details": "Statistics may not be available for dates more than 365 days ago",
            },
        ]

        error_scenario = random.choice(error_scenarios)

        # 実際のLINE APIで発生する可能性のあるエラーパターン（サンプル）
        error_data = {
            "status_code": error_scenario["status_code"],
            "message": error_scenario["message"],
            "endpoint": "insight.followers",
        }

        analysis = self.analyzer.analyze(error_data)

        result["errors"].append(
            {
                "type": "フォロワー数取得エラー",
                "message": error_scenario["message"],
                "details": error_scenario["details"],
                "status_code": error_scenario["status_code"],
                "analysis": analysis,
            }
        )

        return result

    def _generate_interaction_stats(self, user_id: str) -> Dict[str, Any]:
        """ユーザーインタラクション統計の生成"""

        import random

        # ユーザーIDベースのシード値で再現可能な乱数生成
        random.seed(hash(user_id))

        stats = {
            "total_messages": random.randint(10, 500),
            "text_messages": random.randint(5, 300),
            "sticker_messages": random.randint(0, 50),
            "image_messages": random.randint(0, 30),
            "last_interaction": (datetime.now()).isoformat(),
            "favorite_time": f"{random.randint(9, 22):02d}:00-{random.randint(9, 22):02d}:59",
            "response_rate": round(random.uniform(0.7, 1.0), 2),
            "avg_response_time_seconds": random.randint(30, 300),
        }

        return stats


def demo_user_management():
    """ユーザー管理のデモ実行"""

    print("🚀 LINE Bot ユーザー管理エラーハンドリングデモ")
    print("=" * 60)

    user_manager = UserManager("dummy_channel_access_token")

    # テストケース
    test_cases = [
        {
            "name": "正常なユーザープロフィール取得",
            "method": "get_user_profile",
            "args": ["U1234567890123456789012345678901234567890123456789"],
        },
        {
            "name": "無効なユーザーIDフォーマット",
            "method": "get_user_profile",
            "args": ["invalid-user-id"],
        },
        {"name": "空のユーザーID", "method": "get_user_profile", "args": [""]},
        {
            "name": "正常なグループメンバープロフィール取得",
            "method": "get_group_member_profile",
            "args": [
                "C1234567890123456789012345678901234567890123456789",
                "U1234567890123456789012345678901234567890123456789",
            ],
        },
        {
            "name": "無効なグループIDフォーマット",
            "method": "get_group_member_profile",
            "args": [
                "invalid-group-id",
                "U1234567890123456789012345678901234567890123456789",
            ],
        },
        {
            "name": "正常なルームメンバープロフィール取得",
            "method": "get_room_member_profile",
            "args": [
                "R1234567890123456789012345678901234567890123456789",
                "U1234567890123456789012345678901234567890123456789",
            ],
        },
        {"name": "正常なフォロワー数取得", "method": "get_followers_count", "args": []},
        {
            "name": "日付指定でフォロワー数取得",
            "method": "get_followers_count",
            "args": ["20241201"],
        },
        {
            "name": "無効な日付フォーマット",
            "method": "get_followers_count",
            "args": ["2024-12-01"],
        },
        {
            "name": "インタラクション統計取得",
            "method": "get_user_interaction_stats",
            "args": ["U1234567890123456789012345678901234567890123456789"],
        },
    ]

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 テストケース {i}: {test_case['name']}")
        print("-" * 40)

        method = getattr(user_manager, test_case["method"])
        result = method(*test_case["args"])

        print(f"📊 実行結果:")
        print(f"   • 成功: {result['success']}")
        print(f"   • 操作: {result['operation']}")

        if result["success"]:
            print("✅ 取得成功")

            if "profile" in result:
                profile = result["profile"]
                print(f"   • 表示名: {profile.get('displayName', 'N/A')}")
                if result.get("from_cache"):
                    print("   • データソース: キャッシュ")
                else:
                    print("   • データソース: API")

            if "followers" in result:
                print(f"   • フォロワー数: {result['followers']:,}人")
                print(f"   • ターゲットリーチ: {result['targetedReaches']:,.0f}人")
                print(f"   • ブロック数: {result['blocks']:,}人")

            if "stats" in result:
                stats = result["stats"]
                print(f"   • 総メッセージ数: {stats['total_messages']:,}件")
                print(f"   • 応答率: {stats['response_rate']*100:.1f}%")
                print(f"   • 平均応答時間: {stats['avg_response_time_seconds']}秒")

        else:
            print("❌ 取得失敗")
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
    print(f"   • キャッシュエントリ数: {len(user_manager.user_cache)}")
    print(f"   • エラーログ数: {len(user_manager.error_log)}")

    # キャッシュテスト（同じユーザーを再度取得）
    print(f"\n🔄 キャッシュテスト:")
    print("同じユーザープロフィールを2回取得してキャッシュ動作を確認")

    user_id = "U1234567890123456789012345678901234567890123456789"

    print("1回目:")
    result1 = user_manager.get_user_profile(user_id)
    if result1["success"]:
        print(
            f"   データソース: {'キャッシュ' if result1.get('from_cache') else 'API'}"
        )

    print("2回目（すぐ後）:")
    result2 = user_manager.get_user_profile(user_id)
    if result2["success"]:
        print(
            f"   データソース: {'キャッシュ' if result2.get('from_cache') else 'API'}"
        )


if __name__ == "__main__":
    demo_user_management()
