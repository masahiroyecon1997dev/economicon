/**
 * C-13 仮説検定 — Remotion コンポジション
 *
 * 素材: captured/c13/frames/0001.jpg … NNNN.jpg + meta.json
 *
 * フレーム構成:
 *   TitleCard  : 90 frames (3s)
 *   Recording  : meta.json の durationMs から自動計算
 *   Ending     : 120 frames (4s)
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
import { FrameSequence, FrameSequenceMeta } from "../scenes/FrameSequence";
import { Subtitle } from "../scenes/Subtitle";
import { TitleCard } from "../scenes/TitleCard";

loadJP();
loadEN();

// ---------------------------------------------------------------------------
// 型・定数
// ---------------------------------------------------------------------------

export interface C13Props {
  lang?: "ja" | "en";
  _meta?: FrameSequenceMeta;
  [key: string]: unknown;
}

const FPS = 30;
const TITLE_FRAMES = 90;
const ENDING_FRAMES = 120;
const FALLBACK_RECORDING_FRAMES = FPS * 45;

const I18N = { ja, en } as const;

// ---------------------------------------------------------------------------
// calculateMetadata
// ---------------------------------------------------------------------------

export const calculateC13Metadata: CalculateMetadataFunction<
  C13Props
> = async ({ props }) => {
  try {
    const res = await fetch(staticFile("c13/meta.json"));
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const meta = (await res.json()) as FrameSequenceMeta;
    const recordingFrames = Math.ceil((meta.durationMs / 1000) * FPS);
    return {
      durationInFrames: TITLE_FRAMES + recordingFrames + ENDING_FRAMES,
      props: { ...props, _meta: meta },
    };
  } catch {
    return {
      durationInFrames:
        TITLE_FRAMES + FALLBACK_RECORDING_FRAMES + ENDING_FRAMES,
      props,
    };
  }
};

// ---------------------------------------------------------------------------
// コンポジション
// ---------------------------------------------------------------------------

export const C13HypothesisTest: React.FC<C13Props> = ({
  lang = "ja",
  _meta,
}) => {
  const t = I18N[lang].C13;

  if (!_meta) {
    return (
      <AbsoluteFill
        style={{
          background: "#0f0f0f",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <p
          style={{
            color: "#555",
            fontFamily: "sans-serif",
            fontSize: 24,
            textAlign: "center",
          }}
        >
          {"pnpm capture:c13 を実行してください"}
          <br />
          {"(cd video/playwright && pnpm capture:c13)"}
        </p>
      </AbsoluteFill>
    );
  }

  const recordingFrames = Math.ceil((_meta.durationMs / 1000) * FPS);

  let offset = 0;
  const titleFrom = offset;
  offset += TITLE_FRAMES;
  const recordingFrom = offset;
  offset += recordingFrames;
  const endingFrom = offset;

  return (
    <AbsoluteFill>
      <Sequence from={titleFrom} durationInFrames={TITLE_FRAMES}>
        <TitleCard title={t.title} subtitle={t.titleSubtitle} lang={lang} />
      </Sequence>

      <Sequence from={recordingFrom} durationInFrames={recordingFrames}>
        <FrameSequence sceneId="c13" meta={_meta} />
      </Sequence>

      {_meta.cues.map((cue, i) => {
        const fromFrame = recordingFrom + Math.round((cue.timeMs / 1000) * FPS);
        const nextCue = _meta.cues[i + 1];
        const untilFrame = nextCue
          ? recordingFrom + Math.round((nextCue.timeMs / 1000) * FPS)
          : recordingFrom + recordingFrames;
        const duration = Math.max(1, untilFrame - fromFrame);
        const text = lang === "ja" ? cue.textJa : cue.textEn;
        return (
          <Sequence key={i} from={fromFrame} durationInFrames={duration}>
            <Subtitle text={text} lang={lang} />
          </Sequence>
        );
      })}

      <Sequence from={endingFrom} durationInFrames={ENDING_FRAMES}>
        <Ending lang={lang} note={t.ending} />
      </Sequence>
    </AbsoluteFill>
  );
};
