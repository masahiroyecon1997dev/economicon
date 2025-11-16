type SubmitButtonProps = {
  children: string;
  submit: () => void;
};

export const SubmitButton = ({ children, submit }: SubmitButtonProps) => {
  return (
    <button
      onClick={submit}
      className="rounded-md bg-brand-accent px-6 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-brand-accent/90 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
    >
      {children}
    </button>
  );
}
