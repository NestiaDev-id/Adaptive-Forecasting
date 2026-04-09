import { toast } from "sonner";

const CLOUD_API_URL = import.meta.env.VITE_CLOUD_API_URL || "";

export interface UploadInitResponse {
  success: boolean;
  resumableUrl?: string;
  error?: string;
  message?: string;
}

/**
 * Initiates a resumable upload to Nestia's Cloud Service.
 * Uses public mode (isPublic: true) as requested.
 */
export async function initCloudUpload(file: File): Promise<string | null> {
  if (!CLOUD_API_URL) {
    console.error("[CloudUpload] VITE_CLOUD_API_URL is not configured.");
    return null;
  }

  // Remove trailing slash if present to avoid double slashes
  const baseUrl = CLOUD_API_URL.replace(/\/$/, "");
  const targetUrl = `${baseUrl}/api/upload/init`;

  console.log(`[CloudUpload] Initiating Handshake with: ${targetUrl}`);

  try {
    const response = await fetch(targetUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        name: file.name,
        size: file.size,
        type: file.type || "text/csv",
        isPublic: true,
      }),
    });

    const data: UploadInitResponse = await response.json();

    if (!response.ok || !data.success || !data.resumableUrl) {
      throw new Error(data.error || data.message || "Gagal inisialisasi upload.");
    }

    return data.resumableUrl;
  } catch (err) {
    console.error("Cloud upload init error:", err);
    toast.error(`Cloud Error: ${err instanceof Error ? err.message : "Gagal inisialisasi"}`);
    return null;
  }
}

/**
 * Performs the actual file upload using the resumable URL.
 * This directly talks to Google Drive API via the proxied URL.
 */
export async function performResumableUpload(
  resumableUrl: string,
  file: File,
  onProgress?: (percent: number) => void
): Promise<boolean> {
  try {
    // For large files, we could chunk this, but fetch with a large body
    // works for Resumable URLs provided by Google Drive.
    
    // We'll use XHR to get progress events since fetch doesn't support upload progress yet
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      xhr.open("PUT", resumableUrl, true);

      xhr.upload.onprogress = (e) => {
        if (e.lengthComputable && onProgress) {
          const percent = Math.round((e.loaded / e.total) * 100);
          onProgress(percent);
        }
      };

      xhr.onload = () => {
        if (xhr.status === 200 || xhr.status === 201) {
          resolve(true);
        } else {
          reject(new Error(`Upload failed with status ${xhr.status}`));
        }
      };

      xhr.onerror = () => reject(new Error("Network error during upload."));
      xhr.send(file);
    });
  } catch (err) {
    console.error("Resumable upload error:", err);
    return false;
  }
}

/**
 * Finalizes the upload to get the file metadata/ID.
 * Note: Depending on the My-Cloud-Service implementation, 
 * after the PUT is finished, we might need a separate check 
 * or the service might handle it via webhooks.
 */
export async function verifyCloudUpload(): Promise<string | null> {
    // Placeholder: You might need to check /api/drive/files 
    // to find the ID of the file we just uploaded.
    return null; 
}
