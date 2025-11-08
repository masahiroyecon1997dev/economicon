
import { useTranslation } from 'react-i18next';
import { Modal } from '../../molecules/Modal/Modal';

type CalculateProps = {
  isCalculateModal: boolean;
  close: () => void;
};

export const Calculate = ({ isCalculateModal, close }: CalculateProps) => {
  const { t } = useTranslation();

  const calculate = () => { };

  return (
    <Modal
      isOpenModal={isCalculateModal}
      modalTitle={t('CalculateModal.Title')}
      submitButtonName={t('CalculateModal.Execute')}
      submit={calculate}
      close={close}
      modalSize="max-w-2xl"
    >
      <div className="grid grid-cols-3 gap-4 leading-6"></div>
    </Modal>
  );
}
