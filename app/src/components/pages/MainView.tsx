import type { CurrentPageValue } from "../../stores/currentView";
import { useCurrentPageStore } from "../../stores/currentView";
import { Calculation } from "./Calculation";
import { CreateSimulationDataTable } from "./CreateSimulationDataTable";
import { DescriptiveStatistics } from "./DescriptiveStatistics";
import { ImportDataFile } from "./ImportDataFile";
import { JoinTable } from "./JoinTable";
import { Regression } from "./RegressionView";
import { SaveData } from "./SaveData";
import { Table } from "./Table";
import { UnionTable } from "./UnionTable";

const PAGE_COMPONENTS: Record<CurrentPageValue, React.ReactElement> = {
  ImportDataFile: <ImportDataFile />,
  JoinTable: <JoinTable />,
  UnionTable: <UnionTable />,
  DescriptiveStatistics: <DescriptiveStatistics />,
  LinearRegressionForm: <Regression />,
  CreateSimulationDataTable: <CreateSimulationDataTable />,
  CalculationView: <Calculation />,
  SaveData: <SaveData />,
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
