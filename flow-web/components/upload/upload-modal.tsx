"use client";

import * as React from "react";
import { FileUploader } from "./file-uploader";

interface UploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onUploadComplete?: () => void;
}

export function UploadModal({ isOpen, onClose, onUploadComplete }: UploadModalProps) {
  const [error, setError] = React.useState<string | null>(null);

  if (!isOpen) return null;

  const handleUpload = async (files: File[], note: string, tags: string[]) => {
    setError(null);

    try {
      const formData = new FormData();
      files.forEach((file) => formData.append("files", file));
      formData.append("note", note);
      formData.append("tags", JSON.stringify(tags));

      const response = await fetch("/api/upload", {
        method: "POST",
        body: formData,
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.error || result.message || `Upload failed (${response.status})`);
      }

      if (!result.success) {
        // Check individual file results
        const failedFiles = result.results?.filter((r: { success: boolean }) => !r.success) || [];
        if (failedFiles.length > 0) {
          const errors = failedFiles.map((f: { filename: string; error: string }) => `${f.filename}: ${f.error}`).join(", ");
          throw new Error(`Some files failed: ${errors}`);
        }
        throw new Error(result.message || "Upload failed");
      }

      onUploadComplete?.();
    } catch (err) {
      const message = err instanceof Error ? err.message : "Upload failed";
      setError(message);
      throw err; // Re-throw so FileUploader knows it failed
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-background/80 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative z-10 w-full max-w-lg mx-4 bg-card border rounded-lg shadow-lg">
        <FileUploader onUpload={handleUpload} onClose={onClose} error={error} />
      </div>
    </div>
  );
}
