/**
 * C-09 基本統計量 — Remotion コンポジション
 *
 * 使用スクリーンショット: captured/c09/step-01.png … step-06.png
 * (publicDir = ../playwright/captured に設定済み)
 *
 * フレーム構成:
 *   TitleCard  : 90 frames (3s)
 *   6 × Steps  : 120 frames each (4s) = 720 frames
 *   Ending     : 120 frames (4s)
 *   合計        : 930 frames ≈ 31s
 */

import { loadFont as loadEN } from "@remotion/google-fonts/NotoSans";
import { loadFont as loadJP } from "@remotion/google-fonts/NotoSansJP";
import { AbsoluteFill, Sequence } from "remotion";
import en from "../i18n/en.json";
import ja from "../i18n/ja.json";
import { Ending } from "../scenes/Ending";
import { ScreenshotSlide } from "../scenes/ScreenshotSlide";
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
}

const TITLE_FRAMES = 90; // 3s
const STEP_FRAMES = 120; // 4s
const ENDING_FRAMES = 120; // 4s

export const C09_TOTAL_FRAMES = TITLE_FRAMES + 6 * STEP_FRAMES + ENDING_FRAMES; // 930

const I18N = { ja, en } as const;

// ---------------------------------------------------------------------------
// コンポジション
// ---------------------------------------------------------------------------

export const C09DescriptiveStatistics: React.FC<C09Props> = ({
  lang = "ja",
}) => {
  const t = I18N[lang].C09;

  let offset = 0;

  const titleFrom = offset;
  offset += TITLE_FRAMES;

  const stepFroms = t.steps.map((_, i) => {
    const from = offset + i * STEP_FRAMES;
    return from;
  });
  offset += t.steps.length * STEP_FRAMES;

  const endingFrom = offset;

  return (
    <AbsoluteFill>
      {/* タイトルカード */}
      <Sequence from={titleFrom} durationInFrames={TITLE_FRAMES}>
        <TitleCard title={t.title} subtitle={t.titleSubtitle} lang={lang} />
      </Sequence>

      {/* ステップスライド（スクリーンショット + 字幕） */}
      {t.steps.map((stepText, i) => (
        <Sequence key={i} from={stepFroms[i]} durationInFrames={STEP_FRAMES}>
          <ScreenshotSlide
            src={`c09/step-${String(i + 1).padStart(2, "0")}.png`}
          />
          <Subtitle text={stepText} lang={lang} />
        </Sequence>
      ))}

      {/* エンディング */}
      <Sequence from={endingFrom} durationInFrames={ENDING_FRAMES}>
        <Ending lang={lang} note={t.ending} />
      </Sequence>
    </AbsoluteFill>
  );
};
