import "@testing-library/jest-dom";
import { cleanup } from "@testing-library/react";
import { afterEach, beforeAll, vi } from "vitest";

// --- Tauri API Mock ---
vi.mock("@tauri-apps/api/core", () => ({
  invoke: vi.fn(async (cmd: string) => {
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

// --- ResizeObserver Mock ---
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
      this.button = props.button ?? 0;
      this.ctrlKey = props.ctrlKey ?? false;
      this.pointerType = props.pointerType ?? "mouse";
    }
  } as unknown as typeof PointerEvent;

  // Radix UI が内部で使用するポインターキャプチャ API のポリフィル
  window.HTMLElement.prototype.hasPointerCapture = vi.fn();
  window.HTMLElement.prototype.setPointerCapture = vi.fn();
  window.HTMLElement.prototype.releasePointerCapture = vi.fn();
  // Radix UI Select が選択肢のスクロール時に使用する API のポリフィル
  window.HTMLElement.prototype.scrollIntoView = vi.fn();

  global.DOMRect = class DOMRect {
    x: number;
    y: number;
    width: number;
    height: number;
    bottom = 0;
    left = 0;
    right = 0;
    top = 0;

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
