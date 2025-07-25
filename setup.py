#!/usr/bin/env python3
"""
LINE Bot Error Analyzer セットアップスクリプト
"""

from setuptools import setup, find_packages
import os
import re


def get_version():
    """バージョンを __init__.py から取得"""
    version_file = os.path.join(
        os.path.dirname(__file__), "linebot_error_analyzer", "__init__.py"
    )
    if os.path.exists(version_file):
        with open(version_file, "r", encoding="utf-8") as f:
            content = f.read()
            version_match = re.search(
                r'^__version__ = [\'"]([^\'"]*)[\'"]', content, re.M
            )
            if version_match:
                return version_match.group(1)
    return "1.0.0"  # デフォルトバージョン


# README.mdの内容を読み込み
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), "README.md")
    if os.path.exists(readme_path):
        with open(readme_path, "r", encoding="utf-8") as f:
            return f.read()
    return ""


# requirements.txtの内容を読み込み
def read_requirements():
    requirements_path = os.path.join(os.path.dirname(__file__), "requirements.txt")
    requirements = []
    if os.path.exists(requirements_path):
        with open(requirements_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    requirements.append(line)
    return requirements


setup(
    name="linebot-error-analyzer",
    version=get_version(),
    author="らいとん",
    author_email="raitosongwe@gmail.com",
    description="LINE Bot SDK のエラーを自動分析・診断するライブラリ",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/raiton-boo/linebot-error-analyzer",
    project_urls={
        "Bug Reports": "https://github.com/raiton-boo/linebot-error-analyzer/issues",
        "Source": "https://github.com/raiton-boo/linebot-error-analyzer",
        "Documentation": "https://github.com/raiton-boo/linebot-error-analyzer/tree/main/docs",
        "Changelog": "https://github.com/raiton-boo/linebot-error-analyzer/releases",
    },
    packages=find_packages(exclude=["tests*", "examples*"]),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Communications :: Chat",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Software Development :: Bug Tracking",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.9",
    install_requires=[
        # 型ヒント用（Python 3.9-3.12）
        "typing_extensions>=4.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=8.0.0",
            "pytest-asyncio>=0.23.0",
            "pytest-cov>=4.0.0",
            "psutil>=5.9.0",
            "typing_extensions>=4.0.0",
        ],
        "quality": [
            "black>=24.0.0",
            "flake8>=7.0.0",
            "mypy>=1.8.0",
        ],
        "docs": [
            "sphinx>=7.0.0",
            "sphinx-rtd-theme>=2.0.0",
        ],
        "line-sdk": [
            "line-bot-sdk>=3.0.0",
        ],
        "all": [
            "pytest>=8.0.0",
            "pytest-asyncio>=0.23.0",
            "pytest-cov>=4.0.0",
            "psutil>=5.9.0",
            "typing_extensions>=4.0.0",
            "black>=24.0.0",
            "flake8>=7.0.0",
            "mypy>=1.8.0",
            "sphinx>=7.0.0",
            "sphinx-rtd-theme>=2.0.0",
            "line-bot-sdk>=3.0.0",
        ],
    },
    # パッケージデータの設定
    package_data={
        "linebot_error_analyzer": ["py.typed"],  # 型ヒント情報
    },
    include_package_data=True,
    zip_safe=False,
    keywords="linebot, bot, error, analyzer, messaging-api, webhook, diagnostics, line, chatbot",
    # ライセンス情報（SPDX形式）
    license="MIT",
    license_files=["LICENSE"],
    # プラットフォーム情報
    platforms=["any"],
)
