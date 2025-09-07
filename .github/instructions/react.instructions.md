---
applyTo: "AnalysisApp/AnalysisApp/front-analysis-app/src/components/**/**/**/*.tsx"
---

# React TypeScript + Tailwind CSS 開発規約

## 全般的なルール

### コンポーネント設計
- 関数コンポーネントとフックを使用し、クラスコンポーネントは使用しない
- propsはTypeScriptの`type`で定義し、必ず型注釈を付ける
- デフォルトエクスポートではなく、名前付きエクスポートを使用
- コンポーネント名はPascalCaseで記述

### スタイリング
- Tailwind CSSを使用してスタイリングを行う
- インラインスタイルは定数値の場合のみ使用（例：`height: ${HEADER_MENU_HEIGHT}px`）
- クラス名は動的な条件分岐を含む場合、テンプレートリテラルを使用
- ダークモード対応のクラス（`dark:`プレフィックス）を適切に使用

### JSXルール
- JSX内では複雑なロジックを避け、必要に応じて関数に切り出す
- イベントハンドラーは簡潔に記述し、複雑な処理は別関数に分離
- 条件付きレンダリングは三項演算子または論理演算子を使用（記述が10行以内と少ない場合は三項演算子を使用、それ以上を記述する場合は論理演算子を使用）
- mapを使用する際は必ずkeyプロパティを設定

## Atomic Design構成

### Atoms（原子）
- 最小単位の再利用可能なコンポーネント
- ボタン、入力フィールド、アイコンなど基本的なUI要素
- propsは最小限に抑え、汎用性を重視
- 外部依存（API呼び出しなど）は持たない

**命名規則：**
- ディレクトリ：機能別（Button、Input、Icon、TableCellなど）
- ファイル名：具体的な機能名（InputText.tsx、ModalCloseButton.tsx）

**例：**
```tsx
type InputTextProps = {
  value: string;
  change: (event: ChangeEvent<HTMLInputElement>) => void;
  error: string;
};

export function InputText({ value, change, error }: InputTextProps) {
  // 実装
}
```

### Molecules（分子）
- Atomsを組み合わせたコンポーネント
- 特定の機能を持つ小さなコンポーネント群
- ラベル付き入力フィールド、モーダルヘッダーなど
- 国際化（i18n）対応を含む場合がある

**命名規則：**
- ディレクトリ：機能別（InputField、Modal、Table、HeaderMenuDropdownなど）
- ファイル名：具体的な組み合わせを表現

**例：**
```tsx
type InputFieldTextProps = {
  label: string;
  value: string;
  change: (event: ChangeEvent<HTMLInputElement>) => void;
  error: string;
};

export function InputTextField({ label, value, change, error }: InputFieldTextProps) {
  const { t } = useTranslation();
  // Atomsを組み合わせた実装
}
```

### Organisms（有機体）
- MoleculesとAtomsを組み合わせた複雑なコンポーネント
- 特定のビジネスロジックを持つ場合がある
- メインパネル、ヘッダーメニュー、テーブルなど
- 状態管理とAPI呼び出しを含む場合がある

**命名規則：**
- ディレクトリ：画面の主要セクション（MainPanel、Header、Tableなど）
- ファイル名：具体的な機能領域

### Templates（テンプレート）
- ページ全体のレイアウトを定義
- 主にAppコンポーネントとして実装
- 状態管理とデータフェッチングのロジックを含む
- 複数のOrganismsを配置

## TypeScript型定義

### 型定義の場所
- 共通型は`src/types/commonTypes.ts`に定義
- API関連の型は`src/types/apiTypes.ts`に定義
- 状態管理の型は`src/types/stateTypes.ts`に定義

### 型命名規約
- 型名は`Type`サフィックスを付ける（例：`TableInfoType`、`ColumnType`）
- プロパティ名はcamelCaseを使用
- null許容型は`| null`で明示的に定義

### よく使用する型パターン
```tsx
// 基本的なデータ型
export type TableDataCellType = string | number | boolean | null;
export type TalbeDataRowType = { [key: string]: TableDataCellType };

// コンポーネントプロパティ型
type ComponentProps = {
  requiredProp: string;
  optionalProp?: number;
  callbackProp: () => void;
  eventHandlerProp: (event: ChangeEvent<HTMLInputElement>) => void;
};

// バリデーション結果型
export type checkInputType = { isError: boolean; message: string };
```

## 国際化（i18n）対応

### 使用方法
- `react-i18next`を使用
- `useTranslation`フックを活用
- エラーメッセージやUIテキストは翻訳キーを使用

```tsx
import { useTranslation } from 'react-i18next';

export function Component() {
  const { t } = useTranslation();
  
  return (
    <div>
      {error !== '' ? <p className="text-red-500 text-xs mt-1">{t(error)}</p> : null}
    </div>
  );
}
```

### 翻訳キー規約
- エラーメッセージ：`Error.` プレフィックス（例：`Error.Required`、`Error.Number`）
- UI要素：機能別の階層構造

## 状態管理

### useState使用ルール
- 状態の初期値は型を明示的に指定
- 配列の状態更新は関数形式を使用（`setState(prev => [...prev, newItem])`）
- オブジェクトの状態更新はスプレッド演算子を使用

### useEffect使用ルール
- 副作用の処理は適切にクリーンアップ
- 依存配列を正確に指定
- 非同期処理でのrace conditionを防ぐため、ignoreフラグを使用

```tsx
useEffect(() => {
  let ignore = false;
  async function fetchData() {
    const result = await apiCall();
    if (!ignore) {
      setState(result);
    }
  }
  fetchData();
  return () => {
    ignore = true;
  };
}, []);
```

## バリデーション

### 入力検証関数
- `src/function/checkInputFunctions.ts`に共通検証関数を定義
- 検証結果は`checkInputType`型で統一
- エラーメッセージは国際化キーを返す

### 検証関数の命名
- `check` + 検証内容（例：`checkRequired`、`checkNumber`、`checkInteger`）
- 戻り値は`{isError: boolean, message: string}`形式

## 定数管理

### 定数の配置
- UIに関する定数：`src/common/constant.ts`
- スタイル関連の定数：`src/common/styleConstant.ts`

### 定数命名規約
- 全て大文字のSNAKE_CASE
- 単位を含む場合は明示的に記述（例：`HEADER_MENU_HEIGHT`）

## APIとの連携

### API呼び出し
- `src/function/restApis.ts`にAPI関数を定義
- async/await構文を使用
- エラーハンドリングを適切に実装

### 内部関数
- `src/function/internalFunctions.ts`にビジネスロジックを定義
- APIレスポンスの変換やデータ加工処理

## ファイル・ディレクトリ命名規約

### ディレクトリ構造
```
src/
├── components/
│   ├── atoms/
│   │   ├── Button/
│   │   ├── Input/
│   │   └── Icon/
│   ├── molecules/
│   │   ├── InputField/
│   │   ├── Modal/
│   │   └── Table/
│   ├── organisms/
│   │   ├── MainPanel/
│   │   ├── Header/
│   │   └── Table/
│   └── templates/
├── types/
├── common/
├── function/
├── i18n/
└── configs/
```

### ファイル命名
- コンポーネントファイル：PascalCase.tsx
- 型定義ファイル：camelCase.ts
- 関数定義ファイル：camelCase.ts
- 設定ファイル：camelCase.ts

## エラーハンドリング

### エラー表示
- バリデーションエラーは赤色テキストで表示（`text-red-500`）
- エラーメッセージは小さいフォントサイズ（`text-xs`）
- エラー状態の入力フィールドは赤いボーダー（`border-red-300`）

### 条件付きスタイリング
```tsx
className={`border ${
  error !== '' ? 'border-red-300' : 'border-gray-300'
} h-9 block w-full max-w-xs px-4 py-1 text-sm font-normal shadow-xs text-gray-900 bg-transparent rounded-md placeholder-gray-400 focus:outline-none leading-relaxed`}
```

## アニメーション

### Tailwind CSS アニメーション
- モーダルの表示/非表示：`animate-fade-in-down`、`animate-fade-out-up`
- ホバー効果：`hover:` プレフィックスを使用
- フォーカス効果：`focus:` プレフィックスを使用

## アクセシビリティ

### 基本的な配慮
- ボタンには適切な`onClick`ハンドラーを設定
- フォーム要素には適切な`type`属性を指定
- ダークモード対応のスタイルを提供