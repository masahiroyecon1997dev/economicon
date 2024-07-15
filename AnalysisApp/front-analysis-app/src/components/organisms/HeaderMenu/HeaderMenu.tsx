import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { HeaderMenuButton } from '../../atoms/Button/button';

function HeaderMenu() {
  const { t } = useTranslation()

  function selectFile() {
    const a = 1 + 1;
    console.log("aaaa")
  }

  const [openDropdown, setOpenDropdown] = useState<string | null>(null);

  const toggleDropdown = (menu: string | null) => {
    if (openDropdown === menu) {
      setOpenDropdown(null);
    } else {
      setOpenDropdown(menu);
    }
  };


  return (
    <div className="flex bg-gray-100 border-b border-gray-300 p-2 relative">
      <div className="relative">
        <HeaderMenuButton clickEvent={() => selectFile()}>{t('HeaderMenu.File')}</HeaderMenuButton>
        {openDropdown === 'file' && (
          <div className="absolute bg-white shadow-md border mt-1 rounded-md">
            <button className="block px-4 py-2 hover:bg-gray-200 w-full text-left">開く</button>
            <button className="block px-4 py-2 hover:bg-gray-200 w-full text-left">保存</button>
          </div>
        )}
      </div>
      <button className="px-4 py-2 hover:bg-gray-200">編集</button>
      <button className="px-4 py-2 hover:bg-gray-200">表示</button>
      <button className="px-4 py-2 hover:bg-gray-200">挿入</button>
      <button className="px-4 py-2 hover:bg-gray-200">書式</button>
      <button className="px-4 py-2 hover:bg-gray-200">データ</button>
      <button className="px-4 py-2 hover:bg-gray-200">ツール</button>
      <button className="px-4 py-2 hover:bg-gray-200">ヘルプ</button>
    </div>
  );
}

export default HeaderMenu;
