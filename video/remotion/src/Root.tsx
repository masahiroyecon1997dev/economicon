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
import {
  C10GroupStatistics,
  calculateC10Metadata,
} from "./compositions/C10GroupStatistics";
import {
  C11CorrelationMatrix,
  calculateC11Metadata,
} from "./compositions/C11CorrelationMatrix";
import {
  C12ConfidenceInterval,
  calculateC12Metadata,
} from "./compositions/C12ConfidenceInterval";
import {
  C13HypothesisTest,
  calculateC13Metadata,
} from "./compositions/C13HypothesisTest";
import {
  C18PlotView,
  calculateC18Metadata,
} from "./compositions/C18PlotView";
import {
  C19DistributionPreview,
  calculateC19Metadata,
} from "./compositions/C19DistributionPreview";
import {
  C20SimulationData,
  calculateC20Metadata,
} from "./compositions/C20SimulationData";
import {
  C21OutputResult,
  calculateC21Metadata,
} from "./compositions/C21OutputResult";
import {
  C22CiSimulation,
  calculateC22Metadata,
} from "./compositions/C22CiSimulation";
import {
  C23OlsSimulation,
  calculateC23Metadata,
} from "./compositions/C23OlsSimulation";

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

      {/* C-10 グループ別統計量 */}
      <Composition
        id="C10GroupStatistics"
        component={C10GroupStatistics}
        calculateMetadata={calculateC10Metadata}
        durationInFrames={1530}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{ lang: "ja" }}
      />

      {/* C-11 相関行列 */}
      <Composition
        id="C11CorrelationMatrix"
        component={C11CorrelationMatrix}
        calculateMetadata={calculateC11Metadata}
        durationInFrames={1530}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{ lang: "ja" }}
      />

      {/* C-12 信頼区間の計算 */}
      <Composition
        id="C12ConfidenceInterval"
        component={C12ConfidenceInterval}
        calculateMetadata={calculateC12Metadata}
        durationInFrames={1530}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{ lang: "ja" }}
      />

      {/* C-13 仮説検定 */}
      <Composition
        id="C13HypothesisTest"
        component={C13HypothesisTest}
        calculateMetadata={calculateC13Metadata}
        durationInFrames={1530}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{ lang: "ja" }}
      />

      {/* C-18 散布図・ヒストグラムの作成 */}
      <Composition
        id="C18PlotView"
        component={C18PlotView}
        calculateMetadata={calculateC18Metadata}
        durationInFrames={1530}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{ lang: "ja" }}
      />

      {/* C-19 確率分布プレビュー */}
      <Composition
        id="C19DistributionPreview"
        component={C19DistributionPreview}
        calculateMetadata={calculateC19Metadata}
        durationInFrames={1530}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{ lang: "ja" }}
      />

      {/* C-20 シミュレーションデータ生成 */}
      <Composition
        id="C20SimulationData"
        component={C20SimulationData}
        calculateMetadata={calculateC20Metadata}
        durationInFrames={1920}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{ lang: "ja" }}
      />

      {/* C-21 分析結果の出力（LaTeX/Markdown） */}
      <Composition
        id="C21OutputResult"
        component={C21OutputResult}
        calculateMetadata={calculateC21Metadata}
        durationInFrames={1920}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{ lang: "ja" }}
      />

      {/* C-22 信頼区間シミュレーション */}
      <Composition
        id="C22CiSimulation"
        component={C22CiSimulation}
        calculateMetadata={calculateC22Metadata}
        durationInFrames={1530}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{ lang: "ja" }}
      />

      {/* C-23 OLS 推定量シミュレーション */}
      <Composition
        id="C23OlsSimulation"
        component={C23OlsSimulation}
        calculateMetadata={calculateC23Metadata}
        durationInFrames={1920}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{ lang: "ja" }}
      />
    </>
  );
};

registerRoot(RemotionRoot);
