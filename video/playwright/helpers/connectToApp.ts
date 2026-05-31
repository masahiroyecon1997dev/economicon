/**
 * Tauri アプリへの CDP 接続ヘルパー
 *
 * 接続方式は app/e2e/helpers/setupHelpers.ts と同じ CDP パターン。
 * アプリは VS Code タスク「Economicon: App (Debug Port)」で起動しておくこと。
 */
import path from "node:path";
import { fileURLToPath } from "node:url";

import type {
  Browser,
  BrowserContext,
  CDPSession,
  Locator,
  Page,
} from "@playwright/test";
import { chromium } from "@playwright/test";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// ---------------------------------------------------------------------------
// 定数
// ---------------------------------------------------------------------------

/**
 * サンプルデータフォルダのパス。
 * 環境変数 ECONOMICON_TEST_SAMPLE_DIR → リポジトリルートの sample/ の順でフォールバック。
 */
export const SAMPLE_DIR =
  process.env.ECONOMICON_TEST_SAMPLE_DIR ??
  path.resolve(__dirname, "../../../sample");

// ---------------------------------------------------------------------------
// 接続
// ---------------------------------------------------------------------------

export interface AppConnection {
  browser: Browser;
  context: BrowserContext;
  page: Page;
}

/**
 * Tauri アプリへ CDP 経由で接続し、操作可能な Page を返す。
 *
 * - 接続先: http://127.0.0.1:9222
 * - devtools:// ページを自動除外（setupHelpers.ts と同ロジック）
 * - viewport を 1920×1080 に固定
 *
 * @throws アプリが起動していない場合にエラーを投げる
 */
export async function connectToApp(): Promise<AppConnection> {
  let browser: Browser;
  try {
    browser = await chromium.connectOverCDP("http://127.0.0.1:9222");
  } catch (e) {
    throw new Error(
      "アプリ（ポート9222）が見つかりません。" +
        "VS Code タスク「Economicon: App (Debug Port)」でアプリを起動してから再実行してください。",
      { cause: e },
    );
  }

  const context = browser.contexts()[0];

  // devtools:// ページを除外（setupHelpers.ts と同じロジック）
  const page =
    context.pages().find((p) => !p.url().startsWith("devtools://")) ??
    context.pages()[0];

  if (!page) {
    throw new Error("Tauri アプリのページが見つかりません。");
  }

  await page.setViewportSize({ width: 1920, height: 1080 });

  return { browser, context, page };
}

// ---------------------------------------------------------------------------
// スクリーンショットユーティリティ
// ---------------------------------------------------------------------------

/**
 * captured/{sceneId}/ ディレクトリにスクリーンショットを保存する。
 * ファイル名: step-{step:02d}.png（例: step-01.png）
 */
export async function captureStep(
  page: Page,
  sceneId: string,
  step: number,
): Promise<string> {
  const dir = path.resolve(__dirname, `../captured/${sceneId}`);
  const filePath = path.join(dir, `step-${String(step).padStart(2, "0")}.png`);

  // ディレクトリが存在しない場合は作成
  const { mkdir } = await import("node:fs/promises");
  await mkdir(dir, { recursive: true });

  await page.screenshot({ path: filePath, fullPage: false });
  console.log(`📸 captured: ${filePath}`);
  return filePath;
}

// ---------------------------------------------------------------------------
// 動画収録（CDP Screencast）
// ---------------------------------------------------------------------------

/** meta.json のスキーマ */
export interface FrameSequenceMeta {
  /** 保存済みフレーム数 */
  totalFrames: number;
  /** 録画全体の長さ (ms) */
  durationMs: number;
  /** 各フレームの録画開始からの経過時刻 (ms) */
  frameTimestamps: number[];
  /** 字幕キュー（操作ステップごとのテキストと表示開始時刻） */
  cues: Array<{ timeMs: number; textJa: string; textEn: string }>;
}

/**
 * CDP Screencast を使ってアプリ画面を連番 JPEG で記録するクラス。
 *
 * 使い方:
 * ```typescript
 * const rec = await Recorder.create(context, page, "c09");
 * await rec.start();
 * rec.addCue("操作前のキャプション", "Caption before action");
 * await humanClick(page, someLocator);
 * const info = await rec.stop();
 * // → captured/c09/frames/0001.jpg … NNNN.jpg + meta.json が生成される
 * ```
 */
export class Recorder {
  private readonly client: CDPSession;
  private readonly sceneId: string;

  private frames: Array<{ data: string; timestampMs: number }> = [];
  private cues: Array<{ timeMs: number; textJa: string; textEn: string }> = [];
  private startTimeMs = 0;
  private isRecording = false;

  private constructor(__page: Page, client: CDPSession, sceneId: string) {
    this.client = client;
    this.sceneId = sceneId;
  }

  /** CDPSession を作成して Recorder インスタンスを返す */
  static async create(
    context: BrowserContext,
    page: Page,
    sceneId: string,
  ): Promise<Recorder> {
    const client = await context.newCDPSession(page);
    return new Recorder(page, client, sceneId);
  }

  /** 録画を開始する */
  async start(): Promise<void> {
    this.frames = [];
    this.cues = [];
    this.startTimeMs = Date.now();
    this.isRecording = true;

    this.client.on(
      "Page.screencastFrame",
      async ({
        data,
        sessionId,
      }: {
        data: string;
        metadata: unknown;
        sessionId: number;
      }) => {
        if (!this.isRecording) return;
        this.frames.push({ data, timestampMs: Date.now() - this.startTimeMs });
        await this.client
          .send("Page.screencastFrameAck", { sessionId })
          .catch(() => {});
      },
    );

    await this.client.send("Page.startScreencast", {
      format: "jpeg",
      quality: 85,
      everyNthFrame: 1,
    });
  }

  /**
   * 字幕キューを現在時刻で追加する。
   * 操作直前に呼び出すことで「これから何をするか」を示す字幕になる。
   */
  addCue(textJa: string, textEn: string = textJa): void {
    if (!this.isRecording) return;
    const timeMs = Date.now() - this.startTimeMs;
    this.cues.push({ timeMs, textJa, textEn });
  }

  /** 録画を停止してフレームを captured/{sceneId}/ に保存する */
  async stop(): Promise<{ totalFrames: number; durationMs: number }> {
    this.isRecording = false;
    await this.client.send("Page.stopScreencast").catch(() => {});
    await this.client.detach().catch(() => {});
    const info = await this.saveFrames();
    console.log(
      `🎬 録画完了: ${info.totalFrames} フレーム, ${(info.durationMs / 1000).toFixed(1)}s`,
    );
    return info;
  }

  private async saveFrames(): Promise<{
    totalFrames: number;
    durationMs: number;
  }> {
    const { mkdir, writeFile } = await import("node:fs/promises");
    const framesDir = path.resolve(
      __dirname,
      `../captured/${this.sceneId}/frames`,
    );
    await mkdir(framesDir, { recursive: true });

    const frameTimestamps: number[] = [];
    for (let i = 0; i < this.frames.length; i++) {
      const filename = `${String(i + 1).padStart(4, "0")}.jpg`;
      const buffer = Buffer.from(this.frames[i].data, "base64");
      await writeFile(path.join(framesDir, filename), buffer);
      frameTimestamps.push(this.frames[i].timestampMs);
    }

    const durationMs =
      frameTimestamps.length > 0
        ? frameTimestamps[frameTimestamps.length - 1]
        : 0;

    const meta: FrameSequenceMeta = {
      totalFrames: this.frames.length,
      durationMs,
      frameTimestamps,
      cues: this.cues,
    };

    await writeFile(
      path.resolve(__dirname, `../captured/${this.sceneId}/meta.json`),
      JSON.stringify(meta, null, 2),
    );

    return { totalFrames: this.frames.length, durationMs };
  }
}

// ---------------------------------------------------------------------------
// 人間らしい操作ヘルパー
// ---------------------------------------------------------------------------

/** マウス移動のステップ数（小さいほど速い） */
const MOUSE_STEPS = 25;
/** クリック後の待機 (ms) */
const AFTER_CLICK_MS = 700;
/** ホバー後クリックまでの間隔 (ms) */
const PRE_CLICK_MS = 150;

/**
 * 要素にハイライト枠 + クリックパルスを表示し、人間らしいマウス移動でクリックする。
 *
 * @param page     Playwright Page
 * @param locator  クリック対象
 * @param afterMs  クリック後の待機時間（ms）。結果が表示されるまで待ちたい場合は長めに設定
 */
export async function humanClick(
  page: Page,
  locator: Locator,
  afterMs = AFTER_CLICK_MS,
): Promise<void> {
  await locator.waitFor({ state: "visible", timeout: 10_000 });
  const box = await locator.boundingBox();
  if (!box) throw new Error("humanClick: boundingBox が null です");

  const cx = box.x + box.width / 2;
  const cy = box.y + box.height / 2;

  // 1. ハイライト枠を注入（クリック対象を視覚的に囲む）
  await injectHighlight(page, box);

  // 2. マウスをゆっくり移動
  await page.mouse.move(cx, cy, { steps: MOUSE_STEPS });
  await page.waitForTimeout(PRE_CLICK_MS);

  // 3. クリックパルス（オレンジ色の拡散円）を注入
  await injectClickPulse(page, cx, cy);

  // 4. クリック実行
  await page.mouse.click(cx, cy);
  await page.waitForTimeout(afterMs);
}

/**
 * チェックボックスを指定の状態にする（必要な場合のみクリック）
 */
export async function humanCheck(
  page: Page,
  locator: Locator,
  check: boolean,
  afterMs = AFTER_CLICK_MS / 2,
): Promise<void> {
  await locator.waitFor({ state: "visible", timeout: 10_000 });
  const checked = await locator.isChecked().catch(() => false);
  if (checked === check) return;
  await humanClick(page, locator, afterMs);
}

// ---------------------------------------------------------------------------
// DOM インジェクション
// ---------------------------------------------------------------------------

async function injectHighlight(
  page: Page,
  box: { x: number; y: number; width: number; height: number },
): Promise<void> {
  await page.evaluate(
    ({ x, y, w, h }: { x: number; y: number; w: number; h: number }) => {
      const el = document.createElement("div");
      el.style.cssText = [
        "position:fixed",
        `left:${x}px`,
        `top:${y}px`,
        `width:${w}px`,
        `height:${h}px`,
        "box-shadow:0 0 0 3px #ff6b35",
        "border-radius:4px",
        "pointer-events:none",
        "z-index:2147483646",
        "transition:opacity 0.4s ease",
      ].join(";");
      document.body.appendChild(el);
      setTimeout(() => {
        el.style.opacity = "0";
        setTimeout(() => el.remove(), 400);
      }, 750);
    },
    { x: box.x, y: box.y, w: box.width, h: box.height },
  );
}

async function injectClickPulse(
  page: Page,
  cx: number,
  cy: number,
): Promise<void> {
  await page.evaluate(
    ({ x, y }: { x: number; y: number }) => {
      if (!document.getElementById("__ec_pulse_style__")) {
        const style = document.createElement("style");
        style.id = "__ec_pulse_style__";
        style.textContent = `
          @keyframes __ec_pulse__ {
            0%   { transform: scale(0.4); opacity: 0.85; }
            100% { transform: scale(2.2); opacity: 0;    }
          }
        `;
        document.head.appendChild(style);
      }
      const el = document.createElement("div");
      el.style.cssText = [
        "position:fixed",
        `left:${x - 30}px`,
        `top:${y - 30}px`,
        "width:60px",
        "height:60px",
        "border-radius:50%",
        "background:rgba(255,107,53,0.65)",
        "pointer-events:none",
        "z-index:2147483647",
        "animation:__ec_pulse__ 0.45s ease-out forwards",
      ].join(";");
      document.body.appendChild(el);
      setTimeout(() => el.remove(), 460);
    },
    { x: cx, y: cy },
  );
}
