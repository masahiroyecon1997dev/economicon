export type ExplainerSection = {
  heading: string;
  /** セクション本文。"\n\n" で段落分け */
  body: string;
};

export type ExplainerItem = {
  title: string;
  /** 解説本文（プレーンテキスト）。段落は "\n\n" で区切る */
  description: string;
  /** KaTeX 形式の数式文字列。undefined のときは数式ブロックを非表示 */
  formula?: string;
  /** 前提条件・注意事項（プレーンテキスト） */
  assumptions?: string;
  /** 複数セクションを持つ長文解説（formula/assumptions の代替） */
  sections?: ExplainerSection[];
};

export type ExplainerContentMap = Record<string, ExplainerItem>;
