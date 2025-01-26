import React, {
  useState,
  ChangeEvent,
  DragEvent,
  Dispatch,
  SetStateAction,
  useEffect,
} from "react";
import { useTranslation } from "react-i18next";

import { Modal } from "../../molecules/Modal/Modal";
import { Select } from "../../molecules/Select/Select";
import {
  getColumnNameList,
  getTableNameList,
} from "../../../functiom/restApis";
import { SelectListType } from "../../../types/commonTypes";

type LinearRegressionModalProps = {
  isLinearRegressionModal: boolean;
  close: () => void;
};

export function LinearRegressionModal({
  isLinearRegressionModal,
  close,
}: LinearRegressionModalProps) {
  const { t } = useTranslation();
  const [tableNameList, setTableNameList] = useState<SelectListType>([]);
  const [selectedTableName, setSelectedTableName] = useState<String>("");
  const [columnNameList, setColumnNameList] = useState<String[]>([]);
  const [explanatoryVariables, setExplanatoryVariables] = useState<String[]>(
    []
  );

  useEffect(() => {
    let ignore = false;
    async function loadData() {
      const resGetTableNameList = await getTableNameList();
      for (const table of resGetTableNameList.result.tableNameList) {
        setTableNameList((preTableNameList) => [
          ...preTableNameList,
          { value: table, name: table },
        ]);
      }
      const resGetColumnNameList = await getColumnNameList(
        resGetTableNameList.result.tableNameList[0]
      );
      setColumnNameList(resGetColumnNameList.result.columnNameList);
    }
    loadData();
    return () => {
      ignore = true;
    };
  }, []);

  function handleItemClick(item: String) {
    setExplanatoryVariables((preExplanatoryVariable) => [
      ...preExplanatoryVariable,
      item,
    ]);
  }

  function changeTableName(event: ChangeEvent<HTMLSelectElement>) {}

  function executeAnalysis() {}

  return (
    <Modal
      isOpenModal={isLinearRegressionModal}
      modalTitle={t("LinearRegression.Title")}
      submitButtonName={t("LinearRegression.Execute")}
      submit={executeAnalysis}
      close={close}
      modalSize="max-w-2xl"
    >
      <div className="p-3">
        <div className="p-4 rounded-lg text-right text-lg content-center">
          {t("SaveFileModal.TableName")}
        </div>
        <Select
          optionList={tableNameList}
          selectFunc={(event: ChangeEvent<HTMLSelectElement>) =>
            changeTableName(event)
          }
        ></Select>
      </div>
      <div className="w-1/3 bg-gray-100 p-4">
        <h2 className="text-xl font-bold mb-4">候補リスト</h2>
        <ul className="space-y-2">
          {columnNameList.map((columnName, index) => (
            <li
              key={index}
              className="cursor-pointer p-2 bg-white shadow hover:bg-blue-100 rounded"
              onClick={() => handleItemClick(columnName)}
            >
              {columnName}
            </li>
          ))}
        </ul>
      </div>
      {/* 右側の詳細表示枠 */}
      <div className="w-2/3 bg-white p-4">
        <h2 className="text-xl font-bold mb-4">選択された項目</h2>
        {explanatoryVariables ? (
          <div className="p-4 bg-blue-50 shadow rounded">
            <p className="text-lg">{explanatoryVariables}</p>
          </div>
        ) : (
          <p className="text-gray-500">項目を選択してください。</p>
        )}
      </div>
    </Modal>
  );
}
