# 📋 LINE API エラーコード詳細リファレンス

LINE Messaging API のエラーコードの完全なリファレンスです。

## エラーコード体系

LINE API のエラーコードは以下の体系で構成されています：

- **40001-40009**: 認証・トークン関連エラー
- **40010-40099**: リクエスト形式エラー
- **40100-40199**: メッセージ関連エラー
- **40400-40499**: ユーザー・リソース関連エラー
- **42901-42999**: レート制限・クォータエラー
- **50000-50099**: サーバーエラー

## 主要エラーコード一覧

### 🔑 認証・トークン関連（40001-40009）

| エラーコード | HTTP Status | カテゴリ          | 説明                               | 対処法                               |
| ------------ | ----------- | ----------------- | ---------------------------------- | ------------------------------------ |
| `40001`      | 401         | INVALID_TOKEN     | 無効なチャネルアクセストークン     | 正しいトークンを取得・設定           |
| `40002`      | 401         | INVALID_TOKEN     | チャネルアクセストークンが期限切れ | 新しいトークンを発行                 |
| `40003`      | 401         | AUTH_ERROR        | 認証に失敗                         | 認証情報を確認                       |
| `40004`      | 401         | INVALID_SIGNATURE | 署名検証に失敗                     | Webhook 設定と署名生成ロジックを確認 |

### 📝 リクエスト形式エラー（40010-40099）

| エラーコード | HTTP Status | カテゴリ             | 説明                     | 対処法                     |
| ------------ | ----------- | -------------------- | ------------------------ | -------------------------- |
| `40010`      | 400         | INVALID_REQUEST_BODY | 無効なリクエストボディ   | リクエスト形式を確認       |
| `40011`      | 400         | INVALID_JSON         | JSON 形式が不正          | JSON 構文を確認            |
| `40012`      | 400         | INVALID_PARAM        | 無効なパラメータ         | パラメータの値と形式を確認 |
| `40013`      | 400         | INVALID_PARAM        | 必須パラメータが不足     | 必要なパラメータを追加     |
| `40014`      | 400         | PAYLOAD_TOO_LARGE    | リクエストサイズが大きい | リクエストサイズを削減     |

### 💬 メッセージ関連エラー（40100-40199）

| エラーコード | HTTP Status | カテゴリ            | 説明                  | 対処法                 |
| ------------ | ----------- | ------------------- | --------------------- | ---------------------- |
| `40100`      | 400         | INVALID_REPLY_TOKEN | 無効な replyToken     | 正しいトークンを使用   |
| `40101`      | 400         | REPLY_TOKEN_EXPIRED | replyToken の期限切れ | 新しいイベントで再送信 |
| `40102`      | 400         | REPLY_TOKEN_USED    | replyToken 使用済み   | 重複送信を避ける       |

### 👤 ユーザー・リソース関連（40400-40499）

| エラーコード | HTTP Status | カテゴリ               | 説明                   | 対処法             |
| ------------ | ----------- | ---------------------- | ---------------------- | ------------------ |
| `40400`      | 404         | USER_NOT_FOUND         | ユーザーが見つからない | ユーザー ID を確認 |
| `40401`      | 404         | USER_NOT_FOUND         | 無効なユーザー ID      | 正しい ID を使用   |
| `40402`      | 403         | PROFILE_NOT_ACCESSIBLE | プロフィール取得不可   | アクセス権限を確認 |

### ⏱️ レート制限・クォータ（42901-42999）

| エラーコード | HTTP Status | カテゴリ       | 説明                 | 対処法             |
| ------------ | ----------- | -------------- | -------------------- | ------------------ |
| `42901`      | 429         | RATE_LIMIT     | API コール回数の上限 | 時間をおいて再実行 |
| `42902`      | 429         | QUOTA_EXCEEDED | メッセージ配信数上限 | 月次制限を確認     |

**分析例:**

```python
from line_bot_error_analyzer import LineErrorAnalyzer

analyzer = LineErrorAnalyzer()

# エラーコード 40001 の分析
error_data = {
    "status_code": 401,
    "error_code": "40001",
    "message": "Invalid token"
}

result = analyzer.analyze(error_data)
print(f"カテゴリ: {result.category.value}")        # INVALID_TOKEN
print(f"重要度: {result.severity.value}")          # CRITICAL
print(f"リトライ可能: {result.is_retryable}")      # False
print(f"対処法: {result.recommended_action}")
```

```python
# JSON エラーの検出と対処
error_data = {
    "status_code": 400,
    "error_code": "40011",
    "message": "Invalid JSON format"
}

result = analyzer.analyze(error_data)
print(f"カテゴリ: {result.category.value}")  # INVALID_JSON
print(f"対処法: {result.recommended_action}")
```

### メッセージ関連エラー（40100-40199）

| エラーコード | HTTP Status | カテゴリ               | 説明                      | 対処法                                             |
| ------------ | ----------- | ---------------------- | ------------------------- | -------------------------------------------------- |
| `40100`      | 400         | INVALID_REPLY_TOKEN    | 無効な replyToken         | 正しい replyToken を使用してください               |
| `40101`      | 400         | REPLY_TOKEN_EXPIRED    | replyToken の有効期限切れ | 新しいイベントからの replyToken を使用してください |
| `40102`      | 400         | REPLY_TOKEN_USED       | replyToken は既に使用済み | 未使用の replyToken を使用してください             |
| `40103`      | 400         | INVALID_REPLY_TOKEN    | replyToken が存在しません | 有効な replyToken を確認してください               |
| `40110`      | 400         | MESSAGE_SEND_FAILED    | メッセージの送信に失敗    | メッセージ内容と設定を確認してください             |
| `40120`      | 400         | INVALID_MESSAGE_FORMAT | メッセージ形式が無効      | メッセージ形式を確認してください                   |

**replyToken エラーの詳細:**

```python
# replyToken の使用パターン
try:
    line_bot_api.reply_message(reply_token, messages)
except ApiException as e:
    error_info = analyzer.analyze(e)

    if error_info.error_code == "40100":
        print("無効なreplyToken - Webhookイベントから取得したか確認")
    elif error_info.error_code == "40101":
        print("replyToken期限切れ - イベント受信から1分以内に使用")
    elif error_info.error_code == "40102":
        print("replyToken重複使用 - 一度使用したトークンは再利用不可")
```

### ユーザー・リソース関連エラー（40400-40499）

| エラーコード | HTTP Status | カテゴリ       | 説明                           | 対処法                                   |
| ------------ | ----------- | -------------- | ------------------------------ | ---------------------------------------- |
| `40400`      | 404         | USER_NOT_FOUND | ユーザーが見つかりません       | ユーザー ID を確認してください           |
| `40401`      | 404         | USER_NOT_FOUND | 指定したユーザー ID は無効です | 正しいユーザー ID を使用してください     |
| `40402`      | 403         | USER_BLOCKED   | ユーザーにブロックされています | ユーザーのブロック状態を確認してください |
| `40403`      | 403         | FORBIDDEN      | この操作は許可されていません   | 必要な権限があるか確認してください       |

### レート制限・クォータエラー（42901-42999）

| エラーコード | HTTP Status | カテゴリ         | 説明                               | 対処法                               |
| ------------ | ----------- | ---------------- | ---------------------------------- | ------------------------------------ |
| `42901`      | 429         | RATE_LIMIT       | API コール回数の上限に達しました   | レスポンスヘッダーの時間後にリトライ |
| `42902`      | 429         | QUOTA_EXCEEDED   | メッセージ配信数の上限に達しました | 月次制限の回復を待つか、プランを変更 |
| `42903`      | 429         | CONCURRENT_LIMIT | 同時リクエスト数の上限に達しました | 同時リクエスト数を制限してください   |

**レート制限の処理例:**

```python
import asyncio

async def handle_rate_limit_error(error_info):
    """レート制限エラーの適切な処理"""
    if error_info.error_code == "42901":
        retry_after = error_info.retry_after or 60
        print(f"API レート制限: {retry_after}秒後にリトライ")
        await asyncio.sleep(retry_after)
        return True  # リトライ可能

    elif error_info.error_code == "42902":
        print("月次配信制限に達しました - プラン変更を検討してください")
        return False  # リトライ不可

    elif error_info.error_code == "42903":
        print("同時接続制限 - 少し待ってからリトライ")
        await asyncio.sleep(5)
        return True  # リトライ可能
```

### サーバーエラー（50000-50099）

| エラーコード | HTTP Status | カテゴリ     | 説明                   | 対処法                                 |
| ------------ | ----------- | ------------ | ---------------------- | -------------------------------------- |
| `50000`      | 500         | SERVER_ERROR | サーバー内部エラー     | しばらく待ってからリトライしてください |
| `50001`      | 500         | SERVER_ERROR | 一時的なサーバーエラー | 指数バックオフでリトライしてください   |
| `50002`      | 503         | SERVER_ERROR | サービス一時停止中     | サービス復旧まで待機してください       |

## エラーコード分析の実装例

### 詳細分析の実装

```python
class DetailedErrorAnalyzer:
    """詳細なエラーコード分析"""

    def analyze_line_api_error(self, error_code: str, status_code: int) -> dict:
        """LINE API エラーコードの詳細分析"""

        error_info = {
            "error_code": error_code,
            "status_code": status_code,
            "category": self._get_category(error_code),
            "severity": self._get_severity(error_code),
            "is_retryable": self._is_retryable(error_code),
            "retry_strategy": self._get_retry_strategy(error_code),
            "documentation": self._get_documentation_url(error_code)
        }

        return error_info

    def _get_retry_strategy(self, error_code: str) -> dict:
        """エラーコード別のリトライ戦略"""

        strategies = {
            # 認証エラー - リトライ不可
            "40001": {"retryable": False, "action": "fix_token"},
            "40002": {"retryable": False, "action": "refresh_token"},

            # リクエストエラー - 修正後リトライ可
            "40010": {"retryable": True, "action": "fix_request_body"},
            "40011": {"retryable": True, "action": "fix_json_format"},

            # レート制限 - 時間待ちでリトライ可
            "42901": {"retryable": True, "action": "wait_and_retry", "wait_time": "header"},
            "42902": {"retryable": False, "action": "upgrade_plan"},

            # サーバーエラー - 指数バックオフでリトライ
            "50000": {"retryable": True, "action": "exponential_backoff"},
            "50001": {"retryable": True, "action": "exponential_backoff"}
        }

        return strategies.get(error_code, {"retryable": False, "action": "manual_check"})
```

### エラーコード別の対処フロー

```python
async def handle_line_api_error_by_code(error_info: LineErrorInfo) -> bool:
    """エラーコード別の詳細な対処"""

    error_code = error_info.error_code

    # 認証関連エラー
    if error_code in ["40001", "40002"]:
        print("認証エラー: トークンを再設定してください")
        return False

    # replyToken エラー
    elif error_code in ["40100", "40101", "40102"]:
        print(f"replyToken エラー ({error_code}): 新しいイベントから取得してください")
        return False

    # レート制限エラー
    elif error_code == "42901":
        retry_after = error_info.retry_after or 60
        print(f"レート制限: {retry_after}秒待機")
        await asyncio.sleep(retry_after)
        return True

    # サーバーエラー
    elif error_code in ["50000", "50001"]:
        print("サーバーエラー: 指数バックオフでリトライ")
        await asyncio.sleep(2 ** retry_count)  # 指数バックオフ
        return True

    else:
        print(f"未知のエラーコード: {error_code}")
        return False
```

## 分析結果の活用

### ダッシュボード用の集計

```python
def create_error_summary(error_logs: List[dict]) -> dict:
    """エラーコード別の集計データを作成"""

    summary = {
        "total_errors": len(error_logs),
        "by_category": {},
        "by_error_code": {},
        "retryable_count": 0,
        "critical_count": 0
    }

    for error in error_logs:
        error_code = error.get("error_code")
        category = error.get("category")

        # カテゴリ別集計
        summary["by_category"][category] = summary["by_category"].get(category, 0) + 1

        # エラーコード別集計
        if error_code:
            summary["by_error_code"][error_code] = summary["by_error_code"].get(error_code, 0) + 1

        # 属性別集計
        if error.get("is_retryable"):
            summary["retryable_count"] += 1
        if error.get("severity") == "CRITICAL":
            summary["critical_count"] += 1

    return summary
```

### アラート設定

```python
def setup_error_alerts(error_info: LineErrorInfo):
    """エラーの重要度に応じたアラート設定"""

    alert_config = {
        # 即座に対応が必要
        "40001": {"level": "critical", "notify": "immediately"},
        "40002": {"level": "critical", "notify": "immediately"},

        # 監視が必要
        "42901": {"level": "warning", "notify": "if_frequent"},
        "42902": {"level": "critical", "notify": "immediately"},

        # ログ記録のみ
        "50000": {"level": "info", "notify": "daily_summary"},
    }

    config = alert_config.get(error_info.error_code, {"level": "info", "notify": "none"})

    if config["notify"] == "immediately":
        send_immediate_alert(error_info)
    elif config["notify"] == "if_frequent":
        check_frequency_and_alert(error_info)
```

## 次のステップ

- [エラーカテゴリ](categories.md) - エラーカテゴリの詳細
- [トラブルシューティング](troubleshooting.md) - よくある問題の解決方法
- [パフォーマンス最適化](../performance/optimization.md) - エラー処理の最適化
