import {
  AbsoluteFill,
  Img,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

// ---------------------------------------------------------------------------
// 型定義（Playwright 収録側の meta.json と共通スキーマ）
// ---------------------------------------------------------------------------

/** captured/{sceneId}/meta.json のスキーマ */
export interface FrameSequenceMeta {
  /** 保存済みフレーム数 */
  totalFrames: number;
  /** 録画全体の長さ (ms) */
  durationMs: number;
  /** 各フレームの録画開始からの経過時刻 (ms) */
  frameTimestamps: number[];
  /** 字幕キュー */
  cues: Array<{ timeMs: number; textJa: string; textEn: string }>;
}

// ---------------------------------------------------------------------------
// コンポーネント
// ---------------------------------------------------------------------------

interface FrameSequenceProps {
  /** captured/ 配下のサブディレクトリ名（例: "c09"） */
  sceneId: string;
  /** meta.json の内容（calculateMetadata で渡す） */
  meta: FrameSequenceMeta;
}

/**
 * Playwright Screencast で収録した連番 JPEG をタイムライン通りに再生するコンポーネント。
 *
 * - Remotion の現在フレームを経過時刻(ms)に変換し、`meta.frameTimestamps` を
 *   二分探索して最も近いキャプチャフレームを表示する
 * - 変化のない静止画面は少ないフレームしか記録されないが、
 *   Remotion が同じ JPEG を保持し続けるため自然な表示になる
 *
 * 使用例:
 * ```tsx
 * <Sequence from={recordingFrom} durationInFrames={recordingFrames}>
 *   <FrameSequence sceneId="c09" meta={meta} />
 * </Sequence>
 * ```
 */
export const FrameSequence: React.FC<FrameSequenceProps> = ({
  sceneId,
  meta,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const currentTimeMs = (frame / fps) * 1000;

  // 二分探索: currentTimeMs 以下で最大の frameTimestamps インデックスを求める
  let capturedIdx = 0;
  let lo = 0;
  let hi = meta.frameTimestamps.length - 1;
  while (lo <= hi) {
    const mid = (lo + hi) >> 1;
    if (meta.frameTimestamps[mid] <= currentTimeMs) {
      capturedIdx = mid;
      lo = mid + 1;
    } else {
      hi = mid - 1;
    }
  }
  // 範囲クランプ
  capturedIdx = Math.max(0, Math.min(capturedIdx, meta.totalFrames - 1));

  const filename = `${sceneId}/frames/${String(capturedIdx + 1).padStart(4, "0")}.jpg`;

  return (
    <AbsoluteFill style={{ background: "#0f0f0f" }}>
      <Img
        src={staticFile(filename)}
        style={{ width: "100%", height: "100%", objectFit: "contain" }}
      />
    </AbsoluteFill>
  );
};
