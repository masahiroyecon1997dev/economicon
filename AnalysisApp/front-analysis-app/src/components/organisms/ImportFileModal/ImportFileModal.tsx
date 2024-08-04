import React, { useState, ChangeEvent } from "react";
import { useTranslation } from 'react-i18next';

import { IconContext } from "react-icons";
import { FaFileAlt } from "react-icons/fa";

import { importCsv } from "../../../functiom/restApis";

import { ModalHeader } from "../../molecules/ModalHeader/ModalHeader";
import { ModalFooter } from "../../molecules/ModalFooter/ModalFooter";

type ImportFileModalProps = {
  isFileOpenModal: boolean;
  close: () => void;
}

export function ImportFileModal({ isFileOpenModal, close }: ImportFileModalProps) {
  const { t } = useTranslation();
  const [file, setFile] = useState<File>();

  function changeFileInput(event: ChangeEvent<HTMLInputElement>) {
    const files = event.target.files;
    if (!files || files?.length === 0) return;
    setFile(files[0]);
    console.log(files)
  }


  async function importFile() {
    if (!file) return;
    await importCsv(file);
    close();
  }


  if (isFileOpenModal) {
    return (
      <div className="fixed inset-0 z-50 flex justify-center items-center overflow-y-auto overflow-x-hidden w-full md:inset-0">
        <div className="relative p-4 w-full max-w-2xl max-h-full">
          <div className="relative bg-white rounded-lg shadow dark:bg-gray-700">
            <ModalHeader close={() => close()}>{t('ImportFileModal.Title')}</ModalHeader>
              <div className="w-full py-9 bg-gray-50 rounded-2xl border border-gray-300 gap-3 grid border-dashed">
                {(file) ?
                  <div>
                    <div className="grid gap-1">
                      <div className="mx-auto">
                        <IconContext.Provider value={{color: "#4f46e5", size: "40px"}}>
                          <FaFileAlt />
                        </IconContext.Provider>
                      </div>
                    </div>
                    <div className="grid gap-2">
                      <h4 className="text-center text-gray-900 text-sm font-medium leading-snug">{file.name}</h4>
                      <h2 className="text-center text-gray-400 text-xs leading-4">{file.size/1000/1000}MB</h2>
                        <div className="flex items-center justify-center">
                          <label>
                            <input type="file" accept=".csv" hidden onChange={(event) => changeFileInput(event)} />
                            <div className="flex w-28 h-9 px-2 flex-col bg-indigo-600 rounded-full shadow text-white text-xs font-semibold leading-4 items-center justify-center cursor-pointer focus:outline-none">{t("ImportFileModal.OtherChooseFile")}</div>
                          </label>
                        </div>
                    </div>
                  </div>
                :
                  <div>
                    <div className="grid gap-1">
                      <div className="mx-auto">
                        <IconContext.Provider value={{color: "#4f46e5", size: "40px"}}>
                          <FaFileAlt />
                        </IconContext.Provider>
                      </div>
                      <h2 className="text-center text-gray-400 text-xs leading-4">{t("ImportFileModal.Notation")}</h2>
                    </div>
                    <div className="grid gap-2">
                      <h4 className="text-center text-gray-900 text-sm font-medium leading-snug">{t("ImportFileModal.Information")}</h4>
                        <div className="flex items-center justify-center">
                          <label>
                            <input type="file" hidden onChange={(event) => changeFileInput(event)} />
                            <div className="flex w-28 h-9 px-2 flex-col bg-indigo-600 rounded-full shadow text-white text-xs font-semibold leading-4 items-center justify-center cursor-pointer focus:outline-none">{t("ImportFileModal.ChooseFile")}</div>
                          </label>
                        </div>
                    </div>
                  </div>
                }
              </div>
            <ModalFooter close={() => close()} submit={() => importFile()}>{t("ImportFileModal.OpenFile")}</ModalFooter>
          </div>
        </div>
      </div>
    );
  } else {
    return null;
  }
};
