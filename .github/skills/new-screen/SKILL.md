---
name: new-screen
description: React / Tauri で新しい画面・フォームを Economicon に追加するときのワークフロー。
---

# Skill: new-screen

React / Tauri で新しい画面・フォームを Economicon に追加するときのワークフロー。

## 前提確認

- `pnpm gen:all` 実行済みで `src/api/model/` / `src/api/zod/` が最新であること
- 類似フォーム（`app/src/components/organisms/Form/`）を必ず参照してから実装を始める

## Step 1: 使用する API 型を確認

```typescript
// 型は Orval 生成ファイルからのみ import。手書き禁止
import type { XxxRequestBody, XxxResult } from "@/api/model";
import { xxxRequestBodySchema } from "@/api/zod";
```

`src/api/model/` の型名が不明なら `pnpm gen:all` を再実行して `openapi.json` から確認する。

## Step 2: ストア設計

**横断的な状態**（複数コンポーネントで共有）→ Zustand ストアを追加。
**単一コンポーネント内の状態** → `useState` で十分。

```typescript
// app/src/stores/xxxResults.ts
type XxxResultsStore = {
  results: XxxResultType[];
  addResult: (result: XxxResultType) => void;
  clearResults: () => void;
};

export const useXxxResultsStore = create<XxxResultsStore>((set) => ({
  results: [],
  addResult: (result) =>
    set((state) => ({ results: [...state.results, result] })),
  clearResults: () => set({ results: [] }),
}));
```

ストアを追加した場合は必ず `*.test.ts` ペアを作成する。

## Step 3: コンポーネント配置（Atomic Design）

| レイヤー | パス                             | 用途                           |
| -------- | -------------------------------- | ------------------------------ |
| atom     | `src/components/atoms/`          | ボタン・入力（ロジックなし）   |
| molecule | `src/components/molecules/`      | atoms の組み合わせ             |
| organism | `src/components/organisms/Form/` | ビジネスロジック・API 呼び出し |
| page     | `src/components/pages/`          | レイアウト・ルーティング       |

**命名**: `PascalCase.tsx` / named export のみ（`export default` 禁止）。

## Step 4: フォーム実装

```typescript
// Zod スキーマは Orval 生成スキーマを組み合わせて作る
const formSchema = z.object({
  tableName: z.string().min(1, t("ValidationMessages.DataNameSelect")),
  // ... Orval 生成スキーマのフィールドに合わせる
});

const form = useForm({
  defaultValues: { tableName: "", ... },
  validators: { onSubmit: formSchema },
  onSubmit: async ({ value }) => {
    try {
      const api = getEconomiconAppAPI();
      const response = await api.xxxEndpoint(value);
      if (response.code === "OK" && response.result) {
        addResult(response.result as unknown as XxxResultType);
      }
    } catch (error) {
      showMessageDialog(extractApiErrorMessage(error));
    }
  },
});
```

**注意**:

- バックエンド通信は `getEconomiconAppAPI()` 経由（`fetch` / `axios` 直接呼び出し禁止）
- エラーは `extractApiErrorMessage()` + `showMessageDialog()` で表示
- `isSubmitting` 中は入力・ボタンを `disabled` にする

## Step 5: JSX / スタイリング

```tsx
// 条件クラスは必ず cn() を使用
<div className={cn("base-class", isError && "border-red-500")}>

// アイコンは Lucide React から
import { Loader2, AlertCircle } from "lucide-react";

// UI プリミティブは Radix UI から
import * as Select from "@radix-ui/react-select";
```

- `.map()` には必ず一意な `key` prop を付与
- コンパクトなレイアウト（スクロール最小化・プログレッシブ・ディスクロージャー）

## Step 6: i18n キー追加

```json
// app/src/i18n/locales/ja.json
{
  "XxxForm": {
    "Title": "〇〇分析",
    "DataSource": "データソース",
    "SubmitButton": "実行"
  }
}
```

```json
// app/src/i18n/locales/en.json（英語も必ず追加）
{
  "XxxForm": {
    "Title": "Xxx Analysis",
    "DataSource": "Data Source",
    "SubmitButton": "Run"
  }
}
```

JSX 内に日本語を直接書かない。必ず `t("XxxForm.Title")` の形式で参照する。

## Step 7: テスト

**Vitest（ユニット）**: `app/src/tests/XxxForm.test.tsx`

```typescript
import { render, screen } from "@testing-library/react";
import { XxxForm } from "@/components/organisms/Form/XxxForm";

describe("XxxForm", () => {
  it("初期レンダリングで送信ボタンが表示される", () => {
    render(<XxxForm />);
    expect(screen.getByRole("button", { name: /実行/ })).toBeInTheDocument();
  });
});
```

**Playwright（E2E）**: `app/e2e/` にストーリー単位でテストを追加。
操作対象要素には `data-testid` を付与する。

## チェックリスト

- [ ] `pnpm gen:all` 実行済みで型が最新
- [ ] 型は `@/api/model` / `@/api/zod` からのみ import（手書き禁止）
- [ ] `fetch` / `axios` 直接呼び出しがない（`getEconomiconAppAPI()` 経由のみ）
- [ ] JSX 内に日本語ハードコードがない（`t("Key")` を使用）
- [ ] `ja.json` と `en.json` 両方に i18n キーを追加
- [ ] `export default` を使っていない
- [ ] `isSubmitting` 中に入力・ボタンが `disabled`
- [ ] Vitest ユニットテストを追加
