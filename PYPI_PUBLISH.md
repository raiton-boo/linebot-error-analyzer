# PyPI 公開手順

## 事前準備

1. PyPI アカウントの作成

   - https://pypi.org/ でアカウント作成
   - https://test.pypi.org/ でテストアカウント作成

2. 必要なツールのインストール

```bash
pip install --upgrade pip
pip install --upgrade build
pip install --upgrade twine
```

## 公開手順

### 1. バージョン更新

`line_bot_error_analyzer/__init__.py` の `__version__` を更新

### 2. パッケージビルド

```bash
# クリーンビルド
rm -rf dist/ build/ *.egg-info/

# パッケージビルド
python -m build
```

### 3. テスト PyPI での動作確認

```bash
# テストPyPIにアップロード
twine upload --repository testpypi dist/*

# テストインストール
pip install --index-url https://test.pypi.org/simple/ line-bot-error-analyzer
```

### 4. 本番 PyPI に公開

```bash
# 本番PyPIにアップロード
twine upload dist/*
```

## 確認事項

- [ ] バージョン番号の更新
- [ ] README.md の内容確認
- [ ] ライセンス情報の確認
- [ ] テストの実行とパス
- [ ] 依存関係の確認
- [ ] パッケージ構造の確認

## リリース後

1. GitHub でリリースタグを作成
2. Changelog の更新
3. ドキュメントの更新

## トラブルシューティング

### ファイルが重複している場合

```bash
twine upload --skip-existing dist/*
```

### 認証エラーの場合

```bash
# API トークンを使用
twine upload --username __token__ --password [API_TOKEN] dist/*
```
