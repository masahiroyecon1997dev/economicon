# Economicon 動画仕様書

## 1. 概要

### 目的

アプリの変更があっても素早く再収録・再生成できる、**自動化された動画制作パイプライン**を構築する。
YouTube への掲載を前提とし、初学者・学生（アプリ未使用者）向けに日本語・英語の両バージョンを提供する。

### 技術スタック

| レイヤー                 | ツール         | 役割                                                                            |
| ------------------------ | -------------- | ------------------------------------------------------------------------------- |
| アプリ収録               | **Playwright** | デバッグポート経由でアプリを自動操作し、スクリーンショット・動画クリップを取得  |
| 動画編集・合成           | **Remotion**   | React コンポーネントとして動画を定義。字幕・タイトル・トランジション・BGMを合成 |
| ナレーション（将来対応） | TBD            | 将来的に音声ナレーションを追加可能な構造にしておく                              |

### Playwright + Remotion の連携フロー

```
┌──────────────────────────────────────────────────────┐
│ 1. Playwright がアプリを自動操作して素材を収集      │
│    - スクリーンショット（.png）                      │
│    - 操作クリップ（.webm / .mp4 セグメント）         │
└──────────────────────┬───────────────────────────────┘
                       │ captured/ フォルダへ保存
┌──────────────────────▼───────────────────────────────┐
│ 2. Remotion が素材を読み込んで動画を構成            │
│    - タイトルカード・字幕・トランジション            │
│    - BGM（将来: 音声ナレーション）                   │
│    - 日本語 / 英語 の字幕を i18n で切り替え         │
└──────────────────────┬───────────────────────────────┘
                       │ render
┌──────────────────────▼───────────────────────────────┐
│ 3. 最終 MP4 を output/ フォルダへ書き出し           │
└──────────────────────────────────────────────────────┘
```

---

## 2. 動画一覧

### カテゴリ構成

| カテゴリ            | 動画数    | 長さ         | 説明                                    |
| ------------------- | --------- | ------------ | --------------------------------------- |
| **A. 紹介動画**     | 1 本      | 1〜2 分      | Economicon とは何か・何ができるかの概要 |
| **B. 機能紹介動画** | 3 本      | 各 60 秒以内 | 機能グループ別のダイジェスト            |
| **C. 使い方動画**   | 1 本/機能 | 各 60 秒以内 | 機能ごとのステップバイステップ解説      |

### 動画 ID 体系

```
A-01          … 紹介動画
B-01〜B-03    … 機能紹介ダイジェスト
C-01〜C-NN    … 使い方（機能別）
```

---

## 3. 動画 A：紹介動画

### A-01 Economicon とは（1〜2 分）

**目的：** アプリを一度も使ったことのない初学者・学生に「何のためのツールか」を伝える

**シーン構成：**

| #   | 長さ  | 内容                                               | 素材種別                |
| --- | ----- | -------------------------------------------------- | ----------------------- |
| 1   | 8 秒  | タイトルカード（Economicon ロゴ + キャッチコピー） | Remotion アニメーション |
| 2   | 15 秒 | 課題提示：「Excelで統計…計量経済はハードルが高い」 | テキストアニメーション  |
| 3   | 20 秒 | アプリ起動 → CSV インポート → テーブル表示まで     | Playwright 収録クリップ |
| 4   | 20 秒 | OLS 回帰分析の実行 → 結果表示                      | Playwright 収録クリップ |
| 5   | 15 秒 | 機能ハイライト一覧（スプリットスクリーン）         | スクリーンショット群    |
| 6   | 10 秒 | エンディング（URL・チャンネル案内）                | Remotion アニメーション |

---

## 4. 動画 B：機能紹介ダイジェスト

### B-01 データ取り込み・加工編（60 秒以内）

**紹介する機能：** CSV/Excel/Parquet インポート、テーブル結合（Join/Union）、列操作、計算列追加、フィルタ

**シーン構成：**

| #   | 長さ  | 内容                                           | 素材種別            |
| --- | ----- | ---------------------------------------------- | ------------------- |
| 1   | 5 秒  | タイトルカード「データ取り込みと加工」         | Remotion            |
| 2   | 10 秒 | CSV ファイルをドラッグ＆ドロップしてインポート | Playwright クリップ |
| 3   | 10 秒 | 2 テーブルを Join でキー結合                   | Playwright クリップ |
| 4   | 8 秒  | 列メニューからフィルタ・型変換                 | Playwright クリップ |
| 5   | 8 秒  | 計算列追加（例：売上 × 数量）                  | Playwright クリップ |
| 6   | 5 秒  | 加工済みテーブルを Parquet で保存              | Playwright クリップ |
| 7   | 5 秒  | エンディング                                   | Remotion            |

### B-02 統計分析・推定編（60 秒以内）

**紹介する機能：** 基本統計量、相関行列、グループ別統計、信頼区間、仮説検定、プロット

**シーン構成：**

| #   | 長さ  | 内容                                       | 素材種別            |
| --- | ----- | ------------------------------------------ | ------------------- |
| 1   | 5 秒  | タイトルカード「統計分析と推定」           | Remotion            |
| 2   | 8 秒  | 基本統計量（平均・標準偏差・四分位）を表示 | Playwright クリップ |
| 3   | 8 秒  | 相関行列（ヒートマップ表示）               | Playwright クリップ |
| 4   | 10 秒 | 信頼区間を計算・表示                       | Playwright クリップ |
| 5   | 10 秒 | 仮説検定（t 検定）を実行・p 値確認         | Playwright クリップ |
| 6   | 8 秒  | 散布図プロットを作成                       | Playwright クリップ |
| 7   | 5 秒  | エンディング                               | Remotion            |

### B-03 回帰・因果推論編（60 秒以内）

**紹介する機能：** OLS 回帰（通常/HAC/クラスター頑健標準誤差）、結果出力（LaTeX/Markdown）

> **注：** DID / RDD / Heckman はフロント未実装のため、実装後に B-03 または B-04 として追加する。

**シーン構成：**

| #   | 長さ  | 内容                                           | 素材種別            |
| --- | ----- | ---------------------------------------------- | ------------------- |
| 1   | 5 秒  | タイトルカード「回帰分析」                     | Remotion            |
| 2   | 15 秒 | OLS 回帰を実行 → 係数表・p 値・R² を確認       | Playwright クリップ |
| 3   | 10 秒 | HAC 頑健標準誤差に切り替えて再推定             | Playwright クリップ |
| 4   | 15 秒 | 分析結果を LaTeX / Markdown テーブルとして出力 | Playwright クリップ |
| 5   | 5 秒  | エンディング                                   | Remotion            |

---

## 5. 動画 C：機能別使い方動画（各 60 秒以内）

### 使い方動画 一覧

> **試作方針：** 最初は **C-09 基本統計量** を1本試作し、パイプライン全体が動くことを確認する。
> その後、残りの動画を順次追加していく。機能が新たに実装された場合は、動画 ID を末尾に追加する。

| ID             | タイトル                         | 対象機能                                         | 状態         |
| -------------- | -------------------------------- | ------------------------------------------------ | ------------ |
| C-01           | CSV ファイルのインポート         | ImportDataFile（CSV）                            | 実装済み     |
| C-02           | Excel / Parquet のインポート     | ImportDataFile（Excel/Parquet）                  | 実装済み     |
| C-03           | テーブルの Join（結合）          | JoinTable                                        | 実装済み     |
| C-04           | テーブルの Union（縦結合）       | UnionTable                                       | 実装済み     |
| C-05           | 列フィルタ・型変換               | ColumnOperationDialog（Filter/Cast）             | 実装済み     |
| C-06           | 変換列・ダミー変数の追加         | ColumnOperationDialog（Transform/AddDummy）      | 実装済み     |
| C-07           | 計算列の追加                     | Calculation                                      | 実装済み     |
| C-08           | データの保存                     | SaveData                                         | 実装済み     |
| **C-09** ★試作 | 基本統計量                       | DescriptiveStatistics                            | **試作対象** |
| C-10           | グループ別統計量                 | GroupStatistics                                  | 実装済み     |
| C-11           | 相関行列                         | CorrelationMatrix                                | 実装済み     |
| C-12           | 信頼区間の計算                   | ConfidenceIntervalView                           | 実装済み     |
| C-13           | 仮説検定                         | StatisticalTestView                              | 実装済み     |
| C-14           | OLS 線形回帰                     | LinearRegressionForm                             | 実装済み     |
| C-15           | DID 分析（差の差分析）           | DID                                              | 未実装・将来 |
| C-16           | RDD 分析（回帰不連続デザイン）   | RDD                                              | 未実装・将来 |
| C-17           | Heckman 選択モデル               | HeckmanSelection                                 | 未実装・将来 |
| C-18           | 散布図・ヒストグラムの作成       | PlotView                                         | 実装済み     |
| C-19           | 確率分布プレビュー               | DistributionPreview                              | 実装済み     |
| C-20           | シミュレーションデータ生成       | CreateSimulationDataTable                        | 実装済み     |
| C-21           | 分析結果の出力（LaTeX/Markdown） | OutputResultDialog                               | 実装済み     |
| C-22           | 信頼区間シミュレーション         | ConfidenceIntervalSim                            | 実装済み     |
| C-23           | OLS 推定量のシミュレーション     | AsymptoticNormality / Consistency / Unbiasedness | 実装済み     |

### 使い方動画 共通テンプレート

各動画は以下のテンプレートに従うこと：

| #   | 長さ      | 内容                                    | 素材種別            |
| --- | --------- | --------------------------------------- | ------------------- |
| 1   | 5 秒      | タイトルカード（機能名 + 1 行サマリー） | Remotion            |
| 2   | 45〜50 秒 | ステップバイステップ操作（字幕付き）    | Playwright クリップ |
| 3   | 3〜5 秒   | エンディング（次の動画へのリンク示唆）  | Remotion            |

---

## 6. 技術仕様

### 6.1 出力フォーマット

| 項目           | 値                                             |
| -------------- | ---------------------------------------------- |
| 解像度         | 1920 × 1080 (Full HD)                          |
| フレームレート | 30 fps                                         |
| コーデック     | H.264 / MP4                                    |
| 字幕           | Remotion テキストコンポーネントで焼き込み      |
| 言語バリアント | `ja`（日本語）/ `en`（英語）を個別レンダリング |

### 6.2 Playwright 収録仕様

- **接続方式：** Tauri のデバッグポート（`--remote-debugging-port=9222`）経由
- **ブラウザ：** Chromium（Tauri WebView2 ではなく Playwright 組み込みの Chromium を使用）
- **収録解像度：** 1920 × 1080 に viewport を固定
- **出力形式：** `.webm`（収録）→ ffmpeg で `.mp4` に変換
- **スクリーンショット形式：** `.png`（PNG 無圧縮）

> **注意：** Tauri の WebView2 を直接収録する場合は `mssql` や `cdp` 接続の代わりに
> デバッグポートを通じた CDP（Chrome DevTools Protocol）を使用する。

### 6.3 Remotion プロジェクト仕様

- **フレームワーク：** Remotion 4.x / React 19
- **パッケージマネージャ：** pnpm（workspace に追加）
- **フォント：** Noto Sans JP（日本語）/ Noto Sans（英語）
- **カラーパレット：** `brand-primary`（Tailwind のカスタムカラー）を継承
- **i18n：** 字幕テキストは JSON ファイルで管理し、`ja` / `en` を切り替えてレンダリング
- **BGM：** 著作権フリーの楽曲を `video/remotion/src/assets/audio/` に配置（将来対応）

---

## 7. ディレクトリ構成（案）

```
video/
├── playwright/
│   ├── scenes/                  # シーンごとの収録スクリプト
│   │   ├── c01-csv-import.ts
│   │   ├── c02-excel-import.ts
│   │   └── ...
│   ├── helpers/                 # 共通ヘルパー（ファイル選択・待機等）
│   │   └── videoCapture.ts
│   ├── captured/                # 収録済みクリップ（.gitignore 推奨）
│   │   ├── c01-csv-import.webm
│   │   └── ...
│   ├── playwright.config.ts
│   └── package.json
│
├── remotion/
│   ├── src/
│   │   ├── Root.tsx             # Remotion ルート（全動画を登録）
│   │   ├── compositions/        # 動画単位のコンポジション
│   │   │   ├── A01-Introduction/
│   │   │   ├── B01-DataOps/
│   │   │   └── C01-CsvImport/
│   │   ├── scenes/              # 共通シーンコンポーネント
│   │   │   ├── TitleCard.tsx
│   │   │   ├── Subtitle.tsx
│   │   │   ├── VideoClip.tsx    # Playwright 収録クリップの埋め込み
│   │   │   ├── Ending.tsx
│   │   │   └── Highlight.tsx   # 操作箇所をハイライトするオーバーレイ
│   │   ├── i18n/
│   │   │   ├── ja.json
│   │   │   └── en.json
│   │   └── assets/
│   │       ├── fonts/
│   │       └── audio/           # BGM（将来対応）
│   ├── package.json
│   └── remotion.config.ts
│
├── output/                      # レンダリング済み MP4（.gitignore 推奨）
│   ├── ja/
│   │   ├── A01-introduction-ja.mp4
│   │   └── ...
│   └── en/
│       ├── A01-introduction-en.mp4
│       └── ...
│
└── scripts/
    ├── capture-all.ps1          # 全シーンを Playwright で収録
    ├── render-all.ps1           # 全動画を Remotion でレンダリング
    └── pipeline.ps1             # 収録 → レンダリングを一括実行
```

---

## 8. 実行フロー

### 8.1 初回セットアップ

```powershell
# 1. Playwright 依存インストール
cd video/playwright
pnpm install
pnpm exec playwright install chromium

# 2. Remotion 依存インストール
cd ../remotion
pnpm install
```

### 8.2 動画を更新する（再収録フロー）

```powershell
# アプリ変更後、動画を最新化する
cd video

# Step 1: アプリをデバッグポートで起動（別ターミナル）
#   → VS Code タスク「Economicon: App (Debug Port)」を使用

# Step 2: 全シーンを収録
./scripts/capture-all.ps1

# Step 3: 全動画をレンダリング（ja + en）
./scripts/render-all.ps1

# または一括
./scripts/pipeline.ps1
```

### 8.3 特定の動画のみ更新

```powershell
# C-01 のみ再収録
cd video/playwright
pnpm exec ts-node scenes/c01-csv-import.ts

# C-01 のみレンダリング（日本語版）
cd ../remotion
pnpm exec remotion render C01CsvImport output/ja/C01-csv-import-ja.mp4 --props='{"lang":"ja"}'
```

---

## 9. Playwright 収録スクリプトの設計方針

### アプリへの接続

既存の E2E テストヘルパー（`app/e2e/helpers/setupHelpers.ts`）と同じ CDP 接続パターンを使用する。

```typescript
// helpers/videoCapture.ts
import { chromium } from "@playwright/test";

export async function connectToApp() {
  // 既存 E2E テストと同じ接続方式（setupHelpers.ts 参照）
  const browser = await chromium.connectOverCDP("http://127.0.0.1:9222");
  const context = browser.contexts()[0];
  // devtools:// ページを除外（setupHelpers.ts と同じロジック）
  const page =
    context.pages().find((p) => !p.url().startsWith("devtools://")) ??
    context.pages()[0];
  await page.setViewportSize({ width: 1920, height: 1080 });
  return { browser, context, page };
}
```

> **前提：** VS Code タスク `Economicon: App (Debug Port)` でアプリを起動済みであること。

### スクリーンショット取得

```typescript
// シーン内での静止画取得
await page.screenshot({
  path: `captured/c01-step${step}.png`,
  fullPage: false,
});
```

### 動画クリップ収録

```typescript
// 録画開始
await context.tracing.start({ screenshots: true, snapshots: true });
// ... 操作 ...
// 録画終了 → .zip に保存（Playwright Tracing）

// または RecordVideo オプションで webm を直接取得
const context = await browser.newContext({
  recordVideo: {
    dir: "captured/",
    size: { width: 1920, height: 1080 },
  },
});
```

### テストデータ

- 収録に使用するサンプルデータは **`sample/` フォルダのファイルを流用**する
  - `sample/線形回帰サンプル多変量.csv` → C-14 OLS 回帰
  - `sample/ユニオン1.csv` / `sample/ユニオン2.csv` → C-04 Union
  - `sample/回帰分析サンプル多変量.csv` → B-03 回帰ダイジェスト
- 動画収録スクリプトから参照するパスは環境変数 `ECONOMICON_TEST_SAMPLE_DIR` で渡す（既存 E2E テストと同じ方式）

---

## 10. Remotion コンポーネントの設計方針

### 字幕コンポーネント（Subtitle.tsx）

```tsx
// 動画クリップの上に字幕をオーバーレイ
export const Subtitle = ({
  text,
  lang,
}: {
  text: string;
  lang: "ja" | "en";
}) => (
  <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "center" }}>
    <div
      style={{
        background: "rgba(0,0,0,0.6)",
        color: "white",
        padding: "8px 16px",
        borderRadius: 4,
        fontSize: lang === "ja" ? 28 : 26,
        fontFamily: lang === "ja" ? "Noto Sans JP" : "Noto Sans",
        marginBottom: 40,
        maxWidth: "80%",
        textAlign: "center",
      }}
    >
      {text}
    </div>
  </AbsoluteFill>
);
```

### VideoClip コンポーネント（VideoClip.tsx）

```tsx
// Playwright 収録クリップを指定フレームで埋め込む
import { Video, staticFile } from "remotion";

export const VideoClip = ({ src, from, duration }: VideoClipProps) => (
  <Video
    src={staticFile(src)}
    startFrom={from}
    endAt={from + duration}
    style={{ width: "100%", height: "100%" }}
  />
);
```

### i18n 管理

```json
// i18n/ja.json（例）
{
  "C01": {
    "title": "CSV ファイルのインポート",
    "subtitle": "学習したいデータを Economicon に取り込みましょう",
    "steps": [
      "「取り込み」ボタンをクリック",
      "CSV ファイルを選択",
      "エンコーディングを確認して「取り込む」"
    ]
  }
}
```

---

## 11. ナレーション対応（将来）

現時点では字幕のみ。将来的な対応案：

| 方式             | 概要                                                                                     |
| ---------------- | ---------------------------------------------------------------------------------------- |
| **手動収録**     | 字幕テキストを元に人が読み上げた音声を `assets/audio/` に配置し Remotion で同期          |
| **TTS 自動生成** | VOICEVOX / Google Cloud TTS 等で字幕テキストから音声を自動生成してパイプラインに組み込む |

Remotion 側は `<Audio src={staticFile("narration/c01-step1.mp3")} />` を字幕と同フレームに配置する設計で対応可能。

---

## 12. 未確定事項・要確認

| #   | 項目                                                                    | 状態        | 優先度 |
| --- | ----------------------------------------------------------------------- | ----------- | ------ |
| 1   | DID / RDD / Heckman の使い方動画：フロント未実装 → C-15〜17 は将来追加  | ✅ 確定     | —      |
| 2   | Playwright CDP 接続：`--remote-debugging-port=9222` で既存 E2E と同方式 | ✅ 確定     | —      |
| 3   | サンプルデータ：`sample/` フォルダのファイルをそのまま流用              | ✅ 確定     | —      |
| 4   | **試作動画（C-09）でパイプライン全体を検証してから残りに展開**          | 🔲 対応待ち | 高     |
| 5   | BGM の調達（著作権フリーの楽曲ライブラリ選定）                          | 🔲 対応待ち | 低     |
| 6   | YouTube チャンネル名・説明文の策定                                      | 🔲 対応待ち | 低     |
| 7   | 動画サムネイル（Remotion で静止画生成 or 別途作成）                     | 🔲 対応待ち | 低     |
