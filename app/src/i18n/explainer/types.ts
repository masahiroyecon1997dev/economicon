export type ExplainerItemSize = "sm" | "md" | "lg" | "xl" | "2xl";

export type ExplainerItem = {
  title: string;
  /** Markdown 本文。数式は $$...$$（ブロック）/ $...$（インライン）、表は GFM 記法 */
  body: string;
  /** ダイアログ幅。省略時は "md"（max-w-lg 相当） */
  size?: ExplainerItemSize;
};

export type ExplainerContentMap = Record<string, ExplainerItem>;
