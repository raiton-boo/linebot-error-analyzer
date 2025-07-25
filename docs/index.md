# LINE Bot Error Analyzer - ドキュメント

LINE Messaging API のエラーを自動分析・分類する Python ライブラリの技術ドキュメントです。

## 📚 ドキュメント構成

### 🚀 基本ガイド

- [📦 インストールガイド](installation.md) - セットアップ手順
- [⚡ クイックスタート](quickstart.md) - すぐに始める
- [⚙️ 設定ガイド](configuration.md) - 詳細設定

### 🔧 統合・使用例

- [🌟 実用例集](examples/) - 実際のプロジェクトでの活用方法
- [🚀 FastAPI 統合](integration/fastapi.md) - FastAPI での使用方法
- [📡 LINE Bot SDK 統合](integration/line_sdk.md) - SDK との統合

### 🐛 エラーリファレンス

- [📋 LINE API エラーコード](errors/line_api_codes.md) - 全エラーコード詳細
- [🔍 トラブルシューティング](errors/troubleshooting.md) - 問題解決ガイド
- [🎯 エラーフロー](errors/error_flow.md) - エラー分析の流れ

### 🏗️ アーキテクチャ

- [📐 システム設計](architecture/overview.md) - 全体設計
- [🧱 ベースクラス設計](architecture/base_class.md) - 共通ロジック

### 📚 API リファレンス

- [⚙️ 同期分析器](api/analyzer.md) - LineErrorAnalyzer
- [🔄 非同期分析器](api/async_analyzer.md) - AsyncLineErrorAnalyzer
- [🧱 ベースクラス](api/base_analyzer.md) - BaseLineErrorAnalyzer
- [📊 データモデル](api/models.md) - LineErrorInfo 等
- [テスト実行](development/testing.md) - テストの実行方法
- [コントリビューション](development/contributing.md) - プロジェクトへの貢献方法
- [リリースプロセス](development/release.md) - リリース手順

### 例とサンプル

- [基本的な使用例](examples/basic_usage.md) - 基本的な使用方法
- [高度な使用例](examples/advanced_usage.md) - 高度な使用方法
- [実際のプロジェクトでの使用例](examples/real_world.md) - 実際のプロジェクトでの統合例

## バージョン情報

- **現在のバージョン**: 2.0.0
- **互換性**: Python 3.7+
- **LINE Bot SDK**: v2/v3 両対応

## サポート

- [GitHub Issues](https://github.com/raiton-boo/line-api-error-python/issues)
- [ディスカッション](https://github.com/raiton-boo/line-api-error-python/discussions)
- [LINE Developers](https://developers.line.biz/ja/)

## ライセンス

MIT License - 詳細は [LICENSE](../LICENSE) を参照してください。
