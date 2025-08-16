"""
LINE Bot エラー分析 - ログパーサー

エラーログ文字列をパースしてLogParseResultを生成する機能。
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, TYPE_CHECKING
import re

if TYPE_CHECKING:
    from .error_info import LineErrorInfo


@dataclass
class LogParseResult:
    """エラーログ文字列のパース結果"""

    status_code: Optional[int] = None
    message: Optional[str] = None
    headers: Dict[str, str] = field(default_factory=dict)
    request_id: Optional[str] = None
    raw_body: Optional[str] = None
    parse_success: bool = False

    def to_basic_error_info(self) -> "LineErrorInfo":
        """基本情報のみのLineErrorInfoに変換"""
        from .error_info import LineErrorInfo

        return LineErrorInfo(
            status_code=self.status_code or 0,
            message=self.message or "Unknown error",
            category=None,  # パターン未指定
            is_retryable=None,  # パターン未指定
            description="",
            recommended_action="",
            request_id=self.request_id,
            headers=self.headers,
            raw_error={"raw_log": self.raw_body} if self.raw_body else {},
        )


class LogParser:
    """エラーログ文字列をパースするクラス"""

    # 正規表現パターン（issueの例に基づく）
    LOG_PATTERNS = {
        "status_code": r"\((\d+)\)",
        "reason": r"Reason:\s*(.+?)(?:\n|$)",
        "message": r'"message":\s*"([^"]*)"',
        "request_id": r"'x-line-request-id':\s*'([^']*)'",
        "headers": r"HTTPHeaderDict\((\{[^}]+\})\)",
        "response_body": r"HTTP response body:\s*(.+?)(?:\n\n|$)",
    }

    @classmethod
    def parse(cls, log_text: str) -> LogParseResult:
        """ログテキストをパースしてLogParseResultを返す"""
        result = LogParseResult(raw_body=log_text)

        try:
            # ステータスコードの抽出
            status_match = re.search(cls.LOG_PATTERNS["status_code"], log_text)
            if status_match:
                result.status_code = int(status_match.group(1))

            # メッセージの抽出（JSON形式を優先）
            message_match = re.search(cls.LOG_PATTERNS["message"], log_text)
            if message_match:
                result.message = message_match.group(1)
            else:
                # JSON形式がない場合はReasonを使用
                reason_match = re.search(cls.LOG_PATTERNS["reason"], log_text)
                if reason_match:
                    result.message = reason_match.group(1).strip()

            # リクエストIDの抽出
            request_id_match = re.search(cls.LOG_PATTERNS["request_id"], log_text)
            if request_id_match:
                result.request_id = request_id_match.group(1)

            # ヘッダー情報の抽出
            headers_match = re.search(cls.LOG_PATTERNS["headers"], log_text)
            if headers_match:
                headers_str = headers_match.group(1)
                # 簡易的なヘッダーパース（完全なJSONパースではなく）
                header_pairs = re.findall(r"'([^']+)':\s*'([^']*)'", headers_str)
                result.headers = dict(header_pairs)

            # パース成功の判定
            if result.status_code is not None or result.message:
                result.parse_success = True

        except Exception as e:
            # パース失敗時はそのままにしておく
            result.parse_success = False

        return result
