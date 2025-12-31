type SectionHeadingProps = {
  title: string;
};

export const SectionHeading = ({ title }: SectionHeadingProps) => {
  return (
    <h2 className="px-4 pb-4 font-semibold">
      {title}
    </h2>
  );
}
