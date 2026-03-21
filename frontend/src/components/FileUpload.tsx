import { useCallback, useRef, useState } from "react";
import { Upload, FileSpreadsheet, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { motion, AnimatePresence } from "motion/react";
import { parseCSVStream, type ParseProgress, type ParseResult } from "@/lib/csv-parser";
import { toast } from "sonner";

interface Props {
  onDataLoaded: (data: number[], fileName: string) => void;
}

export function FileUpload({ onDataLoaded }: Props) {
  const [dragging, setDragging] = useState(false);
  const [progress, setProgress] = useState<ParseProgress | null>(null);
  const [fileName, setFileName] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const processFile = useCallback(
    async (file: File) => {
      if (!file.name.match(/\.(csv|tsv|txt)$/i)) {
        toast.error("Format tidak didukung. Gunakan file CSV, TSV, atau TXT.");
        return;
      }

      setFileName(file.name);
      setProgress({ bytesRead: 0, totalBytes: file.size, rowsParsed: 0, percent: 0 });

      try {
        const result: ParseResult = await parseCSVStream(file, (p) => {
          setProgress(p);
        });

        if (result.data.length < 10) {
          toast.error(`Hanya ditemukan ${result.data.length} data point. Minimum 10 diperlukan.`);
          setProgress(null);
          setFileName(null);
          return;
        }

        onDataLoaded(result.data, file.name);
        toast.success(
          `${result.rows.toLocaleString()} baris dimuat dari kolom "${result.column}"`,
          { description: `File: ${file.name} (${formatBytes(file.size)})` },
        );

        if (result.errors > 0) {
          toast.warning(`${result.errors} baris dilewati karena bukan angka`);
        }
      } catch (err) {
        toast.error(`Gagal memproses file: ${err instanceof Error ? err.message : "Unknown error"}`);
      } finally {
        setProgress(null);
      }
    },
    [onDataLoaded],
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragging(false);
      const file = e.dataTransfer.files[0];
      if (file) processFile(file);
    },
    [processFile],
  );

  const handleFileInput = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) processFile(file);
      e.target.value = "";
    },
    [processFile],
  );

  const clearFile = () => {
    setFileName(null);
    setProgress(null);
  };

  return (
    <div className="space-y-2">
      <motion.div
        className={`
          relative border-2 border-dashed rounded-lg p-4 text-center cursor-pointer
          ${dragging
            ? "border-blue-500 bg-blue-500/10"
            : "border-border/50 hover:border-border"
          }
        `}
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        whileHover={{ scale: 1.01, backgroundColor: "rgba(59,130,246,0.03)" }}
        whileTap={{ scale: 0.98 }}
        animate={dragging ? { scale: 1.03, borderColor: "#3b82f6" } : { scale: 1 }}
        transition={{ type: "spring", stiffness: 400, damping: 25 }}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".csv,.tsv,.txt"
          className="hidden"
          onChange={handleFileInput}
        />

        <AnimatePresence mode="wait">
          {progress ? (
            <motion.div
              key="progress"
              className="space-y-2"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.2 }}
            >
              <motion.div
                animate={{ rotate: [0, 10, -10, 0] }}
                transition={{ repeat: Infinity, duration: 1.5 }}
              >
                <FileSpreadsheet className="h-5 w-5 mx-auto text-blue-400" />
              </motion.div>
              <p className="text-xs text-muted-foreground">
                Memproses... {progress.percent}%
              </p>
              <div className="h-1.5 bg-secondary rounded-full overflow-hidden">
                <motion.div
                  className="h-full bg-blue-500 rounded-full"
                  animate={{ width: `${progress.percent}%` }}
                  transition={{ duration: 0.3, ease: "easeOut" }}
                />
              </div>
              <p className="text-[10px] text-muted-foreground">
                {progress.rowsParsed.toLocaleString()} baris · {formatBytes(progress.bytesRead)}
              </p>
            </motion.div>
          ) : (
            <motion.div
              key="idle"
              className="space-y-1"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.2 }}
            >
              <Upload className="h-5 w-5 mx-auto text-muted-foreground" />
              <p className="text-xs text-muted-foreground">
                Drop CSV atau <span className="text-blue-400 underline">pilih file</span>
              </p>
              <p className="text-[10px] text-muted-foreground/60">
                Hingga 1GB · diproses di browser
              </p>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>

      <AnimatePresence>
        {fileName && !progress && (
          <motion.div
            className="flex items-center justify-between text-xs bg-secondary/30 rounded-md px-3 py-1.5"
            initial={{ opacity: 0, height: 0, y: -5 }}
            animate={{ opacity: 1, height: "auto", y: 0 }}
            exit={{ opacity: 0, height: 0, y: -5 }}
            transition={{ type: "spring", stiffness: 400, damping: 25 }}
          >
            <span className="text-muted-foreground truncate flex items-center gap-1">
              <FileSpreadsheet className="h-3 w-3 text-emerald-400" />
              {fileName}
            </span>
            <Button variant="ghost" size="sm" className="h-5 w-5 p-0" onClick={(e) => { e.stopPropagation(); clearFile(); }}>
              <X className="h-3 w-3" />
            </Button>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1073741824) return `${(bytes / 1048576).toFixed(1)} MB`;
  return `${(bytes / 1073741824).toFixed(2)} GB`;
}
