---
applyTo: "app/**"
---

# React & Tailwind 実装ルール

## 1. 技術スタック（参考）

- **ランタイム**: React 19 / Vite 7.2.7 (SWC enabled)
- **デスクトップ**: Tauri 2
- **パッケージ管理**: `pnpm`
- **スタイル**: Tailwind CSS 4 / Radix UI / `cn`ユーティリティ（clsx + tailwind-merge）
- **フォーム**: React Hook Form + Zod
- **状態管理**: Zustand（グローバル/共有状態）
- **非同期処理**: useActionState, useFormStatus
- **国際化**: i18next
- **テスト**: Vitest (Unit/Component) & Playwright (E2E)

## 2. 命名規則

| カテゴリ                | 規則                            | 例                                  |
| :---------------------- | :------------------------------ | :---------------------------------- |
| **コンポーネント**      | PascalCase                      | `InputText.tsx`, `AnalysisForm.tsx` |
| **型/インターフェース** | PascalCase + `Type`サフィックス | `UserDataType`, `FormInputType`     |
| **関数**                | camelCase                       | `calculateStatistics.ts`            |
| **定数**                | SCREAMING_SNAKE_CASE            | `API_TIMEOUT_MS`                    |
| **ファイル（非JSX）**   | camelCase                       | `useAuth.ts`, `apiClient.ts`        |

## 3. コンポーネントとJSXルール

- **コンポーネントタイプ**: 関数コンポーネントのみ。クラスコンポーネントは使用不可
- **エクスポート**: 名前付きエクスポートのみ。デフォルトエクスポートは使用不可
- **Props**: 必ずTypeScriptの`type`で定義する
- **ロジック分離**: 複雑なロジックはJSXからhooksやヘルパー関数に抽出する
- **条件分岐**:
  - シンプルなインラインロジック（10行未満）は三項演算子を使用
  - 複雑なレンダリングには論理演算子`&&`または別関数を使用
- **リスト**: `.map()`使用時は必ず一意な`key` propを提供する

## 4. ディレクトリ構造（アトミックデザイン）

- `src/components/atoms/`: 最小のUI要素（Button、Inputなど）。ロジックなし
- `src/components/molecules/`: atomsの組み合わせ。最小限のロジック
- `src/components/organisms/`: 複雑なUIブロック。ビジネスロジックとStateを許可
- `src/components/templates/`: ページレイアウト
- `src/types/`: 型定義（`commonTypes.ts`, `apiTypes.ts`）
- `src/function/`: ビジネスロジックとAPI呼び出し
- `src/common/`: 定数とスタイル定数

## 5. 国際化（i18n）ルール

- **使用法**: JSX内に日本語文字列をハードコーディングしない
- **キー**: `react-i18next`の`t("Key.Name")`を常に使用する
- **補間**: 動的な値には`t("Key", { var: value })`を使用する

## 6. `cn`によるスタイリング

- Tailwindクラスをマージする場合や条件付きスタイルを扱う場合は、必ず`cn()`ユーティリティを使用する
- 例: `className={cn("base-style", isError && "border-red-500", className)}`

## 7. 状態管理（Zustand）

- **グローバル vs ローカル**: コンポーネント内で閉じる状態は`useState`、複数の画面やコンポーネントで横断的に必要な情報は`Zustand`で管理
- **セレクタ形式**: Zustandから値を読み出す際は、不要な再レンダリングを防ぐためセレクタ形式を使用
  - 例: `const value = useStore(state => state.value)`
- **Store分割**: 関心事ごとにStoreを分割し、巨大な単一オブジェクトを避ける

## 8. デスクトップ統合（Tauri）

- **Backend Interaction**: Rust/Pythonバックエンドとの通信にはTauri Commands (`invoke`)を使用
- **System Access**: ファイルシステムアクセスやダイアログにはTauri APIを活用
- **禁止事項**: システム操作のためのTauri Commandが存在する場合に、`fetch`や`axios`でバックエンドAPIを直接呼び出さないこと

## 9. テスト戦略

- **Vitest**: `jsdom`環境で動作。関数の入出力、コンポーネントのレンダリング、イベント発火の検証
- **Playwright**: 実ブラウザで動作。サイドバーのテーブル選択から分析完了までの「一連のストーリー」の検証
- **data-testid**: テストで見つけやすいよう、必要に応じて`data-testid`を付与
- **ロジック分離**: Vitestで独立してテスト可能な純粋関数として抽出
