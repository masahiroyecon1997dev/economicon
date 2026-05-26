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

import { Composition } from "remotion";
import {
  C09DescriptiveStatistics,
  C09_TOTAL_FRAMES,
} from "./compositions/C09DescriptiveStatistics";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      {/* C-09 基本統計量 */}
      <Composition
        id="C09DescriptiveStatistics"
        component={C09DescriptiveStatistics}
        durationInFrames={C09_TOTAL_FRAMES}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{ lang: "ja" }}
      />
    </>
  );
};
