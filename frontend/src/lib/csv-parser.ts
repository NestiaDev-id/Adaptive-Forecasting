/**
 * Client-side streaming CSV parser.
 * Uses File.stream() + ReadableStream to read large files
 * chunk-by-chunk without loading the entire file into RAM.
 */

export interface ParseResult {
  data: number[];
  rows: number;
  column: string;
  errors: number;
}

export interface ParseProgress {
  bytesRead: number;
  totalBytes: number;
  rowsParsed: number;
  percent: number;
}

type ProgressCallback = (p: ParseProgress) => void;

export async function parseCSVStream(
  file: File,
  onProgress?: ProgressCallback,
): Promise<ParseResult> {
  const totalBytes = file.size;
  let bytesRead = 0;
  let rowsParsed = 0;
  let errors = 0;
  let headerParsed = false;
  let targetCol = 0;
  let colName = "value";
  let partial = "";

  const data: number[] = [];

  const stream = file.stream();
  const reader = stream.getReader();
  const decoder = new TextDecoder("utf-8");

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    bytesRead += value.byteLength;
    const chunk = partial + decoder.decode(value, { stream: true });
    const lines = chunk.split(/\r?\n/);

    // last line might be incomplete
    partial = lines.pop() ?? "";

    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed) continue;

      if (!headerParsed) {
        // detect header: if first row contains non-numeric values
        const cols = splitCSVLine(trimmed);
        const firstNumeric = cols.findIndex((c) => !isNaN(Number(c)) && c !== "");
        if (firstNumeric === -1) {
          // all non-numeric → this is a header row
          // find the first column that looks like a data column
          targetCol = cols.findIndex((c) =>
            /value|data|sales|price|amount|qty|quantity|count|total|revenue|volume/i.test(c),
          );
          if (targetCol === -1) targetCol = cols.length > 1 ? 1 : 0;
          colName = cols[targetCol] || "value";
          headerParsed = true;
          continue;
        } else {
          // no header, first row is data
          targetCol = firstNumeric;
          colName = `column_${targetCol}`;
          headerParsed = true;
          // fall through to parse this row
        }
      }

      const cols = splitCSVLine(trimmed);
      const raw = cols[targetCol];
      if (raw !== undefined) {
        const num = Number(raw);
        if (!isNaN(num)) {
          data.push(num);
          rowsParsed++;
        } else {
          errors++;
        }
      }

      // emit progress every 5000 rows
      if (onProgress && rowsParsed % 5000 === 0) {
        onProgress({
          bytesRead,
          totalBytes,
          rowsParsed,
          percent: Math.round((bytesRead / totalBytes) * 100),
        });
      }
    }
  }

  // process any remaining partial line
  if (partial.trim()) {
    const cols = splitCSVLine(partial.trim());
    const raw = cols[targetCol];
    if (raw !== undefined) {
      const num = Number(raw);
      if (!isNaN(num)) {
        data.push(num);
        rowsParsed++;
      }
    }
  }

  onProgress?.({
    bytesRead: totalBytes,
    totalBytes,
    rowsParsed,
    percent: 100,
  });

  return { data, rows: rowsParsed, column: colName, errors };
}

function splitCSVLine(line: string): string[] {
  const result: string[] = [];
  let current = "";
  let inQuotes = false;

  for (let i = 0; i < line.length; i++) {
    const ch = line[i];
    if (ch === '"') {
      inQuotes = !inQuotes;
    } else if ((ch === "," || ch === ";" || ch === "\t") && !inQuotes) {
      result.push(current.trim());
      current = "";
    } else {
      current += ch;
    }
  }
  result.push(current.trim());
  return result;
}
