import { useTranslation } from 'react-i18next';

import { Button } from '../../atoms/button/button';

type ModalFooterProps = {
  children: string;
  close: () => void;
  submit: () => void;
};

export function ModalFooter({ children, close, submit }: ModalFooterProps) {
  const { t } = useTranslation();

  return (
    <div className="flex items-center justify-end p-4 md:p-5 border-t border-gray-200 rounded-b">
      <Button onClick={() => close()} variant="cancel">{t('Common.Cancel')}</Button>
      {children !== '' ? <Button onClick={() => submit()} variant="submit">{children}</Button> : null}
    </div>
  );
}
