/**
 * C-09 蝓ｺ譛ｬ邨ｱ險磯㍼ 窶・Playwright 蜍慕判蜿朱鹸繧ｹ繧ｯ繝ｪ繝励ヨ
 *
 * 螳溯｡悟燕謠・
 *   - VS Code 繧ｿ繧ｹ繧ｯ縲窪conomicon: App (Debug Port)縲阪〒繧｢繝励Μ縺瑚ｵｷ蜍墓ｸ医∩縺ｧ縺ゅｋ縺薙→
 *   - 迺ｰ蠅・､画焚 ECONOMICON_TEST_SAMPLE_DIR 縺ｫ繧ｵ繝ｳ繝励Ν繝輔か繝ｫ繝繝代せ繧定ｨｭ螳夲ｼ育怐逡･譎ゅ・ ../../../sample・・ *
 * 螳溯｡梧婿豕・
 *   cd video/playwright
 *   pnpm capture:c09
 *
 * 蜃ｺ蜉・
 *   captured/c09/frames/0001.jpg 窶ｦ NNNN.jpg
 *   captured/c09/meta.json
 */

import path from "node:path";

import {
  connectToApp,
  humanCheck,
  humanClick,
  Recorder,
  SAMPLE_DIR,
} from "../helpers/connectToApp.js";

// ---------------------------------------------------------------------------
// 螳壽焚
// ---------------------------------------------------------------------------

const SCENE_ID = "c09";
const FILE_NAME = "grunfeld.parquet";
const TABLE_NAME = "grunfeld";
/** 繝√ぉ繝・け縺吶ｋ蛻暦ｼ・runfeld.parquet 縺ｮ謨ｰ蛟､蛻暦ｼ・*/
const COLUMNS = ["invest", "value", "capital"];
/** 邨ｱ險磯㍼繝√ぉ繝・け繝懊ャ繧ｯ繧ｹ蜷阪ヱ繧ｿ繝ｼ繝ｳ */
const STAT_PATTERNS: RegExp[] = [/^蟷ｳ蝮・|^Mean$/i, /^讓呎ｺ門￥蟾ｮ$|^Std Dev$/i];

// ---------------------------------------------------------------------------
// 繝倥Ν繝代・
// ---------------------------------------------------------------------------

/**
 * 繝輔ぃ繧､繝ｫ繝悶Λ繧ｦ繧ｶ縺ｧ SAMPLE_DIR 縺ｾ縺ｧ髯阪ｊ縺ｦ縺・￥縲・ * app/e2e/helpers/appHelpers.ts 縺ｮ navigateFileBrowserToDir 縺ｨ蜷後Ο繧ｸ繝・け縲・ */
async function navigateToSampleDir(
  page: Awaited<ReturnType<typeof connectToApp>>["page"],
): Promise<void> {
  const fileSelectTab = page.getByRole("tab", {
    name: /繝輔ぃ繧､繝ｫ驕ｸ謚桍Select File/i,
  });
  if (await fileSelectTab.isVisible()) {
    await fileSelectTab.click();
  }

  const sep = path.sep;
  const segments = SAMPLE_DIR.split(sep).filter((s) => s.length > 0);

  for (const segment of segments) {
    const folderRow = page
      .getByRole("row", { name: segment })
      .filter({ hasNot: page.locator('[data-file="true"]') });

    if (await folderRow.isVisible()) {
      await folderRow.click();
      await page.waitForTimeout(300);
    }
  }
}

// ---------------------------------------------------------------------------
// 繝｡繧､繝ｳ
// ---------------------------------------------------------------------------

async function main(): Promise<void> {
  const { browser, context, page } = await connectToApp();

  try {
    // 笏笏 竭 繝ｯ繝ｼ繧ｯ繧ｹ繝壹・繧ｹ繧偵Μ繧ｻ繝・ヨ 笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏
    const resetButton = page.getByTestId("left-menu-reset-workspace");
    await resetButton.waitFor({ state: "visible", timeout: 90_000 });

    if (await resetButton.isEnabled()) {
      await resetButton.click();
      const confirmDialog = page
        .getByRole("dialog")
        .or(page.getByRole("alertdialog"));
      await confirmDialog.waitFor({ state: "visible", timeout: 10_000 });
      await confirmDialog.getByRole("button", { name: /^OK$/i }).click();
      await confirmDialog.waitFor({ state: "hidden", timeout: 10_000 });
    }

    await page
      .getByRole("heading", { name: /繝輔ぃ繧､繝ｫ繧偵う繝ｳ繝昴・繝・Select File/i })
      .waitFor({ state: "visible", timeout: 30_000 });

    // 笏笏 竭｡ SAMPLE_DIR 縺ｸ遘ｻ蜍輔＠縺ｦ grunfeld.parquet 繧偵う繝ｳ繝昴・繝・笏笏笏笏笏笏笏笏笏笏笏笏
    await navigateToSampleDir(page);

    const fileRow = page.getByRole("row", { name: FILE_NAME });
    await fileRow.waitFor({ state: "visible", timeout: 15_000 });
    await humanClick(page, fileRow);

    const importDialog = page.getByRole("dialog");
    await importDialog.waitFor({ state: "visible", timeout: 10_000 });

    const importBtn = importDialog.getByRole("button", {
      name: /^繧､繝ｳ繝昴・繝・|^Import$/,
    });
    await humanClick(page, importBtn, 2000);
    await importDialog.waitFor({ state: "hidden", timeout: 30_000 });

    // DataPreview 縺ｫ驕ｷ遘ｻ縺励※繝・・繝悶Ν繧ｿ繝悶′陦ｨ遉ｺ縺輔ｌ繧九∪縺ｧ蠕・ｩ・    await page
      .getByRole("button", { name: TABLE_NAME })
      .waitFor({ state: "visible", timeout: 15_000 });
    await page.waitForTimeout(500);

    // 笏笏 竭｢ 骭ｲ逕ｻ髢句ｧ・笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏
    const rec = await Recorder.create(context, page, SCENE_ID);
    await rec.start();
    console.log("  笆ｶ 骭ｲ逕ｻ髢句ｧ・);

    // 笏笏 step-A: 繝・・繧ｿ繝励Ξ繝薙Η繝ｼ 笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏
    rec.addCue(
      "Grunfeld 繝・・繧ｿ縺悟叙繧願ｾｼ縺ｾ繧後∪縺励◆",
      "Grunfeld data has been imported",
    );
    await page.waitForTimeout(1500);

    // 笏笏 竭｣ 縲悟渕譛ｬ蛻・梵縲阪Γ繝九Η繝ｼ繧帝幕縺・笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏
    rec.addCue(
      "縲悟渕譛ｬ蛻・梵縲坂・縲悟渕譛ｬ邨ｱ險磯㍼縲阪ｒ驕ｸ謚槭＠縺ｾ縺・,
      "Select 'Basic Analysis' 竊・'Descriptive Statistics'",
    );

    const menuBtn = page.getByRole("banner").getByRole("button", {
      name: /蝓ｺ譛ｬ蛻・梵|Basic Analysis/i,
    });
    await humanClick(page, menuBtn, 500);

    const basicStatsItem = page.getByRole("menuitem", {
      name: /蝓ｺ譛ｬ邨ｱ險磯㍼|Descriptive Statistics/i,
    });
    await basicStatsItem.waitFor({ state: "visible", timeout: 5_000 });
    await page.waitForTimeout(400);

    // 笏笏 竭､ 縲悟渕譛ｬ邨ｱ險磯㍼縲阪ｒ繧ｯ繝ｪ繝・け 笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏
    await humanClick(page, basicStatsItem, 1000);

    await page
      .getByRole("heading", { name: /蝓ｺ譛ｬ邨ｱ險磯㍼|Descriptive Statistics/i })
      .waitFor({ state: "visible", timeout: 10_000 });

    // 笏笏 step-B: 繝・・繝悶Ν繧帝∈謚・笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏
    rec.addCue("髮・ｨ医☆繧九ユ繝ｼ繝悶Ν繧帝∈謚槭＠縺ｾ縺・, "Select the table to analyze");

    const dataSelect = page
      .getByLabel(/蟇ｾ雎｡繝・・繧ｿ|Target Data/i)
      .first()
      .or(page.getByRole("combobox").first());
    await humanClick(page, dataSelect, 400);

    const tableOption = page.getByRole("option", {
      name: TABLE_NAME,
      exact: true,
    });
    await tableOption.waitFor({ state: "visible", timeout: 10_000 });
    await humanClick(page, tableOption, 800);

    // 蛻励Μ繧ｹ繝医・繝ｭ繝ｼ繝牙ｮ御ｺ・ｒ蠕・ｩ・    await page
      .getByText(/蛻玲ュ蝣ｱ繧定ｪｭ縺ｿ霎ｼ繧薙〒縺・∪縺處Loading column info/i)
      .waitFor({ state: "hidden", timeout: 15_000 })
      .catch(() => {});

    // 笏笏 step-C: 蛻励ｒ驕ｸ謚・笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏
    rec.addCue(
      "蛻・梵縺吶ｋ蛻励↓繝√ぉ繝・け繧貞・繧後∪縺・,
      "Check the columns to analyze",
    );

    for (const col of COLUMNS) {
      const checkbox = page.getByRole("checkbox", { name: col });
      if (await checkbox.isVisible()) {
        await humanCheck(page, checkbox, true, 350);
      }
    }
    await page.waitForTimeout(500);

    // 笏笏 step-D: 邨ｱ險磯㍼繧帝∈謚・笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏
    rec.addCue(
      "險育ｮ励☆繧狗ｵｱ險磯㍼繧帝∈謚槭＠縺ｾ縺・,
      "Select the statistics to compute",
    );

    for (const pattern of STAT_PATTERNS) {
      const checkbox = page.getByRole("checkbox", { name: pattern });
      if (await checkbox.isVisible()) {
        await humanCheck(page, checkbox, true, 350);
      }
    }
    await page.waitForTimeout(500);

    // 笏笏 竭･ 縲瑚ｨ育ｮ励☆繧九阪ｒ繧ｯ繝ｪ繝・け 笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏
    rec.addCue(
      "縲瑚ｨ育ｮ励☆繧九阪ｒ繧ｯ繝ｪ繝・け縺励※螳溯｡後＠縺ｾ縺・,
      "Click 'Calculate' to run",
    );

    const calcBtn = page.getByRole("button", {
      name: /^(險育ｮ励☆繧弓Calculate)$/i,
    });
    await humanClick(page, calcBtn, 500);

    // 邨先棡繝・・繝悶Ν縺瑚｡ｨ遉ｺ縺輔ｌ繧九∪縺ｧ蠕・ｩ・    await page
      .getByRole("table")
      .waitFor({ state: "visible", timeout: 30_000 });

    // 笏笏 step-E: 邨先棡繧堤｢ｺ隱・笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏
    rec.addCue(
      "蝓ｺ譛ｬ邨ｱ險磯㍼縺ｮ險育ｮ礼ｵ先棡縺瑚｡ｨ遉ｺ縺輔ｌ縺ｾ縺励◆",
      "Descriptive statistics results are displayed",
    );
    await page.waitForTimeout(2500);

    // 笏笏 骭ｲ逕ｻ蛛懈ｭ｢ 笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏
    const info = await rec.stop();
    console.log("");
    console.log("笨・C-09 蜿朱鹸螳御ｺ・);
    console.log(`   繝輔Ξ繝ｼ繝謨ｰ: ${info.totalFrames}`);
    console.log(`   髟ｷ縺・ ${(info.durationMs / 1000).toFixed(1)}s`);
    console.log(`   蜃ｺ蜉帛・: video/playwright/captured/${SCENE_ID}/`);
  } finally {
    await browser.close();
  }
}

main().catch((err: unknown) => {
  console.error("笶・蜿朱鹸螟ｱ謨・", err);
  process.exit(1);
});

const SCENE_ID = "c09";
const FILE_NAME = "grunfeld.parquet";
const TABLE_NAME = "grunfeld";
/** 繝√ぉ繝・け縺吶ｋ蛻暦ｼ・runfeld.parquet 縺ｮ謨ｰ蛟､蛻暦ｼ・*/
const COLUMNS = ["invest", "value", "capital"];
