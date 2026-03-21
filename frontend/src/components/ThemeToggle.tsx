import { useTheme } from "@/lib/theme";
import { Sun, Moon, Monitor, Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { motion, AnimatePresence } from "motion/react";

const modes = [
  { value: "light" as const, icon: Sun, label: "Light", desc: "Mode terang" },
  { value: "dark" as const, icon: Moon, label: "Dark", desc: "Mode gelap" },
  { value: "system" as const, icon: Monitor, label: "System", desc: "Ikuti sistem" },
];

export function ThemeToggle() {
  const { theme, setTheme, resolved } = useTheme();

  const CurrentIcon = resolved === "dark" ? Moon : Sun;

  return (
    <DropdownMenu>
      <DropdownMenuTrigger
        render={<Button variant="ghost" size="sm" className="h-8 w-8 p-0 relative overflow-hidden" />}
      >
        <AnimatePresence mode="wait">
          <motion.div
            key={resolved}
            initial={{ y: -12, opacity: 0, rotate: -90 }}
            animate={{ y: 0, opacity: 1, rotate: 0 }}
            exit={{ y: 12, opacity: 0, rotate: 90 }}
            transition={{ duration: 0.2, ease: "easeInOut" }}
          >
            <CurrentIcon className="h-4 w-4" />
          </motion.div>
        </AnimatePresence>
        <span className="sr-only">Toggle theme</span>
      </DropdownMenuTrigger>

      <DropdownMenuContent align="end" className="w-44">
        {modes.map((mode) => {
          const Icon = mode.icon;
          const isActive = theme === mode.value;

          return (
            <DropdownMenuItem
              key={mode.value}
              onClick={() => setTheme(mode.value)}
              className="flex items-center gap-2 cursor-pointer"
            >
              <motion.div
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.95 }}
                className="flex items-center gap-2 flex-1"
              >
                <Icon className={`h-4 w-4 ${isActive ? "text-blue-500" : "text-muted-foreground"}`} />
                <div className="flex flex-col">
                  <span className={`text-sm ${isActive ? "font-medium" : ""}`}>
                    {mode.label}
                  </span>
                  <span className="text-[10px] text-muted-foreground">
                    {mode.desc}
                  </span>
                </div>
              </motion.div>
              {isActive && (
                <motion.div
                  initial={{ scale: 0, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  transition={{ type: "spring", stiffness: 500, damping: 25 }}
                >
                  <Check className="h-3.5 w-3.5 text-blue-500" />
                </motion.div>
              )}
            </DropdownMenuItem>
          );
        })}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
