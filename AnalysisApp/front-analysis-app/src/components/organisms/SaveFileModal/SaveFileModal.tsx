import React, { useState, ChangeEvent, DragEvent, Dispatch, SetStateAction, useEffect } from "react";
import { useTranslation } from 'react-i18next';
import { saveAs } from 'file-saver';

import { getTableNameList, outputCsv } from "../../../functiom/restApis";
import { SelectListType } from "../../../types/commonTypes";

import { ModalHeader } from "../../molecules/ModalHeader/ModalHeader";
import { ModalFooter } from "../../molecules/ModalFooter/ModalFooter";
import { Select } from "../../molecules/Select/Select";

type SaveFileModalProps = {
  isSaveFileModal: boolean;
  close: () => void;
}

export function SaveFileModal({ isSaveFileModal, close }: SaveFileModalProps) {
  const { t } = useTranslation();
  const [tableList, setTableList] = useState<SelectListType>([]);
  const [selectedTableName, setSelectedTableName] = useState<string>('');

  useEffect(() => {
    if (isSaveFileModal) {
      async function initializeTableList() {
        const resTableNameList = await getTableNameList();
        for (const table of resTableNameList.tableNameList) {
          setTableList((preTableList) => ([...preTableList, { value: table, name: table }]));
        }
        setSelectedTableName(resTableNameList.tableNameList[0]);
      }
      initializeTableList();
    }
  }, [isSaveFileModal])

  function changeTableName(event: ChangeEvent<HTMLSelectElement>) {
    const tableName = event.target.value;
    setSelectedTableName(tableName);
  }

  async function saveFile() {
    const resOutputCsv = await outputCsv(selectedTableName);
    console.log(resOutputCsv);
    const csvData = new Blob([resOutputCsv.csvData], { type: 'text/csv' });
    saveAs(csvData, selectedTableName + '.csv');
    close();
  }


  if (isSaveFileModal) {
    return (
      <div className="fixed inset-0 z-50 flex justify-center items-center overflow-y-auto overflow-x-hidden w-full md:inset-0">
        <div className="relative p-4 w-full max-w-2xl max-h-full">
          <div className="relative bg-white rounded-lg shadow dark:bg-gray-700">
            <ModalHeader close={() => close()}>{t('ImportFileModal.Title')}</ModalHeader>
            <div className="">
              <Select optionList={tableList} selectFunc={(event: ChangeEvent<HTMLSelectElement>) => changeTableName(event)}></Select>
            </div>
            <ModalFooter close={() => close()} submit={() => saveFile()}>{t("ImportFileModal.OpenFile")}</ModalFooter>
          </div>
        </div>
      </div>
    );
  } else {
    return null;
  }
};
