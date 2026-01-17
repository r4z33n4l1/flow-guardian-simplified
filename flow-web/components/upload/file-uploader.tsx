"use client";

import * as React from "react";
import { useDropzone } from "react-dropzone";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";

interface UploadedFile {
  file: File;
  preview?: string;
  status: "pending" | "uploading" | "success" | "error";
  error?: string;
}

interface FileUploaderProps {
  onUpload: (files: File[], note: string, tags: string[]) => Promise<void>;
  onClose?: () => void;
  className?: string;
  error?: string | null;
}

export function FileUploader({ onUpload, onClose, className, error }: FileUploaderProps) {
  const [files, setFiles] = React.useState<UploadedFile[]>([]);
  const [note, setNote] = React.useState("");
  const [tags, setTags] = React.useState<string[]>([]);
  const [tagInput, setTagInput] = React.useState("");
  const [uploading, setUploading] = React.useState(false);

  const onDrop = React.useCallback((acceptedFiles: File[]) => {
    const newFiles = acceptedFiles.map((file) => ({
      file,
      preview: file.type.startsWith("image/")
        ? URL.createObjectURL(file)
        : undefined,
      status: "pending" as const,
    }));
    setFiles((prev) => [...prev, ...newFiles]);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "application/pdf": [".pdf"],
      "text/plain": [".txt"],
      "text/markdown": [".md"],
      "image/*": [".png", ".jpg", ".jpeg"],
    },
    maxSize: 10 * 1024 * 1024, // 10MB
  });

  const removeFile = (index: number) => {
    setFiles((prev) => {
      const newFiles = [...prev];
      if (newFiles[index].preview) {
        URL.revokeObjectURL(newFiles[index].preview!);
      }
      newFiles.splice(index, 1);
      return newFiles;
    });
  };

  const addTag = () => {
    const trimmedTag = tagInput.trim().toLowerCase();
    if (trimmedTag && !tags.includes(trimmedTag)) {
      setTags((prev) => [...prev, trimmedTag]);
      setTagInput("");
    }
  };

  const removeTag = (tag: string) => {
    setTags((prev) => prev.filter((t) => t !== tag));
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      e.preventDefault();
      addTag();
    }
  };

  const handleSubmit = async () => {
    if (files.length === 0) return;

    setUploading(true);
    try {
      await onUpload(
        files.map((f) => f.file),
        note,
        tags
      );
      // Clear state on success
      files.forEach((f) => {
        if (f.preview) URL.revokeObjectURL(f.preview);
      });
      setFiles([]);
      setNote("");
      setTags([]);
      onClose?.();
    } catch (error) {
      console.error("Upload failed:", error);
    } finally {
      setUploading(false);
    }
  };

  const getFileIcon = (type: string) => {
    if (type === "application/pdf") return "PDF";
    if (type.startsWith("image/")) return "IMG";
    if (type === "text/markdown") return "MD";
    return "TXT";
  };

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className={cn("flex flex-col gap-4 p-4", className)}>
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">Add Context</h3>
        {onClose && (
          <Button variant="ghost" size="sm" onClick={onClose}>
            Cancel
          </Button>
        )}
      </div>

      {/* Dropzone */}
      <div
        {...getRootProps()}
        className={cn(
          "border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors",
          isDragActive
            ? "border-primary bg-primary/5"
            : "border-muted-foreground/25 hover:border-muted-foreground/50",
          uploading && "opacity-50 pointer-events-none"
        )}
      >
        <input {...getInputProps()} />
        <div className="flex flex-col items-center gap-2">
          <div className="text-3xl">📎</div>
          {isDragActive ? (
            <p className="text-sm text-muted-foreground">Drop files here...</p>
          ) : (
            <>
              <p className="text-sm font-medium">
                Drop files here or click to upload
              </p>
              <p className="text-xs text-muted-foreground">
                PDF, TXT, MD, PNG, JPG (max 10MB)
              </p>
            </>
          )}
        </div>
      </div>

      {/* File list */}
      {files.length > 0 && (
        <div className="flex flex-col gap-2">
          {files.map((f, i) => (
            <div
              key={i}
              className="flex items-center gap-3 p-2 rounded-lg bg-muted/50"
            >
              <div className="flex items-center justify-center w-10 h-10 rounded bg-primary/10 text-xs font-bold text-primary">
                {getFileIcon(f.file.type)}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">{f.file.name}</p>
                <p className="text-xs text-muted-foreground">
                  {formatSize(f.file.size)}
                </p>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => removeFile(i)}
                disabled={uploading}
              >
                Remove
              </Button>
            </div>
          ))}
        </div>
      )}

      {/* Note */}
      <div className="flex flex-col gap-2">
        <label className="text-sm font-medium">
          Add a note about these files:
        </label>
        <Textarea
          value={note}
          onChange={(e) => setNote(e.target.value)}
          placeholder="Brief description of what these files contain..."
          rows={2}
          disabled={uploading}
        />
      </div>

      {/* Tags */}
      <div className="flex flex-col gap-2">
        <label className="text-sm font-medium">Tags:</label>
        <div className="flex flex-wrap gap-2">
          {tags.map((tag) => (
            <Badge
              key={tag}
              variant="secondary"
              className="cursor-pointer"
              onClick={() => removeTag(tag)}
            >
              {tag} ×
            </Badge>
          ))}
          <input
            type="text"
            value={tagInput}
            onChange={(e) => setTagInput(e.target.value)}
            onKeyDown={handleKeyDown}
            onBlur={addTag}
            placeholder="Add tag..."
            className="flex-1 min-w-[100px] text-sm bg-transparent border-none outline-none placeholder:text-muted-foreground"
            disabled={uploading}
          />
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="p-3 rounded-lg bg-destructive/10 border border-destructive/20 text-destructive text-sm">
          <p className="font-medium">Upload Error</p>
          <p className="text-xs mt-1">{error}</p>
        </div>
      )}

      {/* Submit */}
      <div className="flex justify-end gap-2 pt-2">
        {onClose && (
          <Button variant="outline" onClick={onClose} disabled={uploading}>
            Cancel
          </Button>
        )}
        <Button
          onClick={handleSubmit}
          disabled={files.length === 0 || uploading}
        >
          {uploading ? "Uploading..." : "Add to Memory"}
        </Button>
      </div>
    </div>
  );
}
