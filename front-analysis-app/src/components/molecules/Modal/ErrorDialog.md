# エラーダイアログの使用方法

## 概要
汎用的なエラーダイアログコンポーネントです。非同期関数として実装されており、どのコンポーネントからでも簡単に呼び出すことができます。

## 特徴
- OKボタンのみのシンプルなダイアログ
- ×ボタンによる閉じる機能
- 非同期実行（Promiseベース）
- 国際化対応
- Tailwind CSSによるスタイリング
- ダークモード対応

## 使用方法

### 基本的な使い方

```tsx
import { showErrorDialog } from '../function/errorDialog';

// コンポーネント内での使用
const handleError = async () => {
  try {
    // エラーが発生する可能性のある処理
    await someApiCall();
  } catch (error) {
    // エラーダイアログを表示（OKが押されるまで待機）
    await showErrorDialog('エラー', '処理中にエラーが発生しました。');
    // OKボタンが押された後の処理
    console.log('ユーザーがOKボタンを押しました');
  }
};
```

### 複数行のメッセージ

```tsx
await showErrorDialog(
  'バリデーションエラー',
  'ファイルの読み込みに失敗しました。\n以下の点を確認してください：\n- ファイルが存在するか\n- ファイル形式が正しいか'
);
```

### イベントハンドラー内での使用

```tsx
const handleSubmit = async () => {
  try {
    const result = await submitData();
    if (result.error) {
      await showErrorDialog('送信エラー', result.message);
      return;
    }
    // 成功時の処理
  } catch (error) {
    await showErrorDialog('予期しないエラー', '処理中に予期しないエラーが発生しました。');
  }
};
```

## API

### showErrorDialog(title: string, message: string): Promise<void>

**パラメータ:**
- `title` (string): ダイアログのタイトル
- `message` (string): エラーメッセージ（改行文字 `\n` をサポート）

**戻り値:**
- `Promise<void>`: OKボタンまたは×ボタンが押されたときにresolveされる

### closeErrorDialog(): void

プログラムからダイアログを閉じる場合に使用（通常は使用しません）

## 実装詳細

### ファイル構成
- `src/stores/useErrorDialogStore.ts`: Zustandストア
- `src/components/molecules/Modal/ErrorDialog.tsx`: メインコンポーネント
- `src/components/molecules/Modal/ErrorModalFooter.tsx`: OKボタン用フッター
- `src/function/errorDialog.ts`: ヘルパー関数

### 技術スタック
- React + TypeScript
- Zustand（状態管理）
- Tailwind CSS（スタイリング）
- React i18next（国際化）

## 注意事項
- 一度に複数のエラーダイアログを表示することはできません
- ダイアログが表示されている間は、背景がオーバーレイでブロックされます
- アニメーション効果により、閉じる際に400ms の遅延があります
