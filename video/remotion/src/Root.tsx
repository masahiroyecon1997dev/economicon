/**
 * Remotion ルートコンポーネント
 *
 * 新しい動画を追加する手順:
 * 1. src/compositions/ にコンポジションファイルを作成
 * 2. このファイルで import して <Composition> を追加
 * 3. `pnpm studio` でプレビュー確認
 *
 * 命名規則:
 *   composition id : C09DescriptiveStatistics
 *   output file    : c09-descriptive-statistics-{lang}.mp4
 */

import { Composition, registerRoot } from "remotion";
import {
  A01Introduction,
  calculateA01Metadata,
} from "./compositions/A01Introduction";
import {
  C09DescriptiveStatistics,
  calculateC09Metadata,
} from "./compositions/C09DescriptiveStatistics";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      {/* A-01 紹介動画（全体ダイジェスト） */}
      <Composition
        id="A01Introduction"
        component={A01Introduction}
        calculateMetadata={calculateA01Metadata}
        durationInFrames={1890}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{ lang: "ja" }}
      />

      {/* C-09 基本統計量 */}
      <Composition
        id="C09DescriptiveStatistics"
        component={C09DescriptiveStatistics}
        calculateMetadata={calculateC09Metadata}
        durationInFrames={300}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{ lang: "ja" }}
      />
    </>
  );
};

registerRoot(RemotionRoot);
