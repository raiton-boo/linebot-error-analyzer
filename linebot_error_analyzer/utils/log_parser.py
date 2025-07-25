"""
エラーログ文字列パーサー

LINE Bot APIのエラーログ文字列を解析し、構造化されたデータを抽出する。
正規表現パターンを使用してステータスコード、メッセージ、ヘッダー等を抽出。
"""

import re
import json
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass


@dataclass
class ParsedLogData:
    """
    パースされたログデータ
    
    Args:
        status_code: HTTPステータスコード
        reason: HTTPレスポンス理由フレーズ
        message: エラーメッセージ
        headers: HTTPヘッダー辞書
        body: レスポンスボディ（JSONまたは文字列）
        request_id: LINE APIリクエストID
        raw_log: 元のログ文字列
    """
    status_code: Optional[int] = None
    reason: Optional[str] = None
    message: Optional[str] = None
    headers: Dict[str, str] = None
    body: Optional[Dict[str, Any]] = None
    request_id: Optional[str] = None
    raw_log: str = ""
    
    def __post_init__(self):
        if self.headers is None:
            self.headers = {}
        if self.body is None:
            self.body = {}


class LogParser:
    """
    LINE Bot APIエラーログ文字列パーサー
    
    様々な形式のエラーログ文字列を解析し、構造化されたデータを抽出する。
    複数の正規表現パターンを使用して、異なるログ形式に対応。
    """
    
    def __init__(self):
        """パーサー初期化: 正規表現パターンを構築"""
        self._init_patterns()
    
    def _init_patterns(self):
        """正規表現パターンの初期化"""
        
        # ステータスコード抽出パターン（様々な形式に対応）
        self.status_code_patterns = [
            r'\((\d{3})\)',  # (404)
            r'HTTP\s+(\d{3})',  # HTTP 404
            r'Status:\s*(\d{3})',  # Status: 404
            r'status_code:\s*(\d{3})',  # status_code: 404
            r'(\d{3})\s+[A-Za-z]',  # 404 Not Found
        ]
        
        # HTTPレスポンス理由フレーズ抽出パターン
        self.reason_patterns = [
            r'Reason:\s*(.+?)(?:\n|$)',  # Reason: Not Found
            r'\(\d{3}\)\s*(.+?)(?:\n|$)',  # (404) Not Found
            r'\d{3}\s+(.+?)(?:\n|$)',  # 404 Not Found
        ]
        
        # HTTPヘッダー抽出パターン
        self.headers_patterns = [
            r'HTTP response headers:\s*(.+?)(?:\n|HTTP response body|$)',
            r'Headers:\s*(.+?)(?:\n|Body|$)',
            r'headers:\s*(.+?)(?:\n|body|$)',
        ]
        
        # HTTPレスポンスボディ抽出パターン
        self.body_patterns = [
            r'HTTP response body:\s*(.+?)(?:\n|$)',
            r'Body:\s*(.+?)(?:\n|$)',
            r'body:\s*(.+?)(?:\n|$)',
            r'Response:\s*(.+?)(?:\n|$)',
        ]
        
        # リクエストID抽出パターン
        self.request_id_patterns = [
            r'x-line-request-id[\'"]?\s*:\s*[\'"]([^\'"\s,}]+)',
            r'X-Line-Request-Id[\'"]?\s*:\s*[\'"]([^\'"\s,}]+)',
            r'request.id[\'"]?\s*:\s*[\'"]([^\'"\s,}]+)',
        ]
        
        # HTTPHeaderDict形式の解析パターン
        self.header_dict_pattern = r'HTTPHeaderDict\((\{.+?\})\)'
        
        # JSON形式のボディパターン
        self.json_body_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
    
    def parse(self, log_string: str) -> ParsedLogData:
        """
        ログ文字列を解析して構造化データを抽出
        
        Args:
            log_string: 解析対象のログ文字列
            
        Returns:
            ParsedLogData: 抽出された構造化データ
        """
        parsed = ParsedLogData(raw_log=log_string)
        
        # ステータスコード抽出
        parsed.status_code = self._extract_status_code(log_string)
        
        # レスポンス理由フレーズ抽出
        parsed.reason = self._extract_reason(log_string)
        
        # ヘッダー抽出
        parsed.headers = self._extract_headers(log_string)
        
        # ボディ抽出
        parsed.body = self._extract_body(log_string)
        
        # リクエストID抽出（ヘッダーまたは直接）
        parsed.request_id = self._extract_request_id(log_string, parsed.headers)
        
        # メッセージ抽出（ボディまたは理由フレーズから）
        parsed.message = self._extract_message(parsed.body, parsed.reason)
        
        return parsed
    
    def _extract_status_code(self, log_string: str) -> Optional[int]:
        """ステータスコードを抽出"""
        for pattern in self.status_code_patterns:
            match = re.search(pattern, log_string)
            if match:
                try:
                    return int(match.group(1))
                except (ValueError, IndexError):
                    continue
        return None
    
    def _extract_reason(self, log_string: str) -> Optional[str]:
        """HTTPレスポンス理由フレーズを抽出"""
        for pattern in self.reason_patterns:
            match = re.search(pattern, log_string, re.IGNORECASE)
            if match:
                reason = match.group(1).strip()
                if reason:
                    return reason
        return None
    
    def _extract_headers(self, log_string: str) -> Dict[str, str]:
        """HTTPヘッダーを抽出"""
        headers = {}
        
        # ヘッダー部分を検索
        for pattern in self.headers_patterns:
            match = re.search(pattern, log_string, re.DOTALL | re.IGNORECASE)
            if match:
                headers_text = match.group(1).strip()
                
                # HTTPHeaderDict形式の場合
                dict_match = re.search(self.header_dict_pattern, headers_text)
                if dict_match:
                    try:
                        headers_dict_str = dict_match.group(1)
                        # Pythonの辞書形式をJSONに変換
                        headers_dict_str = re.sub(r"'", '"', headers_dict_str)
                        headers_data = json.loads(headers_dict_str)
                        headers.update(headers_data)
                    except (json.JSONDecodeError, IndexError):
                        pass
                
                # キー:値 形式のヘッダーを解析
                if not headers:  # HTTPHeaderDict形式で解析できなかった場合
                    # Python辞書形式を処理
                    if headers_text.startswith('{') and headers_text.endswith('}'):
                        try:
                            # Python辞書形式をJSONに変換
                            dict_str = re.sub(r"'", '"', headers_text)
                            headers_data = json.loads(dict_str)
                            headers.update(headers_data)
                        except (json.JSONDecodeError, ValueError):
                            # 手動でパースする
                            content = headers_text.strip('{}')
                            pairs = re.findall(r"'([^']+)':\s*'([^']+)'", content)
                            for key, value in pairs:
                                headers[key] = value
                    else:
                        # 通常のキー:値形式
                        header_lines = headers_text.split(',') if ',' in headers_text else [headers_text]
                        for line in header_lines:
                            if ':' in line:
                                try:
                                    key, value = line.split(':', 1)
                                    key = key.strip().strip('\'"')
                                    value = value.strip().strip('\'"')
                                    if key and value:
                                        headers[key] = value
                                except ValueError:
                                    continue
                
                if headers:
                    break
        
        return headers
    
    def _extract_body(self, log_string: str) -> Optional[Dict[str, Any]]:
        """HTTPレスポンスボディを抽出"""
        
        # ボディ部分を検索
        for pattern in self.body_patterns:
            match = re.search(pattern, log_string, re.DOTALL | re.IGNORECASE)
            if match:
                body_text = match.group(1).strip()
                
                # JSON形式かチェック
                json_match = re.search(self.json_body_pattern, body_text)
                if json_match:
                    try:
                        return json.loads(json_match.group(0))
                    except json.JSONDecodeError:
                        pass
                
                # JSON形式でない場合、文字列として返す
                if body_text:
                    return {"message": body_text}
        
        return None
    
    def _extract_request_id(self, log_string: str, headers: Dict[str, str]) -> Optional[str]:
        """リクエストIDを抽出"""
        
        # まずヘッダーから検索
        for header_key in ['x-line-request-id', 'X-Line-Request-Id']:
            if header_key in headers:
                return headers[header_key]
        
        # ヘッダーにない場合、ログ文字列から直接検索
        for pattern in self.request_id_patterns:
            match = re.search(pattern, log_string, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_message(self, body: Optional[Dict[str, Any]], reason: Optional[str]) -> str:
        """エラーメッセージを抽出"""
        
        # ボディからメッセージ抽出
        if body and isinstance(body, dict):
            if 'message' in body:
                return body['message']
            elif 'error' in body:
                return str(body['error'])
            elif 'details' in body:
                return str(body['details'])
        
        # 理由フレーズを使用
        if reason:
            return reason
        
        return "Unknown error"
    
    def is_parseable(self, log_string: str) -> bool:
        """
        ログ文字列が解析可能かどうかを判定
        
        Args:
            log_string: 判定対象のログ文字列
            
        Returns:
            bool: 解析可能な場合True
        """
        if not log_string or not isinstance(log_string, str):
            return False
        
        # 最低限ステータスコードまたはエラー関連キーワードが含まれているかチェック
        has_status_code = any(
            re.search(pattern, log_string) for pattern in self.status_code_patterns
        )
        
        has_error_keywords = bool(re.search(
            r'(error|fail|exception|invalid|unauthorized|forbidden|not found|timeout)',
            log_string, re.IGNORECASE
        ))
        
        return has_status_code or has_error_keywords