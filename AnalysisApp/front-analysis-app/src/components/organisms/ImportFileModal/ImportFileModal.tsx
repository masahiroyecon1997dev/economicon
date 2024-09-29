import React, {
  useState,
  ChangeEvent,
  DragEvent,
  Dispatch,
  SetStateAction,
} from "react";
import { useTranslation } from "react-i18next";

import { IconContext } from "react-icons";
import { FaFileAlt } from "react-icons/fa";

import { TableInfosType } from "../../../types/stateTypes";
import { importCsv } from "../../../functiom/restApis";
import { getTableInfo } from "../../../functiom/internalFunctions";

import { Modal } from "../../molecules/Modal/Modal";

type ImportFileModalProps = {
  isImportFileModal: boolean;
  close: () => void;
  setTableInfos: Dispatch<SetStateAction<TableInfosType>>;
};

export function ImportFileModal({
  isImportFileModal,
  close,
  setTableInfos,
}: ImportFileModalProps) {
  const { t } = useTranslation();
  const [file, setFile] = useState<File>();
  const [dragActive, setDragActive] = useState(false);

  function changeFileInput(event: ChangeEvent<HTMLInputElement>) {
    const files = event.target.files;
    if (!files || files?.length === 0) return;
    setFile(files[0]);
  }

  function handleDrag(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    event.stopPropagation();
    if (event.type === "dragenter" || event.type === "dragover") {
      setDragActive(true);
    } else if (event.type === "dragleave") {
      setDragActive(false);
    }
  }

  function handleDropFile(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    event.stopPropagation();
    setDragActive(false);
    if (event.dataTransfer.files && event.dataTransfer.files[0]) {
      setFile(event.dataTransfer.files[0]);
    }
  }

  async function importFile() {
    if (!file) return;
    const resImportCsv = await importCsv(file);
    const tableInfo = await getTableInfo(resImportCsv.result.tableName);
    setTableInfos((preTableInfos) => [...preTableInfos, tableInfo]);
    close();
  }

  return (
    <Modal
      isOpenModal={isImportFileModal}
      modalTitle={t("ImportFileModal.Title")}
      submitButtonName={t("ImportFileModal.OpenFile")}
      submit={importFile}
      close={close}
    >
      <div
        className={`w-full py-9 bg-gray-50 rounded-2xl border border-gray-300 gap-3 grid border-dashed ${
          dragActive ? "border-blue-500 bg-blue-100" : "border-gray-300"
        }`}
        onDragEnter={(event) => handleDrag(event)}
        onDragOver={(event) => handleDrag(event)}
        onDragLeave={(event) => handleDrag(event)}
        onDrop={(event) => handleDropFile(event)}
      >
        {file ? (
          <div>
            <div className="grid gap-1">
              <div className="mx-auto">
                <IconContext.Provider
                  value={{ color: "#4f46e5", size: "40px" }}
                >
                  <FaFileAlt />
                </IconContext.Provider>
              </div>
            </div>
            <div className="grid gap-2">
              <h4 className="text-center text-gray-900 text-sm font-medium leading-snug">
                {file.name}
              </h4>
              <h2 className="text-center text-gray-400 text-xs leading-4">
                {file.size / 1000 / 1000}MB
              </h2>
              <div className="flex items-center justify-center">
                <label>
                  <input
                    type="file"
                    accept=".csv"
                    hidden
                    onChange={(event) => changeFileInput(event)}
                  />
                  <div className="flex w-28 h-9 px-2 flex-col bg-indigo-600 rounded-full shadow text-white text-xs font-semibold leading-4 items-center justify-center cursor-pointer focus:outline-none">
                    {t("ImportFileModal.OtherChooseFile")}
                  </div>
                </label>
              </div>
            </div>
          </div>
        ) : (
          <div>
            <div className="grid gap-1">
              <div className="mx-auto">
                <IconContext.Provider
                  value={{ color: "#4f46e5", size: "40px" }}
                >
                  <FaFileAlt />
                </IconContext.Provider>
              </div>
              <h2 className="text-center text-gray-400 text-xs leading-4">
                {t("ImportFileModal.Notation")}
              </h2>
            </div>
            <div className="grid gap-2">
              <h4 className="text-center text-gray-900 text-sm font-medium leading-snug">
                {t("ImportFileModal.Information")}
              </h4>
              <div className="flex items-center justify-center">
                <label>
                  <input
                    type="file"
                    hidden
                    onChange={(event) => changeFileInput(event)}
                  />
                  <div className="flex w-28 h-9 px-2 flex-col bg-indigo-600 rounded-full shadow text-white text-xs font-semibold leading-4 items-center justify-center cursor-pointer focus:outline-none">
                    {t("ImportFileModal.ChooseFile")}
                  </div>
                </label>
              </div>
            </div>
          </div>
        )}
      </div>
    </Modal>
  );
}
