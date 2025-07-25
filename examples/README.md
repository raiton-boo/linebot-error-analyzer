# LINE Bot 実用例集 (examples)

このディレクトリには、LINE Bot 開発で頻繁に使用される機能のエラーハンドリング付き実装例が含まれています。

## ファイル構成

各機能について、**シンプル版**と**複雑版**の 2 つのファイルが用意されています。

### 🚀 シンプル版（推奨）

実際の LINE Bot SDK v3 を使用した、コピペですぐに使える実用的な実装です。

- `simple_signature_validation.py` - 署名検証の実用パターン
- `simple_event_processing.py` - イベント処理の実用パターン
- `simple_message_sending.py` - メッセージ送信の実用パターン
- `simple_user_profile.py` - ユーザー管理の実用パターン
- `simple_group_operations.py` - グループ管理の実用パターン

### 📚 複雑版（学習用）

包括的なエラーハンドリングデモ、詳細な分析機能を含む学習用実装です。

- `signature_validation.py` - 署名検証の詳細デモ
- `event_processing.py` - イベント処理の詳細デモ
- `message_sending.py` - メッセージ送信の詳細デモ
- `user_profile.py` - ユーザー管理の詳細デモ
- `group_operations.py` - グループ管理の詳細デモ

## 重要な注意事項

### エラーデータについて

各ファイル内の`error`辞書は、実際の LINE API で発生する可能性のあるエラーパターンを示すためのサンプルです。

```python
# これはサンプルのエラーパターンです
error = {"status_code": 403, "message": "User privacy settings", "endpoint": "profile"}
```

実際の API エラーは例外オブジェクト（`e`）から取得されます：

```python
except Exception as e:
    status = getattr(e, "status", None)  # 実際のステータスコード
    message = str(e)  # 実際のエラーメッセージ
```

## 📁 ディレクトリ構成

```
examples/
├── authentication/         # 認証関連
│   └── signature_validation.py
├── webhook/                # Webhook処理
│   └── event_processing.py
├── messaging/              # メッセージ送信
│   └── message_sending.py
├── user_management/        # ユーザー管理
│   └── user_profile.py
├── group_management/       # グループ管理
│   └── group_operations.py
└── README.md              # このファイル
```

## 🚀 実装例の概要

### 1. 認証処理 (`authentication/`)

**🔐 signature_validation.py**

- LINE Webhook の署名検証
- HMAC-SHA256 による安全な認証
- Flask 統合例付き
- 詳細なエラー分析とレコメンデーション

```python
from examples.authentication.signature_validation import SignatureValidator

validator = SignatureValidator("your_channel_secret")
result = validator.validate_signature(body, signature)
```

**主な機能:**

- ✅ 署名の生成と検証
- ✅ 4 つのテストケース
- ✅ Flask Webhook 例
- ✅ セキュリティベストプラクティス

### 2. Webhook 処理 (`webhook/`)

**📨 event_processing.py**

- Webhook イベントの包括的な処理
- 全イベントタイプ対応（message, follow, join 等）
- JSON 解析エラーハンドリング
- 複数イベント一括処理

```python
from examples.webhook.event_processing import WebhookEventProcessor

processor = WebhookEventProcessor()
result = processor.process_webhook_request(request_body)
```

**対応イベント:**

- ✅ メッセージイベント（text, image, sticker）
- ✅ フォロー/アンフォローイベント
- ✅ グループ参加/退出イベント
- ✅ メンバー参加/退出イベント
- ✅ ポストバック・ビーコンイベント

### 3. メッセージ送信 (`messaging/`)

**💬 message_sending.py**

- Reply API、Push API、Multicast API
- レート制限とメッセージ数制限
- バリデーション機能
- 送信履歴とエラー追跡

```python
from examples.messaging.message_sending import MessageSender

sender = MessageSender("channel_access_token")
result = sender.reply_message(reply_token, messages)
```

**API 機能:**

- ✅ Reply API（最大 5 メッセージ）
- ✅ Push API（レート制限対応）
- ✅ Multicast API（最大 500 宛先）
- ✅ メッセージ形式検証

### 4. ユーザー管理 (`user_management/`)

**👤 user_profile.py**

- ユーザープロフィール取得
- グループ・ルームメンバー情報
- フォロワー統計
- キャッシュ機能付き

```python
from examples.user_management.user_profile import UserManager

manager = UserManager("channel_access_token")
result = manager.get_user_profile(user_id)
```

**管理機能:**

- ✅ プロフィール取得（キャッシュ付き）
- ✅ グループメンバープロフィール
- ✅ フォロワー数・統計情報
- ✅ インタラクション分析

### 5. グループ管理 (`group_management/`)

**🏢 group_operations.py**

- グループ・ルーム情報管理
- メンバーリスト取得（ページネーション対応）
- グループ退出機能
- 活動分析機能

```python
from examples.group_management.group_operations import GroupManager

manager = GroupManager("channel_access_token")
result = manager.get_group_summary(group_id)
```

**管理機能:**

- ✅ グループ情報取得
- ✅ メンバー数・ID リスト取得
- ✅ ページネーション対応
- ✅ グループ活動分析
- ✅ 安全な退出機能

## 🛠️ 使用方法

### 基本的な使用方法

1. **依存関係のインストール**

```bash
pip install -r requirements.txt
```

2. **個別例の実行**

```bash
# 署名検証のデモ
python examples/authentication/signature_validation.py

# Webhook処理のデモ
python examples/webhook/event_processing.py

# メッセージ送信のデモ
python examples/messaging/message_sending.py

# ユーザー管理のデモ
python examples/user_management/user_profile.py

# グループ管理のデモ
python examples/group_management/group_operations.py
```

### 実際のプロジェクトでの使用

```python
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from examples.authentication.signature_validation import SignatureValidator
from examples.webhook.event_processing import WebhookEventProcessor
from examples.messaging.message_sending import MessageSender

# Flask アプリケーション例
from flask import Flask, request, abort

app = Flask(__name__)

# 設定
CHANNEL_SECRET = "your_channel_secret"
CHANNEL_ACCESS_TOKEN = "your_channel_access_token"

# 初期化
validator = SignatureValidator(CHANNEL_SECRET)
processor = WebhookEventProcessor()
sender = MessageSender(CHANNEL_ACCESS_TOKEN)

@app.route("/webhook", methods=['POST'])
def webhook():
    # 1. 署名検証
    signature = request.headers.get('X-Line-Signature')
    body = request.get_data(as_text=True)

    validation_result = validator.validate_signature(body, signature)
    if not validation_result["valid"]:
        abort(400)

    # 2. イベント処理
    processing_result = processor.process_webhook_request(body)

    # 3. レスポンス送信
    for event_result in processor.processed_events:
        if event_result.get("response_message"):
            messages = [{"type": "text", "text": event_result["response_message"]}]
            sender.reply_message(event_result["reply_token"], messages)

    return 'OK'
```

## 🎯 特徴

### 包括的なエラーハンドリング

- **詳細なエラー分析**: LINE API Error Analyzer との統合
- **カテゴリ分類**: Authentication, Permission, Rate Limit 等
- **推奨アクション**: 具体的な解決方法の提示
- **エラーログ**: デバッグ用の詳細情報記録

### 実用的な設計

- **プロダクション対応**: 実際の BOT 開発で使用可能
- **モジュラー設計**: 必要な機能のみ選択利用可能
- **キャッシュ機能**: API コール削減のための効率的なキャッシュ
- **レート制限対応**: API 制限を考慮した安全な実装

### 開発者フレンドリー

- **豊富なテストケース**: 正常系・異常系の両方をカバー
- **デモ機能**: 即座に動作確認可能
- **詳細なドキュメント**: コード内コメントと説明
- **ベストプラクティス**: 推奨される実装パターン

## 📚 関連ドキュメント

- [LINE Bot Error Analyzer メインドキュメント](../README.md)
- [API リファレンス](../docs/api/)
- [アーキテクチャガイド](../docs/architecture/)
- [トラブルシューティング](../docs/errors/)

## 🔧 カスタマイズ

### エラーアナライザーのカスタマイズ

```python
from line_bot_error_analyzer import LineErrorAnalyzer

# カスタム設定でアナライザーを初期化
analyzer = LineErrorAnalyzer()

# カスタムエラーハンドラーの追加
def custom_error_handler(error_data):
    # カスタムロジック
    pass

# 使用例
processor = WebhookEventProcessor(analyzer=analyzer)
```

### キャッシュ設定のカスタマイズ

```python
# キャッシュ有効期限のカスタマイズ（例：UserManager）
class CustomUserManager(UserManager):
    def _get_cache_ttl(self, cache_type):
        cache_ttls = {
            "profile": 7200,    # 2時間
            "group_member": 3600,  # 1時間
            "followers": 1800   # 30分
        }
        return cache_ttls.get(cache_type, 3600)
```

## 🚨 注意事項

### セキュリティ

- **秘密情報の管理**: チャンネルシークレット・アクセストークンは環境変数で管理
- **署名検証の必須実装**: 本番環境では必ず署名検証を実装
- **HTTPS 通信**: Webhook エンドポイントは HTTPS で公開

### パフォーマンス

- **キャッシュの活用**: 同一データの重複取得を避ける
- **レート制限の遵守**: LINE API 制限を超えないよう制御
- **バックグラウンド処理**: 重い処理は非同期で実行

### 運用

- **ログ監視**: エラーログの定期的なチェック
- **メトリクス収集**: 送信成功率・エラー率の監視
- **定期的な更新**: LINE API 仕様変更への対応

## 🤝 貢献

このプロジェクトへの貢献は歓迎します：

1. **バグ報告**: Issues でバグを報告
2. **機能要求**: 新機能のリクエスト
3. **コード貢献**: プルリクエストでコード改善
4. **ドキュメント改善**: 説明の追加・修正

## 📄 ライセンス

このプロジェクトは[MIT License](../LICENSE)の下で公開されています。
