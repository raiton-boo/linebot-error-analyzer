# PyPI 公開手順（CI/CD 前提・メモ）

目的: GitHub Actions 等の CI/CD で PyPI へのビルドおよび公開を自動化している前提で、
ローカルで最低限行う作業と確認事項を簡潔に残すためのメモです。

## 前提

- リポジトリが GitHub にあること
- PyPI API トークンを GitHub Secrets（例: `PYPI_API_TOKEN`）に登録済みであること
- CI ワークフロー（例: `.github/workflows/publish.yml`）がタグプッシュ等で実行されること

## ローカルで行う最小手順

1. バージョン更新

   - `linebot_error_analyzer/__init__.py` の `__version__` を更新

2. 変更をコミットして push

```bash
git add linebot_error_analyzer/__init__.py
git commit -m "Bump version to x.y.z"
git push
```

3. リリースタグを作成して push（タグ作成が CI トリガー）

```bash
git tag vX.Y.Z
git push origin vX.Y.Z
```

※ ローカルでのビルドや `twine upload` は不要です。CI がビルドと公開を行います。

## 推奨ルール（メモ）

- バージョンは semver に従う（例: `1.2.3`）
- タグは `v` プレフィックスを付ける（例: `v1.2.3`）と CI で扱いやすい
- コミットメッセージは明確に（例: `Bump version to 1.2.3`）

## 確認チェックリスト

- [ ] バージョン番号を更新した
- [ ] README.md／ドキュメントの要点を確認した
- [ ] ライセンス情報を確認した
- [ ] 依存関係（requirements）に不要なものがないか確認した

## CI/ワークフロー確認方法

- GitHub の Actions タブで該当ワークフロー実行ログを確認する
