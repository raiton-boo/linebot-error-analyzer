# 🏗️ システム設計概要

LINE Bot エラー分析器のシステム設計と全体的なアーキテクチャについて説明します。

## 🎯 システム概要

LINE Bot エラー分析器は、LINE Messaging API のエラーを自動で分析・分類するためのライブラリです。以下の設計原則に基づいて構築されています：

### 📋 設計原則

1. **単一責任原則**: 各クラスは明確な役割を持つ
2. **開放閉鎖原則**: 拡張に対して開放、修正に対して閉鎖
3. **リスコフ置換原則**: 基底クラスと派生クラスの互換性
4. **依存関係逆転原則**: 抽象に依存し、具象に依存しない

## 🏛️ アーキテクチャ図

```
┌─────────────────────────────────────────────────────────────┐
│                        User Interface                       │
├─────────────────────────────────────────────────────────────┤
│                  Analyzer Layer                             │
│  ┌─────────────────┐    ┌─────────────────────────────────┐ │
│  │ LineErrorAnalyzer│    │ AsyncLineErrorAnalyzer         │ │
│  │   (Sync)        │    │   (Async)                      │ │
│  └─────────────────┘    └─────────────────────────────────┘ │
│                    │    │                                   │
│                    └────┴──────────────────────────────────┐│
│                         │                                  ││
├─────────────────────────────────────────────────────────────┤│
│                Base Analyzer Layer                         ││
│  ┌─────────────────────────────────────────────────────────┐││
│  │               BaseLineErrorAnalyzer                     │││
│  │  - Common Logic                                         │││
│  │  - Error Detection Methods                              │││
│  │  - Shared Processing                                    │││
│  └─────────────────────────────────────────────────────────┘││
├─────────────────────────────────────────────────────────────┤│
│                   Data Layer                               ││
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ ││
│  │ ErrorDatabase   │  │    Models       │  │   Types     │ ││
│  │ - Error Mapping │  │ - LineErrorInfo │  │ - Enums     │ ││
│  │ - Categories    │  │ - ErrorCategory │  │ - Constants │ ││
│  │ - Analysis      │  │ - ErrorSeverity │  │             │ ││
│  └─────────────────┘  └─────────────────┘  └─────────────┘ ││
└─────────────────────────────────────────────────────────────┘│
                                                               │
┌─────────────────────────────────────────────────────────────┘
│                     External Integrations
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐
│  │  LINE Bot SDK   │  │ Web Frameworks  │  │ Custom Apps │
│  │  - v2/v3 API    │  │ - Flask         │  │ - Your Code │
│  │  - Exceptions   │  │ - FastAPI       │  │ - Scripts   │
│  └─────────────────┘  └─────────────────┘  └─────────────┘
```

## 🔄 レイヤー構成

### 1. User Interface Layer

ユーザーが直接使用するインターフェース層：

- **同期分析器**: `LineErrorAnalyzer` - 簡単な同期処理
- **非同期分析器**: `AsyncLineErrorAnalyzer` - 高性能な非同期処理
- **統一インターフェース**: 同じメソッド名で一貫した使用感

### 2. Base Analyzer Layer

共通ロジックを提供する基底クラス層：

- **BaseLineErrorAnalyzer**: 共通処理の実装
- **コード重複排除**: 同期・非同期で共通のロジック
- **保守性向上**: 一箇所の修正で両方に反映

### 3. Data Layer

データの管理と処理を行う層：

- **ErrorDatabase**: エラー分類とマッピング
- **Models**: データ構造の定義
- **Types**: 型定義と列挙型

### 4. External Integrations

外部システムとの統合層：

- **LINE Bot SDK**: v2/v3 両対応
- **Web Frameworks**: Flask、FastAPI 等
- **Custom Applications**: ユーザーのアプリケーション

## 📊 データフロー

### エラー分析の流れ

```
Input Error
     │
     ▼
┌─────────────────┐
│ Error Detection │ ← 型・形式の判定
└─────────────────┘
     │
     ▼
┌─────────────────┐
│ Error Parsing   │ ← データ抽出
└─────────────────┘
     │
     ▼
┌─────────────────┐
│ Category        │ ← エラー分類
│ Classification  │   (多層判定)
└─────────────────┘
     │
     ▼
┌─────────────────┐
│ Result          │ ← 結果生成
│ Generation      │
└─────────────────┘
     │
     ▼
LineErrorInfo Object
```

### 多層エラー判定

```
1. LINE API エラーコード判定 (最優先)
   ├─ 40001-50002 範囲のエラーコード
   └─ 詳細なカテゴリ分類

2. HTTP ステータスコード判定 (基本)
   ├─ 400番台: クライアントエラー
   ├─ 500番台: サーバーエラー
   └─ その他: 特殊ケース

3. メッセージパターン判定 (補助)
   ├─ 正規表現によるパターンマッチ
   └─ キーワードベースの分類
```

## 主要コンポーネント

### BaseLineErrorAnalyzer

```python
class BaseLineErrorAnalyzer:
    """共通ロジックを提供する基底クラス"""

    def _is_v3_api_exception(self, error) -> bool:
        """LINE Bot SDK v3の例外か判定"""

    def _analyze_v3_api_exception(self, error) -> LineErrorInfo:
        """v3 API例外の分析"""

    def _analyze_dict_error(self, error_dict) -> LineErrorInfo:
        """辞書形式エラーの分析"""

    def _create_error_info(self, **kwargs) -> LineErrorInfo:
        """ErrorInfoオブジェクトの生成"""
```

### ErrorDatabase

```python
class ErrorDatabase:
    """エラー分類のデータベース"""

    def analyze_error(self, status_code, error_code, message) -> dict:
        """多層判定によるエラー分析"""

    def get_error_category(self, **kwargs) -> ErrorCategory:
        """エラーカテゴリの取得"""

    def get_recommended_action(self, category) -> str:
        """推奨対処法の取得"""
```

## 設計の利点

### 1. 保守性

- **共通ロジック**: BaseLineErrorAnalyzer により重複排除
- **分離されたデータ**: ErrorDatabase で分類ロジックを集約
- **明確な責任**: 各クラスが明確な役割を持つ

### 2. 拡張性

- **開放閉鎖原則**: 新しいエラーカテゴリを簡単に追加
- **プラグイン構造**: カスタム分析器の作成が容易
- **フレームワーク対応**: 様々な Web フレームワークとの統合

### 3. パフォーマンス

- **非同期処理**: 大量エラーの高速処理
- **バッチ処理**: 効率的な一括分析
- **メモリ効率**: 最適化されたデータ構造

### 4. テスタビリティ

- **単体テスト**: 各コンポーネントを独立してテスト
- **モック対応**: 外部依存関係を簡単にモック
- **カバレッジ**: 79 個のテストで包括的なカバレッジ

## 次のステップ

- [ベースクラス設計](base_class.md) - BaseLineErrorAnalyzer の詳細
- [エラー分析フロー](error_flow.md) - 処理フローの詳細
- [データモデル](data_models.md) - データ構造の詳細
