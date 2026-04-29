import type { CurrentPageValue } from "@/stores/currentView";
import { useCurrentPageStore } from "@/stores/currentView";
import { Calculation } from "@/components/pages/Calculation";
import { ConfidenceIntervalView } from "@/components/pages/ConfidenceIntervalView";
import { CorrelationMatrix } from "@/components/pages/CorrelationMatrix";
import { CreateSimulationDataTable } from "@/components/pages/CreateSimulationDataTable";
import { DescriptiveStatistics } from "@/components/pages/DescriptiveStatistics";
import { ImportDataFile } from "@/components/pages/ImportDataFile";
import { JoinTable } from "@/components/pages/JoinTable";
import { Regression } from "@/components/pages/RegressionView";
import { SaveData } from "@/components/pages/SaveData";
import { Table } from "@/components/pages/Table";
import { UnionTable } from "@/components/pages/UnionTable";

const PAGE_COMPONENTS: Record<CurrentPageValue, React.ReactElement> = {
  ImportDataFile: <ImportDataFile />,
  JoinTable: <JoinTable />,
  UnionTable: <UnionTable />,
  DescriptiveStatistics: <DescriptiveStatistics />,
  CorrelationMatrix: <CorrelationMatrix />,
  ConfidenceIntervalView: <ConfidenceIntervalView />,
  LinearRegressionForm: <Regression />,
  CreateSimulationDataTable: <CreateSimulationDataTable />,
  CalculationView: <Calculation />,
  SaveData: <SaveData />,
  AnalysisResultPreview: <Table />,
  DataPreview: <Table />,
};

export const MainView = () => {
  const currentView = useCurrentPageStore((state) => state.currentView);

  return (
    <main className="flex-1 flex flex-col overflow-hidden h-full bg-brand-secondary">
      <div className="flex-1 overflow-hidden p-4 flex flex-col min-h-0">
        {PAGE_COMPONENTS[currentView]}
      </div>
    </main>
  );
};
