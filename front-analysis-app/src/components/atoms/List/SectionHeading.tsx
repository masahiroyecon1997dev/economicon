type SectionHeadingProps = {
  title: string;
};

export const SectionHeading = ({ title }: SectionHeadingProps) => {
  return (
    <h2 className="text-lg font-semibold mb-4">
      {title}
    </h2>
  );
}
