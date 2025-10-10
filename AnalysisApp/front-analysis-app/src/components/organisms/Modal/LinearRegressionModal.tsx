import type { ChangeEvent } from "react";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import { getColumnInfoList, getTableNameList, linearRegression } from "../../../function/restApis";
import type { ReqLinearRegressionType } from "../../../types/apiTypes";
import type { SelectListType } from "../../../types/commonTypes";
import { Select } from "../../molecules/InputField/Select";
import { Modal } from "../../molecules/Modal/Modal";

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
  const [selectedTableName, setSelectedTableName] = useState<string>("");
  const [columnNameList, setColumnNameList] = useState<SelectListType>([]);
  const [dependentVariable, setDependentVariable] = useState<string>("");
  const [explanatoryVariables, setExplanatoryVariables] = useState<string[]>(
    []
  );
  const [isResultModal, setIsReusltModal] = useState<boolean>(false);
  const [result, setResult] = useState<string>("");

  useEffect(() => {
    let ignore = false;
    async function loadData() {
      const resGetTableNameList = await getTableNameList();
      const resGetColumnNameList = await getColumnInfoList(
        resGetTableNameList.result.tableNameList[0]
      );
      if (!ignore) {
        for (const table of resGetTableNameList.result.tableNameList) {
          setTableNameList((preTableNameList) => [
            ...preTableNameList,
            { value: table, name: table },
          ]);
        }
        setSelectedTableName(resGetTableNameList.result.tableNameList[0]);
        for (const column of resGetColumnNameList.result.columnInfoList) {
          setColumnNameList((preColumnNameList) => [
            ...preColumnNameList,
            { value: column.name, name: column.name },
          ]);
        }
        setDependentVariable(resGetColumnNameList.result.columnInfoList[0].name);
      }
    }
    if (isLinearRegressionModal) {
      loadData();
    }
    return () => {
      ignore = true;
    };
  }, [isLinearRegressionModal]);

  function handleItemClick(item: string) {
    setExplanatoryVariables((preExplanatoryVariable) => [
      ...preExplanatoryVariable,
      item,
    ]);
  }

  function changeTableName(event: ChangeEvent<HTMLSelectElement>) {
    setSelectedTableName(event.target.value);
  }

  function changeDependentVariable(event: ChangeEvent<HTMLSelectElement>) {
    setDependentVariable(event.target.value);
  }

  async function executeAnalysis() {
    const reqLinearRegression: ReqLinearRegressionType = {
      tableName: selectedTableName,
      dependentVariable: dependentVariable,
      explanatoryVariables: explanatoryVariables,
    };
    console.log(reqLinearRegression);
    const resLinearRegression = await linearRegression(reqLinearRegression);
    console.log(resLinearRegression.result.regressionResult);
    setResult(resLinearRegression.result.regressionResult);
    openResultModal();
  }

  function openResultModal() {
    setIsReusltModal(true);
  }

  function closeResultModal() {
    setIsReusltModal(false);
  }

  return (
    <>
      <Modal
        isOpenModal={isLinearRegressionModal && !isResultModal}
        modalTitle={t("LinearRegressionModal.Title")}
        submitButtonName={t("LinearRegressionModal.Execute")}
        submit={executeAnalysis}
        close={close}
        modalSize="max-w-2xl"
      >
        <div className="p-3">
          <div className="grid grid-cols-3 gap-4 leading-6">
            <div className="py-1 px-4 rounded-lg text-right text-lg content-center">
              {t("LinearRegressionModal.TableName")}
            </div>
            <Select
              optionList={tableNameList}
              selectFunc={(event: ChangeEvent<HTMLSelectElement>) =>
                changeTableName(event)
              }
            ></Select>
          </div>
        </div>
        <div className="p-3">
          <div className="grid grid-cols-3 gap-4 leading-6">
            <div className="py-1 px-4 rounded-lg text-right text-lg content-center">
              {t("LinearRegressionModal.DependentVariable")}
            </div>
            <Select
              optionList={columnNameList}
              selectFunc={(event: ChangeEvent<HTMLSelectElement>) =>
                changeDependentVariable(event)
              }
            ></Select>
          </div>
        </div>
        <div className="flex">
          <div className="w-1/2 bg-gray-100 p-4">
            <h2 className="text-xl font-bold mb-4">
              {t("LinearRegressionModal.ColumnName")}
            </h2>
            <ul className="space-y-2">
              {columnNameList.map((columnName, index) => (
                <li
                  key={index}
                  className="cursor-pointer p-2 bg-white shadow hover:bg-blue-100 rounded"
                  onClick={() => handleItemClick(columnName.name)}
                >
                  {columnName.name}
                </li>
              ))}
            </ul>
          </div>
          <div className="w-1/2 bg-white p-4">
            <h2 className="text-xl font-bold mb-4">
              {t("LinearRegressionModal.ExplanatoryVariable")}
            </h2>
            {explanatoryVariables.map((explanatoryVariable, index) => (
              <div key={index} className="p-2 bg-blue-50 shadow">
                <p className="text">{explanatoryVariable}</p>
              </div>
            ))}
          </div>
        </div>
      </Modal>
      <Modal
        isOpenModal={isResultModal}
        modalTitle={t("LinearRegressionModal.Title")}
        submitButtonName=""
        submit={executeAnalysis}
        close={closeResultModal}
        modalSize="max-w-3xl"
      >
        <pre className="whitespace-pre-wrap text-gray-800 text-center">
          {result}
        </pre>
      </Modal>
    </>
  );
}
