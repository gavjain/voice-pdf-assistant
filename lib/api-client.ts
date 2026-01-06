const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface UploadResponse {
  file_id: string;
  filename: string;
  page_count: number;
  size_mb: number;
}

export interface ProcessRequest {
  file_id: string;
  intent: string;
  parameters: Record<string, any>;
}

export interface ProcessResponse {
  result_file_id: string;
  filename: string;
  message: string;
  operation: string;
}

export interface ErrorResponse {
  error: string;
}

export interface HealthCheckResponse {
  status: string;
  message: string;
  version: string;
}

// Helper function to fetch with timeout
async function fetchWithTimeout(
  url: string,
  options: RequestInit = {},
  timeout = 30000
): Promise<Response> {
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeout);

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
    });
    clearTimeout(id);
    return response;
  } catch (error) {
    clearTimeout(id);
    if (error instanceof Error && error.name === "AbortError") {
      throw new Error("Request timeout - server may be waking up. Please try again.");
    }
    throw error;
  }
}

// Helper function to retry requests with exponential backoff
async function retryRequest<T>(
  requestFn: () => Promise<T>,
  maxRetries = 3,
  isFirstRequest = false
): Promise<T> {
  let lastError: Error | null = null;

  for (let i = 0; i < maxRetries; i++) {
    try {
      return await requestFn();
    } catch (error) {
      lastError = error instanceof Error ? error : new Error("Unknown error");
      
      // Don't retry on certain errors
      if (
        lastError.message.includes("Upload failed") ||
        lastError.message.includes("Processing failed") ||
        lastError.message.includes("not found")
      ) {
        throw lastError;
      }

      // For first request or timeout errors, retry with longer delays
      if (i < maxRetries - 1) {
        const delay = isFirstRequest ? (i + 1) * 3000 : (i + 1) * 1000;
        await new Promise((resolve) => setTimeout(resolve, delay));
      }
    }
  }

  throw lastError || new Error("Request failed after retries");
}

export class PDFApiClient {
  private serverReady = false;

  async uploadPDF(file: File): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append("file", file);

    return retryRequest(async () => {
      const response = await fetchWithTimeout(
        `${API_URL}/api/upload`,
        {
          method: "POST",
          body: formData,
        },
        90000 // 90 second timeout for first request
      );

      if (!response.ok) {
        const error: ErrorResponse = await response.json();
        throw new Error(error.error || "Upload failed");
      }

      this.serverReady = true;
      return response.json();
    }, 3, !this.serverReady);
  }

  async processCommand(request: ProcessRequest): Promise<ProcessResponse> {
    return retryRequest(async () => {
      const response = await fetchWithTimeout(
        `${API_URL}/api/process`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(request),
        },
        60000 // 60 second timeout
      );

      if (!response.ok) {
        const error: ErrorResponse = await response.json();
        throw new Error(error.error || "Processing failed");
      }

      return response.json();
    }, 2);
  }

  getDownloadUrl(fileId: string): string {
    return `${API_URL}/api/download/${fileId}`;
  }

  async downloadFile(fileId: string): Promise<void> {
    window.location.href = this.getDownloadUrl(fileId);
  }

  async healthCheck(): Promise<HealthCheckResponse> {
    try {
      const response = await fetchWithTimeout(
        `${API_URL}/api/health`,
        {},
        90000 // 90 second timeout for wake-up
      );
      
      if (!response.ok) {
        throw new Error("Health check failed");
      }
      
      this.serverReady = true;
      return response.json();
    } catch (error) {
      throw error instanceof Error ? error : new Error("Health check failed");
    }
  }

  async pingServer(): Promise<boolean> {
    try {
      await this.healthCheck();
      return true;
    } catch (error) {
      return false;
    }
  }

  isServerReady(): boolean {
    return this.serverReady;
  }
}

export const apiClient = new PDFApiClient();
