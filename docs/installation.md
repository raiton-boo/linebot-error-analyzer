# 📦 インストールガイド

LINE Bot Error Analyzer の詳細なインストール手順とセットアップ方法を説明します。

## 要件

### Python バージョン

- **Python 3.9+** (推奨: Python 3.11+)
- 標準ライブラリのみを使用するため、外部依存関係は不要

### 対応プラットフォーム

- macOS
- Linux (Ubuntu, CentOS, etc.)
- Windows 10/11

## インストール方法

### 方法 1: pip でインストール（推奨）

```bash
# PyPI からインストール
pip install line-bot-error-analyzer

# インストール確認
python -c "from line_bot_error_analyzer import LineErrorAnalyzer; print('インストール成功！')"
```

### 方法 2: GitHub からクローン

```bash
# リポジトリをクローン
git clone https://github.com/raiton-boo/line-bot-error-analyzer.git
cd line-bot-error-analyzer

# 開発用インストール
pip install -e .

# テスト実行
pytest tests/ -v
```

### 方法 3: ZIP ダウンロード

1. [GitHub リポジトリ](https://github.com/raiton-boo/line-bot-error-analyzer)から ZIP をダウンロード
2. 任意のディレクトリに展開
3. Python パスに追加

```bash
# ZIP 展開後
cd line-bot-error-analyzer-main

# Python パスに追加
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

## 開発環境のセットアップ

### テスト実行環境

```bash
# テスト用依存関係をインストール
pip install -r requirements.txt

# テスト実行
python -m pytest tests/ -v
```

### 開発ツール

```bash
# 開発用ツールのインストール
pip install black flake8 mypy

# コードフォーマット
black line_bot_error_detective/

# 構文チェック
flake8 line_bot_error_detective/

# 型チェック
mypy line_bot_error_detective/
```

## 設定確認

### インストール確認スクリプト

```python
#!/usr/bin/env python3
"""インストール確認スクリプト"""

def verify_installation():
    try:
        # 基本インポート確認
        from line_bot_error_detective import LineErrorAnalyzer, AsyncLineErrorAnalyzer
        print("✅ 基本インポート: OK")

        # 同期分析器テスト
        analyzer = LineErrorAnalyzer()
        result = analyzer.analyze({"status_code": 401, "message": "Auth error"})
        print(f"✅ 同期分析器: OK - {result.category.value}")

        # 非同期分析器テスト
        import asyncio
        async def test_async():
            async_analyzer = AsyncLineErrorAnalyzer()
            result = await async_analyzer.analyze({"status_code": 429, "message": "Rate limit"})
            return result.category.value

        category = asyncio.run(test_async())
        print(f"✅ 非同期分析器: OK - {category}")

        print("\n🎉 インストール完了！正常に動作しています。")
        return True

    except Exception as e:
        print(f"❌ エラー: {e}")
        return False

if __name__ == "__main__":
    verify_installation()
```

### LINE Bot SDK との統合確認

```python
# LINE Bot SDK v3 との統合テスト（オプション）
def test_line_sdk_integration():
    try:
        # LINE Bot SDK v3 のインストール確認
        import linebot.v3
        print("✅ LINE Bot SDK v3: インストール済み")

        # 統合テスト
        from linebot.v3.exceptions import ApiException
        from line_bot_error_detective import LineErrorAnalyzer

        analyzer = LineErrorAnalyzer()

        # モック ApiException
        class MockApiException(ApiException):
            def __init__(self):
                self.status_code = 401
                self.detail = type('obj', (object,), {'error_code': '40001'})()

        result = analyzer.analyze(MockApiException())
        print(f"✅ LINE SDK 統合: OK - {result.category.value}")

    except ImportError:
        print("ℹ️  LINE Bot SDK v3: 未インストール（統合機能は利用不可）")
    except Exception as e:
        print(f"⚠️  LINE SDK 統合エラー: {e}")

if __name__ == "__main__":
    test_line_sdk_integration()
```

## トラブルシューティング

### よくある問題

#### 1. ImportError: No module named 'line_bot_error_detective'

**原因**: Python パスが正しく設定されていない

**解決方法**:

```bash
# 現在のディレクトリを確認
pwd

# Python パスに追加
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# または、ディレクトリを移動
cd /path/to/line-api-error-python
python -c "from line_bot_error_detective import LineErrorAnalyzer"
```

#### 2. Python バージョンエラー

**原因**: Python 3.7 未満を使用

**解決方法**:

```bash
# Python バージョン確認
python --version

# Python 3.8+ をインストール（例: Ubuntu）
sudo apt update
sudo apt install python3.8

# macOS (Homebrew)
brew install python@3.8
```

#### 3. テスト実行エラー

**原因**: pytest がインストールされていない

**解決方法**:

```bash
# pytest をインストール
pip install pytest pytest-asyncio

# テスト実行
python -m pytest tests/ -v
```

### パフォーマンスの最適化

#### メモリ使用量の最適化

```python
# 大量エラー処理時のメモリ最適化
from line_bot_error_detective import AsyncLineErrorAnalyzer

async def optimized_batch_processing():
    analyzer = AsyncLineErrorAnalyzer()

    # バッチサイズを調整してメモリ使用量を制御
    batch_size = 50  # デフォルトは 100

    errors = [{"status_code": 400 + i % 100} for i in range(10000)]
    results = await analyzer.analyze_batch(errors, batch_size=batch_size)

    return results
```

#### CPU 使用率の最適化

```python
# 同期処理での高速化
from concurrent.futures import ThreadPoolExecutor
from line_bot_error_detective import LineErrorAnalyzer

def parallel_processing(errors):
    analyzer = LineErrorAnalyzer()

    with ThreadPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(analyzer.analyze, errors))

    return results
```

## 次のステップ

1. **[クイックスタート](quickstart.md)** - 基本的な使い方を学ぶ
2. **[API リファレンス](api/analyzer.md)** - 詳細な API を理解する
3. **[統合ガイド](integration/)** - フレームワークとの統合方法
4. **[実用例](examples/)** - 実際のプロジェクトでの活用方法

## サポート

- **[GitHub Issues](https://github.com/raiton-boo/line-api-error-python/issues)** - バグ報告・機能要望
- **[プルリクエスト](https://github.com/raiton-boo/line-api-error-python/pulls)** - 貢献・改善提案
- **[ディスカッション](https://github.com/raiton-boo/line-api-error-python/discussions)** - 質問・相談
