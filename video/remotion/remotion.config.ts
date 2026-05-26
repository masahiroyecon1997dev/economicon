import { Config } from "@remotion/cli/config";

// スクリーンショット出力先
// staticFile("c09/step-01.png") → ../playwright/captured/c09/step-01.png
Config.setPublicDir("../playwright/captured");

// 出力設定
Config.setVideoImageFormat("jpeg");
Config.setOverwriteOutput(true);
Config.setConcurrency(2);
