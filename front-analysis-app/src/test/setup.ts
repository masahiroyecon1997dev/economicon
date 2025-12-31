import "@testing-library/jest-dom";
import { cleanup } from "@testing-library/react";
import { afterEach, beforeAll } from "vitest";

// ResizeObserverのモック
class ResizeObserverMock {
  observe() {}
  unobserve() {}
  disconnect() {}
}

// グローバルにResizeObserverを設定
beforeAll(() => {
  global.ResizeObserver =
    ResizeObserverMock as unknown as typeof ResizeObserver;

  // PointerEventのモック（必要に応じて）
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

  // DOMRectのモック
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

// 各テスト後にクリーンアップを実行
afterEach(() => {
  cleanup();
});
