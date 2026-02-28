type SectionHeadingProps = {
  title: string;
};

export const SectionHeading = ({ title }: SectionHeadingProps) => {
  return <h2 className="px-4 pt-3 pb-2 font-semibold">{title}</h2>;
};
