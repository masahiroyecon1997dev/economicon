import React, { useState, Dispatch, SetStateAction } from 'react';
import { useTranslation } from 'react-i18next';

import { TableInfosType } from '../../../types/stateTypes';

import { HeaderMenuDropdown } from '../../molecules/HeaderMenuDropdown/HeaderMenuDropdown';
import { ImportFileModal } from '../ImportFileModal/ImportFileModal';
import { SaveFileModal } from '../SaveFileModal/SaveFileModal';

type HeaderMenuProps = {
  setTableInfos: Dispatch<SetStateAction<TableInfosType>>;
}

export function HeaderMenu({setTableInfos}: HeaderMenuProps) {
  const { t } = useTranslation();
  const [isImportFileModal, setIsImportFileModal] = useState<boolean>(false);
  const [isSaveFileModal, setIsSaveFileModal] = useState<boolean>(false);

  const fileDropdownListElement = [
    { dropdownListName: t('HeaderMenu.FileOpen'), dropdownListFunction: openSelectFileModal },
    { dropdownListName: t('HeaderMenu.FileSave'), dropdownListFunction: openSaveFileModal },
  ];
  const dataGenerationDropdownListElement = [
    { dropdownListName: t('HeaderMenu.DataGeneration'), dropdownListFunction: openSelectFileModal },
    { dropdownListName: t('HeaderMenu.SampleData'), dropdownListFunction: openSelectFileModal },
  ];

  function openSelectFileModal() {
    setIsImportFileModal(true);
  }

  function closeSelectFileModal() {
    setIsImportFileModal(false);
  }

  function openSaveFileModal() {
    setIsSaveFileModal(true);
  }

  function closeSaveFileModal() {
    setIsSaveFileModal(false);
  }




  return (
    <>
      <div className="flex bg-gray-100 border-b border-gray-300 relative">
        <div className="relative">
          <HeaderMenuDropdown dropdownListElement={fileDropdownListElement}>{t('HeaderMenu.File')}</HeaderMenuDropdown>
        </div>
        <div className="relative">
          <HeaderMenuDropdown dropdownListElement={dataGenerationDropdownListElement}>{t('HeaderMenu.Data')}</HeaderMenuDropdown>
        </div>
        <button className="px-4 py-2 hover:bg-gray-200">編集</button>
        <button className="px-4 py-2 hover:bg-gray-200">表示</button>
        <button className="px-4 py-2 hover:bg-gray-200">挿入</button>
        <button className="px-4 py-2 hover:bg-gray-200">書式</button>
        <button className="px-4 py-2 hover:bg-gray-200">データ</button>
        <button className="px-4 py-2 hover:bg-gray-200">ツール</button>
        <button className="px-4 py-2 hover:bg-gray-200">ヘルプ</button>
      </div>
      <ImportFileModal isImportFileModal={isImportFileModal} close={closeSelectFileModal} setTableInfos={setTableInfos} />
      <SaveFileModal isSaveFileModal={isSaveFileModal} close={closeSaveFileModal} />
    </>
  );
}
