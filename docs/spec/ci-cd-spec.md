# CI/CD Spec

Economicon の CI/CD パイプライン・ビルドスクリプト・リリース手順の設計仕様書。
Claude Code などの AI エージェントがワークフロー修正・スクリプト変更を行う際の参照ドキュメント。

---

## 1. ブランチ戦略

| ブランチ    | 役割                                 |
| ----------- | ------------------------------------ |
| `main`      | リリース済みの安定版。直接 push 禁止 |
| `dev`       | 開発統合ブランチ。CI テストが必須    |
| `feature/*` | 機能開発ブランチ。`dev` へ PR する   |

CI ワークフローのトリガーは原則 `dev` ブランチへの push / PR。
リリースビルドは現在 `workflow_dispatch`（手動）のみ。正式リリース時は `tags: ["v*"]` に切り替える。

---

## 2. GitHub Actions ワークフロー一覧

| ファイル                     | トリガー                                           | ランナー                                      | 役割                                      |
| ---------------------------- | -------------------------------------------------- | --------------------------------------------- | ----------------------------------------- |
| `api.yaml`                   | push/PR → `dev`（`api/**`）+ `workflow_dispatch`   | `ubuntu-24.04` 固定                           | Python lint + テスト                      |
| `app.yaml`                   | push/PR → `dev`（`app/**`）+ `workflow_dispatch`   | Unit: `ubuntu-latest` / E2E: `windows-latest` | フロントエンド Unit + E2E テスト          |
| `release.yaml`               | `workflow_dispatch`                                | `windows-latest`                              | Windows インストーラー/ポータブル版ビルド |
| `security-scan.yaml`         | PR → `dev` / `main` + `workflow_dispatch`          | `ubuntu-latest`                               | 依存関係脆弱性スキャン                    |
| `codeql.yml`                 | PR → `dev` / `main` + `workflow_dispatch`          | `ubuntu-latest`                               | CodeQL 静的解析                           |
| `video.yaml`                 | push/PR → `dev`（`video/**`）+ `workflow_dispatch` | `ubuntu-latest`                               | 動画生成パイプライン型チェック            |
| `workflow-pinning-lint.yaml` | push → `dev` / PR → `dev` `main`（`workflows/**`） | `ubuntu-latest`                               | アクション SHA ピン留め検証               |

---

## 3. 各ワークフロー詳細

### 3.1 API Test CI（`api.yaml`）

**ランナー固定**: `ubuntu-24.04`
数値ベンチマークの金標準（gold）を生成した環境に合わせ、runner 更新による数値揺れを防止する。

```
actions/checkout
setup-uv (キャッシュ: api/uv.lock)
uv python install 3.14.3
uv sync --group dev
ruff check .
テスト用設定ファイル作成（~/.economicon/economicon.config.json, language=ja）
pytest tests --cov=economicon --cov-report=xml
codecov/codecov-action (CODECOV_TOKEN)
```

**注意点**:

- Python バージョンは matrix で管理（現在 `"3.14.3"` 固定）
- テスト前に日本語ロケール設定ファイルを作成する（API のエラーメッセージが日本語で生成される前提）

---

### 3.2 Frontend Test CI（`app.yaml`）

**2 ジョブ構成**:

#### unit-test（`ubuntu-latest`）

```
actions/checkout
pnpm/action-setup (latest-10)
actions/setup-node (Node.js 24, pnpm cache)
pnpm install --frozen-lockfile
pnpm test --run
pnpm test:coverage --run
codecov/codecov-action (coverage/coverage-final.json, CODECOV_TOKEN)
```

#### e2e-test（`windows-latest`）

```
actions/checkout
pnpm/action-setup + setup-node (Node.js 24.15.0 固定)
pnpm install --frozen-lockfile
actions-rust-lang/setup-rust-toolchain
swatinem/rust-cache (app/src-tauri -> target)
astral-sh/setup-uv (キャッシュ: api/uv.lock)
[インライン PowerShell] Python Embedded runtime 準備（STEP 1-5 相当）
pnpm exec tauri build --debug --no-bundle
Playwright バージョン取得 → Chromium キャッシュ確認・インストール
pnpm exec playwright test
```

**E2E 用 runtime 準備のポイント**:

- `build.ps1` は呼び出さず、ジョブ内インライン PowerShell で Python Embedded の最小セットアップを実行
- `python-x86_64-pc-windows-msvc.exe` へのリネームは Tauri の `externalBin` 命名規則に必須
- Playwright ブラウザは `~\AppData\Local\ms-playwright` にキャッシュ（Playwright バージョン文字列をキャッシュキーに使用）

---

### 3.3 Release Build（`release.yaml`）

**現状**: `workflow_dispatch` のみ（手動実行）
**将来**: `tags: ["v*"]` トリガーに切り替え予定

```
actions/checkout
pnpm/action-setup + setup-node (Node.js 24)
pnpm install --frozen-lockfile
actions-rust-lang/setup-rust-toolchain
swatinem/rust-cache (app/src-tauri -> target)
cargo install cargo-about --version 0.9.0 --locked
astral-sh/setup-uv (キャッシュ: api/uv.lock)
.\packaging\build\build.ps1 -CI -PackageTarget all
actions/upload-artifact:
  - economicon-windows-installer (*.exe, 14日保持)
  - economicon-windows-portable  (*.zip, 14日保持)
```

`-CI` スイッチにより STEP 0（前提ツール確認・対話プロンプト）をスキップ。

---

### 3.4 Security Scan（`security-scan.yaml`）

PR → `dev` / `main` に対して 4 つの脆弱性スキャンを並列実行する。

| ジョブ                   | ツール                          | 対象                |
| ------------------------ | ------------------------------- | ------------------- |
| `python-audit`           | `pip-audit`（uv経由）           | `api/`              |
| `react-audit`            | `pnpm audit --audit-level high` | `app/`              |
| `rust-audit`             | `cargo-audit`                   | `app/src-tauri/`    |
| `video-playwright-audit` | `pnpm audit`                    | `video/playwright/` |

---

### 3.5 CodeQL Analysis（`codeql.yml`）

PR → `dev` / `main` に対して静的解析を実行する。

| 言語                    | 対象   |
| ----------------------- | ------ |
| `javascript-typescript` | `app/` |
| `python`                | `api/` |

設定ファイル: `.github/codeql/codeql-config.yml`

---

### 3.6 Video CI（`video.yaml`）

`video/**` への変更時にトリガー。3 ジョブ構成。

| ジョブ                  | 内容                                                             |
| ----------------------- | ---------------------------------------------------------------- |
| `typecheck-playwright`  | `video/playwright/` の `tsc --noEmit`                            |
| `typecheck-remotion`    | `video/remotion/` の `tsc --noEmit`                              |
| `remotion-compositions` | Remotion コンポジション検証（`typecheck-remotion` 通過後に実行） |

---

### 3.7 Workflow Pinning Lint（`workflow-pinning-lint.yaml`）

`uses:` エントリが完全 40 文字 SHA にピン留めされているかを検証するインラインスクリプト（Python）。
ローカル参照（`./`）は除外。失敗したエントリのファイル名・行番号・参照文字列を報告して CI を落とす。

**ルール**: 全 `uses:` は `owner/action@<40桁SHA>  # vX.Y.Z` の形式で記述すること。

---

## 4. セキュリティ規約

### 4.1 Permissions の最小化

全ワークフローの最上位に `permissions: {}` を宣言し、各ジョブに必要な権限のみを付与する。

```yaml
permissions: {} # ワークフロー全体のデフォルト

jobs:
  build:
    permissions:
      contents: read # ジョブに必要な最小権限のみ
```

### 4.2 アクション SHA ピン留め

`uses:` は全てコミット SHA（40 文字）にピン留めする。
バージョンタグ（`@v4`）は改ざんリスクがあるため禁止。
`workflow-pinning-lint.yaml` が自動検証する。

```yaml
# ❌ 禁止
- uses: actions/checkout@v4

# ✅ 必須
- uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
```

### 4.3 シークレット

| シークレット名  | 用途                                                      |
| --------------- | --------------------------------------------------------- |
| `CODECOV_TOKEN` | Codecov へのカバレッジアップロード（api.yaml / app.yaml） |

---

## 5. Dependabot 設定

全エコシステムで `dev` ブランチをターゲットにし、毎週月曜に時差スケジュールで実行する。

| エコシステム     | ディレクトリ        | 実行時刻（JST） | ラベル                           |
| ---------------- | ------------------- | --------------- | -------------------------------- |
| `github-actions` | `/`                 | 09:00           | `dependencies`, `github-actions` |
| `npm`            | `/app`              | 09:30           | `dependencies`, `frontend`       |
| `uv`             | `/api`              | 10:00           | `dependencies`, `api`            |
| `cargo`          | `/app/src-tauri`    | 10:30           | `dependencies`, `rust`           |
| `npm`            | `/video/playwright` | 11:00           | `dependencies`, `video`          |
| `npm`            | `/video/remotion`   | 11:30           | `dependencies`, `video`          |

**共通設定**:

- `cooldown.default-days: 10`（リリース後 10 日未満の版は自動 PR しない）
- `open-pull-requests-limit: 3`（エコシステム別上限）
- コミットプレフィックス: CI 系は `ci`、依存関係は `deps` / `deps-dev`

---

## 6. ビルドスクリプト（`packaging/build/build.ps1`）

Windows NSIS インストーラー（`.exe`）とポータブル版（`.zip`）を生成するローカル・CI 兼用スクリプト。

### 6.1 パラメータ

| パラメータ       | 型                                 | デフォルト  | 説明                                           |
| ---------------- | ---------------------------------- | ----------- | ---------------------------------------------- |
| `-Mode`          | `dev` \| `build`                   | `build`     | `dev` は STEP 8 以降（Tauri ビルド）をスキップ |
| `-PackageTarget` | `installer` \| `portable` \| `all` | `installer` | 生成する成果物の種類                           |
| `-CI`            | switch                             | `$false`    | STEP 0（前提確認・対話）をスキップ             |

### 6.2 ビルドステップ（11 ステップ）

| ステップ | 内容                                                                                                        |
| -------- | ----------------------------------------------------------------------------------------------------------- |
| STEP 0   | 前提ツール確認（`uv` / `pnpm` / `cargo` / `tauri-cli`）。CI モード時スキップ                                |
| STEP 1   | Python 3.14.3 Embedded Package ダウンロード → SHA-256 検証 → `resources/runtime/` に展開                    |
| STEP 2   | `python3XX._pth` を編集（`import site` 有効化 + `site-packages` パス追加）                                  |
| STEP 3   | `python.exe` → `binaries/python-x86_64-pc-windows-msvc.exe` にコピー（Tauri externalBin 命名規則）          |
| STEP 4   | `uv export --frozen --no-dev` → `uv pip install --target site-packages --no-cache`（lock ファイル厳守）     |
| STEP 5   | `api/main.py` → `resources/`、`api/economicon/` → `runtime/site-packages/economicon/`（`__pycache__` 削除） |
| STEP 6   | ライセンス収集（Python: `pip-licenses`、JS: `rollup-plugin-license`、Rust: `cargo-about`）                  |
| STEP 7   | Python プリコンパイル（`python -O -m compileall -q -j 0`）                                                  |
| STEP 8   | `pnpm build`（React / Vite フロントエンドビルド）                                                           |
| STEP 9   | `pnpm tauri build`（NSIS インストーラー生成）または `--no-bundle`（ポータブル用 EXE のみ）                  |
| STEP 10  | 成果物を `packaging/build/release/` へ集約（インストーラー `.exe` / ポータブル `.zip`）                     |

### 6.3 成果物構造

```
packaging/build/release/
├── Economicon_X.Y.Z_x64-setup.exe   # NSIS インストーラー
└── economicon-windows-portable.zip  # ポータブル版
    ├── Economicon.exe
    ├── python.exe                   # Python サイドカー
    ├── resources/
    │   ├── main.py
    │   ├── runtime/
    │   │   ├── python3XX.zip        # 標準ライブラリ
    │   │   └── site-packages/
    │   │       └── economicon/      # API ソース
    │   ├── THIRD-PARTY-LICENSES/
    │   └── LICENSE
    └── *.dll
```

### 6.4 Python Embedded Package のバージョン更新手順

Python バージョン（`$PYTHON_VERSION`）を変更する場合:

1. `build.ps1` の `$PYTHON_VERSION` と `$PYTHON_VERSION_SHORT` を更新
2. `https://www.python.org/downloads/release/python-<ver>/` から `embed-amd64` の SHA-256 を取得
3. `$PYTHON_EMBED_SHA256` を新しいハッシュ値に更新（`REPLACEME_SHA256` のまま実行すると即座に失敗する）
4. `api.yaml` の `python-version` matrix も同じバージョンに揃える
5. `app.yaml` E2E ジョブの `$PYTHON_VERSION` 変数も同様に更新

---

## 7. API ランタイム増分同期（`packaging/build/sync-api-runtime.ps1`）

`build.ps1` でフル構築済みの `runtime/` に対して、API ソースのみを再同期するスクリプト。
Python パッケージの再インストールは行わない。

| パラメータ | 説明                                                             |
| ---------- | ---------------------------------------------------------------- |
| `-Compile` | 同期後に `main.py` と `economicon/` を `.pyc` プリコンパイルする |

**対象**:

- `resources/main.py`
- `runtime/site-packages/economicon/`（`__pycache__` を削除して上書き）
- `target/debug/resources/`（デバッグビルドが存在する場合も同期）

`runtime/` が未存在の場合はエラー終了する（先に `build.ps1` を実行すること）。

---

## 8. バージョン管理（`packaging/versioning/bump-version.ps1`）

6 ファイルのバージョンを一括更新するスクリプト。

| パラメータ | 説明                                            |
| ---------- | ----------------------------------------------- |
| `-Version` | 新しいバージョン（例: `0.6.0`、X.Y.Z 形式のみ） |
| `-DryRun`  | ファイルを変更せず差分のみ表示                  |

### 更新対象ファイル

| ファイル                        | 更新パターン           | エンコーディング   |
| ------------------------------- | ---------------------- | ------------------ |
| `api/pyproject.toml`            | `version = "..."`      | UTF-8              |
| `app/src-tauri/Cargo.toml`      | `version = "..."`      | UTF-8              |
| `app/package.json`              | `"version": "..."`     | UTF-8              |
| `app/src-tauri/tauri.conf.json` | `"version": "..."`     | UTF-8              |
| `packaging/build/build.ps1`     | `$APP_VERSION = "..."` | **UTF-8 with BOM** |
| `api/gen_openapi.py`            | `version="..."`        | UTF-8              |

**リリース手順**:

```powershell
# 1. DryRun で差分を確認
powershell -File packaging/versioning/bump-version.ps1 -Version 0.7.0 -DryRun

# 2. 問題なければ実際に更新
powershell -File packaging/versioning/bump-version.ps1 -Version 0.7.0

# 3. API クライアント再生成
cd app; pnpm gen:all

# 4. コミット
git add -A
git commit -m "chore: bump version to 0.7.0"
```

---

## 9. ローカルビルド手順

### 9.1 フルビルド（インストーラー + ポータブル両方）

```powershell
# リポジトリルートで実行
.\packaging\build\build.ps1 -PackageTarget all
```

### 9.2 インストーラーのみ

```powershell
.\packaging\build\build.ps1
# または
.\packaging\build\build.ps1 -PackageTarget installer
```

### 9.3 開発用（Tauri ビルドなし・runtime 構築のみ）

```powershell
.\packaging\build\build.ps1 -Mode dev
```

---

## 10. キャッシュ戦略

| ジョブ         | キャッシュ対象                  | キャッシュキー                 |
| -------------- | ------------------------------- | ------------------------------ |
| 全 pnpm ジョブ | `~/.pnpm-store`                 | `pnpm-lock.yaml` のハッシュ    |
| 全 uv ジョブ   | `~/.cache/uv`                   | `api/uv.lock` のハッシュ       |
| Rust ジョブ    | `app/src-tauri/target`          | `swatinem/rust-cache` 自動管理 |
| E2E Playwright | `~\AppData\Local\ms-playwright` | Playwright バージョン文字列    |
| cargo-audit    | `~/.cargo/bin/cargo-audit`      | `v1-{os}-cargo-audit`          |
