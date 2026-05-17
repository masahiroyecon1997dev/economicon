import { useCallback, useEffect, useRef, useState } from "react";

export type AnimationSpeed = "slow" | "normal" | "fast";

export const SPEED_INTERVAL_MS: Record<AnimationSpeed, number> = {
  slow: 400,
  normal: 100,
  fast: 20,
};

type AnimState = { frame: number; playing: boolean; syncedTotal: number };

/**
 * シミュレーション・アニメーション共通ロジック。
 * フレームを一定間隔でインクリメントし、末尾に達したら自動停止する。
 *
 * @param totalFrames 総フレーム数。変化時にリセットされる。
 * @param speed アニメーション速度。変化時はインターバルが再起動される。
 */
export const useSimulationAnimation = (
  totalFrames: number,
  speed: AnimationSpeed,
) => {
  const [{ frame, playing, syncedTotal }, setAnimState] = useState<AnimState>({
    frame: 0,
    playing: false,
    syncedTotal: totalFrames,
  });

  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  /** stale closure を避けるため最新フレームを ref で管理 */
  const frameRef = useRef(0);
  /** stale closure を避けるため最新総フレーム数を ref で管理 */
  const totalRef = useRef(totalFrames);

  // totalFrames 変化時はレンダー中に状態をリセット（getDerivedStateFromProps パターン）
  // effect 内の setState による cascading render を回避する
  if (syncedTotal !== totalFrames) {
    setAnimState({ frame: 0, playing: false, syncedTotal: totalFrames });
  }

  const clear = useCallback(() => {
    if (intervalRef.current !== null) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, []);

  // totalFrames 変化後の ref 同期とインターバルクリア（setState は行わない）
  useEffect(() => {
    totalRef.current = totalFrames;
    clear();
    frameRef.current = 0;
  }, [totalFrames, clear]);

  // playing / speed が変わったらインターバルを再起動
  useEffect(() => {
    if (!playing) {
      clear();
      return;
    }
    const ms = SPEED_INTERVAL_MS[speed];
    intervalRef.current = setInterval(() => {
      frameRef.current += 1;
      const next = frameRef.current;
      if (next >= totalRef.current) {
        clearInterval(intervalRef.current!);
        intervalRef.current = null;
        setAnimState((prev) => ({ ...prev, frame: next, playing: false }));
      } else {
        setAnimState((prev) => ({ ...prev, frame: next }));
      }
    }, ms);
    return clear;
  }, [playing, speed, clear]);

  // アンマウント時クリーンアップ
  useEffect(() => () => clear(), [clear]);

  const play = useCallback(() => {
    if (frameRef.current >= totalRef.current) return;
    setAnimState((prev) => ({ ...prev, playing: true }));
  }, []);

  const pause = useCallback(() => {
    setAnimState((prev) => ({ ...prev, playing: false }));
  }, []);

  const reset = useCallback(() => {
    clear();
    frameRef.current = 0;
    setAnimState((prev) => ({ ...prev, frame: 0, playing: false }));
  }, [clear]);

  return { frame, playing, play, pause, reset };
};
