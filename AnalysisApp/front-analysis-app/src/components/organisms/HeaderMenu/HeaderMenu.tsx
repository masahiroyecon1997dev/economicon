import React, { useState, Dispatch, SetStateAction } from 'react';
import { useTranslation } from 'react-i18next';

import { TableInfosType } from '../../../types/stateTypes';

import { HeaderMenuDropdown } from '../../molecules/HeaderMenuDropdown/HeaderMenuDropdown';
import { ImportFileModal } from '../ImportFileModal/ImportFileModal';

type HeaderMenuProps = {
  setTableInfos: Dispatch<SetStateAction<TableInfosType>>;
}

export function HeaderMenu({setTableInfos}: HeaderMenuProps) {
  const { t } = useTranslation();
  const [isFileOpenModal, setIsFileOpenModal] = useState<boolean>(false);
  const fileDropdownListElement = [
    { dropdownListName: t('HeaderMenu.FileOpen'), dropdownListFunction: openSelectFileModal },
    { dropdownListName: t('HeaderMenu.FileSave'), dropdownListFunction: openSelectFileModal },
  ];

  function openSelectFileModal() {
    setIsFileOpenModal(true);
  }

  function closeSelectFileModal() {
    setIsFileOpenModal(false);
  }


  return (
    <>
      <div className="flex bg-gray-100 border-b border-gray-300 p-2 relative">
        <div className="relative">
          <HeaderMenuDropdown dropdownListElement={fileDropdownListElement}>{t('HeaderMenu.File')}</HeaderMenuDropdown>
        </div>
        <button className="px-4 py-2 hover:bg-gray-200">編集</button>
        <button className="px-4 py-2 hover:bg-gray-200">表示</button>
        <button className="px-4 py-2 hover:bg-gray-200">挿入</button>
        <button className="px-4 py-2 hover:bg-gray-200">書式</button>
        <button className="px-4 py-2 hover:bg-gray-200">データ</button>
        <button className="px-4 py-2 hover:bg-gray-200">ツール</button>
        <button className="px-4 py-2 hover:bg-gray-200">ヘルプ</button>
      </div>
      <ImportFileModal isFileOpenModal={isFileOpenModal} close={closeSelectFileModal} setTableInfos={setTableInfos}/>
    </>
  );
}
