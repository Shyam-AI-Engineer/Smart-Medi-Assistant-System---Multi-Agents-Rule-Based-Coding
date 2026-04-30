"use client";

import { useState, useRef } from "react";
import { Upload } from "lucide-react";
import { cn } from "@/lib/cn";

interface ReportUploadZoneProps {
  onFileChange: (file: File | null) => void;
  selectedFile: File | null;
  error: string | null;
}

const ALLOWED_TYPES = {
  "application/pdf": ".pdf",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
  "text/plain": ".txt",
};

const MAX_SIZE = 10 * 1024 * 1024; // 10 MB

export function ReportUploadZone({ onFileChange, selectedFile, error }: ReportUploadZoneProps) {
  const [isDragging, setIsDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const isValidFile = (file: File): boolean => {
    const isValidType = Object.keys(ALLOWED_TYPES).includes(file.type) ||
      file.name.endsWith(".pdf") ||
      file.name.endsWith(".docx") ||
      file.name.endsWith(".txt");

    const isValidSize = file.size <= MAX_SIZE;

    return isValidType && isValidSize;
  };

  const handleFileSelect = (file: File) => {
    if (!isValidFile(file)) {
      if (file.size > MAX_SIZE) {
        onFileChange(null);
        return;
      }
      onFileChange(null);
      return;
    }
    onFileChange(file);
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFileSelect(files[0]);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFileSelect(e.target.files[0]);
    }
  };

  return (
    <div className="space-y-3">
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        className={cn(
          "relative border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors",
          isDragging
            ? "border-brand-500 bg-brand-50"
            : "border-border bg-bg-subtle hover:border-brand-400"
        )}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.docx,.txt,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,text/plain"
          onChange={handleChange}
          className="hidden"
        />

        <Upload className="size-8 mx-auto mb-2 text-ink-muted" />
        <p className="text-sm font-medium text-ink">
          {selectedFile ? selectedFile.name : "Drag or click to upload"}
        </p>
        {selectedFile && (
          <p className="text-xs text-ink-muted mt-1">
            {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
          </p>
        )}
        {!selectedFile && (
          <p className="text-xs text-ink-muted mt-1">
            PDF, DOCX, or TXT (max 10 MB)
          </p>
        )}
      </div>

      {error && (
        <p className="text-xs text-danger-600">{error}</p>
      )}
    </div>
  );
}
