import "@testing-library/jest-dom";
import { cleanup } from "@testing-library/react";
import { afterEach, beforeAll, vi } from "vitest";

// --- Tauri API Mock ---
// @tauri-apps/api/core モジュールをモック化
vi.mock("@tauri-apps/api/core", () => ({
  invoke: vi.fn(async (cmd: string, args: any) => {
    console.log(`[Tauri Mock] invoke called: ${cmd}`, args);
    // コマンドに応じたレスポンスを定義
    switch (cmd) {
      case "proxy_request":
        return { message: "Mock response from proxy_request" };
      case "upload_file":
        return { message: "Mock response from upload_file" };
      default:
        return {};
    }
  }),
}));

// --- Existing Mocks ---
// ResizeObserverのモック
class ResizeObserverMock {
  observe() {}
  unobserve() {}
  disconnect() {}
}

beforeAll(() => {
  global.ResizeObserver =
    ResizeObserverMock as unknown as typeof ResizeObserver;

  global.PointerEvent = class PointerEvent extends Event {
    button: number;
    ctrlKey: boolean;
    pointerType: string;

    constructor(type: string, props: PointerEventInit = {}) {
      super(type, props);
      this.button = props.button || 0;
      this.ctrlKey = props.ctrlKey || false;
      this.pointerType = props.pointerType || "mouse";
    }
  } as unknown as typeof PointerEvent;

  global.DOMRect = class DOMRect {
    x: number;
    y: number;
    width: number;
    height: number;
    bottom: number = 0;
    left: number = 0;
    right: number = 0;
    top: number = 0;

    constructor(x = 0, y = 0, width = 0, height = 0) {
      this.x = x;
      this.y = y;
      this.width = width;
      this.height = height;
      this.left = x;
      this.top = y;
      this.right = x + width;
      this.bottom = y + height;
    }
    toJSON() {
      return JSON.stringify(this);
    }
  } as unknown as typeof DOMRect;
});

afterEach(() => {
  cleanup();
});
