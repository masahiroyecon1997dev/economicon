# economicon

データ分析のための Web アプリケーション。Django バックエンド + React フロントエンドで構成されています。

## 技術スタック

### バックエンド (Python)

- **Python**: 3.14
- **フレームワーク**: FastAPI 0.128.0
- **パッケージマネージャー**: uv
- **データ処理**: Polars, NumPy, SciPy, statsmodels
- **ASGI サーバー**: Uvicorn 0.40.0
- **テスト**: pytest 9.0.2, Coverage

### フロントエンド (React)

- **Node.js**: 18+ (fnm で管理)
- **フレームワーク**: React 19.2.3 + TypeScript
- **ビルドツール**: Vite 7.2.7
- **パッケージマネージャー**: pnpm
- **デスクトップアプリ**: Tauri
- **スタイリング**: Tailwind CSS 4.1.18
- **UI コンポーネント**: Radix UI Primitives
- **状態管理**: Zustand
- **国際化**: react-i18next
- **テスト**: Vitest (ユニットテスト), Playwright (E2E テスト)

## 開発環境のセットアップ

詳細なセットアップ手順は以下のドキュメントを参照してください：

- **[共通セットアップ](docs/setup/common.md)** - 前提条件とGit、VS Code の設定
- **[バックエンドセットアップ](docs/setup/backend.md)** - Python 3.14、uv、FastAPIの環境構築
- **[フロントエンドセットアップ](docs/setup/frontend.md)** - fnm、Node.js、pnpm、Vite、Tauriの環境構築

### クイックスタート

```powershell
# リポジトリのクローン
git clone https://github.com/masahiroyecon1997dev/economicon.git
cd economicon

# バックエンドのセットアップと起動
cd api
uv venv --python 3.14
.venv\Scripts\Activate.ps1
uv sync
uvicorn main:app --reload --host 127.0.0.1 --port 8000

# 別のターミナルでフロントエンドのセットアップと起動
cd app
pnpm install
pnpm dev
```

### Docker 環境での開発

Docker を使用した開発環境も提供しています。詳細は[共通セットアップガイド](docs/setup/common.md#docker-環境での開発)を参照してください。

```powershell
# VS Code で Dev Container を使用
# 1. Dev Containers 拡張機能をインストール
# 2. F1 → "Dev Containers: Rebuild and Reopen in Container"
```

## デバッグ

### VS Code デバッグ設定

- **api-server**: REST API サーバーのデバッグ (Python/FastAPI)
- **pytest**: バックエンドテストのデバッグ (pytest)
- **Launch Chrome**: フロントエンドのデバッグ (React)

## 開発コマンド

### フロントエンド (pnpm)

```powershell
pnpm dev              # 開発サーバーの起動 (Vite)
pnpm build            # プロダクションビルド
pnpm lint             # ESLint チェックの実行
pnpm preview          # ビルド結果のプレビュー
pnpm test             # ユニットテストの実行 (Vitest)
pnpm test:ui          # ユニットテストのUIモード
pnpm test:coverage    # カバレッジ付きテスト
pnpm test:e2e         # E2Eテストの実行 (Playwright)
pnpm test:e2e:ui      # E2EテストのUIモード
pnpm test:e2e:headed  # ブラウザを表示してE2E実行
pnpm test:e2e:debug   # E2Eテストのデバッグモード
```

###ApiServer
uvicorn main:app --reload # 開発サーバーの起動
pytest tests # テストの実行
pytest tests -v # 詳細表示でテスト実行
pytest tests --cov=analysisapp # 開発サーバーの起動
pytest tests # テストの実行
pytest tests -v # 詳細表示でテスト実行
pytest tests --cov=economicon # カバレッジ付きテスト

````

### ビルドとデプロイ

```powershell
.\app_build.ps1       # Reactビルド + Djangoへの統合
````

このスクリプトは以下を実行します：

1. React アプリケーションのビルド (pnpm build)
2. ビルド成果物を FastAPI の static/templates ディレクトリへコピー
3. パスの修正

## ライセンスチェック

### フロントエンド (React)

ビルド時に自動的にライセンス情報が `dist/LICENSES.txt` に出力されます (rollup-plugin-license 使用)。

手動確認の場合：

```powershell
pnpm license-checker --summary              # 一覧表示
pnpm license-checker --json > licenses.json # JSON形式で出力
```

### バックエンド (Python)

```powershell
pip-licenses                # 一覧表示
pip-licenses --format=json  # JSON形式で出力
```

## git のプッシュからマージの流れ

### 1. 作業ブランチの作成（dev から派生）

git checkout dev
git pull origin dev
git checkout -b feature/your-feature-name

### 2. 作業完了後、dev に PR を作成

git push -u origin feature/your-feature-name

#### GitHub で feature/your-feature-name → dev の PR を作成

### 3. dev での作業が完了したら、main に PR を作成

#### GitHub で dev → main の PR を作成

## テスト

### バックエンドテスト

```powershell
# 全テストの実行
cd api
pytest tests

# 詳細表示でテスト実行
pytest tests -v

# 特定のテストの実行
pytest tests/test_create_table.py

# カバレッジ付きテスト
pytest tests --cov=economicon --cov-report=html
coverage report -m           # ターミナルにレポート表示
```

### フロントエンドテスト

#### ユニットテスト (Vitest)

```powershell
# 全テストの実行
cd app
pnpm test

# UIモードでテスト実行
pnpm test:ui

# カバレッジ付きテスト
pnpm test:coverage

# 特定のテストファイルを実行
pnpm test -- Tooltip.test.tsx
```

#### E2E テスト (Playwright)

```powershell
# 全E2Eテストの実行
cd app
pnpm test:e2e

# UIモードで実行（テスト結果をブラウザで確認）
pnpm test:e2e:ui

# ブラウザを表示して実行
pnpm test:e2e:headed

# デバッグモードで実行
pnpm test:e2e:debug

# 特定のブラウザでテスト実行
pnpm test:e2e --project=chromium
pnpm test:e2e --project=firefox
pnpm test:e2e --project=webkit

# テストレポートの表示
pnpm test:e2e:report
```

## プロジェクト構造

```
economicon/
├── ApiServer/                   # FastAPIバックエンド
│   ├── main.py                  # FastAPIエントリーポイント
│   ├── analysisapp/             # メインAPIアプリケーション
│   │   ├── routers/             # FastAPIエンドポイント
│   │   ├── schemas/             # Pydanticモデル
│   │   ├── services/            # ビジネスロジック
│   │   ├── utils/               # ユーティリティ
│   │   ├── i18n/                # 国際化
│   │   └── locales/             # 翻訳ファイル
│   ├── tests/                   # テストコード
│   └── python-requirements/     # 依存関係定義
├── app/          # Reactフロントエンド
│   ├── src/
│   │   ├── components/          # UIコンポーネント (Atomic Design)
│   │   │   ├── atoms/           # 基本コンポーネント
│   │   │   ├── molecules/       # 複合コンポーネント
│   │   │   └── organisms/       # 複雑なコンポーネント
│   │   ├── stores/              # Zustand状態管理
│   │   ├── types/               # TypeScript型定義
│   │   ├── i18n/                # 国際化設定
│   │   └── function/            # ユーティリティ関数
│   ├── src-tauri/               # Tauriデスクトップアプリ
│   ├── vite.config.ts           # Vite設定
│   ├── tailwind.config.ts       # Tailwind CSS設定
│   └── package.json
├── docs/                        # ドキュメント
│   └── setup/                   # セットアップガイド
│       ├── common.md            # 共通セットアップ
│       ├── backend.md           # バックエンドセットアップ
│       └── frontend.md          # フロントエンドセットアップ
├── .github/
│   └── instructions/            # Copilot指示書
├── app_build.ps1                # ビルドスクリプト
└── README.md
```

## トラブルシューティング

セットアップやビルドで問題が発生した場合は、以下のドキュメントを参照してください：

- [バックエンドのトラブルシューティング](docs/setup/backend.md#トラブルシューティング)
- [フロントエンドのトラブルシューティング](docs/setup/frontend.md#トラブルシューティング)
