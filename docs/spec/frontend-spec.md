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

## 将来検討

### Plotly.js を使った統計ビジュアライゼーション

既存の「可視化」メニューにサブメニューとして追加する教育用シミュレーション群。
データ生成・計算は FastAPI バックエンドで行い、フロントエンドは Plotly.js でレンダリングする。
既存の業務用チャート機能（ChartView）とは切り分けて実装する。

#### 1. 信頼区間シミュレーション

**概要**
「M 回サンプリングを繰り返すと、そのうち約 95% の信頼区間が真の値を含む」という定義を
アニメーションとカウンターで直感的に示す。試行回数を増やすほど実際の含有率が指定した信頼水準に収束することを第2プロットで補完する。
平均の CI と分散の CI をタブで切り替えて確認できる。

**レイアウト（2 プロット、上下配置）**

| プロット           | 縦軸               | 横軸                 | 内容                                                                                   |
| ------------------ | ------------------ | -------------------- | -------------------------------------------------------------------------------------- |
| 上（横棒グラフ）   | 試行番号（1 〜 M） | 推定値の範囲         | 各試行の信頼区間を横棒で表示。真の値を垂直実線で引く。真の値を含む → 緑、含まない → 赤 |
| 下（折れ線グラフ） | 実際の含有率（%）  | 累計試行数（1 〜 M） | 含有率の推移。信頼水準（例: 95%）を水平破線で示す                                      |

**アニメーション**

- 横棒を 1 本ずつ追加しながら上プロットを描画する
- 下プロットの折れ線はリアルタイムに更新される
- 上部に「k / M（z.z%）の信頼区間が真の値を含む」カウンターを常時表示

**ユーザー設定パラメータ**

| パラメータ               | デフォルト | 備考                     |
| ------------------------ | ---------- | ------------------------ |
| 試行回数 M               | 100        |                          |
| 各試行のサンプルサイズ n | 30         |                          |
| 信頼水準                 | 95%        | 90% / 95% / 99% から選択 |
| 真の母平均 μ             | 0          | 平均の CI タブで使用     |
| 真の母分散 σ²            | 1          | 分散の CI タブで使用     |

---

#### 2. 回帰係数の漸近正規性

**概要**
OLS 推定量の漸近正規性を示す。サンプルサイズ n が大きいほど β̂ の標本分布が正規分布に近づくことをヒストグラムと正規分布曲線の重ね合わせで示す。
誤差分布スイッチにより「仮定が満たされないと収束が保証されない」ことも同一 UI で確認できる。

**レイアウト（1 プロット）**

- ヒストグラム（横軸 = β̂、縦軸 = 密度）
- 漸近分散から導出した正規分布曲線を重ね合わせる
- 真の係数値 β を垂直実線で表示

**n の選択（ボタン選択式）**
10 / 20 / 30 / 50 / 100 / 1000（切り替えるとシミュレーション再実行）

**スライダー**

| パラメータ      | 範囲      |
| --------------- | --------- |
| 真の回帰係数 β  | −3 〜 3   |
| 誤差項の分散 σ² | 0.1 〜 10 |

**誤差分布スイッチ（3 択）**

| 選択肢               | 挙動                                                                                 |
| -------------------- | ------------------------------------------------------------------------------------ |
| 正規誤差             | n が大きいほど正規分布に収束（CLT 成立）                                             |
| コーシー誤差（厚裾） | 分散が存在しないため CLT 不成立。n=1000 でも正規分布に収束しない                     |
| 内生性あり           | CLT は成立するが、分布の中心が真の値から系統的にずれたままになる（不一致推定量の例） |

---

#### 3. 一致性（Consistency）

**概要**
観測数を 1 件ずつ増やしながら OLS を再推定し、サンプルサイズが増えるにつれ推定値が真の値に確率収束することをアニメーションで示す。
OLS の外生性仮定が崩れると収束先が真の値からずれたままになることをスイッチで比較できる。

**レイアウト（1 プロット）**

- 折れ線グラフ（横軸 = サンプルサイズ n、縦軸 = 推定値 β̂）
- 真の値 β を水平破線で表示
- アニメーション: サンプルサイズを段階的に増やしながら折れ線をなめらかに描画。上下に振れながら真の値に近づく軌跡を表現する

**スイッチ（2 択）**

| 選択肢                     | 内容                                               |
| -------------------------- | -------------------------------------------------- |
| OLS 仮定あり（外生性成立） | n → ∞ で真の値に収束する                           |
| 内生性あり（外生性不成立） | n → ∞ でも推定値がバイアスを持ち真の値に収束しない |

---

#### 4. 不偏性（Unbiasedness）

**概要**
同一の母集団から繰り返しサンプルを取り直して OLS を M 回実行すると、β̂ の標本平均が真の値 β に収束することを 2 プロットのアニメーションで示す。

**レイアウト（2 プロット、上下配置）**

| プロット           | 縦軸                 | 横軸               | 内容                                                                          |
| ------------------ | -------------------- | ------------------ | ----------------------------------------------------------------------------- |
| 上（ヒストグラム） | 頻度                 | β̂ の値             | 試行を重ねるごとにバーを更新。真の値 β を赤垂直線、累積平均を青垂直線で重ねる |
| 下（折れ線グラフ） | 累積平均 − β（差分） | 試行番号（1 〜 M） | 差分がゼロへ収束する様子を表示。ゼロを水平破線で示す                          |

**アニメーション**
試行を 1 件ずつ追加し、上下のプロットを同時に更新する。

**ユーザー設定パラメータ**

| パラメータ               | デフォルト |
| ------------------------ | ---------- |
| 試行回数 M               | 200        |
| 各試行のサンプルサイズ n | 50         |
| 真の回帰係数 β           | 1.0        |
| 誤差項の分散 σ²          | 1.0        |

---

### 実装設計

#### 共通設計方針

| 項目                   | 方針                                                                                                    |
| ---------------------- | ------------------------------------------------------------------------------------------------------- |
| メニュー配置           | 既存「可視化」メニューに 4 項目追加（PlotView・分布プレビューと同列）                                   |
| パラメータ変更トリガー | debounce 300ms 自動再実行（DistributionPreview と同方式）。アニメーション中は先にリセットしてから再実行 |
| アニメーション速度     | 遅い / 普通 / 速い の 3 段階を UI で選択可能                                                            |
| アニメーション完了後   | ループなし。全データ表示のまま停止。再生ボタンで最初から再生                                            |
| x_mean / x_variance    | 「詳細設定」折りたたみセクションに配置（初期値: 0 / 1）                                                 |
| レイアウト基準         | `grid-cols-[300px_1fr]`（左ペイン: パラメータ、右ペイン: プロット）                                     |

#### 新規 WorkFeatureKey

```typescript
// workspaceTabs.ts に追加
| "ConfidenceIntervalSim"
| "AsymptoticNormality"
| "Consistency"
| "Unbiasedness"
```

#### 各スライダーの step 値

| パラメータ               | step |
| ------------------------ | ---- |
| 真の回帰係数 β           | 0.1  |
| 誤差分散 σ²              | 0.1  |
| 内生性の強さ γ           | 0.1  |
| 試行回数 M（整数）       | 1    |
| サンプルサイズ n（整数） | 1    |
| 母平均 μ                 | 0.1  |
| 母分散 σ²（CI 用）       | 0.1  |
| n_max（整数）            | 1    |

#### 共通コンポーネント設計

**DistributionPreview から分離して共通化するもの**

| コンポーネント   | 分類                 | 概要                                                                                                                                                                          |
| ---------------- | -------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `PlotPanel`      | `molecules/Loading/` | `div ref` + Loader2 overlay + ErrorAlert + purge 処理を一体化。props: `plotRef`, `loading`, `error`, `className?`, `testId?`                                                  |
| `SimParamSlider` | `molecules/Field/`   | ラベル・現在値・min/max 表示付き `<input type="range">`。DistributionPreview のインライン実装を切り出す。props: `label`, `min`, `max`, `step`, `value`, `onChange`, `testId?` |

**4 シミュレーション画面用の新規共通コンポーネント**

| コンポーネント       | 分類                   | 概要                                                                                                                                                                                            |
| -------------------- | ---------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `CollapsibleSection` | `molecules/Layout/`    | 折りたたみ可能なセクション。「詳細設定」（xDistribution パラメータ）に使用。props: `title`, `children`, `defaultOpen?`                                                                          |
| `AnimationControls`  | `molecules/ActionBar/` | 再生 / 一時停止 / リセット ボタン + 速度セレクター（遅/普/速）+ フレームカウンター表示。props: `playing`, `canPlay`, `frame`, `total`, `speed`, `onPlay`, `onPause`, `onReset`, `onSpeedChange` |

**新規 hooks**

| フック                   | 用途                                                                                                                |
| ------------------------ | ------------------------------------------------------------------------------------------------------------------- |
| `useSimulationAnimation` | setInterval ベースのフレーム管理。CI シミュレーション・一致性・不偏性で共用。speed に応じてインターバルを切り替える |

#### 各画面のコンポーネント構成

**1. 信頼区間シミュレーション（`ConfidenceIntervalSim`）**

```
左ペイン
├─ Tabs: 平均 CI / 分散 CI              ← ciType 切り替え
├─ RadioTagGroup: 信頼水準 90% / 95% / 99%
├─ SimParamSlider: 試行回数 M
├─ SimParamSlider: サンプルサイズ n
├─ SimParamSlider: 母平均 μ             (平均 CI タブのみ)
├─ SimParamSlider: 母分散 σ²            (分散 CI タブのみ)
└─ CollapsibleSection「詳細設定」
   ├─ SimParamSlider: x_mean
   └─ SimParamSlider: x_variance

右ペイン
├─ AnimationControls
│  （再生/停止/リセット + 速度 + カウンター「k / M（z.z%）の CI が真の値を含む」）
├─ PlotPanel（上: 横棒グラフ — 各試行の CI。真の値を垂直実線。含む→緑、含まない→赤）
└─ PlotPanel（下: 折れ線グラフ — 累計含有率。信頼水準を水平破線）
```

**2. 漸近正規性（`AsymptoticNormality`）**

```
左ペイン
├─ RadioTagGroup: n = 10 / 20 / 30 / 50 / 100 / 1000
├─ SimParamSlider: 真の回帰係数 β
├─ SimParamSlider: 誤差分散 σ²
├─ RadioTagGroup: 誤差タイプ（正規誤差 / コーシー誤差 / 内生性あり）
├─ SimParamSlider: 内生性の強さ γ       ← endogenous 選択時のみ表示
└─ CollapsibleSection「詳細設定」
   ├─ SimParamSlider: x_mean
   └─ SimParamSlider: x_variance

右ペイン
└─ PlotPanel（ヒストグラム + 漸近正規分布曲線 + 真の値 β 垂直線）
   ※アニメーションなし。debounce で自動更新
   ※コーシー選択時は正規分布曲線なし・「CLT 不成立」テキスト表示
   ※内生性あり時は「不一致推定量のため分布中心がずれる」テキスト表示
```

**3. 一致性（`Consistency`）**

```
左ペイン
├─ RadioTagGroup: 外生性成立 / 内生性あり
├─ SimParamSlider: n_max
├─ SimParamSlider: 真の回帰係数 β
├─ SimParamSlider: 誤差分散 σ²
├─ SimParamSlider: 内生性の強さ γ       ← 内生性あり選択時のみ表示
└─ CollapsibleSection「詳細設定」
   ├─ SimParamSlider: x_mean
   └─ SimParamSlider: x_variance

右ペイン
├─ AnimationControls
└─ PlotPanel（折れ線グラフ + 真の値 β 水平破線 + 確率極限水平実線）
   ※内生性あり時: 確率極限 = β + γ/2 を実線で追加表示
```

**4. 不偏性（`Unbiasedness`）**

```
左ペイン
├─ SimParamSlider: 試行回数 M
├─ SimParamSlider: サンプルサイズ n
├─ SimParamSlider: 真の回帰係数 β
├─ SimParamSlider: 誤差分散 σ²
└─ CollapsibleSection「詳細設定」
   ├─ SimParamSlider: x_mean
   └─ SimParamSlider: x_variance

右ペイン
├─ AnimationControls
├─ PlotPanel（上: ヒストグラム — 真の値 β 赤垂直線 + 累積平均 β̂ 青垂直線）
└─ PlotPanel（下: 折れ線グラフ — 累積平均 − β の推移 + ゼロ水平破線）
```

#### 新規作成ファイル一覧

```
app/src/
  components/
    molecules/
      Loading/
        PlotPanel.tsx
      Field/
        SimParamSlider.tsx
      Layout/
        CollapsibleSection.tsx
      ActionBar/
        AnimationControls.tsx
    pages/
      ConfidenceIntervalSim.tsx
      AsymptoticNormality.tsx
      Consistency.tsx
      Unbiasedness.tsx
  hooks/
    useSimulationAnimation.ts
    useConfidenceIntervalSim.ts
    useAsymptoticNormality.ts
    useConsistency.ts
    useUnbiasedness.ts
```

#### 変更が必要な既存ファイル

| ファイル                                           | 変更内容                                                      |
| -------------------------------------------------- | ------------------------------------------------------------- |
| `app/src/stores/workspaceTabs.ts`                  | `WorkFeatureKey` に 4 値追加                                  |
| `app/src/components/pages/WorkspaceSurface.tsx`    | `WORK_TAB_COMPONENTS` に 4 画面追加                           |
| `app/src/components/organisms/Header/AppBar.tsx`   | 「可視化」メニューに 4 項目追加                               |
| `app/src/components/pages/DistributionPreview.tsx` | `PlotPanel` / `SimParamSlider` を利用する形にリファクタリング |
| `app/src/i18n/locales/ja.json`                     | 4 画面分の i18n キー追加                                      |
| `app/src/i18n/locales/en.json`                     | 4 画面分の i18n キー追加                                      |

---

## テスト注意事項

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

#### Phase 1: 共通基盤

1. **`SimParamSlider`** — DistributionPreview のインラインスライダーを Molecule として切り出す
   - Vitest: props 経由で label・value・min/max が正しくレンダリングされること / `onChange` が呼ばれること
2. **`PlotPanel`** — DistributionPreview の Plotly コンテナ部分を Molecule として切り出す
   - Vitest: `loading=true` で Loader2 が表示されること / `error` が非 null でエラー文字列が表示されること
3. **`CollapsibleSection`** — 折りたたみセクションを新規作成
   - Vitest: クリックで展開・折りたたみが切り替わること
4. **`useSimulationAnimation`** — フレーム管理 hook を新規作成
   - Vitest: `play()` → フレームが進む / `pause()` → フレームが止まる / `reset()` → 0 に戻る / speed 変更でインターバルが変わること
5. **`AnimationControls`** — 上記 hook を組み合わせた UI コンポーネントを新規作成
   - Vitest: 再生・一時停止・リセットのクリックが各コールバックを呼ぶこと / フレームカウンターが正しく表示されること
6. **`DistributionPreview` のリファクタリング** — `PlotPanel` / `SimParamSlider` に切り替える
   - 既存テストが引き続き通ることを確認

#### Phase 2: ストア・ルーティング拡張

7. **`workspaceTabs.ts`** — `WorkFeatureKey` に 4 値追加
8. **`WorkspaceSurface.tsx`** — `WORK_TAB_COMPONENTS` に 4 画面追加（空の placeholder コンポーネントで先行登録）
9. **`AppBar.tsx`** — 「可視化」メニューに 4 項目追加
10. **i18n（`ja.json` / `en.json`）** — 4 画面分のキーをまとめて追加

#### Phase 3: 各シミュレーション画面（アニメーションなし画面を先行）

11. **`useAsymptoticNormality`** — API フック（debounce 付き）
    - Vitest: invoke モック経由でリザルトが取得できること / エラー時に `error` がセットされること
12. **`AsymptoticNormality`** — 漸近正規性画面（アニメーションなし。最もシンプルなため先行）
    - Vitest: n ボタン切り替えで hook が再実行されること / コーシー時に CLT 不成立テキストが表示されること

#### Phase 4: アニメーション付き画面（複雑度の低い順）

13. **`useConsistency`** — API フック
    - Vitest: invoke モック、result 検証
14. **`Consistency`** — 一致性画面
    - Vitest: 外生性/内生性スイッチで確率極限表示が切り替わること / AnimationControls が正しく動作すること
15. **`useUnbiasedness`** — API フック
    - Vitest: invoke モック、result 検証
16. **`Unbiasedness`** — 不偏性画面
    - Vitest: アニメーションで上下プロットが同時に更新されること
17. **`useConfidenceIntervalSim`** — API フック
    - Vitest: invoke モック、result 検証
18. **`ConfidenceIntervalSim`** — 信頼区間シミュレーション画面（最もパラメータが多い）
    - Vitest: 平均 CI / 分散 CI タブ切り替えで表示パラメータが変わること / カウンター表示が正しいこと
