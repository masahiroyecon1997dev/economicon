interface ViewHeaderProps {
  title: string;
  description: string;
}

export const ViewHeader = ({ title, description }: ViewHeaderProps) => {
  return (
    <header className="shrink-0">
      <h1 className="text-xl md:text-2xl font-bold text-black">{title}</h1>
      <p className="mt-1 md:mt-2 text-xs md:text-sm text-black/60">{description}</p>
    </header>
  );
};
