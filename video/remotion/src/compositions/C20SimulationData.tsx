/**
 * C-20 シミュレーションデータ生成 — Remotion コンポジション
 *
 * 素材: captured/c20/frames/0001.jpg … NNNN.jpg + meta.json
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

export interface C20Props {
  lang?: "ja" | "en";
  _meta?: FrameSequenceMeta;
  [key: string]: unknown;
}

const FPS = 30;
const TITLE_FRAMES = 90;
const ENDING_FRAMES = 120;
const FALLBACK_RECORDING_FRAMES = FPS * 60;

const I18N = { ja, en } as const;

// ---------------------------------------------------------------------------
// calculateMetadata
// ---------------------------------------------------------------------------

export const calculateC20Metadata: CalculateMetadataFunction<
  C20Props
> = async ({ props }) => {
  try {
    const res = await fetch(staticFile("c20/meta.json"));
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

export const C20SimulationData: React.FC<C20Props> = ({
  lang = "ja",
  _meta,
}) => {
  const t = I18N[lang].C20;
  const recordingFrames = _meta
    ? Math.ceil((_meta.durationMs / 1000) * FPS)
    : FALLBACK_RECORDING_FRAMES;

  return (
    <AbsoluteFill>
      {/* TitleCard */}
      <Sequence durationInFrames={TITLE_FRAMES}>
        <TitleCard title={t.title} subtitle={t.titleSubtitle} lang={lang} />
      </Sequence>

      {/* 収録映像 */}
      <Sequence from={TITLE_FRAMES} durationInFrames={recordingFrames}>
        {_meta ? (
          <FrameSequence sceneId="c20" meta={_meta} />
        ) : (
          <AbsoluteFill
            style={{
              background: "#000",
              color: "#fff",
              justifyContent: "center",
              alignItems: "center",
            }}
          >
            <span>収録映像なし（収録後に再レンダリングしてください）</span>
          </AbsoluteFill>
        )}
        {_meta?.cues?.map((cue, i) => {
          const startF = Math.round((cue.timeMs / 1000) * FPS);
          const nextMs = _meta.cues[i + 1]?.timeMs ?? _meta.durationMs;
          const dur = Math.max(
            30,
            Math.round(((nextMs - cue.timeMs) / 1000) * FPS) - 10,
          );
          return (
            <Sequence key={i} from={startF} durationInFrames={dur}>
              <Subtitle
                text={lang === "ja" ? cue.textJa : cue.textEn}
                lang={lang}
              />
            </Sequence>
          );
        })}
      </Sequence>

      {/* Ending */}
      <Sequence
        from={TITLE_FRAMES + recordingFrames}
        durationInFrames={ENDING_FRAMES}
      >
        <Ending lang={lang} note={t.ending} />
      </Sequence>
    </AbsoluteFill>
  );
};
