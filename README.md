# Economicon

---

## Project Status

> [!WARNING]
> **This project is currently in Pre-release / Minimum Viable Product (MVP) stage.**
>
> - Not all statistical features have been implemented yet. Additional features will be added incrementally.
> - APIs and UI are subject to breaking changes without prior notice.

---

## Concept

**"Making econometrics more accessible and intuitive."**

Economicon is a standalone GUI application designed for **students, undergraduates, graduate students, and researchers** who want to quickly explore data properties and analytical trends — without writing a single line of code.

- **Ease of use**: Build and run econometric models through point-and-click workflows.
- **Clarity**: Results are presented clearly, including coefficients, standard errors, t-statistics, p-values, and confidence intervals.
- **Learning-oriented**: The interface is designed to guide users through proper analytical workflows (e.g., appropriate test ordering).

---

## ⚠️ Disclaimer

> [!IMPORTANT]
> **This tool is intended for learning and rapid data exploration ONLY.**
>
> - **MIT License**: This software is provided under the MIT License. There is **no warranty** of any kind regarding the accuracy of computational results.
> - **Use at your own risk**: You are solely responsible for any decisions made based on outputs from this tool.
> - **Double-check for serious research**: For academic theses, published papers, or any high-stakes decision-making, we **strongly recommend** verifying results using established statistical packages such as R (`plm`, `fixest`) or Stata.
> - **Partial coverage**: While key models are numerically validated against R outputs, not all edge cases are covered.

---

## Technology Stack

### Backend (Statistical Engine)

| Component         | Library        | Role                                         |
| ----------------- | -------------- | -------------------------------------------- |
| Regression Engine | `statsmodels`  | OLS, WLS, GLS, robust SEs                    |
| Panel / IV Models | `linearmodels` | Fixed Effects, Random Effects, 2SLS, GMM-IV  |
| Statistical Tests | `scipy`        | t-test, z-test, F-test, normality tests      |
| Data Processing   | `polars`       | High-performance in-memory data manipulation |
| Numerical Core    | `numpy`        | Array operations and linear algebra          |
| API Framework     | `FastAPI`      | REST API with OpenAPI schema generation      |

### Frontend (Desktop App)

| Component         | Library                  |
| ----------------- | ------------------------ |
| UI Framework      | React 19 + TypeScript    |
| Desktop Runtime   | Tauri (Rust-based)       |
| Build Tool        | Vite                     |
| Component Library | Radix UI + Tailwind CSS  |
| Data Table        | TanStack Table / Virtual |

### Numerical Validation

Results for key models are cross-validated against R (`plm`, `fixest`) using standard benchmark datasets (e.g., Grunfeld), maintaining numerical agreement within $10^{-8}$.

---

## Contribution Policy

> [!NOTE]
> **Pull Requests are not accepted.**
>
> To maintain code integrity and security, this project does **not** accept external Pull Requests.
>
> - **Bug reports**: Please open a GitHub Issue.
> - **Feature requests**: Please open a GitHub Issue.
>
> All code changes are managed solely by the maintainer.

---

---

## プロジェクトステータス

> [!WARNING]
> **本プロジェクトは現在プレリリース（Pre-release）かつ最小構成（MVP）段階です。**
>
> - 全ての統計機能が実装されているわけではなく、順次追加予定です。
> - API および UI は予告なく破壊的変更が加わる可能性があります。

---

## コンセプト

**「計量経済学を、もっと身近に、直感的に。」**

Economiconは、**計量経済学の初学者・学部生・大学院生・研究者**が、コードを書かずにGUI操作だけでデータの性質や分析の傾向を素早く確認できるスタンドアロン型アプリケーションです。

- **使いやすさ**: データの読み込みから高度な統計分析（固定効果・操作変数法など）まで、クリック操作で完結。
- **見やすさ**: 係数・標準誤差・t値・p値・信頼区間をセットで明瞭に表示。
- **学習のしやすさ**: 分析の作法（検定の順序など）をナビゲートし、専門用語にはツールチップで補足説明を提供。

---

## ⚠️ 免責事項

> [!IMPORTANT]
> **本ツールは「学習」および「迅速なデータ探索」を目的としています。**
>
> - **MITライセンス**: 本ソフトウェアはMITライセンスで提供されており、計算結果の正確性に関するいかなる保証もありません。
> - **自己責任の原則**: 本ツールの出力結果に基づく判断は、すべて利用者自身の責任において行ってください。
> - **厳密な研究への利用について**: 学位論文・学術論文・重要な意思決定に使用する場合は、必ず R（`plm`, `fixest`）や Stata 等の標準的な統計パッケージで結果を再確認することを**強く推奨します**。
> - **検証範囲の限界**: 主要なモデルについてはRの出力との数値照合テストを実施していますが、すべてのエッジケースを網羅しているわけではありません。

---

## テクノロジースタック

### バックエンド（統計エンジン）

| コンポーネント         | ライブラリ     | 役割                             |
| ---------------------- | -------------- | -------------------------------- |
| 回帰分析エンジン       | `statsmodels`  | OLS・WLS・GLS・ロバスト標準誤差  |
| パネル・操作変数モデル | `linearmodels` | 固定効果・変量効果・2SLS・GMM-IV |
| 統計検定               | `scipy`        | t検定・z検定・F検定・正規性検定  |
| データ処理             | `polars`       | 高速インメモリデータ操作         |
| 数値計算コア           | `numpy`        | 配列演算・線形代数               |
| APIフレームワーク      | `FastAPI`      | OpenAPIスキーマ付きREST API      |

### フロントエンド（デスクトップアプリ）

| コンポーネント           | ライブラリ               |
| ------------------------ | ------------------------ |
| UIフレームワーク         | React 19 + TypeScript    |
| デスクトップ実行環境     | Tauri（Rustベース）      |
| ビルドツール             | Vite                     |
| コンポーネントライブラリ | Radix UI + Tailwind CSS  |
| データテーブル           | TanStack Table / Virtual |

### 数値照合テスト

主要モデルの結果は、標準ベンチマークデータセット（Grunfeld等）を用いてR（`plm`, `fixest`）と数値照合を行い、$10^{-8}$ 以下の誤差での一致を確認しています。

---

## 貢献ポリシー

> [!NOTE]
> **プルリクエスト（PR）は受け付けていません。**
>
> コードの整合性とセキュリティを維持するため、外部からのPRは受け付けていません。
>
> - **バグ報告**: GitHub Issue でご報告ください。
> - **機能提案**: GitHub Issue でご提案ください。
>
> コードの変更はすべてメンテナーが管理します。

---
