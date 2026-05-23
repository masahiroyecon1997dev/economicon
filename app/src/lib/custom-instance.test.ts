import { customInstance } from "@/api/mutator/custom-instance";
import { invoke } from "@tauri-apps/api/core";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@tauri-apps/api/core", () => ({
  invoke: vi.fn(),
}));

describe("customInstance", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("PATCH を proxy_request に中継する", async () => {
    vi.mocked(invoke).mockResolvedValue({ code: "OK" });

    const response = await customInstance<{ code: string }>({
      url: "/api/analysis/results/result-1",
      method: "PATCH",
      data: { name: "updated" },
    });

    expect(invoke).toHaveBeenCalledWith("proxy_request", {
      method: "PATCH",
      path: "/api/analysis/results/result-1",
      body: { name: "updated" },
      query: undefined,
    });
    expect(response).toEqual({ code: "OK" });
  });
});