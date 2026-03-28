---
applyTo: "app/**"
---

# React & Tailwind 実装ルール

## 1. 技術スタック
- React 19 / Vite 7 (SWC) / Tauri 2 / pnpm
- スタイル: Tailwind CSS 4 / Radix UI / `cn`（clsx + tailwind-merge）
- フォーム: **@tanstack/react-form** + Zod
- 状態管理: Zustand / テーブル: @tanstack/react-table + react-virtual
- 国際化: i18next / APIクライアント: orval生成
- テスト: Vitest (Unit) & Playwright (E2E)

## 2. 命名規則
- コンポーネント: PascalCase（`InputText.tsx`）/ 型/IF: PascalCase+`Type`（`UserDataType`）
- 関数・hooks: camelCase（`useAuth.ts`）/ 定数: SCREAMING_SNAKE_CASE

## 3. コンポーネント・JSXルール
- 関数コンポーネントのみ。デフォルトエクスポート禁止
- Propsは`type`で定義。複雑ロジックはhooksへ抽出
- `.map()`には必ず一意な`key` propを付与

## 4. ディレクトリ構造（アトミックデザイン）
- `src/components/atoms/`: 最小UI（ロジックなし）
- `src/components/molecules/`: atomsの組み合わせ
- `src/components/organisms/`: ビジネスロジック・State許可
- `src/components/templates/`: レイアウト
- `src/components/pages/`: ページコンポーネント
- `src/types/`: 型定義 / `src/lib/`: ユーティリティ
- `src/constants/`: 定数 / `src/hooks/`: カスタムhooks
- `src/stores/`: Zustand stores

## 5. i18n・スタイリング
- JSX内に日本語ハードコーディング禁止。`react-i18next`の`t("Key")`を使用
- Tailwind条件クラスは必ず`cn()`使用: `cn("base", isError && "border-red-500")`

## 6. Zustand
- 単一コンポーネント内→`useState`、横断的情報→`Zustand`（Store分割すること）
- セレクタ形式: `const v = useStore(s => s.value)`

## 7. Tauri統合
- バックエンド通信: Tauri Commands (`invoke`)のみ。`fetch`/`axios`直接呼び出し禁止

## 8. テスト
- Vitest (`jsdom`): 関数入出力・コンポーネントレンダリング
- Playwright: Table選択→分析完了の一連ストーリー。`data-testid`を適宜付与
