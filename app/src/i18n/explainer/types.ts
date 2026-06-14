export type ExplainerItem = {
  title: string;
  /** 解説本文（プレーンテキスト）。段落は "\n\n" で区切る */
  description: string;
  /** KaTeX 形式の数式文字列。undefined のときは数式ブロックを非表示 */
  formula?: string;
  /** 前提条件・注意事項（プレーンテキスト） */
  assumptions?: string;
};

export type ExplainerContentMap = Record<string, ExplainerItem>;
