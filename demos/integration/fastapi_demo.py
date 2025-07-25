"""
LINE Bot Error Analyzer - FastAPI統合デモ

このデモでは以下の統合パターンを実演します：
1. FastAPIアプリケーションとの統合
2. エラーハンドリングミドルウェア
3. リアルタイムエラー監視
4. API レスポンスでのエラー情報提供
"""

import sys
import os
from typing import Dict, Any, List
import asyncio
import json
from datetime import datetime

# プロジェクトルートを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from linebot_error_analyzer import AsyncLineErrorAnalyzer
from linebot_error_analyzer.core.models import ErrorCategory, ErrorSeverity

# FastAPIが利用可能かチェック
try:
    from fastapi import FastAPI, HTTPException, Request, Response
    from fastapi.responses import JSONResponse
    from starlette.middleware.base import BaseHTTPMiddleware
    from pydantic import BaseModel

    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    FastAPI = None
    BaseModel = None
    BaseHTTPMiddleware = None
    print("ℹ️  FastAPIが利用できません。デモ用のシミュレーションを実行します。")


# Pydanticモデル定義（FastAPIが利用可能な場合）
if FASTAPI_AVAILABLE:

    class ErrorAnalysisRequest(BaseModel):
        status_code: int
        message: str
        endpoint: str = ""
        headers: Dict[str, str] = {}
        error_code: str = ""
        request_id: str = ""

    class ErrorAnalysisResponse(BaseModel):
        analysis_result: Dict[str, Any]
        recommendations: List[str]
        severity: str
        is_retryable: bool
        retry_after: int = None


class ErrorAnalyzerMiddleware:
    """エラー分析ミドルウェア（FastAPI用）"""

    def __init__(self, app, analyzer: AsyncLineErrorAnalyzer = None):
        self.app = app
        self.analyzer = analyzer or AsyncLineErrorAnalyzer()
        self.error_log = []

    async def __call__(self, request: Request, call_next):
        """ミドルウェア処理"""

        start_time = datetime.now()

        try:
            # リクエスト処理
            response = await call_next(request)

            # エラーレスポンスの場合は分析
            if response.status_code >= 400:
                await self._analyze_error_response(request, response)

            return response

        except Exception as e:
            # 例外が発生した場合も分析
            error_data = {
                "status_code": 500,
                "message": str(e),
                "endpoint": str(request.url.path),
                "headers": dict(request.headers),
            }

            analysis = await self._analyze_error(error_data)

            # エラーログに記録
            self.error_log.append(
                {
                    "timestamp": start_time.isoformat(),
                    "error": error_data,
                    "analysis": analysis,
                    "request_info": {
                        "method": request.method,
                        "url": str(request.url),
                        "client": request.client.host if request.client else "unknown",
                    },
                }
            )

            # エラーレスポンス返却
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal server error",
                    "analysis": analysis,
                    "request_id": error_data.get("request_id", "unknown"),
                },
            )

    async def _analyze_error_response(self, request: Request, response: Response):
        """エラーレスポンスの分析"""

        error_data = {
            "status_code": response.status_code,
            "message": f"HTTP {response.status_code} error",
            "endpoint": str(request.url.path),
            "headers": dict(response.headers),
        }

        analysis = await self._analyze_error(error_data)

        # レスポンスヘッダーに分析結果を追加
        response.headers["X-Error-Category"] = analysis.get("category", "unknown")
        response.headers["X-Error-Severity"] = analysis.get("severity", "unknown")
        response.headers["X-Is-Retryable"] = str(analysis.get("is_retryable", False))

    async def _analyze_error(self, error_data: Dict[str, Any]) -> Dict[str, Any]:
        """エラー分析実行"""

        try:
            result = await self.analyzer.analyze(error_data)
            return {
                "category": result.category.value,
                "severity": result.severity.value,
                "is_retryable": result.is_retryable,
                "recommended_action": result.recommended_action,
                "documentation_url": result.documentation_url,
                "retry_after": result.retry_after,
            }
        except Exception as e:
            return {
                "category": "UNKNOWN",
                "severity": "HIGH",
                "is_retryable": False,
                "error": f"Analysis failed: {str(e)}",
            }

    def get_error_statistics(self) -> Dict[str, Any]:
        """エラー統計情報を取得"""

        if not self.error_log:
            return {"total_errors": 0}

        # 統計計算
        total_errors = len(self.error_log)
        categories = {}
        severities = {}
        retryable_count = 0

        for log_entry in self.error_log:
            analysis = log_entry.get("analysis", {})

            # カテゴリ統計
            category = analysis.get("category", "UNKNOWN")
            categories[category] = categories.get(category, 0) + 1

            # 重要度統計
            severity = analysis.get("severity", "UNKNOWN")
            severities[severity] = severities.get(severity, 0) + 1

            # リトライ可能統計
            if analysis.get("is_retryable", False):
                retryable_count += 1

        return {
            "total_errors": total_errors,
            "retryable_errors": retryable_count,
            "retryable_percentage": (
                (retryable_count / total_errors * 100) if total_errors > 0 else 0
            ),
            "category_distribution": categories,
            "severity_distribution": severities,
            "recent_errors": self.error_log[-10:],  # 最新10件
        }


def create_demo_app():
    """デモ用FastAPIアプリケーション作成"""

    if not FASTAPI_AVAILABLE:
        return None

    app = FastAPI(
        title="LINE Bot Error Analyzer Demo",
        description="エラー分析機能統合デモAPI",
        version="1.0.0",
    )

    # エラー分析ミドルウェアを追加
    analyzer = AsyncLineErrorAnalyzer()
    error_middleware = ErrorAnalyzerMiddleware(app, analyzer)
    app.add_middleware(BaseHTTPMiddleware, dispatch=error_middleware)

    @app.get("/")
    async def root():
        """ルートエンドポイント"""
        return {
            "message": "LINE Bot Error Analyzer Demo API",
            "endpoints": [
                "/analyze - エラー分析API",
                "/simulate-error/{status_code} - エラーシミュレーション",
                "/error-stats - エラー統計情報",
                "/health - ヘルスチェック",
            ],
        }

    @app.post("/analyze", response_model=ErrorAnalysisResponse)
    async def analyze_error(request: ErrorAnalysisRequest):
        """エラー分析API"""

        try:
            error_data = request.dict()
            result = await analyzer.analyze(error_data)

            # 推奨アクションリスト作成
            recommendations = [result.recommended_action]
            if result.is_retryable:
                recommendations.append("リトライを実行してください")
            if result.retry_after:
                recommendations.append(
                    f"{result.retry_after}秒後にリトライしてください"
                )

            return ErrorAnalysisResponse(
                analysis_result=result.to_dict(),
                recommendations=recommendations,
                severity=result.severity.value,
                is_retryable=result.is_retryable,
                retry_after=result.retry_after,
            )

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

    @app.get("/simulate-error/{status_code}")
    async def simulate_error(status_code: int, message: str = "Simulated error"):
        """エラーシミュレーション"""

        # 意図的にエラーを発生させる
        if status_code == 400:
            raise HTTPException(status_code=400, detail="Bad request simulation")
        elif status_code == 401:
            raise HTTPException(status_code=401, detail="Unauthorized simulation")
        elif status_code == 403:
            raise HTTPException(status_code=403, detail="Forbidden simulation")
        elif status_code == 404:
            raise HTTPException(status_code=404, detail="Not found simulation")
        elif status_code == 429:
            raise HTTPException(status_code=429, detail="Rate limit simulation")
        elif status_code == 500:
            raise HTTPException(status_code=500, detail="Internal error simulation")
        else:
            return {"message": f"No simulation available for status code {status_code}"}

    @app.get("/error-stats")
    async def get_error_statistics():
        """エラー統計情報取得"""

        return error_middleware.get_error_statistics()

    @app.get("/health")
    async def health_check():
        """ヘルスチェック"""

        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "analyzer": "operational",
        }

    return app


async def demo_without_fastapi():
    """FastAPIなしでの統合デモ"""

    print("🔧 FastAPI統合シミュレーション")
    print("-" * 50)

    analyzer = AsyncLineErrorAnalyzer()

    # 模擬HTTPリクエスト/レスポンス
    simulated_requests = [
        {
            "method": "POST",
            "path": "/api/message/push",
            "status": 401,
            "message": "Invalid token",
        },
        {
            "method": "GET",
            "path": "/api/user/profile",
            "status": 404,
            "message": "User not found",
        },
        {
            "method": "POST",
            "path": "/api/rich-menu",
            "status": 413,
            "message": "Image too large",
        },
        {
            "method": "GET",
            "path": "/api/audience",
            "status": 403,
            "message": "Insufficient permissions",
        },
        {
            "method": "POST",
            "path": "/webhook",
            "status": 500,
            "message": "Processing failed",
        },
    ]

    print("📡 模擬APIリクエスト処理:")

    for i, request in enumerate(simulated_requests, 1):
        print(f"\n🌐 リクエスト {i}: {request['method']} {request['path']}")

        # エラー分析
        error_data = {
            "status_code": request["status"],
            "message": request["message"],
            "endpoint": request["path"],
        }

        try:
            result = await analyzer.analyze(error_data)

            print(f"   📊 分析結果:")
            print(f"     • ステータス: {result.status_code}")
            print(f"     • カテゴリ: {result.category.value}")
            print(f"     • 重要度: {result.severity.value}")
            print(f"     • リトライ可能: {'はい' if result.is_retryable else 'いいえ'}")
            print(f"     • 推奨アクション: {result.recommended_action}")

            # 模擬レスポンスヘッダー
            print(f"   📤 レスポンスヘッダー:")
            print(f"     X-Error-Category: {result.category.value}")
            print(f"     X-Error-Severity: {result.severity.value}")
            print(f"     X-Is-Retryable: {result.is_retryable}")

        except Exception as e:
            print(f"   ❌ 分析エラー: {e}")


async def demo_error_monitoring():
    """エラー監視デモ"""

    print("\n\n📊 リアルタイムエラー監視デモ")
    print("-" * 50)

    analyzer = AsyncLineErrorAnalyzer()
    error_monitor = ErrorAnalyzerMiddleware(None, analyzer)

    # 模擬エラーストリーム
    error_stream = [
        {"status_code": 401, "message": "Token expired", "endpoint": "/api/auth"},
        {"status_code": 429, "message": "Rate limit", "endpoint": "/api/message"},
        {
            "status_code": 500,
            "message": "DB connection failed",
            "endpoint": "/api/user",
        },
        {"status_code": 400, "message": "Invalid JSON", "endpoint": "/api/webhook"},
        {"status_code": 403, "message": "Permission denied", "endpoint": "/api/admin"},
    ]

    print("🔄 エラーストリーム処理中...")

    for i, error in enumerate(error_stream, 1):
        # エラー分析と記録
        analysis = await error_monitor._analyze_error(error)

        # ログに追加（模擬）
        error_monitor.error_log.append(
            {
                "timestamp": datetime.now().isoformat(),
                "error": error,
                "analysis": analysis,
                "request_info": {
                    "method": "POST",
                    "url": f"https://api.example.com{error['endpoint']}",
                    "client": f"192.168.1.{i}",
                },
            }
        )

        print(
            f"   📝 エラー {i}: {error['endpoint']} ({error['status_code']}) -> {analysis['category']}"
        )

        # 小さな遅延でストリーミング感を演出
        await asyncio.sleep(0.1)

    # 統計情報表示
    stats = error_monitor.get_error_statistics()

    print(f"\n📈 監視統計:")
    print(f"   • 総エラー数: {stats['total_errors']}")
    print(
        f"   • リトライ可能: {stats['retryable_errors']}/{stats['total_errors']} ({stats['retryable_percentage']:.1f}%)"
    )

    print(f"\n📂 カテゴリ別分布:")
    for category, count in stats["category_distribution"].items():
        print(f"     • {category}: {count}件")

    print(f"\n🚨 重要度別分布:")
    for severity, count in stats["severity_distribution"].items():
        print(f"     • {severity}: {count}件")


async def main():
    """メイン実行関数"""

    print("🌐 LINE Bot Error Analyzer - FastAPI統合デモ")
    print("=" * 60)

    if FASTAPI_AVAILABLE:
        print("✅ FastAPIが利用可能です")
        print("📝 実際のWebアプリケーションでは以下のようにエラー分析を統合できます:")
        print("   1. エラーハンドリングミドルウェアの追加")
        print("   2. API レスポンスへの分析結果追加")
        print("   3. リアルタイムエラー監視")
        print("   4. 統計情報の提供")

        # FastAPIアプリケーション作成デモ
        app = create_demo_app()
        print(f"\n🚀 FastAPIアプリケーションが作成されました")
        print("   実際に起動するには: uvicorn demo_fastapi:app --reload")
    else:
        print("ℹ️  FastAPIが利用できないため、シミュレーションで実行します")
        print("   実際に使用するには: pip install fastapi uvicorn")

    try:
        # 統合デモ実行
        await demo_without_fastapi()
        await demo_error_monitoring()

        print("\n\n🎉 FastAPI統合デモが完了しました！")
        print("\n🔧 統合のポイント:")
        print("   • ミドルウェアによる自動エラー分析")
        print("   • レスポンスヘッダーでの分析結果提供")
        print("   • リアルタイムエラー統計とモニタリング")
        print("   • RESTful APIでの分析結果提供")

    except Exception as e:
        print(f"\n❌ 統合デモ中にエラーが発生しました: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
