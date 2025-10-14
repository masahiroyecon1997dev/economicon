import { useTranslation } from 'react-i18next';

import { CancelButton } from '../../atoms/Button/CancelButton';
import { SubmitButton } from '../../atoms/Button/SubmitButton';

type ModalFooterProps = {
  children: string;
  close: () => void;
  submit: () => void;
};

export function ModalFooter({ children, close, submit }: ModalFooterProps) {
  const { t } = useTranslation();

  return (
    <div className="flex items-center justify-end p-4 md:p-5 border-t border-gray-200 rounded-b dark:border-gray-600">
      <CancelButton cancel={() => close()}>{t('Common.Cancel')}</CancelButton>
      {children !== '' ? <SubmitButton submit={() => submit()}>{children}</SubmitButton> : null}
    </div>
  );
}
