type SimParamSliderProps = {
  label: string;
  min: number;
  max: number;
  step: number;
  value: number;
  onChange: (value: number) => void;
  /** input[type=range] の data-testid */
  sliderTestId?: string;
  /** 現在値スパンの data-testid */
  valueTestId?: string;
};

export const SimParamSlider = ({
  label,
  min,
  max,
  step,
  value,
  onChange,
  sliderTestId,
  valueTestId,
}: SimParamSliderProps) => {
  return (
    <div className="flex flex-col gap-1">
      <div className="flex justify-between text-sm">
        <span className="text-text-main/80">{label}</span>
        <span className="font-mono text-brand-accent" data-testid={valueTestId}>
          {value}
        </span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        className="w-full accent-brand-accent"
        data-testid={sliderTestId}
        onChange={(e) => onChange(parseFloat(e.target.value))}
      />
      <div className="flex justify-between text-xs text-text-main/40">
        <span>{min}</span>
        <span>{max}</span>
      </div>
    </div>
  );
};
