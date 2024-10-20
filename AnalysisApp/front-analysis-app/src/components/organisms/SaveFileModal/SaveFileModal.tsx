import React, { useState, ChangeEvent, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { saveAs } from "file-saver";

import { getTableNameList, outputCsv } from "../../../functiom/restApis";
import { SelectListType } from "../../../types/commonTypes";

import { Modal } from "../../molecules/Modal/Modal";
import { Select } from "../../molecules/Select/Select";

type SaveFileModalProps = {
  isSaveFileModal: boolean;
  close: () => void;
};

export function SaveFileModal({ isSaveFileModal, close }: SaveFileModalProps) {
  const { t } = useTranslation();
  const [tableList, setTableList] = useState<SelectListType>([]);
  const [selectedTableName, setSelectedTableName] = useState<string>("");

  useEffect(() => {
    if (isSaveFileModal) {
      async function initializeTableList() {
        const resTableNameList = await getTableNameList();
        for (const table of resTableNameList.result.tableNameList) {
          setTableList((preTableList) => [
            ...preTableList,
            { value: table, name: table },
          ]);
        }
        setSelectedTableName(resTableNameList.result.tableNameList[0]);
      }
      initializeTableList();
    }
  }, [isSaveFileModal]);

  function changeTableName(event: ChangeEvent<HTMLSelectElement>) {
    const tableName = event.target.value;
    setSelectedTableName(tableName);
  }

  async function saveFile() {
    const resOutputCsv = await outputCsv(selectedTableName);
    console.log(resOutputCsv);
    const csvData = new Blob([resOutputCsv.result.csvData], {
      type: "text/csv",
    });
    saveAs(csvData, selectedTableName + ".csv");
    close();
  }

  return (
    <Modal
      isOpenModal={isSaveFileModal}
      modalTitle={t("SaveFileModal.Title")}
      submitButtonName={t("SaveFileModal.Download")}
      submit={saveFile}
      close={close}
      modalSize="max-w-2xl"
    >
      <div className="grid grid-cols-3 gap-4 leading-6">
        <div className="p-4 rounded-lg text-right text-lg content-center">
          {t("SaveFileModal.TableName")}
        </div>
        <div className="p-4 rounded-lg col-span-2">
          <Select
            optionList={tableList}
            selectFunc={(event: ChangeEvent<HTMLSelectElement>) =>
              changeTableName(event)
            }
          ></Select>
        </div>
      </div>
    </Modal>
  );
}
