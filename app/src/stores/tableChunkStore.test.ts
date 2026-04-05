import { beforeEach, describe, expect, it } from "vitest";
import { CHUNK_SIZE, useTableChunkStore } from "./tableChunkStore";

// MAX_CACHE_CHUNKS はモジュール内プライベートだが CHUNK_SIZE は公開済み
const MAX_CACHE_CHUNKS = 20;

const makeBytes = (fill: number, size = 4): Uint8Array =>
  new Uint8Array(size).fill(fill);

beforeEach(() => {
  useTableChunkStore.setState({ _cache: new Map(), versions: {} });
});

// ---------------------------------------------------------------------------
// CHUNK_SIZE 定数
// ---------------------------------------------------------------------------
describe("CHUNK_SIZE", () => {
  it("test_CHUNK_SIZE_is500", () => {
    expect(CHUNK_SIZE).toBe(500);
  });
});

// ---------------------------------------------------------------------------
// setChunk / getChunk / hasChunk
// ---------------------------------------------------------------------------
describe("useTableChunkStore.setChunk", () => {
  it("test_setChunk_newTable_storesData", () => {
    const { setChunk, getChunk, hasChunk } = useTableChunkStore.getState();
    const data = makeBytes(1);
    setChunk("tableA", 0, data);

    expect(hasChunk("tableA", 0)).toBe(true);
    expect(getChunk("tableA", 0)).toEqual(data);
  });

  it("test_setChunk_incrementsVersion", () => {
    const { setChunk } = useTableChunkStore.getState();
    setChunk("tableA", 0, makeBytes(1));
    setChunk("tableA", 1, makeBytes(2));

    const versions = useTableChunkStore.getState().versions;
    expect(versions["tableA"]).toBe(2);
  });

  it("test_setChunk_differentTables_independentVersions", () => {
    const { setChunk } = useTableChunkStore.getState();
    setChunk("tableA", 0, makeBytes(1));
    setChunk("tableB", 0, makeBytes(2));
    setChunk("tableB", 1, makeBytes(3));

    const versions = useTableChunkStore.getState().versions;
    expect(versions["tableA"]).toBe(1);
    expect(versions["tableB"]).toBe(2);
  });

  it("test_setChunk_lruEviction_removesOldestWhenFull", () => {
    const { setChunk, hasChunk } = useTableChunkStore.getState();

    // MAX_CACHE_CHUNKS 個埋める
    for (let i = 0; i < MAX_CACHE_CHUNKS; i++) {
      setChunk("tableA", i, makeBytes(i));
    }
    // 全部存在するはず
    expect(hasChunk("tableA", 0)).toBe(true);

    // MAX+1 番目を追加 → chunk 0 が evict されるはず
    setChunk("tableA", MAX_CACHE_CHUNKS, makeBytes(MAX_CACHE_CHUNKS));
    expect(hasChunk("tableA", 0)).toBe(false);
    expect(hasChunk("tableA", MAX_CACHE_CHUNKS)).toBe(true);
  });

  it("test_setChunk_overwriteExisting_noEviction", () => {
    const { setChunk, hasChunk } = useTableChunkStore.getState();
    const newData = makeBytes(99);

    // MAX 個埋める
    for (let i = 0; i < MAX_CACHE_CHUNKS; i++) {
      setChunk("tableA", i, makeBytes(i));
    }

    // 既存チャンク 0 を上書き → evict 不要
    setChunk("tableA", 0, newData);
    expect(hasChunk("tableA", 0)).toBe(true);
    expect(useTableChunkStore.getState().getChunk("tableA", 0)).toEqual(
      newData,
    );
  });
});

describe("useTableChunkStore.getChunk", () => {
  it("test_getChunk_uncachedChunk_returnsUndefined", () => {
    const { getChunk } = useTableChunkStore.getState();
    expect(getChunk("nonExistent", 0)).toBeUndefined();
  });
});

describe("useTableChunkStore.hasChunk", () => {
  it("test_hasChunk_uncachedChunk_returnsFalse", () => {
    const { hasChunk } = useTableChunkStore.getState();
    expect(hasChunk("tableA", 99)).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// clearTable
// ---------------------------------------------------------------------------
describe("useTableChunkStore.clearTable", () => {
  it("test_clearTable_removesAllChunksForTable", () => {
    const { setChunk, hasChunk, clearTable } = useTableChunkStore.getState();
    setChunk("tableA", 0, makeBytes(1));
    setChunk("tableA", 1, makeBytes(2));
    setChunk("tableB", 0, makeBytes(3));

    clearTable("tableA");

    expect(hasChunk("tableA", 0)).toBe(false);
    expect(hasChunk("tableA", 1)).toBe(false);
    // tableB は無影響
    expect(hasChunk("tableB", 0)).toBe(true);
  });

  it("test_clearTable_incrementsVersionForClearedTable", () => {
    const { setChunk, clearTable } = useTableChunkStore.getState();
    setChunk("tableA", 0, makeBytes(1)); // version=1
    clearTable("tableA"); // version=2

    expect(useTableChunkStore.getState().versions["tableA"]).toBe(2);
  });

  it("test_clearTable_unknownTable_doesNotThrow", () => {
    const { clearTable } = useTableChunkStore.getState();
    expect(() => clearTable("nonExistent")).not.toThrow();
  });
});

// ---------------------------------------------------------------------------
// clearAll
// ---------------------------------------------------------------------------
describe("useTableChunkStore.clearAll", () => {
  it("test_clearAll_removesAllTablesAndClearsVersions", () => {
    const { setChunk, hasChunk, clearAll } = useTableChunkStore.getState();
    setChunk("tableA", 0, makeBytes(1));
    setChunk("tableB", 0, makeBytes(2));

    clearAll();

    expect(hasChunk("tableA", 0)).toBe(false);
    expect(hasChunk("tableB", 0)).toBe(false);
    expect(useTableChunkStore.getState().versions).toEqual({});
  });
});
