import React, { Dispatch, SetStateAction } from 'react';
import { useTranslation } from 'react-i18next';
import { getTableInfo } from '../../../function/internalFunctions';
import { TableInfosType, TableListType } from '../../../types/stateTypes';

type LeftSideMenuProps = {
  tableInfos: TableInfosType;
  setTableInfos: Dispatch<SetStateAction<TableInfosType>>;
  tableList: TableListType;
};

export function LeftSideMenu({ tableInfos, setTableInfos, tableList }: LeftSideMenuProps) {
  const { t } = useTranslation();

  async function clickTableName(tableName: string) {
    const sameTableNameInfos = tableInfos.filter(tableInfo => tableInfo.tableName === tableName);
    if (sameTableNameInfos.length > 0) {
      setTableInfos(preTableInfos =>
        preTableInfos.map(tableInfo => {
          if (tableInfo.tableName === tableName) {
            return { ...tableInfo, isActive: true };
          } else {
            return { ...tableInfo, isActive: false };
          }
        })
      );
    } else {
      const tableInfo = await getTableInfo(tableName);
      setTableInfos(preTableInfos => [
        ...preTableInfos.map(info => ({ ...info, isActive: false })),
        tableInfo,
      ]);
    }
  }

  const getActiveTableName = () => {
    const activeTable = tableInfos.find(tableInfo => tableInfo.isActive);
    return activeTable?.tableName || null;
  };

  const activeTableName = getActiveTableName();

  return (
    <aside className="w-64 shrink-0 border-r border-gray-200 bg-gray-50 p-4">
      <h2 className="text-lg font-semibold mb-4 text-gray-900">{t('Common.Table')}</h2>
      <nav className="flex flex-col gap-1">
        {tableList.map((table, index) => (
          <a
            key={index}
            className={`flex items-center justify-between rounded-md px-3 py-2 transition-colors cursor-pointer ${
              activeTableName === table
                ? 'bg-gray-200 text-gray-900 font-medium'
                : 'hover:bg-gray-100 text-gray-600 hover:text-gray-900'
            }`}
            onClick={() => clickTableName(table)}
          >
            <span>{table}</span>
            <svg
              className="size-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path d="M9 5l7 7-7 7" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" />
            </svg>
          </a>
        ))}
      </nav>
    </aside>
  );
}
