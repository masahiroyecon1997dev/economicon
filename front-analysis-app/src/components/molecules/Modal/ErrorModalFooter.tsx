import { useTranslation } from 'react-i18next';

import { SubmitButton } from '../../atoms/Button/SubmitButton';

type ErrorModalFooterProps = {
  onOk: () => void;
};

export function ErrorModalFooter({ onOk }: ErrorModalFooterProps) {
  const { t } = useTranslation();

  return (
    <div className="flex items-center justify-end p-4 md:p-5 border-t border-gray-200 rounded-b dark:border-gray-600">
      <SubmitButton submit={onOk}>{t('Common.OK')}</SubmitButton>
    </div>
  );
}
