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

export class PDFApiClient {
  async uploadPDF(file: File): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch(`${API_URL}/api/upload`, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const error: ErrorResponse = await response.json();
      throw new Error(error.error || "Upload failed");
    }

    return response.json();
  }

  async processCommand(request: ProcessRequest): Promise<ProcessResponse> {
    const response = await fetch(`${API_URL}/api/process`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const error: ErrorResponse = await response.json();
      throw new Error(error.error || "Processing failed");
    }

    return response.json();
  }

  getDownloadUrl(fileId: string): string {
    return `${API_URL}/api/download/${fileId}`;
  }

  async downloadFile(fileId: string): Promise<void> {
    window.location.href = this.getDownloadUrl(fileId);
  }

  async healthCheck(): Promise<{
    status: string;
    message: string;
    version: string;
  }> {
    const response = await fetch(`${API_URL}/api/health`);
    return response.json();
  }
}

export const apiClient = new PDFApiClient();
