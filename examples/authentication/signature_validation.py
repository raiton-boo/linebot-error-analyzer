"""
LINE Bot 署名検証エラーハンドリング例

このファイルでは、LINE Webhookの署名検証でよく発生するエラーと
その適切なハンドリング方法を示します。

注意：このファイル内のerror辞書は、実際のLINE APIで発生する可能性のあるエラーパターンを
示すためのサンプルです。実際のAPIエラーは例外オブジェクトから取得されます。
このファイルは複雑なデモ用実装です。シンプルな実装は simple_signature_validation.py を参照してください。
"""

import sys
import os
import hashlib
import hmac
import base64
from typing import Optional, Dict, Any

# プロジェクトルートを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from line_bot_error_analyzer import LineErrorAnalyzer


class SignatureValidator:
    """LINE Bot署名検証クラス（エラーハンドリング付き）"""

    def __init__(
        self, channel_secret: str, analyzer: Optional[LineErrorAnalyzer] = None
    ):
        self.channel_secret = channel_secret
        self.analyzer = analyzer or LineErrorAnalyzer()

    def validate_signature(self, body: str, signature: str) -> Dict[str, Any]:
        """
        署名検証（包括的エラーハンドリング付き）

        Args:
            body: リクエストボディ
            signature: X-Line-Signature ヘッダーの値

        Returns:
            Dict: 検証結果と詳細情報
        """

        result = {
            "is_valid": False,
            "error": None,
            "error_analysis": None,
            "recommendations": [],
        }

        try:
            # 1. 署名の存在確認
            if not signature:
                # 実際のLINE APIで発生する可能性のあるエラーパターン（サンプル）
                error_data = {
                    "status_code": 400,
                    "message": "Missing X-Line-Signature header",
                    "endpoint": "webhook.signature_validation",
                }
                result["error"] = "署名ヘッダーが存在しません"
                result["error_analysis"] = self.analyzer.analyze(error_data)
                result["recommendations"] = [
                    "X-Line-Signatureヘッダーが設定されているか確認してください",
                    "LINE Developer Consoleでwebhook URLが正しく設定されているか確認してください",
                ]
                return result

            # 2. 署名フォーマット確認
            if not signature.startswith("sha256="):
                # 実際のLINE APIで発生する可能性のあるエラーパターン（サンプル）
                error_data = {
                    "status_code": 400,
                    "message": "Invalid signature format",
                    "endpoint": "webhook.signature_validation",
                }
                result["error"] = "署名フォーマットが無効です"
                result["error_analysis"] = self.analyzer.analyze(error_data)
                result["recommendations"] = [
                    "署名は'sha256='で始まる必要があります",
                    "LINE Platform側からの正規リクエストか確認してください",
                ]
                return result

            # 3. Channel Secretの確認
            if not self.channel_secret:
                # 実際のLINE APIで発生する可能性のあるエラーパターン（サンプル）
                error_data = {
                    "status_code": 500,
                    "message": "Channel secret not configured",
                    "endpoint": "webhook.signature_validation",
                }
                result["error"] = "Channel Secretが設定されていません"
                result["error_analysis"] = self.analyzer.analyze(error_data)
                result["recommendations"] = [
                    "環境変数LINE_CHANNEL_SECRETを設定してください",
                    "LINE Developer Consoleから正しいChannel Secretを取得してください",
                ]
                return result

            # 4. 署名の生成と検証
            hash_value = hmac.new(
                self.channel_secret.encode("utf-8"),
                body.encode("utf-8"),
                hashlib.sha256,
            ).digest()

            expected_signature = base64.b64encode(hash_value).decode("utf-8")
            received_signature = signature[7:]  # 'sha256='を除去

            # 5. 署名の比較
            if not hmac.compare_digest(expected_signature, received_signature):
                # 実際のLINE APIで発生する可能性のあるエラーパターン（サンプル）
                error_data = {
                    "status_code": 401,
                    "message": "Invalid signature",
                    "endpoint": "webhook.signature_validation",
                }
                result["error"] = "署名が一致しません"
                result["error_analysis"] = self.analyzer.analyze(error_data)
                result["recommendations"] = [
                    "Channel Secretが正しいか確認してください",
                    "リクエストボディが改変されていないか確認してください",
                    "エンコーディング（UTF-8）が正しいか確認してください",
                ]
                return result

            # 6. 検証成功
            result["is_valid"] = True
            return result

        except UnicodeDecodeError as e:
            # 実際のLINE APIで発生する可能性のあるエラーパターン（サンプル）
            error_data = {
                "status_code": 400,
                "message": f"Unicode decode error: {str(e)}",
                "endpoint": "webhook.signature_validation",
            }
            result["error"] = "文字エンコーディングエラー"
            result["error_analysis"] = self.analyzer.analyze(error_data)
            result["recommendations"] = [
                "リクエストボディのエンコーディングがUTF-8か確認してください",
                "リクエストヘッダーのContent-Typeを確認してください",
            ]
            return result

        except Exception as e:
            # 実際のLINE APIで発生する可能性のあるエラーパターン（サンプル）
            error_data = {
                "status_code": 500,
                "message": f"Unexpected error in signature validation: {str(e)}",
                "endpoint": "webhook.signature_validation",
            }
            result["error"] = "予期しないエラー"
            result["error_analysis"] = self.analyzer.analyze(error_data)
            result["recommendations"] = [
                "アプリケーションログを確認してください",
                "Channel Secretとリクエストデータを再確認してください",
            ]
            return result


def demo_signature_validation():
    """署名検証のデモ実行"""

    print("🔐 LINE Bot 署名検証エラーハンドリングデモ")
    print("=" * 60)

    # テスト用のChannel Secret（実際は環境変数から取得）
    channel_secret = "your-channel-secret-here"
    validator = SignatureValidator(channel_secret)

    # テストケース
    test_cases = [
        {
            "name": "正常な署名",
            "body": '{"events":[]}',
            "signature": "sha256="
            + base64.b64encode(
                hmac.new(
                    channel_secret.encode("utf-8"),
                    '{"events":[]}'.encode("utf-8"),
                    hashlib.sha256,
                ).digest()
            ).decode("utf-8"),
            "description": "正しい署名での検証",
        },
        {
            "name": "署名ヘッダーなし",
            "body": '{"events":[]}',
            "signature": "",
            "description": "X-Line-Signatureヘッダーが欠如",
        },
        {
            "name": "不正な署名フォーマット",
            "body": '{"events":[]}',
            "signature": "invalid-format",
            "description": "sha256=で始まらない署名",
        },
        {
            "name": "署名不一致",
            "body": '{"events":[]}',
            "signature": "sha256=invalid-signature-here",
            "description": "計算された署名と異なる",
        },
    ]

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 テストケース {i}: {test_case['name']}")
        print(f"📝 説明: {test_case['description']}")

        result = validator.validate_signature(test_case["body"], test_case["signature"])

        if result["is_valid"]:
            print("✅ 署名検証成功")
        else:
            print(f"❌ 署名検証失敗: {result['error']}")

            if result["error_analysis"]:
                analysis = result["error_analysis"]
                print(f"📊 エラー分析:")
                print(f"   • カテゴリ: {analysis.category.value}")
                print(f"   • 重要度: {analysis.severity.value}")
                print(f"   • 推奨アクション: {analysis.recommended_action}")

            if result["recommendations"]:
                print(f"💡 具体的な対処法:")
                for rec in result["recommendations"]:
                    print(f"   • {rec}")

        print("-" * 40)


def create_flask_webhook_example():
    """Flask用のWebhookエンドポイント例"""

    return '''
# Flask + LINE Bot Webhook例（署名検証付き）

from flask import Flask, request, abort
import os

app = Flask(__name__)

# 環境変数からChannel Secretを取得
CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET')
validator = SignatureValidator(CHANNEL_SECRET)

@app.route("/webhook", methods=['POST'])
def webhook():
    """LINE Webhook エンドポイント"""
    
    # 署名検証
    signature = request.headers.get('X-Line-Signature', '')
    body = request.get_data(as_text=True)
    
    validation_result = validator.validate_signature(body, signature)
    
    if not validation_result["is_valid"]:
        # 検証失敗時のログ出力
        print(f"署名検証失敗: {validation_result['error']}")
        
        if validation_result["error_analysis"]:
            analysis = validation_result["error_analysis"]
            print(f"エラー詳細: {analysis.category.value} - {analysis.recommended_action}")
        
        # HTTPステータスコードを分析結果に基づいて設定
        if validation_result["error_analysis"]:
            status_code = validation_result["error_analysis"].status_code
        else:
            status_code = 400
            
        abort(status_code)
    
    # 正常な処理
    try:
        # ここでイベント処理を実行
        events = request.json.get('events', [])
        # ... イベント処理ロジック
        
        return 'OK'
        
    except Exception as e:
        # その他のエラーハンドリング
        # 実際のLINE APIで発生する可能性のあるエラーパターン（サンプル）
        error_data = {
            "status_code": 500,
            "message": f"Event processing error: {str(e)}",
            "endpoint": "webhook.event_processing"
        }
        
        analyzer = LineErrorAnalyzer()
        analysis = analyzer.analyze(error_data)
        
        print(f"イベント処理エラー: {analysis.recommended_action}")
        return 'Internal Server Error', 500

if __name__ == "__main__":
    app.run(debug=True)
'''


if __name__ == "__main__":
    demo_signature_validation()

    print("\n\n📄 実装例:")
    print("=" * 60)
    print("Flask用のWebhook実装例:")
    print(create_flask_webhook_example())
