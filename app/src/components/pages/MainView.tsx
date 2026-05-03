import { CorrelationMatrix } from "@/components/pages/CorrelationMatrix";
import { DescriptiveStatistics } from "@/components/pages/DescriptiveStatistics";
import { ImportDataFile } from "@/components/pages/ImportDataFile";
import { SaveData } from "@/components/pages/SaveData";
import { WorkspaceSurface } from "@/components/pages/WorkspaceSurface";
import type { CurrentPageValue } from "@/stores/currentView";
import { useCurrentPageStore } from "@/stores/currentView";

const PAGE_COMPONENTS: Record<CurrentPageValue, React.ReactElement> = {
  ImportDataFile: <ImportDataFile />,
  JoinTable: <WorkspaceSurface />,
  UnionTable: <WorkspaceSurface />,
  DescriptiveStatistics: <DescriptiveStatistics />,
  CorrelationMatrix: <CorrelationMatrix />,
  ConfidenceIntervalView: <WorkspaceSurface />,
  LinearRegressionForm: <WorkspaceSurface />,
  CreateSimulationDataTable: <WorkspaceSurface />,
  CalculationView: <WorkspaceSurface />,
  SaveData: <SaveData />,
  AnalysisResultPreview: <WorkspaceSurface />,
  DataPreview: <WorkspaceSurface />,
};

export const MainView = () => {
  const currentView = useCurrentPageStore((state) => state.currentView);

  return (
    <main className="flex-1 flex flex-col overflow-hidden h-full bg-brand-secondary">
      <div className="flex-1 overflow-hidden p-2 flex flex-col min-h-0">
        {PAGE_COMPONENTS[currentView]}
      </div>
    </main>
  );
};
