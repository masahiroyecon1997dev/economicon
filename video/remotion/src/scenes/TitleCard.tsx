import {
  AbsoluteFill,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

interface TitleCardProps {
  title: string;
  subtitle?: string;
  /** "ja" | "en" — フォントファミリー切り替えに使用 */
  lang: "ja" | "en";
}

/** フォント設定 */
const FONTS: Record<"ja" | "en", string> = {
  ja: '"Noto Sans JP", sans-serif',
  en: '"Noto Sans", sans-serif',
};

/** brand-primary グラデーション背景のタイトルカード */
export const TitleCard: React.FC<TitleCardProps> = ({
  title,
  subtitle,
  lang,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const fontFamily = FONTS[lang];

  const opacity = spring({ frame, fps, config: { damping: 20 } });
  const translateY = spring({
    frame,
    fps,
    config: { damping: 20, stiffness: 80 },
    from: 30,
    to: 0,
  });

  return (
    <AbsoluteFill
      style={{
        background: "linear-gradient(135deg, #1e3a5f 0%, #2d5f8f 100%)",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        gap: 24,
      }}
    >
      <div
        style={{
          opacity,
          transform: `translateY(${String(translateY)}px)`,
          color: "white",
          fontSize: 72,
          fontWeight: 700,
          fontFamily,
          textAlign: "center",
          padding: "0 120px",
          lineHeight: 1.2,
        }}
      >
        {title}
      </div>
      {subtitle && (
        <div
          style={{
            opacity,
            transform: `translateY(${String(translateY)}px)`,
            color: "rgba(255,255,255,0.80)",
            fontSize: 36,
            fontFamily,
            textAlign: "center",
            padding: "0 160px",
          }}
        >
          {subtitle}
        </div>
      )}
    </AbsoluteFill>
  );
};
