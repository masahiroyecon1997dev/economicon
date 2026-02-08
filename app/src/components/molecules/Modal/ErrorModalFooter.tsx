import { useTranslation } from 'react-i18next';

import { Button } from '../../atoms/Button/Button';

type ErrorModalFooterProps = {
  onOk: () => void;
};

export function ErrorModalFooter({ onOk }: ErrorModalFooterProps) {
  const { t } = useTranslation();

  return (
    <div className="flex items-center justify-end p-4 md:p-5 border-t border-gray-200 rounded-b">
      <Button onClick={onOk} variant="primary">{t('Common.OK')}</Button>
    </div>
  );
}
