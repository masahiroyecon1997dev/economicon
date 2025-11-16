import { useState } from "react";
import { getColumnList } from "../../../function/restApis";
import { useTableListStore } from "../../../stores/useTableListStore";
import type { ColumnType } from "../../../types/commonTypes";

export const LinearRegressionFormView = () => {
  const tableList = useTableListStore((state) => state.tableList);
  const [columnList, setColumnList] = useState<ColumnType[]>([]);
  const [selectedTableName, setSelectedTableName] = useState<string>("");
  const [dependentVariable, setDependentVariable] = useState<string>("");
  const [independentVariables, setIndependentVariables] = useState<string[]>([]);



  const handleTableChange = async (event: React.ChangeEvent<HTMLSelectElement>) => {
    const selectedTable = event.target.value;
    setSelectedTableName(selectedTable);
    const resColumnList = await getColumnList(selectedTable);
    setColumnList(resColumnList.result.columnInfoList);
  };



  return (
    <div className="mx-auto max-w-4xl">
      <div className="mb-8 flex flex-wrap items-center justify-between gap-4">
        <div className="flex flex-col gap-1">
          <p className="text-3xl font-bold text-text-heading">Create New Regression Analysis</p>
          <p className="text-base font-normal text-text-main/80">Select the table and variables for the analysis.</p>
        </div>
      </div>
      <div className="flex flex-col gap-8">
        <div className="rounded-xl border border-border-color bg-white p-6 shadow-sm">
          <h2 className="mb-4 text-xl font-bold leading-tight text-text-heading">1. Select Data Table</h2>
          <div>
            <label className="mb-2 block text-sm font-medium text-text-main" htmlFor="data-table">Data Table</label>
            <div className="relative">
              {/* <span
                className="material-symbols-outlined pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-text-main/50">table</span> */}
              <select
                className="w-full rounded-lg border-border-color py-2.5 pl-10 pr-4 text-text-main shadow-sm focus:border-accent focus:ring-accent"
                id="data-table"
                value={selectedTableName}
                onChange={handleTableChange}
              >
                <option value="" disabled>Select a table</option>
                {tableList.map((table, index) => (
                  <option key={index} value={table}>{table}</option>
                ))}
              </select>
            </div>
          </div>
        </div>
        <div className="rounded-xl border border-border-color bg-white p-6 shadow-sm">
          <h2 className="mb-4 text-xl font-bold leading-tight text-text-heading">2. Select Variables</h2>
          <div className="grid grid-cols-1 gap-8 md:grid-cols-2">
            <div>
              <label className="mb-2 block text-sm font-medium text-text-main">Dependent Variable (Y)</label>
              <p className="mb-3 text-sm text-text-main/60">Select one variable you want to predict.</p>
              <div className="h-64 overflow-y-auto rounded-lg border border-border-color bg-secondary p-2">
                <ul className="flex flex-col gap-1">
                  {columnList.map((column, index) => (
                    <li key={index}>
                      <label
                        className="flex w-full cursor-pointer items-center gap-3 rounded-md p-2 hover:bg-white">
                        <input className="h-4 w-4 border-gray-300 text-accent focus:ring-accent" name="dependent-variable" type="radio" />
                        <span>{column.name}</span>
                      </label>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
            <div>
              <label className="mb-2 block text-sm font-medium text-text-main">Independent Variables (X)</label>
              <p className="mb-3 text-sm text-text-main/60">Select one or more variables to use for prediction.</p>
              <div className="h-64 overflow-y-auto rounded-lg border border-border-color bg-secondary p-2">
                <ul className="flex flex-col gap-1">
                  {columnList.map((column, index) => (
                    <li key={index}>
                      <label
                        className="flex w-full cursor-pointer items-center gap-3 rounded-md p-2 hover:bg-white">
                        <input className="h-4 w-4 rounded border-gray-300 text-accent focus:ring-accent" type="checkbox" />
                        <span>{column.name}</span>
                      </label>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
          <div className="mt-6">
            <label className="mb-2 block text-sm font-medium text-text-main">Selected Independent Variables:</label>
            <div className="flex flex-wrap gap-2 rounded-lg border border-border-color bg-secondary p-3 min-h-[44px]">
              {independentVariables.map((variable, index) => (
                <span
                  className="flex items-center gap-1.5 rounded-full bg-accent/20 px-3 py-1 text-sm font-medium text-accent">
                  {variable}
                  <button
                    className="text-accent/70 hover:text-accent">
                    <span
                      className="material-symbols-outlined !text-base">
                      close
                    </span>
                  </button>
                </span>
              ))}
            </div>
          </div>
        </div>
        <div className="flex justify-end">
          <button
            className="flex items-center justify-center gap-2 rounded-lg bg-accent px-6 py-3 text-base font-bold text-white shadow-sm transition-colors hover:bg-[#2980b9]">
            <span className="material-symbols-outlined">rocket_launch</span>
            Run Analysis
          </button>
        </div>
      </div>
    </div>
  );
}
