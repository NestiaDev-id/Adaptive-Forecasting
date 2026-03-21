import { createContext, useContext, useEffect, useState, type ReactNode } from "react";

type Theme = "light" | "dark" | "system";

interface ThemeCtx {
  theme: Theme;
  setTheme: (t: Theme) => void;
  resolved: "light" | "dark";
}

const ThemeContext = createContext<ThemeCtx>({
  theme: "system",
  setTheme: () => {},
  resolved: "dark",
});

export function useTheme() {
  return useContext(ThemeContext);
}

function getSystemTheme(): "light" | "dark" {
  return window.matchMedia("(prefers-color-scheme: dark)").matches
    ? "dark"
    : "light";
}

function resolve(theme: Theme): "light" | "dark" {
  return theme === "system" ? getSystemTheme() : theme;
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setThemeState] = useState<Theme>(() => {
    const saved = localStorage.getItem("afe-theme") as Theme | null;
    return saved ?? "system";
  });

  const [resolved, setResolved] = useState<"light" | "dark">(() =>
    resolve(theme),
  );

  const setTheme = (t: Theme) => {
    localStorage.setItem("afe-theme", t);
    setThemeState(t);
  };

  useEffect(() => {
    const r = resolve(theme);
    setResolved(r);
    document.documentElement.classList.toggle("dark", r === "dark");
  }, [theme]);

  // listen for system preference changes
  useEffect(() => {
    if (theme !== "system") return;
    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    const handler = () => {
      const r = getSystemTheme();
      setResolved(r);
      document.documentElement.classList.toggle("dark", r === "dark");
    };
    mq.addEventListener("change", handler);
    return () => mq.removeEventListener("change", handler);
  }, [theme]);

  return (
    <ThemeContext value={{ theme, setTheme, resolved }}>
      {children}
    </ThemeContext>
  );
}
