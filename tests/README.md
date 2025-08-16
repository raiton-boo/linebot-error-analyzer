# テストケース

このディレクトリには LINE Bot Error Analyzer のテストケースが含まれています。

## テストファイル構成

### 基本テスト

- `test_analyzer.py` - 同期版アナライザーの基本機能テスト
- `test_async_analyzer.py` - 非同期版アナライザーのテスト
- `test_log_parsing.py` - ログ文字列解析機能のテスト (Issue #1)

### 機能別テスト

- `test_api_patterns.py` - API パターン指定による解析テスト
- `test_error_handling.py` - エラーハンドリングのテスト
- `test_edge_cases.py` - エッジケースのテスト
- `test_integration.py` - 統合テスト
- `test_performance.py` - パフォーマンステスト
- `test_types.py` - 型関連のテスト

### Manual テスト (開発・検証用)

- `manual/test_simple_validation.py` - 基本動作確認
- `manual/test_real_error_validation.py` - 実際のエラーログでの検証
- `manual/test_comprehensive_validation.py` - 包括的な動作検証
- `manual/test_api_specific_validation.py` - API 固有のエラー検証

## テスト実行方法

### 1. 全テスト実行

```bash
# unittest使用
python -m unittest discover tests

# pytest使用
pytest

# 専用スクリプト使用
python tests/run_tests.py
```

### 2. 特定のテストファイル実行

```bash
# unittest
python -m unittest tests.test_analyzer

# pytest
pytest tests/test_analyzer.py

# 専用スクリプト
python tests/run_tests.py -m tests.test_analyzer
```

### 3. Manual テスト実行

```bash
# Manual テスト実行
python tests/run_tests.py --manual

# 個別実行
python tests/manual/test_simple_validation.py
```

## テストカテゴリ

### Unit Tests

- 各クラス・メソッドの単体テスト
- モック使用による I/O 分離

### Integration Tests

- 複数コンポーネント間の結合テスト
- 実際のエラーパターンでのテスト

### Performance Tests

- 大量データでの性能テスト
- メモリ使用量のテスト
- 同時実行のテスト

## CI/CD での実行

GitHub Actions でのテスト実行設定例：

```yaml
- name: Run Tests
  run: |
    python -m pytest tests/ -v --tb=short
    python tests/run_tests.py --all
```

## テスト追加時のガイドライン

1. **ファイル命名**: `test_<機能名>.py`
2. **クラス命名**: `Test<機能名>`
3. **メソッド命名**: `test_<テスト内容>`
4. **ドキュメント**: 各テストメソッドに docstring を記述
5. **アサーション**: 適切な assert メソッドを使用
6. **クリーンアップ**: `setUp`/`tearDown`でリソース管理

## 依存関係

テスト実行に必要なパッケージ：

- `unittest` (標準ライブラリ)
- `pytest` (オプション、より詳細な出力)
- `asyncio` (非同期テスト用)
- `threading` (並行性テスト用)
