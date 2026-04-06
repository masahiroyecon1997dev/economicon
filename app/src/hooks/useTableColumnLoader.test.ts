import { act, renderHook, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { getEconomiconAppAPI } from "@/api/endpoints";
import * as messageDialog from "@/lib/dialog/message";
import { useLoadingStore } from "@/stores/loading";
import { useTableInfosStore } from "@/stores/tableInfos";
import { useTableColumnLoader } from "@/hooks/useTableColumnLoader";

vi.mock("../api/endpoints", () => ({
  getEconomiconAppAPI: vi.fn(),
}));

vi.mock("react-i18next", () => {
  const t = (key: string) => key;
  return {
    useTranslation: () => ({
      t,
      i18n: { language: "ja" },
    }),
  };
});

vi.mock("../lib/dialog/message", () => ({
  showMessageDialog: vi.fn(),
}));

const mockGetColumnList = vi.fn();

beforeEach(() => {
  vi.mocked(getEconomiconAppAPI).mockReturnValue({
    getColumnList: mockGetColumnList,
  } as never);
  mockGetColumnList.mockReset();
  vi.mocked(messageDialog.showMessageDialog).mockResolvedValue(undefined);

  // activeTableName をリセット
  useTableInfosStore.setState({ tableInfos: [], activeTableName: null });
  // clearLoading() でモジュールレベルの _loadingTimer も含めてリセットする
  useLoadingStore.getState().clearLoading();
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe("useTableColumnLoader", () => {
  describe("autoLoadOnMount=true (デフォルト)", () => {
    it("test_autoLoad_withActiveTable_callsGetColumnList", async () => {
      useTableInfosStore.setState({
        tableInfos: [
          {
            tableName: "tableA",
            columnList: [],
            totalRows: 0,
            isActive: true,
          },
        ],
        activeTableName: "tableA",
      });

      mockGetColumnList.mockResolvedValueOnce({
        code: "OK",
        result: {
          columnInfoList: [
            { name: "id", type: "Int64" },
            { name: "name", type: "String" },
          ],
        },
      });

      const { result } = renderHook(() => useTableColumnLoader());

      await waitFor(() => {
        expect(result.current.columnList).toHaveLength(2);
      });

      expect(mockGetColumnList).toHaveBeenCalledWith({
        tableName: "tableA",
        isNumberOnly: undefined,
      });
    });

    it("test_autoLoad_numericOnly_passesIsNumberOnlyTrue", async () => {
      useTableInfosStore.setState({
        tableInfos: [
          {
            tableName: "tableA",
            columnList: [],
            totalRows: 0,
            isActive: true,
          },
        ],
        activeTableName: "tableA",
      });

      mockGetColumnList.mockResolvedValueOnce({
        code: "OK",
        result: { columnInfoList: [{ name: "price", type: "Float64" }] },
      });

      const { result } = renderHook(() =>
        useTableColumnLoader({ numericOnly: true }),
      );

      await waitFor(() => {
        expect(result.current.columnList).toHaveLength(1);
      });

      expect(mockGetColumnList).toHaveBeenCalledWith({
        tableName: "tableA",
        isNumberOnly: true,
      });
    });

    it("test_autoLoad_noActiveTable_doesNotCallAPI", async () => {
      // activeTableName = null → selectedTableName = ""
      const { result } = renderHook(() => useTableColumnLoader());

      await act(async () => {
        await new Promise((r) => setTimeout(r, 50));
      });

      expect(mockGetColumnList).not.toHaveBeenCalled();
      expect(result.current.columnList).toEqual([]);
    });

    it("test_autoLoad_apiReturnsNGCode_showsMessageDialog", async () => {
      useTableInfosStore.setState({
        tableInfos: [
          {
            tableName: "tableA",
            columnList: [],
            totalRows: 0,
            isActive: true,
          },
        ],
        activeTableName: "tableA",
      });

      mockGetColumnList.mockResolvedValueOnce({ code: "NG" });

      renderHook(() => useTableColumnLoader());

      await waitFor(() => {
        expect(messageDialog.showMessageDialog).toHaveBeenCalled();
      });
    });

    it("test_autoLoad_apiThrows_showsMessageDialog", async () => {
      useTableInfosStore.setState({
        tableInfos: [
          {
            tableName: "tableA",
            columnList: [],
            totalRows: 0,
            isActive: true,
          },
        ],
        activeTableName: "tableA",
      });

      mockGetColumnList.mockRejectedValueOnce(new Error("network error"));

      renderHook(() => useTableColumnLoader());

      await waitFor(() => {
        expect(messageDialog.showMessageDialog).toHaveBeenCalled();
      });
    });
  });

  describe("autoLoadOnMount=false", () => {
    it("test_autoLoadFalse_doesNotCallAPI", async () => {
      useTableInfosStore.setState({
        tableInfos: [
          {
            tableName: "tableA",
            columnList: [],
            totalRows: 0,
            isActive: true,
          },
        ],
        activeTableName: "tableA",
      });

      renderHook(() => useTableColumnLoader({ autoLoadOnMount: false }));

      await act(async () => {
        await new Promise((r) => setTimeout(r, 50));
      });

      expect(mockGetColumnList).not.toHaveBeenCalled();
    });
  });

  describe("setSelectedTableName", () => {
    it("test_setSelectedTableName_triggersReload", async () => {
      mockGetColumnList
        .mockResolvedValueOnce({
          code: "OK",
          result: { columnInfoList: [{ name: "id", type: "Int64" }] },
        })
        .mockResolvedValueOnce({
          code: "OK",
          result: { columnInfoList: [{ name: "price", type: "Float64" }] },
        });

      useTableInfosStore.setState({
        tableInfos: [
          {
            tableName: "tableA",
            columnList: [],
            totalRows: 0,
            isActive: true,
          },
        ],
        activeTableName: "tableA",
      });

      const { result } = renderHook(() => useTableColumnLoader());

      await waitFor(() => {
        expect(result.current.columnList).toHaveLength(1);
      });

      act(() => {
        result.current.setSelectedTableName("tableB");
      });

      await waitFor(() => {
        expect(result.current.columnList[0].name).toBe("price");
      });

      expect(mockGetColumnList).toHaveBeenCalledTimes(2);
    });
  });
});
