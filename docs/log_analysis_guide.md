# エラーログ解析機能ガイド

## 概要

LINE Bot Error Analyzer v2.1.0 では、新しくエラーログ文字列の解析機能とAPIパターンベースの分析機能が追加されました。この機能により、構造化されていないログ文字列からエラー情報を抽出し、APIの文脈に応じた詳細な分析が可能になります。

## 新機能の特徴

### 1. ログ文字列の直接解析
- 正規表現パターンを使用したログ文字列からの情報抽出
- ステータスコード、メッセージ、ヘッダー、リクエストIDの自動抽出
- HTTPHeaderDict形式およびPython辞書形式のヘッダー解析対応

### 2. APIパターンベース分析
- エンドポイント別の文脈に応じたエラー分析
- 同一エラーコードでもAPIパターンによる異なる解釈
- ユーザー関連、メッセージ関連、リッチメニュー関連APIの特別処理

### 3. 完全な後方互換性
- 既存コードの変更不要
- 新機能は追加メソッドとして提供
- 既存の分析結果に影響なし

## 基本的な使用方法

### 同期版での使用

```python
from linebot_error_analyzer import LineErrorAnalyzer

analyzer = LineErrorAnalyzer()

# 基本的なログ解析
log_string = "(404) Not Found"
result = analyzer.analyze_log(log_string)

print(f"カテゴリ: {result.category.value}")  # RESOURCE_NOT_FOUND
print(f"重要度: {result.severity.value}")    # MEDIUM
print(f"対処法: {result.recommended_action}")
```

### 非同期版での使用

```python
import asyncio
from linebot_error_analyzer import AsyncLineErrorAnalyzer

async def analyze_logs():
    analyzer = AsyncLineErrorAnalyzer()
    
    log_string = "(401) Unauthorized"
    result = await analyzer.analyze_log(log_string)
    
    print(f"カテゴリ: {result.category.value}")  # AUTH_ERROR

asyncio.run(analyze_logs())
```

## APIパターンを使用した文脈解析

### パターン指定による詳細分析

同じエラーコードでも、APIパターンを指定することで、より具体的で業務ロジックに即した分析結果を得ることができます。

```python
log_string = "(404) Not found"

# パターンなしの場合
result1 = analyzer.analyze_log(log_string)
print(result1.category.value)  # RESOURCE_NOT_FOUND

# ユーザープロフィール取得パターンの場合
result2 = analyzer.analyze_log(log_string, api_pattern="user.user_profile")
print(result2.category.value)  # USER_BLOCKED

# メッセージ送信パターンの場合
result3 = analyzer.analyze_log(log_string, api_pattern="message.message_push")
print(result3.category.value)  # RESOURCE_NOT_FOUND（特別処理なし）
```

### サポートされているAPIパターン

#### ユーザー関連API (`user.*`)
- `user.user_profile` - ユーザープロフィール取得
- `user.user_followers` - フォロワー情報取得
- `user.membership` - メンバーシップ管理

**特別処理される例:**
- 404エラー → `USER_BLOCKED` または `PROFILE_NOT_ACCESSIBLE`
- 403エラー → `PROFILE_NOT_ACCESSIBLE`

#### メッセージ関連API (`message.*`)
- `message.message_reply` - 返信メッセージ
- `message.message_push` - プッシュメッセージ
- `message.message_multicast` - マルチキャスト
- `message.message_broadcast` - ブロードキャスト

**特別処理される例:**
- 400エラー + "reply token" → `INVALID_REPLY_TOKEN`, `REPLY_TOKEN_EXPIRED`, `REPLY_TOKEN_USED`
- 400エラー + "payload" → `PAYLOAD_TOO_LARGE`

#### リッチメニュー関連API (`rich_menu.*`)
- `rich_menu.rich_menu_create` - リッチメニュー作成
- `rich_menu.rich_menu_image` - リッチメニュー画像
- `rich_menu.rich_menu_link` - リッチメニューリンク

**特別処理される例:**
- 400エラー + "size" / "image" → `RICH_MENU_SIZE_ERROR`
- 400エラー + "rich menu" → `RICH_MENU_ERROR`

## 対応するログ形式

### 1. Issue例のログ形式
```
(404)
Reason: Not Found
HTTP response headers: HTTPHeaderDict({'server': 'legy', 'x-line-request-id': 'e40f3c8f-ab14-4042-9194-4c26ee828b80'})
HTTP response body: {"message":"Not found"}
```

### 2. シンプルなステータスコード形式
```
(401) Unauthorized
HTTP 429 Too Many Requests
Status: 500
```

### 3. ヘッダー付きログ
```
(429)
Headers: {'retry-after': '60', 'x-line-request-id': 'test-123'}
```

### 4. JSONボディ付きログ
```
Status: 400
Body: {"error": "Invalid request", "details": "Missing required field"}
```

## 詳細な使用例

### Issue例の完全な解析

```python
from linebot_error_analyzer import LineErrorAnalyzer

analyzer = LineErrorAnalyzer()

# Issue で提供されたログ例
issue_log = """(404)
Reason: Not Found
HTTP response headers: HTTPHeaderDict({'server': 'legy', 'cache-control': 'no-cache, no-store, max-age=0, must-revalidate', 'content-type': 'application/json', 'date': 'Fri, 25 Jul 2025 18:23:24 GMT', 'expires': '0', 'pragma': 'no-cache', 'x-content-type-options': 'nosniff', 'x-frame-options': 'DENY', 'x-line-request-id': 'e40f3c8f-ab14-4042-9194-4c26ee828b80', 'x-xss-protection': '1; mode=block', 'content-length': '23'})
HTTP response body: {"message":"Not found"}"""

# ユーザープロフィール取得時のエラーとして解析
result = analyzer.analyze_log(issue_log, api_pattern="user.user_profile")

print(f"ステータスコード: {result.status_code}")     # 404
print(f"メッセージ: {result.message}")             # Not found
print(f"カテゴリ: {result.category.value}")        # USER_BLOCKED
print(f"重要度: {result.severity.value}")          # MEDIUM
print(f"リトライ可能: {result.is_retryable}")       # False
print(f"リクエストID: {result.request_id}")        # e40f3c8f-ab14-4042-9194-4c26ee828b80
print(f"推奨対処法: {result.recommended_action}")   # エラー詳細を確認し、必要に応じてサポートに連絡してください。
```

### 複数ログの一括解析

```python
import asyncio
from linebot_error_analyzer import AsyncLineErrorAnalyzer

async def batch_analysis():
    analyzer = AsyncLineErrorAnalyzer()
    
    logs = [
        "(404) User not found",
        "(401) Invalid access token",
        "(429) Rate limit exceeded",
        "(500) Internal server error"
    ]
    
    # 並行解析
    results = await analyzer.analyze_multiple(logs)
    
    for i, result in enumerate(results):
        print(f"ログ {i+1}: {result.category.value}")

asyncio.run(batch_analysis())
```

### メインanalyze()メソッドでの文字列解析

新機能では、既存の `analyze()` メソッドでも文字列を直接受け取れるようになりました：

```python
# 従来通りの辞書形式
error_dict = {"status_code": 404, "message": "Not found"}
result1 = analyzer.analyze(error_dict)

# 新機能：文字列の直接解析
error_string = "(404) Not found"
result2 = analyzer.analyze(error_string)

# どちらも同様の結果を返す
print(result1.category.value)  # RESOURCE_NOT_FOUND
print(result2.category.value)  # RESOURCE_NOT_FOUND
```

## 実用的な活用シナリオ

### 1. ログ監視システムでの活用

```python
def monitor_line_bot_logs(log_stream):
    analyzer = LineErrorAnalyzer()
    
    for log_entry in log_stream:
        try:
            result = analyzer.analyze_log(log_entry.text, api_pattern=log_entry.endpoint)
            
            if result.severity.value in ['CRITICAL', 'HIGH']:
                send_alert(f"重要なエラー検出: {result.category.value}")
                
            if result.is_retryable:
                schedule_retry(log_entry, result.retry_after)
                
        except Exception as e:
            print(f"ログ解析エラー: {e}")
```

### 2. エラー統計収集

```python
async def collect_error_statistics(log_files):
    analyzer = AsyncLineErrorAnalyzer()
    error_stats = {}
    
    for log_file in log_files:
        logs = parse_log_file(log_file)
        results = await analyzer.analyze_multiple(logs)
        
        for result in results:
            category = result.category.value
            error_stats[category] = error_stats.get(category, 0) + 1
    
    return error_stats
```

### 3. 運用ダッシュボードでの表示

```python
def format_error_for_dashboard(log_string, api_pattern=None):
    analyzer = LineErrorAnalyzer()
    result = analyzer.analyze_log(log_string, api_pattern)
    
    return {
        'timestamp': datetime.now(),
        'status': result.status_code,
        'category': result.category.value,
        'severity': result.severity.value,
        'message': result.message,
        'action': result.recommended_action,
        'retryable': result.is_retryable,
        'request_id': result.request_id
    }
```

## パフォーマンス考慮事項

### ログ解析の処理時間
- 単一ログの解析: 通常 1-2ms
- 正規表現パターンマッチング: 高度に最適化済み
- メモリ使用量: 解析後のデータは構造化されて保存

### 大量ログ処理の推奨事項
```python
# 非同期版を使用した効率的な大量処理
async def process_large_log_batch(logs, batch_size=100):
    analyzer = AsyncLineErrorAnalyzer()
    results = []
    
    for i in range(0, len(logs), batch_size):
        batch = logs[i:i + batch_size]
        batch_results = await analyzer.analyze_multiple(batch)
        results.extend(batch_results)
        
        # バッチ間で短時間待機（CPU負荷軽減）
        await asyncio.sleep(0.01)
    
    return results
```

## トラブルシューティング

### よくある問題と解決方法

#### 1. ログがパースできない
```python
from linebot_error_analyzer.utils.log_parser import LogParser

parser = LogParser()
if not parser.is_parseable(log_string):
    print("このログ形式はサポートされていません")
    # フォールバック処理
```

#### 2. 予期しないカテゴリ結果
- APIパターンの指定を確認
- ログ内のキーワードがパターンマッチングに影響している可能性

#### 3. パフォーマンスの問題
- 非同期版の使用を検討
- バッチサイズの調整
- ログ前処理による不要データの除去

## 更新情報

### v2.1.0 の新機能
- ✨ エラーログ文字列の直接解析機能
- 🎯 APIパターンベースの文脈解析
- ⚡ 非同期ログ解析サポート
- 🔍 詳細なログパース情報
- 📊 JSON形式での結果出力拡張
- 🧪 包括的なテストカバレッジ

### 既存機能への影響
- 既存のAPIは変更なし
- 新機能は追加メソッドとして提供
- 後方互換性を完全に維持
- パフォーマンスへの影響なし

## サンプルコード集

完全なサンプルコードは `demo_log_analysis.py` をご参照ください。このデモスクリプトには以下の内容が含まれています：

- Issue例のログ解析
- 各種パターンでの解析例
- 非同期処理のデモ
- 詳細な結果表示
- JSON出力例

```bash
python demo_log_analysis.py
```