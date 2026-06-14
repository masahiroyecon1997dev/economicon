import type { ExplainerContentMap } from "./types";

export const jaExplainer = {
  mean: {
    title: "平均の信頼区間（t 分布）",
    description:
      "標本平均 x̄ を点推定値とし、t 分布を用いて母平均 μ の信頼区間を計算します。標本が正規分布から得られている場合、または大標本（中心極限定理）の場合に適用できます。",
    formula: "\\bar{x} \\pm t_{\\alpha/2,\\, n-1} \\cdot \\frac{s}{\\sqrt{n}}",
    assumptions:
      "データが独立同一分布（i.i.d.）に従うこと。標本数が少ない場合は正規分布に近いことが望ましい。",
  },
  median: {
    title: "中央値の信頼区間（ブートストラップ）",
    description:
      "ブートストラップ法（1,000 回再サンプリング）で中央値の信頼区間を推定します。分布形状への仮定が不要なノンパラメトリックな手法です。",
    formula:
      "\\left[\\hat{m}^*_{(\\alpha/2)},\\;\\hat{m}^*_{(1-\\alpha/2)}\\right]",
    assumptions:
      "データが元の母集団の代表的な標本であること。標本数が小さい場合は区間の精度が下がる。",
  },
  proportion: {
    title: "比率の信頼区間（Wilson スコア区間）",
    description:
      "二値データ（0 または 1 のみ）の成功割合 p̂ に対して、Wilson スコア区間を計算します。Wald 区間より小標本での被覆率が良好です。列の値が 0 と 1 のみであることが必要です。",
    formula:
      "\\frac{\\hat{p} + \\dfrac{z^2}{2n} \\pm z\\sqrt{\\dfrac{\\hat{p}(1-\\hat{p})}{n} + \\dfrac{z^2}{4n^2}}}{1 + \\dfrac{z^2}{n}}",
    assumptions:
      "列の値が 0 または 1（二値）のみであること。それ以外の値を含む場合は API エラーが返される。",
  },
  variance: {
    title: "分散の信頼区間（カイ二乗分布）",
    description:
      "標本分散 s² を点推定値とし、カイ二乗分布を用いて母分散 σ² の信頼区間を計算します。データが正規分布に従う場合に正確な区間が得られます。",
    formula:
      "\\left[\\frac{(n-1)s^2}{\\chi^2_{\\alpha/2,\\, n-1}},\\;\\frac{(n-1)s^2}{\\chi^2_{1-\\alpha/2,\\, n-1}}\\right]",
    assumptions:
      "データが正規分布に従うこと。正規性から大きく外れる場合は区間の信頼性が低下する。",
  },
  standard_deviation: {
    title: "標準偏差の信頼区間",
    description:
      "分散の信頼区間の平方根として標準偏差 σ の信頼区間を算出します。分散の信頼区間と同じ前提条件（正規分布仮定）が適用されます。",
    formula:
      "\\left[\\sqrt{\\text{CI}_{\\text{lower}}(\\sigma^2)},\\;\\sqrt{\\text{CI}_{\\text{upper}}(\\sigma^2)}\\right]",
    assumptions: "データが正規分布に従うこと（分散 CI の前提と同様）。",
  },
} satisfies ExplainerContentMap;
