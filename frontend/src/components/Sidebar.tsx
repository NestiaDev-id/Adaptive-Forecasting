import { NavLink } from "react-router-dom";
import { Globe, FlaskConical, Sparkles } from "lucide-react";
import { ThemeToggle } from "@/components/ThemeToggle";
import { motion } from "motion/react";

const NAV_ITEMS = [
  {
    to: "/",
    icon: Globe,
    label: "Global Monitor",
    description: "Live cuaca & event",
  },
  {
    to: "/sandbox",
    icon: FlaskConical,
    label: "Research Sandbox",
    description: "Upload & prediksi",
  },
];

export function Sidebar() {
  return (
    <motion.aside
      className="fixed left-0 top-0 bottom-0 w-64 bg-card/80 backdrop-blur-xl border-r border-border/50 z-50 flex flex-col"
      initial={{ x: -264 }}
      animate={{ x: 0 }}
      transition={{ duration: 0.4, ease: [0.25, 0.46, 0.45, 0.94] }}
    >
      {/* Logo */}
      <div className="p-5 border-b border-border/50">
        <div className="flex items-center gap-3">
          <motion.div
            className="h-9 w-9 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center shadow-lg shadow-blue-500/20"
            whileHover={{ rotate: 15, scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
            transition={{ type: "spring", stiffness: 400 }}
          >
            <Sparkles className="h-5 w-5 text-white" />
          </motion.div>
          <div>
            <h1 className="text-sm font-bold text-foreground leading-tight">
              Adaptive Forecasting
            </h1>
            <p className="text-[10px] text-muted-foreground">Engine v1.0</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-3 space-y-1">
        {NAV_ITEMS.map((item, i) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === "/"}
            className={({ isActive }) =>
              `group flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all duration-200 ${
                isActive
                  ? "bg-primary/10 text-primary font-medium shadow-sm"
                  : "text-muted-foreground hover:text-foreground hover:bg-secondary/50"
              }`
            }
          >
            {({ isActive }) => (
              <motion.div
                className="flex items-center gap-3 w-full"
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.2 + i * 0.1 }}
              >
                <item.icon
                  className={`h-4.5 w-4.5 transition-colors ${
                    isActive ? "text-primary" : "text-muted-foreground group-hover:text-foreground"
                  }`}
                />
                <div>
                  <div className="leading-tight">{item.label}</div>
                  <div className="text-[10px] text-muted-foreground leading-tight">
                    {item.description}
                  </div>
                </div>
                {isActive && (
                  <motion.div
                    className="ml-auto h-1.5 w-1.5 rounded-full bg-primary"
                    layoutId="active-dot"
                    transition={{ type: "spring", stiffness: 300 }}
                  />
                )}
              </motion.div>
            )}
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-border/50 flex items-center justify-between">
        <span className="text-[10px] text-muted-foreground">
          BMKG · NASA EONET
        </span>
        <ThemeToggle />
      </div>
    </motion.aside>
  );
}
