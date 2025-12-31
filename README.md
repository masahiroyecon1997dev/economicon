# AnalysisApp

データ分析のための Web アプリケーション。Django バックエンド + React フロントエンドで構成されています。

## 技術スタック

### バックエンド (Python)

- **フレームワーク**: Django 5.2.3 + Django REST Framework
- **パッケージマネージャー**: uv
- **データ処理**: Polars, NumPy, SciPy, statsmodels
- **テスト**: Django TestCase, Coverage

### フロントエンド (React)

- **フレームワーク**: React 19.2.3 + TypeScript
- **ビルドツール**: Vite 7.2.7
- **パッケージマネージャー**: pnpm
- **スタイリング**: Tailwind CSS 4.1.18
- **UI コンポーネント**: Radix UI Primitives
- **状態管理**: Zustand
- **国際化**: react-i18next
- **テスト**: Vitest (ユニットテスト), Playwright (E2E テスト)

## 開発環境のセットアップ

### 前提条件

- Python 3.11 以上
- Node.js 18 以上
- pnpm (グローバルインストール推奨)
- uv (Python パッケージマネージャー)

### セットアップ手順

#### 1. Python バックエンド

```powershell
# uvのインストール (未インストールの場合)
pip install uv

# 仮想環境の作成と依存関係のインストール
uv venv
.venv\Scripts\Activate.ps1  # Windows
uv pip install -r .\python-requirements\windows-requirements.txt

# データベースのマイグレーション
python manage.py migrate

# 開発サーバーの起動
python manage.py runserver
```

#### 2. React フロントエンド

```powershell
# pnpmインストール
npm install -g pnpm@latest-10
# 依存関係のインストール
cd front-analysis-app
pnpm install

# 開発サーバーの起動
pnpm dev
```

### Docker 環境での開発

1. Docker のインストール
2. Visual Studio Code にて以下の拡張機能を追加
   - Dev Containers
3. Dev Containers の「開発コンテナー: キャッシュなしでリビルドし、コンテナーで再度開く」を実行
   ※次回以降「開発コンテナー: コンテナーで再度開く」を実行

## デバッグ

### VS Code デバッグ設定

- **api-server**: REST API サーバーのデバッグ (Python/Django)
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

### バックエンド (Python/Django)

```powershell
python manage.py runserver                    # 開発サーバーの起動
python manage.py test                          # テストの実行
python manage.py makemessages -l ja           # 翻訳ファイルの更新
python manage.py compilemessages -l ja        # 翻訳ファイルのコンパイル
python manage.py migrate                      # データベースマイグレーション
```

### ビルドとデプロイ

```powershell
.\app_build.ps1       # Reactビルド + Djangoへの統合
```

このスクリプトは以下を実行します：

1. React アプリケーションのビルド (pnpm build)
2. ビルド成果物を Django の static/templates ディレクトリへコピー
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
cd ApiServer\analysisapp
python manage.py test

# 特定のテストの実行
python manage.py test api.tests.test_create_table

# カバレッジ付きテスト
coverage run manage.py test
coverage report -m           # ターミナルにレポート表示
coverage html                # HTMLレポート生成
```

### フロントエンドテスト

#### ユニットテスト (Vitest)

```powershell
# 全テストの実行
cd front-analysis-app
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
cd front-analysis-app
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
AnalysisApp/
├── ApiServer/                    # Djangoバックエンド
│   └── analysisapp/
│       ├── api/                  # メインAPIアプリケーション
│       │   ├── apis/            # API実装
│       │   │   ├── python_apis/  # ビジネスロジック
│       │   │   ├── rest_apis/    # RESTエンドポイント
│       │   │   └── utilities/    # ユーティリティ
│       │   ├── tests/           # テストコード
│       │   ├── static/          # 静的ファイル
│       │   └── templates/       # テンプレート
│       ├── analysisapp/         # Django設定
│       └── manage.py
├── front-analysis-app/          # Reactフロントエンド
│   ├── src/
│   │   ├── components/         # UIコンポーネント (Atomic Design)
│   │   │   ├── atoms/          # 基本コンポーネント
│   │   │   ├── molecules/      # 複合コンポーネント
│   │   │   └── organisms/      # 複雑なコンポーネント
│   │   ├── stores/             # Zustand状態管理
│   │   ├── types/              # TypeScript型定義
│   │   ├── i18n/               # 国際化設定
│   │   └── function/           # ユーティリティ関数
│   ├── vite.config.ts          # Vite設定
│   ├── tailwind.config.ts      # Tailwind CSS設定
│   └── package.json
├── .github/
│   └── instructions/           # Copilot指示書
├── app_build.ps1               # ビルドスクリプト
└── README.md
```

## トラブルシューティング

### Python パッケージのインストールエラー

```powershell
# uvを最新版に更新
pip install --upgrade uv

# キャッシュをクリアして再インストール
uv pip install --reinstall -r python-requirements\windows-requirements.txt
```

### フロントエンドのビルドエラー

```powershell
# node_modulesを削除して再インストール
cd front-analysis-app
Remove-Item -Recurse -Force node_modules
pnpm install
```

### Django マイグレーションエラー

```powershell
# マイグレーションファイルを削除して再生成
python manage.py migrate --fake api zero
python manage.py migrate
```

## 今後の課題

### 機能追加

1. ジョイン・ユニオン機能の強化
2. エクセルライクなグリッド機能
3. gretl と同等の分析機能

### API 機能

1. 行作成、行削除機能
2. ダミー変数作成の拡張（複数値対応、数値範囲対応）
3. 統計検定機能（Z 検定、t 検定、F 検定）
4. 回帰分析の拡張（ロジット・プロビット分析）
5. パネルデータ分析（固定効果モデル、変量効果モデル）
6. 操作変数法

### 技術的改善

1. CI/CD パイプラインの構築 (GitHub Actions 導入済み)
2. API ドキュメントの自動生成（Swagger/OpenAPI）
3. パフォーマンス最適化
4. テストカバレッジの向上
