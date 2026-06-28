/**
 * A-01 紹介動画 — Remotion コンポジション
 *
 * フレーム構成:
 *   TitleCard        : 120 frames (4s)
 *   ProblemStatement : 210 frames (7s)
 *   FrameSequence    : a01-import の durationMs から自動計算（フォールバック 20s）
 *   FrameSequence    : a01-ols の durationMs から自動計算（フォールバック 20s）
 *   FeatureHighlight : 210 frames (7s)
 *   Ending           : 150 frames (5s)
 *
 * 字幕: 各 meta.json の cues 配列（収録スクリプトの addCue() で記録）から自動生成
 *
 * 収録前に以下を実行:
 *   cd video/playwright && pnpm capture:a01
 */

import { loadFont as loadEN } from "@remotion/google-fonts/NotoSans";
import { loadFont as loadJP } from "@remotion/google-fonts/NotoSansJP";
import {
  AbsoluteFill,
  CalculateMetadataFunction,
  Sequence,
  staticFile,
} from "remotion";
import en from "../i18n/en.json";
import ja from "../i18n/ja.json";
import { Ending } from "../scenes/Ending";
import { FeatureHighlight } from "../scenes/FeatureHighlight";
import { FrameSequence, FrameSequenceMeta } from "../scenes/FrameSequence";
import { ProblemStatement } from "../scenes/ProblemStatement";
import { Subtitle } from "../scenes/Subtitle";
import { TitleCard } from "../scenes/TitleCard";

// フォントを登録（CSS font-family が有効になる）
loadJP();
loadEN();

// ---------------------------------------------------------------------------
// 型・定数
// ---------------------------------------------------------------------------

export interface A01Props {
  /** 表示言語。レンダリング時は --props='{"lang":"en"}' で指定する。 */
  lang?: "ja" | "en";
  /** calculateMetadata が a01-import/meta.json から読み込んで注入するデータ。手動設定不要。 */
  _metaImport?: FrameSequenceMeta;
  /** calculateMetadata が a01-ols/meta.json から読み込んで注入するデータ。手動設定不要。 */
  _metaOls?: FrameSequenceMeta;
  /** Remotion の CalculateMetadataFunction に必要なインデックスシグネチャ */
  [key: string]: unknown;
}

const FPS = 30;
const TITLE_FRAMES = 120; // 4s
const PROBLEM_FRAMES = 210; // 7s
const HIGHLIGHT_FRAMES = 210; // 7s
const ENDING_FRAMES = 150; // 5s
/** meta.json 未生成時の各クリップのフォールバック尺 (frames) */
const FALLBACK_CLIP_FRAMES = FPS * 20; // 20s

const I18N = { ja, en } as const;

// ---------------------------------------------------------------------------
// calculateMetadata — 2 つの meta.json から尺を動的に決定する
// ---------------------------------------------------------------------------

export const calculateA01Metadata: CalculateMetadataFunction<
  A01Props
> = async ({ props }) => {
  const fetchMeta = async (
    path: string,
  ): Promise<FrameSequenceMeta | undefined> => {
    try {
      const res = await fetch(staticFile(path));
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return (await res.json()) as FrameSequenceMeta;
    } catch {
      return undefined;
    }
  };

  const [_metaImport, _metaOls] = await Promise.all([
    fetchMeta("a01-import/meta.json"),
    fetchMeta("a01-ols/meta.json"),
  ]);

  const importFrames = _metaImport
    ? Math.ceil((_metaImport.durationMs / 1000) * FPS)
    : FALLBACK_CLIP_FRAMES;
  const olsFrames = _metaOls
    ? Math.ceil((_metaOls.durationMs / 1000) * FPS)
    : FALLBACK_CLIP_FRAMES;

  const durationInFrames =
    TITLE_FRAMES +
    PROBLEM_FRAMES +
    importFrames +
    olsFrames +
    HIGHLIGHT_FRAMES +
    ENDING_FRAMES;

  return {
    durationInFrames,
    props: { ...props, _metaImport, _metaOls },
  };
};

// ---------------------------------------------------------------------------
// プレースホルダー（meta.json 未生成時）
// ---------------------------------------------------------------------------

const ClipPlaceholder: React.FC<{ message: string }> = ({ message }) => (
  <AbsoluteFill
    style={{
      background: "#0a1a2e",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
    }}
  >
    <p
      style={{
        color: "#444",
        fontFamily: "sans-serif",
        fontSize: 22,
        textAlign: "center",
        lineHeight: 1.6,
      }}
    >
      {message}
      <br />
      {"(cd video/playwright && pnpm capture:a01)"}
    </p>
  </AbsoluteFill>
);

// ---------------------------------------------------------------------------
// コンポジション
// ---------------------------------------------------------------------------

export const A01Introduction: React.FC<A01Props> = ({
  lang = "ja",
  _metaImport,
  _metaOls,
}) => {
  const t = I18N[lang].A01;

  const importFrames = _metaImport
    ? Math.ceil((_metaImport.durationMs / 1000) * FPS)
    : FALLBACK_CLIP_FRAMES;
  const olsFrames = _metaOls
    ? Math.ceil((_metaOls.durationMs / 1000) * FPS)
    : FALLBACK_CLIP_FRAMES;

  // フレームオフセットを順番に積み上げる
  let offset = 0;
  const titleFrom = offset;
  offset += TITLE_FRAMES;

  const problemFrom = offset;
  offset += PROBLEM_FRAMES;

  const importFrom = offset;
  offset += importFrames;

  const olsFrom = offset;
  offset += olsFrames;

  const highlightFrom = offset;
  offset += HIGHLIGHT_FRAMES;

  const endingFrom = offset;

  return (
    <AbsoluteFill>
      {/* ── タイトルカード ── */}
      <Sequence from={titleFrom} durationInFrames={TITLE_FRAMES}>
        <TitleCard title={t.title} subtitle={t.titleSubtitle} lang={lang} />
      </Sequence>

      {/* ── 課題提示テキストアニメーション ── */}
      <Sequence from={problemFrom} durationInFrames={PROBLEM_FRAMES}>
        <ProblemStatement
          lines={[...t.problemLines]}
          solution={t.problemSolution}
          lang={lang}
          durationInFrames={PROBLEM_FRAMES}
        />
      </Sequence>

      {/* ── CSV インポートクリップ ── */}
      <Sequence from={importFrom} durationInFrames={importFrames}>
        {_metaImport ? (
          <FrameSequence sceneId="a01-import" meta={_metaImport} />
        ) : (
          <ClipPlaceholder message="a01-import クリップ未収録" />
        )}
      </Sequence>

      {/* CSV インポートクリップの字幕 */}
      {_metaImport?.cues.map((cue, i) => {
        const fromFrame = importFrom + Math.round((cue.timeMs / 1000) * FPS);
        const nextCue = _metaImport.cues[i + 1];
        const untilFrame = nextCue
          ? importFrom + Math.round((nextCue.timeMs / 1000) * FPS)
          : importFrom + importFrames;
        const duration = Math.max(1, untilFrame - fromFrame);
        const text = lang === "ja" ? cue.textJa : cue.textEn;
        return (
          <Sequence
            key={`import-cue-${i}`}
            from={fromFrame}
            durationInFrames={duration}
          >
            <Subtitle text={text} lang={lang} />
          </Sequence>
        );
      })}

      {/* ── OLS 回帰クリップ ── */}
      <Sequence from={olsFrom} durationInFrames={olsFrames}>
        {_metaOls ? (
          <FrameSequence sceneId="a01-ols" meta={_metaOls} />
        ) : (
          <ClipPlaceholder message="a01-ols クリップ未収録" />
        )}
      </Sequence>

      {/* OLS クリップの字幕 */}
      {_metaOls?.cues.map((cue, i) => {
        const fromFrame = olsFrom + Math.round((cue.timeMs / 1000) * FPS);
        const nextCue = _metaOls.cues[i + 1];
        const untilFrame = nextCue
          ? olsFrom + Math.round((nextCue.timeMs / 1000) * FPS)
          : olsFrom + olsFrames;
        const duration = Math.max(1, untilFrame - fromFrame);
        const text = lang === "ja" ? cue.textJa : cue.textEn;
        return (
          <Sequence
            key={`ols-cue-${i}`}
            from={fromFrame}
            durationInFrames={duration}
          >
            <Subtitle text={text} lang={lang} />
          </Sequence>
        );
      })}

      {/* ── 機能ハイライト ── */}
      <Sequence from={highlightFrom} durationInFrames={HIGHLIGHT_FRAMES}>
        <FeatureHighlight
          title={t.featureHighlightTitle}
          labels={[...t.featureLabels]}
          descs={[...t.featureDescs]}
          lang={lang}
          durationInFrames={HIGHLIGHT_FRAMES}
        />
      </Sequence>

      {/* ── エンディング ── */}
      <Sequence from={endingFrom} durationInFrames={ENDING_FRAMES}>
        <Ending lang={lang} note={t.ending} />
      </Sequence>
    </AbsoluteFill>
  );
};
