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
  C01CsvImport,
  calculateC01Metadata,
} from "./compositions/C01CsvImport";
import {
  C02ExcelParquetImport,
  calculateC02Metadata,
} from "./compositions/C02ExcelParquetImport";
import { C03Join, calculateC03Metadata } from "./compositions/C03Join";
import { C04Union, calculateC04Metadata } from "./compositions/C04Union";
import {
  C05ColumnFilterCast,
  calculateC05Metadata,
} from "./compositions/C05ColumnFilterCast";
import {
  C06TransformDummy,
  calculateC06Metadata,
} from "./compositions/C06TransformDummy";
import {
  C07Calculation,
  calculateC07Metadata,
} from "./compositions/C07Calculation";
import { C08SaveData, calculateC08Metadata } from "./compositions/C08SaveData";
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

      {/* C-01 CSV ファイルのインポート */}
      <Composition
        id="C01CsvImport"
        component={C01CsvImport}
        calculateMetadata={calculateC01Metadata}
        durationInFrames={1530}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{ lang: "ja" }}
      />

      {/* C-02 Excel / Parquet のインポート */}
      <Composition
        id="C02ExcelParquetImport"
        component={C02ExcelParquetImport}
        calculateMetadata={calculateC02Metadata}
        durationInFrames={1980}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{ lang: "ja" }}
      />

      {/* C-03 テーブルの Join */}
      <Composition
        id="C03Join"
        component={C03Join}
        calculateMetadata={calculateC03Metadata}
        durationInFrames={1530}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{ lang: "ja" }}
      />

      {/* C-04 テーブルの Union */}
      <Composition
        id="C04Union"
        component={C04Union}
        calculateMetadata={calculateC04Metadata}
        durationInFrames={1530}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{ lang: "ja" }}
      />

      {/* C-05 列フィルタ・型変換 */}
      <Composition
        id="C05ColumnFilterCast"
        component={C05ColumnFilterCast}
        calculateMetadata={calculateC05Metadata}
        durationInFrames={1530}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{ lang: "ja" }}
      />

      {/* C-06 変換列・ダミー変数の追加 */}
      <Composition
        id="C06TransformDummy"
        component={C06TransformDummy}
        calculateMetadata={calculateC06Metadata}
        durationInFrames={1530}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{ lang: "ja" }}
      />

      {/* C-07 計算列の追加 */}
      <Composition
        id="C07Calculation"
        component={C07Calculation}
        calculateMetadata={calculateC07Metadata}
        durationInFrames={1530}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{ lang: "ja" }}
      />

      {/* C-08 データの保存 */}
      <Composition
        id="C08SaveData"
        component={C08SaveData}
        calculateMetadata={calculateC08Metadata}
        durationInFrames={1980}
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
