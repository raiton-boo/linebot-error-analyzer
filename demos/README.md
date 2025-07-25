# LINE Bot Error Analyzer - デモンストレーション

このフォルダには、LINE Bot Error Analyzer の様々な使用例とデモンストレーションが含まれています。

## 📁 フォルダ構成

```
demos/
├── basic/                  # 基本的な使用例
│   ├── simple_analysis_demo.py       # 基本的なエラー分析デモ
│   └── hierarchical_structure_demo.py # 階層構造デモ
├── advanced/               # 高度な機能デモ
│   ├── async_demo.py              # 非同期処理デモ
│   └── performance_demo.py        # パフォーマンス分析デモ
└── integration/            # 統合例
    └── fastapi_demo.py            # FastAPI統合デモ
```

## 🚀 実行方法

### 基本デモ

最初に基本的な機能を確認したい場合：

```bash
# 基本的なエラー分析
python demos/basic/simple_analysis_demo.py

# 階層構造の活用例
python demos/basic/hierarchical_structure_demo.py
```

### 高度なデモ

パフォーマンスや非同期処理を確認したい場合：

```bash
# 非同期処理デモ
python demos/advanced/async_demo.py

# パフォーマンステスト（要: psutil）
pip install psutil
python demos/advanced/performance_demo.py
```

### 統合デモ

実際のアプリケーションとの統合例：

```bash
# FastAPI統合デモ（要: FastAPI）
pip install fastapi uvicorn
python demos/integration/fastapi_demo.py
```

## 📋 各デモの内容

### 📖 basic/simple_analysis_demo.py

**基本的なエラー分析機能のデモ**

- 辞書形式エラーの分析
- SDK 例外のシミュレーション
- 複数エラーの一括分析
- 出力形式の例

```python
from line_bot_error_analyzer import LineErrorAnalyzer

analyzer = LineErrorAnalyzer()
result = analyzer.analyze({"status_code": 401, "message": "Invalid token"})
print(f"カテゴリ: {result.category.value}")
```

### 🏗️ basic/hierarchical_structure_demo.py

**階層構造エラーデータベースの活用デモ**

- エンドポイント指定による詳細分析
- カテゴリ別フィルタリング
- 階層構造での情報取得

```python
category, severity, retryable = db.analyze_error(
    status_code=400,
    message="",
    endpoint="message.message_push"
)
```

### ⚡ advanced/async_demo.py

**非同期処理とパフォーマンス最適化のデモ**

- 非同期エラー分析
- 並行バッチ処理
- エラーハンドリングとリトライ
- ストリーミング分析

```python
analyzer = AsyncLineErrorAnalyzer()
results = await analyzer.analyze_multiple(errors)
```

### 🔬 advanced/performance_demo.py

**パフォーマンス分析とベンチマーク**

- メモリ使用量監視
- 処理速度ベンチマーク
- スケーラビリティテスト
- リソース効率の測定

**依存関係**: `pip install psutil`

### 🌐 integration/fastapi_demo.py

**FastAPI アプリケーションとの統合例**

- エラーハンドリングミドルウェア
- API レスポンスでの分析結果提供
- リアルタイムエラー監視
- RESTful エラー分析 API

**依存関係**: `pip install fastapi uvicorn`

## 🛠️ 実行時の注意

### 依存関係

デモによっては追加のライブラリが必要です：

```bash
# 基本デモ: 追加ライブラリ不要
# パフォーマンスデモ用
pip install psutil

# FastAPI統合デモ用
pip install fastapi uvicorn pydantic
```

### Python パス

各デモは相対パスでプロジェクトルートを参照します。プロジェクトルートから実行することを推奨します：

```bash
# プロジェクトルートから実行
cd /path/to/line-api-error-py
python demos/basic/simple_analysis_demo.py
```

## 🎯 学習パス

推奨する学習順序：

1. **basic/simple_analysis_demo.py** - 基本機能の理解
2. **basic/hierarchical_structure_demo.py** - 階層構造の活用
3. **advanced/async_demo.py** - 非同期処理の習得
4. **advanced/performance_demo.py** - パフォーマンス特性の理解
5. **integration/fastapi_demo.py** - 実際の統合パターン

## 🔍 トラブルシューティング

### ImportError が発生する場合

```bash
# プロジェクトを開発モードでインストール
pip install -e .

# または、パッケージをインストール
pip install line-bot-error-analyzer
```

### デモが実行できない場合

1. Python のバージョンを確認（3.8 以上推奨）
2. 必要な依存関係をインストール
3. プロジェクトルートから実行

### パフォーマンスデモでエラーが出る場合

```bash
# psutil をインストール
pip install psutil

# システム権限が必要な場合があります
sudo python demos/advanced/performance_demo.py
```

## 📚 関連リソース

- [メイン API ドキュメント](../docs/api/)
- [統合ガイド](../docs/integration/)
- [実用例](../examples/)
- [テストケース](../tests/)

## 🤝 貢献

デモの改善や新しい使用例の追加は歓迎します！

1. 新しいデモファイルを適切なフォルダに作成
2. 適切なドキュメントとコメントを追加
3. この README を更新
4. プルリクエストを送信

---

🎉 **楽しいデモ体験を！** 質問がある場合は、イシューを作成してください。
