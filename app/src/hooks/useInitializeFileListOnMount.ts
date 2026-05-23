import { getFiles, getFilesSafe } from "@/api/bridge/tauri-commands";
import { useFilesStore } from "@/stores/files";
import { useEffect, useRef } from "react";

export const useInitializeFileListOnMount = () => {
  const directoryPath = useFilesStore((state) => state.directoryPath);
  const setFiles = useFilesStore((state) => state.setFiles);
  const initialDirectoryPathRef = useRef(directoryPath);

  useEffect(() => {
    let cancelled = false;

    const initializeFiles = async () => {
      try {
        const result = initialDirectoryPathRef.current
          ? await getFiles(initialDirectoryPathRef.current)
          : await getFilesSafe("");

        if (!cancelled) {
          setFiles(result);
        }
      } catch {
        // Keep the current list if the initial refresh fails.
      }
    };

    void initializeFiles();

    return () => {
      cancelled = true;
    };
  }, [setFiles]);
};
