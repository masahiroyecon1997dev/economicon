# Frontend Spec

## 目的

フロントエンド(appディレクトリ)の未解消タスクと保留中の設計課題だけを管理する。
実装済みの修正履歴、完了済みタスクはこの文書に残さない。

## 運用ルール

- 未実装・未修正の項目だけを記載する。
- 実装完了を確認した項目はこの文書から削除する。
- フロントエンド単独で完結しない項目は、依存する API / Rust / Tauri 側の変更も併記する。
- リファクタリング項目は、未解消のものだけを残す。

## 現行の前提

- 分析フォームは workspace の work tab として開く。
- 分析成功後は result tab を開き、WorkspaceSurface に戻す。
- data tab / result tab / work tab は workspaceTabs ストアで管理する。
- `currentView` は `"ImportDataFile" | "SaveData" | "Workspace"` の 3 値のみを取る。
- workspace 内で何を表示するかは `activeTabId` のみが決定する。

## 未修正 backlog

### 1. 分析画面の UI 密度調整

- [open] 詳細オプションが多い分析画面は、初期表示をよりコンパクトに保つレイアウトへ寄せる。
- [open] 14 inch 前後の画面で、主要操作と必須入力がスクロール過多にならない状態を目標とする。

対象候補:

- Linear Regression
- Statistical Test
- 今後オプションが増える分析フォーム

### 3. Linear Regression の列指定 UI 改善

- [open] 選択済みの列と未選択の列の状態差を、より直感的に分かる UI にする。
- [open] 役割ごとの誤選択防止を強める。
- [open] 説明変数、被説明変数、補助オプションの関係が一画面で把握しやすい構成に見直す。

### 4. FilterColumnForm の型整理

- [open] `FilterColumnForm` では `form as unknown as FilterFormType` が残っている。
- [open] `ReactFormExtendedApi` 周辺の型付けを整理し、二重キャストを削除する。

対象:

- `app/src/components/organisms/Dialog/ColumnOperationForms/FilterColumnForm.tsx`

## E2E backlog

### 1. ファイル削除フロー

- [open] ImportDataFile のファイル選択タブで、削除確認ダイアログ、削除完了、一覧再読込までを E2E で確認する。
- [open] 可能なら削除不可ケースも追加で検証する。

### 2. 相関行列のテーブル作成

- [open] 相関行列フォームの実行後、新テーブルがサイドバーに追加されることを E2E で確認する。
- [open] result tab が開くことも確認対象に含める。

### 3. 仮説検定の正常系

- [open] 仮説検定フォームの実行後、result tab に検定統計量と p 値が表示されることを E2E で確認する。

### 4. プロットビューの正常系

- [open] プロットビューの実行によってプロットが表示されることを E2E で確認する。

### 5. グループ別統計量の正常系

- [open] グループ別統計量の実行後、新規テーブルが表示されることを E2E で確認する。

### 6. 分布プレビューの正常系

- [open] 分布プレビューの実行によってプロットが表示されることを E2E で確認する。

## テスト知見（恒久）

### Radix UI コンポーネントのクリックシミュレーション

**問題**: `fireEvent.click()` は Radix UI のインタラクティブ要素（`TabsTrigger` 等）に対して機能しない。
Radix UI は `onPointerDown` / `onClick` の組み合わせで状態遷移するため、`fireEvent.click` が
pointer イベントを伴わずに click イベントのみを発火させると状態が更新されない。

**解決策**: `@testing-library/user-event` の `userEvent.setup().click()` を使用する。

```typescript
import userEvent from "@testing-library/user-event";

it("タブを切り替えると対応するコンテンツが表示される", async () => {
  const user = userEvent.setup();
  render(<MyComponent />);

  // ❌ 機能しない
  // fireEvent.click(screen.getByText("VarianceTab"));

  // ✅ 正しい方法
  await user.click(screen.getByText("VarianceTab"));

  expect(screen.getByTestId("variance-content")).toBeInTheDocument();
});
```

**適用対象**: `TabsTrigger`、`SelectTrigger` など Radix UI Primitive が提供する button 系要素全般。

> **注意**: `userEvent.setup()` は各テストケース内で毎回呼ぶ。`beforeEach` で共有しない。

### 制御済みラジオ入力のクリックシミュレーション

**問題**: `checked={value === selected}` で制御する `<input type="radio">` に対して `userEvent.click()` が機能しない。
jsdom 上では制御済みラジオ入力の `onChange` が `userEvent` によって発火されない場合がある。

**解決策**: `fireEvent.click(screen.getByDisplayValue(value))` を使用する。

```typescript
// ❌ 機能しない場合がある
// await userEvent.click(screen.getByRole("radio", { name: "内生性あり" }));

// ✅ 正しい方法（displayValue はラジオの value 属性値）
fireEvent.click(screen.getByDisplayValue("true"));
```
