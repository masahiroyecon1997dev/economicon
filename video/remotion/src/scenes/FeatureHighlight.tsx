import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

interface FeatureHighlightProps {
  /** セクションタイトル */
  title: string;
  /** 機能名の配列（labels[i] と descs[i] が 1 カードに対応） */
  labels: readonly string[];
  /** 機能説明の配列 */
  descs: readonly string[];
  /** "ja" | "en" — フォントファミリー切り替えに使用 */
  lang: "ja" | "en";
  /**
   * このコンポーネントが <Sequence> 内でレンダリングされる場合、
   * Sequence の durationInFrames をここに渡すこと。
   */
  durationInFrames: number;
}

const FONTS: Record<"ja" | "en", string> = {
  ja: '"Noto Sans JP", sans-serif',
  en: '"Noto Sans", sans-serif',
};

/** カードのアクセントカラー（brand-primary 系トーン） */
const ACCENT_COLORS = [
  "#4d9fe8",
  "#3b8dd6",
  "#2d7bc4",
  "#5aafef",
  "#6cbdf5",
  "#7ccbff",
] as const;

/** カードが出現し始めるフレーム */
const CARDS_START_FRAME = 30;
/** カード間のスタッガー（frames） */
const CARD_STAGGER = 18;

/**
 * 機能ハイライトグリッドコンポーネント（A-01 シーン 5 用）
 *
 * - タイトルが frame 0 に spring fade-in
 * - 6 枚のカードが CARDS_START_FRAME からスタッガーで登場
 * - 3 列 × 2 行グリッド
 */
export const FeatureHighlight: React.FC<FeatureHighlightProps> = ({
  title,
  labels,
  descs,
  lang,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const fontFamily = FONTS[lang];

  const titleOpacity = spring({
    frame,
    fps,
    config: { damping: 22, stiffness: 100 },
  });
  const titleY = spring({
    frame,
    fps,
    config: { damping: 18, stiffness: 80 },
    from: 20,
    to: 0,
  });

  return (
    <AbsoluteFill
      style={{
        background: "linear-gradient(160deg, #0d1f35 0%, #112840 100%)",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        gap: 48,
        padding: "60px 120px",
      }}
    >
      {/* タイトル */}
      <div
        style={{
          opacity: titleOpacity,
          transform: `translateY(${String(titleY)}px)`,
          color: "rgba(255,255,255,0.95)",
          fontSize: lang === "ja" ? 52 : 46,
          fontFamily,
          fontWeight: 700,
          textAlign: "center",
          letterSpacing: lang === "ja" ? "0.04em" : "0",
        }}
      >
        {title}
      </div>

      {/* カードグリッド（3 × 2） */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(3, 1fr)",
          gap: 32,
          width: "100%",
          maxWidth: 1440,
        }}
      >
        {labels.map((label, i) => {
          const cardStart = CARDS_START_FRAME + i * CARD_STAGGER;
          const cardOpacity = spring({
            frame: frame - cardStart,
            fps,
            config: { damping: 20, stiffness: 90 },
          });
          const cardY = spring({
            frame: frame - cardStart,
            fps,
            config: { damping: 16, stiffness: 80 },
            from: 30,
            to: 0,
          });
          const accentColor =
            ACCENT_COLORS[i % ACCENT_COLORS.length] ?? ACCENT_COLORS[0];

          // アクセントバーの幅アニメーション
          const barWidth = interpolate(
            frame,
            [cardStart, cardStart + 35],
            [0, 40],
            { extrapolateRight: "clamp" },
          );

          return (
            <div
              key={i}
              style={{
                opacity: frame < cardStart ? 0 : cardOpacity,
                transform: `translateY(${String(cardY)}px)`,
                background: "rgba(255,255,255,0.06)",
                border: `1px solid ${accentColor}44`,
                borderRadius: 16,
                padding: "28px 32px",
                display: "flex",
                flexDirection: "column",
                gap: 12,
              }}
            >
              {/* アクセントバー */}
              <div
                style={{
                  width: barWidth,
                  height: 4,
                  borderRadius: 2,
                  background: accentColor,
                }}
              />
              {/* 機能名 */}
              <div
                style={{
                  color: "rgba(255,255,255,0.95)",
                  fontSize: lang === "ja" ? 30 : 28,
                  fontFamily,
                  fontWeight: 700,
                  lineHeight: 1.3,
                }}
              >
                {label}
              </div>
              {/* 説明 */}
              <div
                style={{
                  color: "rgba(255,255,255,0.60)",
                  fontSize: lang === "ja" ? 22 : 20,
                  fontFamily,
                  lineHeight: 1.4,
                }}
              >
                {descs[i]}
              </div>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};
