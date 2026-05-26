# 動画制作ガイド

Playwright でアプリ操作を自動収録し、Remotion で字幕・タイトルを合成して MP4 を出力するパイプラインの手順書。

## 目次

- [ディレクトリ構成](#ディレクトリ構成)
- [初回セットアップ](#初回セットアップ)
- [動画を作成する（基本フロー）](#動画を作成する基本フロー)
- [特定の動画だけを更新する](#特定の動画だけを更新する)
- [新しい動画を追加する](#新しい動画を追加する)
- [Remotion Studio でプレビューする](#remotion-studio-でプレビューする)
- [トラブルシューティング](#トラブルシューティング)

---

## ディレクトリ構成

```
video/
├── playwright/                  # Playwright 収録プロジェクト
│   ├── helpers/
│   │   └── connectToApp.ts      # CDP 接続・スクリーンショットヘルパー
│   ├── scenes/                  # シーンごとの収録スクリプト
│   │   └── c09-descriptive-statistics.ts
│   ├── captured/                # 収録済みスクリーンショット出力先（.gitignore）
│   │   └── c09/
│   │       ├── step-01.png
│   │       └── ...
│   ├── package.json
│   ├── tsconfig.json
│   └── playwright.config.ts
│
├── remotion/                    # Remotion 合成プロジェクト
│   ├── src/
│   │   ├── Root.tsx             # 全コンポジション登録
│   │   ├── compositions/        # 動画単位のコンポジション
│   │   │   └── C09DescriptiveStatistics.tsx
│   │   ├── scenes/              # 共通シーンコンポーネント
│   │   │   ├── TitleCard.tsx
│   │   │   ├── Subtitle.tsx
│   │   │   ├── ScreenshotSlide.tsx
│   │   │   └── Ending.tsx
│   │   └── i18n/
│   │       ├── ja.json          # 日本語字幕
│   │       └── en.json          # 英語字幕
│   ├── remotion.config.ts       # publicDir = ../playwright/captured
│   ├── package.json
│   └── tsconfig.json
│
└── output/                      # レンダリング済み MP4（.gitignore）
    ├── ja/
    └── en/
```

> **`captured/` と `output/` は `.gitignore` 対象。** Git には含まれません。

---

## 初回セットアップ

### 前提条件

| ツール       | バージョン | 確認コマンド |
| ------------ | ---------- | ------------ |
| Node.js      | 24+        | `node -v`    |
| pnpm         | 10+        | `pnpm -v`    |
| Rust / Cargo | (Tauri 用) | `cargo -V`   |

### 1. Playwright プロジェクト

```powershell
cd video/playwright
pnpm install
pnpm exec playwright install chromium
```

### 2. Remotion プロジェクト

```powershell
cd video/remotion
pnpm install
```

---

## 動画を作成する（基本フロー）

### Step 1 — アプリを起動する

VS Code の **コマンドパレット** から以下のタスクを実行します：

```
Tasks: Run Task → Economicon: App (Debug Port)
```

または PowerShell で直接起動：

```powershell
cd app
$env:WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS = '--remote-debugging-port=9222'
pnpm tauri dev
```

> アプリが完全に起動してファイルインポート画面が表示されるまで待ってから次の手順へ進んでください。

### Step 2 — スクリーンショットを収録する

```powershell
cd video/playwright

# サンプルデータフォルダを指定（省略時はリポジトリの sample/ フォルダを使用）
$env:ECONOMICON_TEST_SAMPLE_DIR = "<リポジトリ格納場所>/economicon/sample"

# C-09 基本統計量の収録
pnpm capture:c09
```

収録が完了すると `captured/c09/step-01.png` ～ `step-06.png` が生成されます。

### Step 3 — Remotion Studio でプレビューする

```powershell
cd video/remotion
pnpm studio
```

ブラウザで `http://localhost:3000` が開きます。左パネルから **C09DescriptiveStatistics** を選択してプレビューを確認します。

### Step 4 — MP4 をレンダリングする

```powershell
cd video/remotion

# 日本語版
pnpm render:c09:ja

# 英語版
pnpm render:c09:en
```

出力先：

| 言語   | ファイルパス                                        |
| ------ | --------------------------------------------------- |
| 日本語 | `video/output/ja/c09-descriptive-statistics-ja.mp4` |
| 英語   | `video/output/en/c09-descriptive-statistics-en.mp4` |

---

## 特定の動画だけを更新する

アプリの UI が変更されたとき、影響する動画だけを再収録・再レンダリングします。

```powershell
# 1. アプリを起動（Step 1 と同じ）

# 2. 該当するシーンを収録
cd video/playwright
pnpm capture:c09   # 例: C-09

# 3. Studio でプレビュー確認
cd ../remotion
pnpm studio

# 4. レンダリング
pnpm render:c09:ja
pnpm render:c09:en
```

---

## 新しい動画を追加する

新しい機能の動画（例: C-10 グループ別統計量）を追加する手順です。

### 1. 字幕テキストを追加する

`video/remotion/src/i18n/ja.json` と `en.json` に新しいキーを追加します：

```json
{
  "C09": { ... },
  "C10": {
    "title": "グループ別統計量",
    "titleSubtitle": "カテゴリ別に集計する",
    "steps": [
      "「基本分析」→「グループ別統計量」を選択",
      "グループ列と集計列を指定します",
      "「計算する」をクリックして結果を確認します"
    ],
    "ending": "次の動画：相関行列"
  }
}
```

### 2. 収録スクリプトを作成する

`video/playwright/scenes/c10-group-statistics.ts` を作成します。
`c09-descriptive-statistics.ts` を参考にシーン固有の操作手順を実装してください。

収録スクリプトの基本構造：

```typescript
import {
  captureStep,
  connectToApp,
  SAMPLE_DIR,
} from "../helpers/connectToApp.js";

const SCENE_ID = "c10";

async function main(): Promise<void> {
  const { browser, page } = await connectToApp();
  try {
    // 1. ワークスペースをリセット
    // 2. データをインポート
    // 3. 各ステップで captureStep(page, SCENE_ID, N) を呼ぶ
    // 4. コンソールに完了メッセージを出力
  } finally {
    await browser.close();
  }
}

main().catch((err: unknown) => {
  console.error("❌ キャプチャ失敗:", err);
  process.exit(1);
});
```

### 3. Remotion コンポジションを作成する

`video/remotion/src/compositions/C10GroupStatistics.tsx` を作成します。
`C09DescriptiveStatistics.tsx` をコピーして ID と i18n キーを変更するだけで基本的には動作します。

### 4. Root.tsx にコンポジションを登録する

```typescript
// video/remotion/src/Root.tsx
import { C10GroupStatistics, C10_TOTAL_FRAMES } from "./compositions/C10GroupStatistics";

<Composition
  id="C10GroupStatistics"
  component={C10GroupStatistics}
  durationInFrames={C10_TOTAL_FRAMES}
  fps={30}
  width={1920}
  height={1080}
  defaultProps={{ lang: "ja" }}
/>
```

### 5. package.json にスクリプトを追加する

`video/playwright/package.json`：

```json
"capture:c10": "tsx scenes/c10-group-statistics.ts"
```

`video/remotion/package.json`：

```json
"render:c10:ja": "remotion render src/Root.tsx C10GroupStatistics ../output/ja/c10-group-statistics-ja.mp4 --props={\"lang\":\"ja\"}",
"render:c10:en": "remotion render src/Root.tsx C10GroupStatistics ../output/en/c10-group-statistics-en.mp4 --props={\"lang\":\"en\"}"
```

---

## Remotion Studio でプレビューする

```powershell
cd video/remotion
pnpm studio
```

| 操作                          | 内容                                          |
| ----------------------------- | --------------------------------------------- |
| 左パネル → コンポジション選択 | 動画を切り替える                              |
| スペースキー                  | 再生 / 一時停止                               |
| 右クリック → "Edit Props"     | `lang` を `"en"` に変更して英語版をプレビュー |
| `J` / `L` キー                | コマ送り                                      |

> **スクリーンショットが表示されない場合**
> `captured/c09/` にファイルが存在するか確認してください。
> `pnpm capture:c09` を先に実行する必要があります（アプリ起動が前提）。

---

## トラブルシューティング

### `アプリ（ポート9222）が見つかりません` エラー

アプリが起動していないか、デバッグポートが有効になっていません。
VS Code タスク「**Economicon: App (Debug Port)**」でアプリを起動してから再実行してください。

### スクリーンショットが真っ黒になる

- アプリの起動が完了していない状態で収録を開始した可能性があります
- ターミナルで `pnpm capture:c09` を実行する前にアプリのファイルインポート画面が表示されていることを確認してください

### Remotion Studio で `Cannot find module` エラー

```powershell
cd video/remotion
pnpm install
```

を再実行してください。

### フォントが表示されない（レンダリング時）

Remotion のレンダリング環境がインターネットにアクセスできる必要があります。
Google Fonts CDN にアクセスできない環境では、フォントファイルをローカルに配置して
`@remotion/google-fonts` のローカルフォント設定を使用してください。

---

## 参考

- **動画仕様書**: [`docs/spec/video-spec.md`](../spec/video-spec.md)
- **E2E テストヘルパー（Playwright 接続の参考実装）**: [`app/e2e/helpers/setupHelpers.ts`](../../app/e2e/helpers/setupHelpers.ts)
- **Remotion 公式ドキュメント**: https://www.remotion.dev/docs
