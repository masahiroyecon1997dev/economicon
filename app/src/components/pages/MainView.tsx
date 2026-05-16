import { ImportDataFile } from "@/components/pages/ImportDataFile";
import { SaveData } from "@/components/pages/SaveData";
import { WorkspaceSurface } from "@/components/pages/WorkspaceSurface";
import { useCurrentPageStore } from "@/stores/currentView";

export const MainView = () => {
  const currentView = useCurrentPageStore((state) => state.currentView);

  return (
    <main className="flex-1 flex flex-col overflow-hidden h-full bg-brand-secondary">
      <div className="flex-1 overflow-hidden p-2 flex flex-col min-h-0">
        {currentView === "ImportDataFile" && <ImportDataFile />}
        {currentView === "SaveData" && <SaveData />}
        {currentView === "Workspace" && <WorkspaceSurface />}
      </div>
    </main>
  );
};
