import {
  AbsoluteFill,
  Img,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

interface ScreenshotSlideProps {
  /**
   * captured/{sceneId}/step-{n:02d}.png 形式の相対パス。
   * Remotion の public ディレクトリ（src/public/ or captured/）からの相対パスを指定する。
   * 例: "c09/step-01.png"
   */
  src: string;
  /** フェードインアニメーションを有効にするか（デフォルト: true） */
  fadeIn?: boolean;
}

/**
 * Playwright で撮影したスクリーンショットを全画面表示するコンポーネント。
 * Subtitle コンポーネントと組み合わせて使用する。
 *
 * 使用例:
 * ```tsx
 * <Sequence from={0} durationInFrames={90}>
 *   <ScreenshotSlide src="c09/step-01.png" />
 *   <Subtitle text="「基本分析」メニューをクリックします" lang="ja" />
 * </Sequence>
 * ```
 */
export const ScreenshotSlide: React.FC<ScreenshotSlideProps> = ({
  src,
  fadeIn = true,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const opacity = fadeIn
    ? spring({ frame, fps, config: { damping: 20, stiffness: 80 } })
    : 1;

  return (
    <AbsoluteFill style={{ background: "#0f0f0f" }}>
      <Img
        src={staticFile(src)}
        style={{
          width: "100%",
          height: "100%",
          objectFit: "contain",
          opacity,
        }}
      />
    </AbsoluteFill>
  );
};
