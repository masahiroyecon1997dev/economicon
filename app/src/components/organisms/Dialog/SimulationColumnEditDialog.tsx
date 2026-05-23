import { Button } from "@/components/atoms/Button/Button";
import { BaseDialog } from "@/components/molecules/Dialog/BaseDialog";
import { SimulationColumnConfig } from "@/components/organisms/Form/SimulationColumnConfig";
import { DIST_PARAM_DEFAULTS } from "@/constants/simulation";
import { useWorkspaceTabsStore } from "@/stores/workspaceTabs";
import type { SimulationColumnSetting } from "@/types/commonTypes";
import { useTranslation } from "react-i18next";

const FORM_ID = "simulation-column-config-form";

type SimulationColumnEditDialogProps = {
  isOpen: boolean;
  column: SimulationColumnSetting;
  index: number;
  onSave: (id: string, updates: Partial<SimulationColumnSetting>) => void;
  onRemove: (id: string) => void;
  onClose: () => void;
  canRemove: boolean;
  disabled?: boolean;
};

export const SimulationColumnEditDialog = ({
  isOpen,
  column,
  index,
  onSave,
  onClose,
  disabled = false,
}: SimulationColumnEditDialogProps) => {
  const { t } = useTranslation();
  const openWorkTab = useWorkspaceTabsStore((s) => s.openWorkTab);

  const handleOpenPreview = () => {
    const distributionType = column.distributionType ?? "normal";
    const distributionParams = column.distributionParams ?? {
      ...DIST_PARAM_DEFAULTS[distributionType],
    };
    openWorkTab("DistributionPreview", t("HeaderMenu.DistributionPreview"), {
      distributionType,
      distributionParams,
    });
  };

  return (
    <BaseDialog
      open={isOpen}
      onOpenChange={(open) => {
        if (!open) onClose();
      }}
      title={`${t("CreateSimulationDataTableView.EditColumn")} ${index + 1}${t("Common.ColumnSuffix")}`}
      maxWidth="2xl"
      className="max-h-[90vh]"
      footerVariant="confirm"
      submitLabel={t("Common.Save")}
      submitFormId={FORM_ID}
      isSubmitDisabled={disabled}
      footerLeft={
        <Button
          type="button"
          variant="outline"
          onClick={handleOpenPreview}
          data-testid="open-distribution-preview-btn"
        >
          {t("HeaderMenu.DistributionPreview")}
        </Button>
      }
    >
      <div className="app-scrollbar overflow-y-auto max-h-[calc(90vh-160px)]">
        <SimulationColumnConfig
          formId={FORM_ID}
          column={column}
          onSaved={(updates) => {
            onSave(column.id, updates);
            onClose();
          }}
          disabled={disabled}
        />
      </div>
    </BaseDialog>
  );
};
