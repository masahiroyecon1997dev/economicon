type SubmitButtonProps = {
  children: string;
  submit: () => void;
};

export function SubmitButton({ children, submit }: SubmitButtonProps) {
  return (
    <button
      className="w-28 h-9 px-5 py-2.5 ms-3
            text-center text-xs text-white font-medium
            rounded-full focus:ring-4 focus:outline-none border
            bg-indigo-600 border-indigo-700
            hover:bg-indigo-800
            focus:ring-blue-300
            dark:bg-indigo-600 dark:hover:bg-indigo-600 dark:focus:ring-indigo-800"
      onClick={() => submit()}
    >
      {children}
    </button>
  );
}
