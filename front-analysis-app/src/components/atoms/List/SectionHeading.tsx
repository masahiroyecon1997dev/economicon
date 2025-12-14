type SectionHeadingProps = {
  title: string;
};

export const SectionHeading = ({ title }: SectionHeadingProps) => {
  return (
    <h2 className="px-4 pb-4 text-lg font-semibold">
      {title}
    </h2>
  );
}
