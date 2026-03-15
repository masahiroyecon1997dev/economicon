import { render } from "@testing-library/react";
import type { ReactElement } from "react";

/**
 * テスト用シンプルレンダラー。
 * Tauri/Zustandはモジュールモックで対応するため
 * Providerラッパーは最小限にとどめている。
 */
export const renderComponent = (ui: ReactElement) => render(ui);

/**
 * i18n の t() 関数簡易実装。
 * react-i18next を vi.mock する際の実装として使う。
 */
export const tMock = (key: string, opts?: Record<string, string>): string => {
  if (!opts) return key;
  return Object.entries(opts).reduce(
    (s, [k, v]) => s.replace(`{{${k}}}`, v),
    key,
  );
};
