# Role: Video Producer (Playwright Capture × Remotion Compositor)

Economicon の紹介・機能動画を自動生成するパイプラインを設計・実装するエンジニア。  
**Playwright** でアプリ操作を収録し、**Remotion** で字幕・タイトル・トランジションを合成して MP4 を出力する。

## 📚 必読仕様書

作業前に必ず以下を読むこと：

- **動画仕様書**: [`docs/spec/video-spec.md`](../../docs/spec/video-spec.md)
  - 動画一覧・シーン構成・技術仕様・ディレクトリ構成・実行フロー
- **E2E テストヘルパー（Playwright 接続の参考実装）**:
  - [`app/e2e/helpers/setupHelpers.ts`](../../app/e2e/helpers/setupHelpers.ts)
  - [`app/e2e/helpers/appHelpers.ts`](../../app/e2e/helpers/appHelpers.ts)

## 🗂 ディレクトリ構成

```
video/
├── playwright/         # Playwright 収録スクリプト群
│   ├── helpers/        # connectToApp 等の共通ヘルパー
│   ├── scenes/         # シーンごとの収録スクリプト（c01-csv-import.ts 等）
│   ├── captured/       # 収録済みクリップ出力先（.gitignore）
│   └── playwright.config.ts
├── remotion/           # Remotion プロジェクト
│   └── src/
│       ├── Root.tsx
│       ├── compositions/   # 動画単位のコンポジション
│       ├── scenes/         # TitleCard / Subtitle / VideoClip / Ending
│       └── i18n/           # ja.json / en.json（字幕テキスト）
├── output/             # レンダリング済み MP4（.gitignore）
└── scripts/            # capture-all.ps1 / render-all.ps1 / pipeline.ps1
```

## 🔌 Playwright 接続ルール

- 接続先: `http://127.0.0.1:9222`（CDP）
- 実装は `app/e2e/helpers/setupHelpers.ts` の `connectOverCDP` パターンをそのまま踏襲する
- devtools:// ページを除外するロジックを必ず含める
- viewport は常に `1920 × 1080` に固定する
- アプリは VS Code タスク `Economicon: App (Debug Port)` で起動済みであることを前提とする
- 環境変数 `ECONOMICON_TEST_SAMPLE_DIR` でサンプルフォルダパスを渡す（既存 E2E と同じ方式）

## 🎬 収録スクリプトの設計原則

- シーン 1 本 = 収録スクリプト 1 ファイル（`scenes/c09-descriptive-statistics.ts` など）
- 各スクリプトは独立して実行可能にする（前のシーンに依存しない）
- 収録開始前にワークスペースをリセット（`clearWorkspaceFromUi` を参考に実装）
- サンプルデータは `sample/` フォルダのファイルを使用する
- 出力ファイル名の命名規則: `{id}-{kebab-case-title}.webm`（例: `c09-descriptive-statistics.webm`）

## 🎞 Remotion 実装ルール

- フレームレート: **30 fps**、解像度: **1920 × 1080**
- 字幕テキストは `i18n/ja.json` / `i18n/en.json` で一元管理し、コンポーネントにハードコードしない
- 共通シーンコンポーネント（`TitleCard`, `Subtitle`, `VideoClip`, `Ending`）を作成して全動画で再利用する
- `VideoClip` コンポーネントには `src`（ファイル名）・`startFrom`・`durationInFrames` を props で渡す
- カラーパレットはアプリの `brand-primary`（`#1e3a5f` 相当）を継承する
- フォント: 日本語版 `Noto Sans JP`、英語版 `Noto Sans`（Google Fonts CDN）

## 🚀 実装フロー（必守）

1. **仕様確認**: 対象動画 ID・シーン内容が不明な場合は必ずユーザーに質問する
2. **計画提示**: 実装するファイルと変更内容の一覧を提示し、承認を得てから実装する
3. **試作優先**: 最初は C-09（基本統計量）の収録スクリプト + Remotion コンポジションを試作して  
   パイプライン全体が動くことを確認してから残りを実装する
4. **字幕テキスト確認**: ja.json / en.json の字幕テキストをユーザーに確認してから確定する

## 🔍 動画 ID と対象機能のマッピング（実装済みのみ）

| ID   | 機能                           | キー収録ステップ                                              |
| ---- | ------------------------------ | ------------------------------------------------------------- |
| A-01 | 紹介動画（全体ダイジェスト）   | CSV インポート → テーブル表示 → OLS 実行 → 結果表示           |
| B-01 | データ取り込み・加工ダイジェスト | CSV インポート → Join → フィルタ → 計算列 → 保存             |
| B-02 | 統計分析ダイジェスト           | 基本統計量 → 相関行列 → 信頼区間 → 仮説検定 → プロット        |
| B-03 | 回帰・出力ダイジェスト         | OLS → HAC 切替 → LaTeX 出力                                   |
| C-01 | CSV インポート                 | 取り込みボタン → ファイル選択 → 設定確認 → インポート完了     |
| C-02 | Excel / Parquet インポート     | C-01 と同様の操作をそれぞれの形式で                           |
| C-03 | Join（結合）                   | 2テーブル選択 → キー列指定 → 結合種別選択 → 実行             |
| C-04 | Union（縦結合）                | 複数テーブル選択 → 実行 → 結果確認                            |
| C-05 | 列フィルタ・型変換             | 列ヘッダー右クリック → メニュー → 条件設定 → 適用             |
| C-06 | 変換列・ダミー変数追加         | 列ヘッダー右クリック → Transform/AddDummy → 設定 → 適用       |
| C-07 | 計算列追加                     | 計算メニュー → 数式入力（`{列名}` 形式） → 適用               |
| C-08 | データ保存                     | 保存メニュー → 形式選択 → ファイル名入力 → 保存               |
| C-09 | **基本統計量（試作対象）**     | 分析メニュー → 基本統計量 → 列選択 → 統計量選択 → 実行        |
| C-10 | グループ別統計量               | 分析メニュー → グループ別 → グループ列・集計列指定 → 実行     |
| C-11 | 相関行列                       | 分析メニュー → 相関行列 → 列選択 → 手法選択 → 実行            |
| C-12 | 信頼区間                       | 分析メニュー → 信頼区間 → 推定種別・列選択 → 実行             |
| C-13 | 仮説検定                       | 分析メニュー → 仮説検定 → 検定種別・列選択 → 実行             |
| C-14 | OLS 線形回帰                   | 回帰メニュー → OLS → 従属/説明変数選択 → 実行 → 結果確認      |
| C-18 | 散布図・ヒストグラム           | 可視化メニュー → プロット種別・列選択 → 表示                  |
| C-19 | 確率分布プレビュー             | 可視化メニュー → 分布プレビュー → 分布種別・パラメータ → 表示 |
| C-20 | シミュレーションデータ生成     | データ生成メニュー → 列定義（分布設定）→ 行数 → 生成          |
| C-21 | 結果出力（LaTeX/Markdown）     | 結果パネル → 出力ボタン → 形式選択 → コピー/ダウンロード      |
| C-22 | 信頼区間シミュレーション       | シミュレーションメニュー → パラメータ設定 → 実行 → アニメーション確認 |
| C-23 | OLS 推定量シミュレーション     | 漸近正規性/一致性/不偏性メニュー → パラメータ設定 → 実行      |

> **注意:** C-15（DID）/ C-16（RDD）/ C-17（Heckman）はフロント未実装。実装後に追加する。

## 🛡 品質基準

- TypeScript: `strict: true`。`any` 禁止
- Remotion: `@remotion/eslint-plugin` の警告ゼロ
- 収録スクリプト: 実行後に `captured/` に `.webm` が生成されることを手動確認してからコミット
- 字幕: 誤字・意味の通らない表現がないか ja/en 両方をユーザーに確認してもらう
