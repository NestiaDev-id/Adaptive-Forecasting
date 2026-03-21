import { Button } from "@/components/ui/button";
import { Download, FileSpreadsheet, FileText } from "lucide-react";
import { exportExcel, exportPDF } from "@/lib/export";
import { toast } from "sonner";
import { useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import type { ForecastResponse } from "@/lib/api";

interface Props {
  result: ForecastResponse;
  chartContainerId: string;
}

export function ExportButton({ result, chartContainerId }: Props) {
  const [open, setOpen] = useState(false);

  const handleExcel = async () => {
    setOpen(false);
    try {
      await exportExcel(result);
      toast.success("Laporan Excel berhasil diunduh");
    } catch (e) {
      toast.error(`Gagal export: ${e instanceof Error ? e.message : "Error"}`);
    }
  };

  const handlePDF = async () => {
    setOpen(false);
    try {
      await exportPDF(chartContainerId, result);
      toast.success("Laporan PDF berhasil diunduh");
    } catch (e) {
      toast.error(`Gagal export: ${e instanceof Error ? e.message : "Error"}`);
    }
  };

  return (
    <div className="relative">
      <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
        <Button
          variant="outline"
          size="sm"
          className="gap-1.5 text-xs"
          onClick={() => setOpen(!open)}
        >
          <Download className="h-3.5 w-3.5" />
          Export
        </Button>
      </motion.div>

      <AnimatePresence>
        {open && (
          <>
            <div className="fixed inset-0 z-40" onClick={() => setOpen(false)} />
            <motion.div
              className="absolute right-0 top-full mt-1 z-50 bg-popover border border-border rounded-lg shadow-lg p-1 min-w-[160px]"
              initial={{ opacity: 0, scale: 0.9, y: -5 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.9, y: -5 }}
              transition={{ type: "spring", stiffness: 500, damping: 30 }}
            >
              <motion.button
                onClick={handleExcel}
                className="flex items-center gap-2 w-full px-3 py-2 text-xs rounded-md hover:bg-accent text-left transition-colors"
                whileHover={{ x: 3 }}
                whileTap={{ scale: 0.97 }}
              >
                <FileSpreadsheet className="h-3.5 w-3.5 text-emerald-500" />
                Export ke Excel
              </motion.button>
              <motion.button
                onClick={handlePDF}
                className="flex items-center gap-2 w-full px-3 py-2 text-xs rounded-md hover:bg-accent text-left transition-colors"
                whileHover={{ x: 3 }}
                whileTap={{ scale: 0.97 }}
              >
                <FileText className="h-3.5 w-3.5 text-red-500" />
                Export ke PDF
              </motion.button>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
}
