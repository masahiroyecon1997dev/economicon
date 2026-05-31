/**
 * C-09 基本統計量 — Remotion コンポジション
 *
 * 素材: captured/c09/frames/0001.jpg … NNNN.jpg + meta.json
 * (publicDir = ../playwright/captured に設定済み)
 *
 * フレーム構成:
 *   TitleCard  : 90 frames (3s)
 *   Recording  : meta.json の durationMs から自動計算
 *   Ending     : 120 frames (4s)
 *
 * 字幕: meta.json の cues 配列（収録スクリプトの addCue() で記録）から自動生成
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

// フォントを登録（CSS font-family が有効になる）
loadJP();
loadEN();

// ---------------------------------------------------------------------------
// 型・定数
// ---------------------------------------------------------------------------

export interface C09Props {
  /** 表示言語。レンダリング時は --props='{"lang":"en"}' で指定する。 */
  lang?: "ja" | "en";
  /** calculateMetadata が meta.json から読み込んで注入するデータ。手動設定不要。 */
  _meta?: FrameSequenceMeta;
  /** Remotion の CalculateMetadataFunction に必要なインデックスシグネチャ */
  [key: string]: unknown;
}

const FPS = 30;
const TITLE_FRAMES = 90; // 3s
const ENDING_FRAMES = 120; // 4s
/** meta.json 未生成時のフォールバック収録尺 (frames) */
const FALLBACK_RECORDING_FRAMES = FPS * 15; // 15s

const I18N = { ja, en } as const;

// ---------------------------------------------------------------------------
// calculateMetadata — meta.json から尺を動的に決定する
// ---------------------------------------------------------------------------

export const calculateC09Metadata: CalculateMetadataFunction<
  C09Props
> = async ({ props }) => {
  try {
    const res = await fetch(staticFile("c09/meta.json"));
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const meta = (await res.json()) as FrameSequenceMeta;
    const recordingFrames = Math.ceil((meta.durationMs / 1000) * FPS);
    return {
      durationInFrames: TITLE_FRAMES + recordingFrames + ENDING_FRAMES,
      props: { ...props, _meta: meta },
    };
  } catch {
    // meta.json 未生成時はフォールバック尺を使用
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

export const C09DescriptiveStatistics: React.FC<C09Props> = ({
  lang = "ja",
  _meta,
}) => {
  const t = I18N[lang].C09;

  // meta.json 未生成時はプレースホルダーを表示
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
          {"pnpm capture:c09 を実行してください"}
          <br />
          {"(cd video/playwright && pnpm capture:c09)"}
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
      {/* タイトルカード */}
      <Sequence from={titleFrom} durationInFrames={TITLE_FRAMES}>
        <TitleCard title={t.title} subtitle={t.titleSubtitle} lang={lang} />
      </Sequence>

      {/* フレームシーケンス（実収録映像） */}
      <Sequence from={recordingFrom} durationInFrames={recordingFrames}>
        <FrameSequence sceneId="c09" meta={_meta} />
      </Sequence>

      {/* 字幕（cues ベース・収録スクリプトの addCue() に対応） */}
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

      {/* エンディング */}
      <Sequence from={endingFrom} durationInFrames={ENDING_FRAMES}>
        <Ending lang={lang} note={t.ending} />
      </Sequence>
    </AbsoluteFill>
  );
};
