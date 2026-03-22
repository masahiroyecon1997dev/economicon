import { useState } from "react";
import { useTranslation } from "react-i18next";
import type {
  DistributionType,
  SimulationColumnSetting,
} from "../../../types/commonTypes";
import { BaseDialog } from "../../molecules/Dialog/BaseDialog";
import { SimulationColumnConfig } from "../Form/SimulationColumnConfig";

type SimulationColumnEditDialogProps = {
  isOpen: boolean;
  column: SimulationColumnSetting;
  index: number;
  distributionOptions: Array<{
    value: DistributionType;
    label: string;
    params: string[];
  }>;
  onUpdate: (id: string, updates: Partial<SimulationColumnSetting>) => void;
  onDataTypeChange: (id: string, dataType: "distribution" | "fixed") => void;
  onDistributionTypeChange: (
    id: string,
    distributionType: DistributionType,
  ) => void;
  onDistributionParamChange: (id: string, param: string, value: number) => void;
  onRemove: (id: string) => void;
  onClose: () => void;
  canRemove: boolean;
  error: {
    columnName: string | undefined;
    distributionParams: Record<string, string | undefined> | undefined;
    fixedValue: string | undefined;
  };
  disabled?: boolean;
};

export const SimulationColumnEditDialog = ({
  isOpen,
  column,
  index,
  distributionOptions,
  onUpdate,
  onClose,
  error,
  disabled = false,
}: SimulationColumnEditDialogProps) => {
  const { t } = useTranslation();
  const [editingColumn, setEditingColumn] =
    useState<SimulationColumnSetting>(column);
  const [columnNameError, setColumnNameError] = useState<string | undefined>();

  const handleCancel = () => {
    setEditingColumn(column);
    setColumnNameError(undefined);
    onClose();
  };

  const handleSave = () => {
    if (!editingColumn.columnName || editingColumn.columnName.trim() === "") {
      setColumnNameError(t("ValidationMessages.ColumnNameRequired"));
      return;
    }
    setColumnNameError(undefined);

    // 変更があったフィールドのみを親へ反映
    const updates: Partial<SimulationColumnSetting> = {};
    (
      Object.keys(editingColumn) as Array<keyof SimulationColumnSetting>
    ).forEach((key) => {
      if (key !== "id" && key !== "errorMessage") {
        if (editingColumn[key] !== column[key]) {
          (updates as Record<string, unknown>)[key] = editingColumn[key];
        }
      }
    });
    if (Object.keys(updates).length > 0) {
      onUpdate(column.id, updates);
    }
    onClose();
  };

  const isSaveDisabled = disabled;

  const handleLocalUpdate = (
    _id: string,
    updates: Partial<SimulationColumnSetting>,
  ) => {
    if ("columnName" in updates) {
      setColumnNameError(undefined);
    }
    setEditingColumn((prev) => ({ ...prev, ...updates }));
  };

  const handleLocalDataTypeChange = (
    _id: string,
    dataType: "distribution" | "fixed",
  ) => {
    const updates: Partial<SimulationColumnSetting> = {
      dataType: dataType,
    };

    if (dataType === "distribution") {
      updates.distributionType = "uniform";
      updates.distributionParams = { low: 0, high: 10 };
      updates.fixedValue = "";
    } else {
      updates.fixedValue = "";
      updates.distributionType = undefined;
      updates.distributionParams = undefined;
    }

    setEditingColumn((prev) => ({ ...prev, ...updates }));
  };

  const handleLocalDistributionTypeChange = (
    _id: string,
    distributionType: DistributionType,
  ) => {
    const distOption = distributionOptions.find(
      (d) => d.value === distributionType,
    );
    if (!distOption) return;

    const defaultParams: Record<string, number> = {};
    distOption.params.forEach((param) => {
      switch (param) {
        case "low":
          defaultParams[param] = 0;
          break;
        case "high":
          defaultParams[param] = 10;
          break;
        case "mean":
          defaultParams[param] = 0;
          break;
        case "deviation":
          defaultParams[param] = 1;
          break;
        case "rate":
          defaultParams[param] = 1;
          break;
        case "scale":
          defaultParams[param] = 1;
          break;
        case "alpha":
          defaultParams[param] = 2;
          break;
        case "beta":
          defaultParams[param] = 2;
          break;
        case "logMean":
          defaultParams[param] = 0;
          break;
        case "logSD":
          defaultParams[param] = 1;
          break;
        case "trials":
          defaultParams[param] = 10;
          break;
        case "probability":
          defaultParams[param] = 0.5;
          break;
        case "populationSize":
          defaultParams[param] = 20;
          break;
        case "numberOfSuccesses":
          defaultParams[param] = 5;
          break;
        case "sampleSize":
          defaultParams[param] = 10;
          break;
        default:
          defaultParams[param] = 1;
      }
    });

    setEditingColumn((prev) => ({
      ...prev,
      distributionType: distributionType,
      distributionParams: defaultParams,
    }));
  };

  const handleLocalDistributionParamChange = (
    _id: string,
    param: string,
    value: number,
  ) => {
    setEditingColumn((prev) => ({
      ...prev,
      distributionParams: {
        ...prev.distributionParams,
        [param]: value,
      },
    }));
  };

  return (
    <BaseDialog
      open={isOpen}
      onOpenChange={(open) => {
        if (!open) handleCancel();
      }}
      title={`${t("CreateSimulationDataTableView.EditColumn")} ${index + 1}${t("Common.ColumnSuffix")}`}
      maxWidth="2xl"
      className="max-h-[90vh]"
      footerVariant="confirm"
      submitLabel={t("Common.Save")}
      onSubmit={handleSave}
      isSubmitDisabled={isSaveDisabled}
    >
      <div className="overflow-y-auto max-h-[calc(90vh-160px)]">
        <SimulationColumnConfig
          column={editingColumn}
          distributionOptions={distributionOptions}
          onUpdate={handleLocalUpdate}
          onDataTypeChange={handleLocalDataTypeChange}
          onDistributionTypeChange={handleLocalDistributionTypeChange}
          onDistributionParamChange={handleLocalDistributionParamChange}
          error={{
            ...error,
            columnName: columnNameError ?? error.columnName,
          }}
          disabled={disabled}
        />
      </div>
    </BaseDialog>
  );
};
