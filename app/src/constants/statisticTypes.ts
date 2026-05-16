import { DescriptiveStatisticType } from "@/api/model";

/**
 * 全統計量タイプのリスト（表示・送信順を固定）
 */
export const ALL_STAT_TYPES: DescriptiveStatisticType[] = [
  DescriptiveStatisticType.count,
  DescriptiveStatisticType.mean,
  DescriptiveStatisticType.median,
  DescriptiveStatisticType.mode,
  DescriptiveStatisticType.variance,
  DescriptiveStatisticType.std_dev,
  DescriptiveStatisticType.min,
  DescriptiveStatisticType.max,
  DescriptiveStatisticType.range,
  DescriptiveStatisticType.iqr,
  DescriptiveStatisticType.null_count,
  DescriptiveStatisticType.null_ratio,
  DescriptiveStatisticType.skewness,
  DescriptiveStatisticType.kurtosis,
  DescriptiveStatisticType.population_variance,
];
