import { ModalCloseButton } from '../../atoms/Button/ModalCloseButton';
import { ModalHeaderTitle } from '../../atoms/Modal/ModalHeaderTitle';

type ModalHeaderProps = {
  children: string;
  close: () => void;
};

export function ModalHeader({ children, close }: ModalHeaderProps) {
  return (
    <div className="flex items-center justify-between p-4 md:p-5 border-b border-b-gray-300 rounded-t">
      <ModalHeaderTitle>{children}</ModalHeaderTitle>
      <ModalCloseButton close={() => close()}></ModalCloseButton>
    </div>
  );
}
