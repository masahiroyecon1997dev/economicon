import {
  AbsoluteFill,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

interface SubtitleProps {
  text: string;
  lang: "ja" | "en";
  /** 表示位置（デフォルト: bottom） */
  position?: "bottom" | "top";
}

const FONTS: Record<"ja" | "en", string> = {
  ja: '"Noto Sans JP", sans-serif',
  en: '"Noto Sans", sans-serif',
};

/** 動画クリップ下部に半透明背景でテキストをオーバーレイする字幕コンポーネント */
export const Subtitle: React.FC<SubtitleProps> = ({
  text,
  lang,
  position = "bottom",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const fontFamily = FONTS[lang];

  const opacity = spring({ frame, fps, config: { damping: 20 } });

  return (
    <AbsoluteFill
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: position === "bottom" ? "flex-end" : "flex-start",
        padding: position === "bottom" ? "0 0 60px 0" : "60px 0 0 0",
      }}
    >
      <div
        style={{
          opacity,
          background: "rgba(0, 0, 0, 0.65)",
          color: "white",
          padding: "12px 32px",
          borderRadius: 6,
          fontSize: lang === "ja" ? 30 : 28,
          fontFamily,
          maxWidth: "75%",
          textAlign: "center",
          lineHeight: 1.5,
        }}
      >
        {text}
      </div>
    </AbsoluteFill>
  );
};
