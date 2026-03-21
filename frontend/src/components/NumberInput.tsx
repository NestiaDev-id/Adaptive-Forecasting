import { useCallback } from "react";
import { ChevronUp, ChevronDown } from "lucide-react";
import { Input } from "@/components/ui/input";
import { motion } from "motion/react";

interface Props {
  value: number;
  onChange: (v: number) => void;
  min?: number;
  max?: number;
  step?: number;
  label?: string;
  className?: string;
}

export function NumberInput({
  value,
  onChange,
  min = 0,
  max = 999,
  step = 1,
  label,
  className = "",
}: Props) {
  const increment = useCallback(() => {
    onChange(Math.min(value + step, max));
  }, [value, step, max, onChange]);

  const decrement = useCallback(() => {
    onChange(Math.max(value - step, min));
  }, [value, step, min, onChange]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const v = parseInt(e.target.value, 10);
    if (!isNaN(v)) {
      onChange(Math.max(min, Math.min(max, v)));
    }
  };

  return (
    <div className={className}>
      {label && (
        <label className="text-[10px] text-muted-foreground block mb-1">
          {label}
        </label>
      )}
      <div className="relative group">
        <Input
          type="number"
          value={value}
          onChange={handleChange}
          min={min}
          max={max}
          className="pr-7 text-xs font-mono h-8 bg-secondary/30 border-border/50 text-foreground"
        />

        {/* Custom spin buttons */}
        <div className="absolute right-0 top-0 bottom-0 w-6 flex flex-col border-l border-border/30 opacity-0 group-hover:opacity-100 group-focus-within:opacity-100 transition-opacity duration-200">
          <motion.button
            type="button"
            onClick={increment}
            className="flex-1 flex items-center justify-center rounded-tr-lg hover:bg-accent transition-colors text-muted-foreground hover:text-foreground"
            whileTap={{ scale: 0.85 }}
            tabIndex={-1}
          >
            <ChevronUp className="h-3 w-3" />
          </motion.button>
          <div className="h-px bg-border/30" />
          <motion.button
            type="button"
            onClick={decrement}
            className="flex-1 flex items-center justify-center rounded-br-lg hover:bg-accent transition-colors text-muted-foreground hover:text-foreground"
            whileTap={{ scale: 0.85 }}
            tabIndex={-1}
          >
            <ChevronDown className="h-3 w-3" />
          </motion.button>
        </div>
      </div>
    </div>
  );
}
