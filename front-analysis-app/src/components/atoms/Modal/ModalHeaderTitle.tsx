type ModalHeaderTitleProps = {
  children: string;
}

export const ModalHeaderTitle = ({ children }: ModalHeaderTitleProps) => {
  return (
    <h3 className="text-xl font-semibold text-gray-900 dark:text-white">
      {children}
    </h3>
  )
}
