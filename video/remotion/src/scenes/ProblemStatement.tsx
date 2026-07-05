import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

interface ProblemStatementProps {
  /** 課題を説明する文章（順番に表示される） */
  lines: readonly string[];
  /** 解決策テキスト（最後に強調表示） */
  solution: string;
  /** "ja" | "en" — フォントファミリー切り替えに使用 */
  lang: "ja" | "en";
  /**
   * このコンポーネントが <Sequence> 内でレンダリングされる場合、
   * Sequence の durationInFrames をここに渡すこと。
   * (useVideoConfig().durationInFrames は Composition の総フレーム数を返すため)
   */
  durationInFrames: number;
}

const FONTS: Record<"ja" | "en", string> = {
  ja: '"Noto Sans JP", sans-serif',
  en: '"Noto Sans", sans-serif',
};

/**
 * 課題提示 → 解決策アニメーションコンポーネント（A-01 シーン 2 用）
 *
 * - 各 line が順番に spring fade-in
 * - 直前の line はフェードダウンして強調を絞る
 * - 最後の ~30% で solution テキストが登場
 */
export const ProblemStatement: React.FC<ProblemStatementProps> = ({
  lines,
  solution,
  lang,
  durationInFrames,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const fontFamily = FONTS[lang];

  // 各 line に割り当てるフレーム数（全体の 68%）
  const lineRegion = Math.floor(durationInFrames * 0.68);
  const lineInterval =
    lines.length > 0 ? Math.floor(lineRegion / lines.length) : lineRegion;
  // solution が登場するフレーム
  const solutionStart = Math.floor(durationInFrames * 0.68);

  return (
    <AbsoluteFill
      style={{
        background: "linear-gradient(160deg, #0d1f35 0%, #0a1628 100%)",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        gap: 40,
        padding: "80px 200px",
      }}
    >
      {/* 課題テキスト一覧 */}
      {lines.map((line, i) => {
        const lineStart = i * lineInterval;
        const fadeIn = spring({
          frame: frame - lineStart,
          fps,
          config: { damping: 22, stiffness: 100 },
        });
        const translateY = spring({
          frame: frame - lineStart,
          fps,
          config: { damping: 18, stiffness: 80 },
          from: 24,
          to: 0,
        });

        // 次の line が出たら薄くする
        const dimStart = (i + 1) * lineInterval;
        const dimOpacity =
          frame >= dimStart
            ? interpolate(frame, [dimStart, dimStart + 25], [1, 0.28], {
                extrapolateRight: "clamp",
              })
            : 1;

        const opacity = frame < lineStart ? 0 : fadeIn * dimOpacity;

        return (
          <div
            key={i}
            style={{
              opacity,
              color: "rgba(255,255,255,0.88)",
              fontSize: lang === "ja" ? 44 : 40,
              fontFamily,
              fontWeight: 500,
              textAlign: "center",
              lineHeight: 1.45,
              transform: `translateY(${String(translateY)}px)`,
            }}
          >
            {line}
          </div>
        );
      })}

      {/* 解決策テキスト（divider + 強調色） */}
      {frame >= solutionStart && (
        <div
          style={{
            opacity: spring({
              frame: frame - solutionStart,
              fps,
              config: { damping: 20, stiffness: 90 },
            }),
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: 24,
            marginTop: 16,
          }}
        >
          {/* セパレーター */}
          <div
            style={{
              width: interpolate(
                frame,
                [solutionStart, solutionStart + 40],
                [0, 320],
                { extrapolateRight: "clamp" },
              ),
              height: 2,
              background:
                "linear-gradient(90deg, transparent, #4d9fe8, transparent)",
            }}
          />
          {/* ソリューションテキスト */}
          <div
            style={{
              color: "#4d9fe8",
              fontSize: lang === "ja" ? 56 : 50,
              fontFamily,
              fontWeight: 700,
              textAlign: "center",
              lineHeight: 1.35,
              transform: `translateY(${String(
                spring({
                  frame: frame - solutionStart,
                  fps,
                  config: { damping: 18, stiffness: 80 },
                  from: 20,
                  to: 0,
                }),
              )}px)`,
            }}
          >
            {solution}
          </div>
        </div>
      )}
    </AbsoluteFill>
  );
};
