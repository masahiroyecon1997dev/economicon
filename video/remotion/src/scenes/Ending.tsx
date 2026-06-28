import {
  AbsoluteFill,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

interface EndingProps {
  lang: "ja" | "en";
  /** 表示するリンクや追加テキスト（省略可） */
  note?: string;
}

const COPY: Record<"ja" | "en", { thanks: string; channel: string }> = {
  ja: {
    thanks: "ご視聴ありがとうございました",
    channel: "他の機能の解説動画もご覧ください",
  },
  en: {
    thanks: "Thank you for watching!",
    channel: "Check out our other tutorial videos",
  },
};

const FONTS: Record<"ja" | "en", string> = {
  ja: '"Noto Sans JP", sans-serif',
  en: '"Noto Sans", sans-serif',
};

/** 動画末尾のエンディングカード */
export const Ending: React.FC<EndingProps> = ({ lang, note }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const copy = COPY[lang];
  const fontFamily = FONTS[lang];

  const opacity = spring({ frame, fps, config: { damping: 20 } });

  return (
    <AbsoluteFill
      style={{
        background: "linear-gradient(135deg, #1e3a5f 0%, #0d1f35 100%)",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        gap: 32,
      }}
    >
      {/* ロゴ or アプリ名 */}
      <div
        style={{
          opacity,
          color: "white",
          fontSize: 56,
          fontWeight: 700,
          fontFamily,
          letterSpacing: "0.05em",
        }}
      >
        Economicon
      </div>

      {/* 感謝メッセージ */}
      <div
        style={{
          opacity,
          color: "rgba(255,255,255,0.85)",
          fontSize: 32,
          fontFamily,
          textAlign: "center",
        }}
      >
        {copy.thanks}
      </div>

      {/* サブテキスト */}
      <div
        style={{
          opacity,
          color: "rgba(255,255,255,0.55)",
          fontSize: 22,
          fontFamily,
          textAlign: "center",
        }}
      >
        {note ?? copy.channel}
      </div>
    </AbsoluteFill>
  );
};
