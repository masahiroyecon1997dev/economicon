type SectionHeadingProps = {
  title: string;
  className?: string;
};

export function SectionHeading({ title, className = "" }: SectionHeadingProps) {
  return (
    <h2 className={`text-lg font-semibold mb-4 text-brand-primary ${className}`}>
      {title}
    </h2>
  );
}
