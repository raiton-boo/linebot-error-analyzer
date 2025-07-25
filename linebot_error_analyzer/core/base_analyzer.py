"""
LINE Bot エラー分析器 - ベースクラス

同期・非同期分析器の共通ロジックを提供するベースクラス。
エラータイプ判定、分析メソッドの基本実装を含む。
"""

from __future__ import annotations
import json
from typing import Any, Dict, List, Optional, Union, TYPE_CHECKING
from .models import LineErrorInfo, ErrorCategory, ErrorSeverity
from ..database import ErrorDatabase
from ..exceptions import AnalyzerError, UnsupportedErrorTypeError, InvalidErrorDataError
from ..utils.log_parser import LogParser

if TYPE_CHECKING:
    from ..utils.types import (
        SupportedErrorType,
        StatusCode,
        ErrorMessage,
        Headers,
        RawErrorData,
        RequestId,
    )


class BaseLineErrorAnalyzer:
    """
    LINE Bot エラー分析器ベースクラス

    同期・非同期分析器の共通ロジックを提供。
    エラータイプ判定、分析メソッドの基本実装を含む。
    """

    def __init__(self) -> None:
        """ベース分析器を初期化"""
        self.db: ErrorDatabase = ErrorDatabase()
        self.log_parser: LogParser = LogParser()

    # エラータイプ判定メソッド

    def _is_v3(self, error: "SupportedErrorType") -> bool:
        """v3 ApiExceptionかどうか判定"""
        return (
            hasattr(error, "__module__")
            and "linebot.v3" in str(error.__module__)
            and hasattr(error, "status")
            and hasattr(error, "body")
        )

    def _is_v3_sig(self, error: "SupportedErrorType") -> bool:
        """v3 署名エラーかどうか判定"""
        return (
            hasattr(error, "__module__")
            and "linebot.v3" in str(error.__module__)
            and (
                "InvalidSignatureError" in str(type(error))
                or (
                    hasattr(error, "__class__")
                    and hasattr(error.__class__, "__name__")
                    and error.__class__.__name__ == "InvalidSignatureError"
                )
            )
        )

    def _is_v2(self, error: "SupportedErrorType") -> bool:
        """v2 LineBotApiErrorかどうか判定"""
        return (
            hasattr(error, "__module__")
            and "linebot" in str(error.__module__)
            and "v3" not in str(error.__module__)
            and hasattr(error, "status_code")
            and hasattr(error, "error")
        )

    def _is_v2_sig(self, error: "SupportedErrorType") -> bool:
        """v2 署名エラーかどうか判定"""
        return (
            hasattr(error, "__module__")
            and "linebot" in str(error.__module__)
            and "v3" not in str(error.__module__)
            and "InvalidSignatureError" in str(type(error))
        )

    # 共通分析メソッド

    def _analyze_v3_sig(self, error: Any) -> LineErrorInfo:
        """v3 署名エラーの分析"""
        return self._create_info(
            status_code=400,
            message=str(error),
            headers={},
            error_data={},
            request_id=None,
            category=ErrorCategory.INVALID_SIGNATURE,
            severity=ErrorSeverity.CRITICAL,
            is_retryable=False,
            description=self.db.get_error_details(ErrorCategory.INVALID_SIGNATURE)[
                "description"
            ],
            recommended_action=self.db.get_error_details(
                ErrorCategory.INVALID_SIGNATURE
            )["action"],
            documentation_url=self.db.get_error_details(
                ErrorCategory.INVALID_SIGNATURE
            )["doc_url"],
            raw_error={"error_type": "InvalidSignatureError", "message": str(error)},
        )

    def _analyze_v2_sig(self, error: Any) -> LineErrorInfo:
        """v2 署名エラーの分析"""
        return self._create_info(
            status_code=400,
            message=str(error),
            headers={},
            error_data={},
            request_id=None,
            category=ErrorCategory.INVALID_SIGNATURE,
            severity=ErrorSeverity.CRITICAL,
            is_retryable=False,
            description=self.db.get_error_details(ErrorCategory.INVALID_SIGNATURE)[
                "description"
            ],
            recommended_action=self.db.get_error_details(
                ErrorCategory.INVALID_SIGNATURE
            )["action"],
            documentation_url=self.db.get_error_details(
                ErrorCategory.INVALID_SIGNATURE
            )["doc_url"],
            raw_error={"error_type": "InvalidSignatureError", "message": str(error)},
        )

    def _analyze_dict(self, error: Dict[str, Any]) -> LineErrorInfo:
        """辞書形式のエラーデータを分析"""
        # status_codeの型変換（文字列や浮動小数点も受け入れる）
        raw_status_code = error.get("status_code", 0)
        try:
            if isinstance(raw_status_code, (int, float)):
                status_code = int(raw_status_code)
            elif isinstance(raw_status_code, str) and raw_status_code.isdigit():
                status_code = int(raw_status_code)
            else:
                status_code = 0
        except (ValueError, TypeError):
            status_code = 0

        message = error.get("message", "Unknown error")
        error_code = error.get("error_code")
        headers = error.get("headers", {})
        details = error.get("details", [])
        request_id = error.get("request_id")

        return self._create_info(
            status_code=status_code,
            message=message,
            headers=headers,
            error_data=error,
            request_id=request_id,
            error_code=error_code,
            raw_error=error,
        )

    def _analyze_response(self, error: Any) -> LineErrorInfo:
        """HTTPレスポンス類似オブジェクトを分析"""
        try:
            status_code = getattr(error, "status_code", 0)
            headers = {}

            # ヘッダーの安全な取得
            if hasattr(error, "headers"):
                try:
                    headers = dict(error.headers) if error.headers else {}
                except (TypeError, ValueError):
                    headers = {}

            # テキストレスポンスの取得とJSON解析試行
            message = "Unknown error"
            error_data = {}

            if hasattr(error, "text"):
                try:
                    response_text = error.text
                    if isinstance(response_text, str):
                        try:
                            parsed_data = json.loads(response_text)
                            if isinstance(parsed_data, dict):
                                error_data = parsed_data
                                message = parsed_data.get("message", response_text)
                            else:
                                message = response_text
                        except json.JSONDecodeError:
                            message = response_text
                    else:
                        message = str(response_text)
                except (AttributeError, TypeError):
                    pass

            return self._create_info(
                status_code=status_code,
                message=message,
                headers=headers,
                error_data=error_data,
                request_id=headers.get("x-line-request-id")
                or headers.get("X-Line-Request-Id"),
                raw_error=error_data
                or {"status_code": status_code, "message": message},
            )

        except Exception as e:
            raise AnalyzerError(f"レスポンス形式オブジェクトの分析に失敗しました: {str(e)}", e)

    # ========== ヘルパーメソッド ==========

    def _create_info(
        self,
        status_code: int,
        message: str,
        headers: Dict[str, str],
        error_data: Dict[str, Any],
        request_id: Optional[str] = None,
        error_code: Optional[str] = None,
        category: Optional[ErrorCategory] = None,
        severity: Optional[ErrorSeverity] = None,
        is_retryable: Optional[bool] = None,
        description: Optional[str] = None,
        recommended_action: Optional[str] = None,
        documentation_url: Optional[str] = None,
        raw_error: Optional[Dict[str, Any]] = None,
    ) -> LineErrorInfo:
        """LineErrorInfoオブジェクトを作成する共通メソッド"""

        # 自動分析（引数で指定されていない場合）
        if category is None or severity is None or is_retryable is None:
            auto_category, auto_severity, auto_retryable = self.db.analyze_error(
                status_code, message
            )
            category = category or auto_category
            severity = severity or auto_severity
            is_retryable = is_retryable if is_retryable is not None else auto_retryable

        # 詳細情報の取得
        if (
            description is None
            or recommended_action is None
            or documentation_url is None
        ):
            details = self.db.get_error_details(category)
            description = description or details["description"]
            recommended_action = recommended_action or details["action"]
            documentation_url = documentation_url or details["doc_url"]

        # retry_afterの取得
        retry_after = None
        if is_retryable:
            if category == ErrorCategory.RATE_LIMIT:
                retry_after = self._extract_retry_after(headers)
                # ヘッダーにない場合はデフォルト値を使用
                if retry_after is None:
                    retry_after = 60  # RATE_LIMITのデフォルト
            elif category == ErrorCategory.SERVER_ERROR:
                # サーバーエラーのデフォルトリトライ時間
                retry_after = 10

        # 詳細情報の抽出
        details_list = (
            error_data.get("details", []) if isinstance(error_data, dict) else []
        )

        return LineErrorInfo(
            status_code=status_code,
            error_code=error_code,
            message=message,
            category=category,
            severity=severity,
            is_retryable=is_retryable,
            description=description,
            recommended_action=recommended_action,
            retry_after=retry_after,
            details=details_list,
            raw_error=raw_error or {},
            request_id=request_id,
            headers=headers,
            documentation_url=documentation_url,
        )

    def _extract_retry_after(self, headers: Dict[str, str]) -> Optional[int]:
        """Retry-Afterヘッダーからリトライ時間を抽出"""
        retry_after_header = headers.get("Retry-After") or headers.get("retry-after")
        if retry_after_header:
            try:
                return int(retry_after_header)
            except (ValueError, TypeError):
                pass
        return None

    def _safe_get_attribute(self, obj: Any, attr: str, default: Any = None) -> Any:
        """オブジェクトから属性を安全に取得"""
        try:
            return getattr(obj, attr, default)
        except (AttributeError, TypeError):
            return default

    def _safe_dict_conversion(self, obj: Any) -> Dict[str, Any]:
        """オブジェクトを辞書に安全に変換"""
        try:
            if hasattr(obj, "items"):
                return dict(obj.items())
            elif hasattr(obj, "__iter__") and not isinstance(obj, (str, bytes)):
                return dict(obj)
            else:
                return {}
        except (TypeError, AttributeError, ValueError):
            return {}

    def _analyze_log_string(
        self, 
        log_string: str, 
        api_pattern: Optional[str] = None
    ) -> LineErrorInfo:
        """
        エラーログ文字列を解析してLineErrorInfoを返す
        
        Args:
            log_string: 解析対象のログ文字列
            api_pattern: APIパターン（例: "user.user_profile", "message.message_push"）
            
        Returns:
            LineErrorInfo: ログ文字列の分析結果
            
        Raises:
            AnalyzerError: ログ解析処理中のエラー
        """
        try:
            # ログ文字列を解析
            if not self.log_parser.is_parseable(log_string):
                raise AnalyzerError(f"ログ文字列を解析できません: {log_string[:100]}...")
            
            parsed = self.log_parser.parse(log_string)
            
            # パースしたデータから辞書形式のエラーデータを構築
            error_data = {}
            if parsed.status_code is not None:
                error_data["status_code"] = parsed.status_code
            if parsed.message:
                error_data["message"] = parsed.message
            if parsed.headers:
                error_data["headers"] = parsed.headers
            if parsed.body:
                error_data.update(parsed.body)
            if parsed.request_id:
                error_data["request_id"] = parsed.request_id
            
            # メッセージが設定されていない場合はreasonまたはデフォルト値を使用
            message = parsed.message or parsed.reason or "Unknown error"
            
            # APIパターンを考慮した分析
            category, severity, is_retryable = self._analyze_with_pattern(
                parsed.status_code or 0,
                message,
                api_pattern
            )
            
            return self._create_info(
                status_code=parsed.status_code or 0,
                message=message,
                headers=parsed.headers,
                error_data=error_data,
                request_id=parsed.request_id,
                category=category,
                severity=severity,
                is_retryable=is_retryable,
                raw_error={
                    "log_string": log_string,
                    "parsed_data": {
                        "status_code": parsed.status_code,
                        "reason": parsed.reason,
                        "message": parsed.message,
                        "headers": parsed.headers,
                        "body": parsed.body,
                        "request_id": parsed.request_id,
                    },
                    "api_pattern": api_pattern,
                },
            )
            
        except Exception as e:
            raise AnalyzerError(
                f"ログ文字列の分析に失敗しました: {str(e)}。"
                f"ログ抜粋: {log_string[:100]}...",
                e,
            )

    def _analyze_with_pattern(
        self, 
        status_code: int, 
        message: str, 
        api_pattern: Optional[str]
    ) -> tuple[ErrorCategory, ErrorSeverity, bool]:
        """
        APIパターンを考慮したエラー分析
        
        Args:
            status_code: HTTPステータスコード
            message: エラーメッセージ
            api_pattern: APIパターン文字列
            
        Returns:
            tuple: (ErrorCategory, ErrorSeverity, is_retryable)
        """
        # 基本的な分析結果を取得
        base_category, base_severity, base_retryable = self.db.analyze_error(
            status_code, message
        )
        
        # APIパターンが指定されていない場合は基本分析結果を返す
        if not api_pattern:
            return base_category, base_severity, base_retryable
        
        # パターン固有の分析を実行
        return self._analyze_pattern_specific_error(
            status_code, message, api_pattern, base_category, base_severity, base_retryable
        )

    def _analyze_pattern_specific_error(
        self,
        status_code: int,
        message: str,
        api_pattern: str,
        base_category: ErrorCategory,
        base_severity: ErrorSeverity,
        base_retryable: bool,
    ) -> tuple[ErrorCategory, ErrorSeverity, bool]:
        """
        APIパターン固有のエラー分析
        
        Args:
            status_code: HTTPステータスコード
            message: エラーメッセージ
            api_pattern: APIパターン
            base_category: 基本カテゴリ
            base_severity: 基本重要度
            base_retryable: 基本リトライ可否
            
        Returns:
            tuple: (ErrorCategory, ErrorSeverity, is_retryable)
        """
        message_lower = message.lower()
        
        # ユーザー関連APIパターンの特別処理
        if api_pattern.startswith("user."):
            return self._analyze_user_pattern_error(
                status_code, message_lower, base_category, base_severity, base_retryable
            )
        
        # メッセージ関連APIパターンの特別処理
        elif api_pattern.startswith("message."):
            return self._analyze_message_pattern_error(
                status_code, message_lower, base_category, base_severity, base_retryable
            )
        
        # リッチメニュー関連APIパターンの特別処理
        elif api_pattern.startswith("rich_menu."):
            return self._analyze_rich_menu_pattern_error(
                status_code, message_lower, base_category, base_severity, base_retryable
            )
        
        # その他のパターンは基本分析結果を返す
        return base_category, base_severity, base_retryable

    def _analyze_user_pattern_error(
        self,
        status_code: int,
        message_lower: str,
        base_category: ErrorCategory,
        base_severity: ErrorSeverity,
        base_retryable: bool,
    ) -> tuple[ErrorCategory, ErrorSeverity, bool]:
        """ユーザー関連APIパターンのエラー分析"""
        
        # 404エラーの詳細分析
        if status_code == 404:
            if any(keyword in message_lower for keyword in ["not found", "blocked", "unavailable"]):
                return ErrorCategory.USER_BLOCKED, ErrorSeverity.MEDIUM, False
            elif "profile" in message_lower:
                return ErrorCategory.PROFILE_NOT_ACCESSIBLE, ErrorSeverity.MEDIUM, False
            else:
                return ErrorCategory.USER_NOT_FOUND, ErrorSeverity.MEDIUM, False
        
        # 403エラーの詳細分析  
        elif status_code == 403:
            if "profile" in message_lower:
                return ErrorCategory.PROFILE_NOT_ACCESSIBLE, ErrorSeverity.HIGH, False
            else:
                return ErrorCategory.FORBIDDEN, ErrorSeverity.HIGH, False
        
        return base_category, base_severity, base_retryable

    def _analyze_message_pattern_error(
        self,
        status_code: int,
        message_lower: str,
        base_category: ErrorCategory,
        base_severity: ErrorSeverity,
        base_retryable: bool,
    ) -> tuple[ErrorCategory, ErrorSeverity, bool]:
        """メッセージ関連APIパターンのエラー分析"""
        
        # 400エラーの詳細分析
        if status_code == 400:
            if any(keyword in message_lower for keyword in ["reply token", "token"]):
                if "expired" in message_lower:
                    return ErrorCategory.REPLY_TOKEN_EXPIRED, ErrorSeverity.HIGH, False
                elif "used" in message_lower:
                    return ErrorCategory.REPLY_TOKEN_USED, ErrorSeverity.HIGH, False
                else:
                    return ErrorCategory.INVALID_REPLY_TOKEN, ErrorSeverity.HIGH, False
            elif "payload" in message_lower and "large" in message_lower:
                return ErrorCategory.PAYLOAD_TOO_LARGE, ErrorSeverity.MEDIUM, False
        
        return base_category, base_severity, base_retryable

    def _analyze_rich_menu_pattern_error(
        self,
        status_code: int,
        message_lower: str,
        base_category: ErrorCategory,
        base_severity: ErrorSeverity,
        base_retryable: bool,
    ) -> tuple[ErrorCategory, ErrorSeverity, bool]:
        """リッチメニュー関連APIパターンのエラー分析"""
        
        # 400エラーの詳細分析
        if status_code == 400:
            if any(keyword in message_lower for keyword in ["size", "image", "dimension"]):
                return ErrorCategory.RICH_MENU_SIZE_ERROR, ErrorSeverity.MEDIUM, False
            elif "rich" in message_lower and "menu" in message_lower:
                return ErrorCategory.RICH_MENU_ERROR, ErrorSeverity.MEDIUM, False
        
        return base_category, base_severity, base_retryable
