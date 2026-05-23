"use client";

import { useState, useRef, useCallback } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { uploadImagesBatch, labelFromFilename } from "@/lib/api";
import { toast } from "sonner";

type PendingFile = {
  file: File;
  preview: string;
  label: string;
};

const MAX_FILES = 30;

export function UploadForm() {
  const [pending, setPending] = useState<PendingFile[]>([]);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [dragActive, setDragActive] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const router = useRouter();

  const addFiles = useCallback((fileList: FileList | File[]) => {
    const incoming = Array.from(fileList).filter((f) => f.type.startsWith("image/"));
    if (incoming.length === 0) {
      setError("Please select image files only");
      toast.error("Invalid file type. Images only.");
      return;
    }

    setError(null);
    setPending((prev) => {
      const room = MAX_FILES - prev.length;
      const slice = incoming.slice(0, room);
      if (incoming.length > room) {
        toast.warning(`Only ${MAX_FILES} images at a time. Added ${room} of ${incoming.length}.`);
      }
      const next: PendingFile[] = [...prev];
      for (const file of slice) {
        if (prev.some((p) => p.file.name === file.name && p.file.size === file.size)) continue;
        next.push({
          file,
          preview: URL.createObjectURL(file),
          label: labelFromFilename(file.name) || file.name,
        });
      }
      return next;
    });
  }, []);

  const removeFile = (index: number) => {
    setPending((prev) => {
      const copy = [...prev];
      URL.revokeObjectURL(copy[index].preview);
      copy.splice(index, 1);
      return copy;
    });
  };

  const clearAll = () => {
    pending.forEach((p) => URL.revokeObjectURL(p.preview));
    setPending([]);
    setProgress(0);
    setError(null);
    if (inputRef.current) inputRef.current.value = "";
  };

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragActive(false);
      if (e.dataTransfer.files.length) addFiles(e.dataTransfer.files);
    },
    [addFiles]
  );

  const handleUpload = async () => {
    if (pending.length === 0) return;
    setUploading(true);
    setProgress(10);
    setError(null);
    try {
      setProgress(35);
      const result = await uploadImagesBatch(pending.map((p) => p.file));
      setProgress(100);
      toast.success(
        `Uploaded ${result.uploaded} item(s). AI is analyzing using file names as hints.`
      );
      if (result.failed > 0) {
        toast.warning(`${result.failed} file(s) failed`);
      }
      setTimeout(() => {
        clearAll();
        router.push("/");
      }, 800);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Upload failed";
      setError(msg);
      toast.error(`Upload failed: ${msg}`);
      setUploading(false);
      setProgress(0);
    }
  };

  return (
    <div className="p-4 md:p-8 animate-fade-in flex flex-col gap-4 max-w-2xl md:mx-auto w-full">
      <div>
        <h1 className="text-xl font-semibold text-slate-100">Add Clothing</h1>
        <p className="text-sm text-slate-500 mt-1">
          Upload one or many photos. Name files clearly (e.g.{" "}
          <span className="text-slate-400">black_jordan_4_sneakers.jpg</span>) so AI
          identifies each item correctly.
        </p>
      </div>

      {pending.length === 0 ? (
        <Card
          className={`border-2 border-dashed transition-colors duration-200 cursor-pointer min-h-[280px] flex items-center justify-center ${
            dragActive
              ? "border-violet-500 bg-violet-500/5"
              : "border-slate-800 hover:border-slate-700 bg-slate-950"
          }`}
          onDragOver={(e) => {
            e.preventDefault();
            setDragActive(true);
          }}
          onDragLeave={() => setDragActive(false)}
          onDrop={handleDrop}
          onClick={() => inputRef.current?.click()}
        >
          <div className="flex flex-col items-center justify-center p-6 text-center">
            <div className="w-14 h-14 rounded-full bg-slate-900 border border-slate-800 flex items-center justify-center mb-4">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="w-6 h-6 text-violet-400"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              >
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                <polyline points="17 8 12 3 7 8" />
                <line x1="12" y1="3" x2="12" y2="15" />
              </svg>
            </div>
            <p className="text-sm text-slate-300 font-medium mb-1">Upload photos</p>
            <p className="text-sm text-slate-500">Tap to browse or drag & drop multiple files</p>
          </div>
        </Card>
      ) : (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <p className="text-sm text-slate-400">
              {pending.length} photo{pending.length !== 1 ? "s" : ""} selected
            </p>
            {!uploading && (
              <button
                type="button"
                onClick={() => inputRef.current?.click()}
                className="text-sm text-violet-400 hover:text-violet-300"
              >
                + Add more
              </button>
            )}
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 max-h-[420px] overflow-y-auto pr-1">
            {pending.map((item, index) => (
              <Card
                key={`${item.file.name}-${index}`}
                className="overflow-hidden border-slate-900 bg-slate-950 relative"
              >
                <div className="aspect-square bg-slate-900">
                  <img
                    src={item.preview}
                    alt={item.label}
                    className="w-full h-full object-cover"
                  />
                </div>
                <div className="p-2 border-t border-slate-900">
                  <p className="text-[11px] text-slate-300 truncate font-medium" title={item.label}>
                    {item.label ? `Hint: ${item.label}` : item.file.name}
                  </p>
                  <p className="text-[10px] text-slate-600 truncate">AI names from photo</p>
                </div>
                {!uploading && (
                  <button
                    type="button"
                    onClick={() => removeFile(index)}
                    className="absolute top-1.5 right-1.5 w-7 h-7 rounded-full bg-slate-950/90 border border-slate-800 flex items-center justify-center text-slate-400 hover:text-white"
                    aria-label="Remove"
                  >
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      className="w-3.5 h-3.5"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                    >
                      <line x1="18" y1="6" x2="6" y2="18" />
                      <line x1="6" y1="6" x2="18" y2="18" />
                    </svg>
                  </button>
                )}
              </Card>
            ))}
          </div>

          {uploading && (
            <div className="space-y-2 py-2">
              <Progress value={progress} className="h-2 bg-slate-900" />
              <p className="text-sm text-slate-400 text-center">
                Uploading {pending.length} item{pending.length !== 1 ? "s" : ""}…
              </p>
            </div>
          )}

          {error && (
            <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
              {error}
            </div>
          )}

          {!uploading && (
            <div className="flex gap-3">
              <Button
                variant="outline"
                className="flex-1 border-slate-800 text-slate-300 hover:bg-slate-900"
                onClick={clearAll}
              >
                Clear all
              </Button>
              <Button
                className="flex-1 bg-violet-600 hover:bg-violet-500 text-white font-medium"
                onClick={handleUpload}
              >
                Upload {pending.length} & Analyze
              </Button>
            </div>
          )}
        </div>
      )}

      <input
        ref={inputRef}
        type="file"
        accept="image/*"
        multiple
        className="hidden"
        onChange={(e) => {
          if (e.target.files?.length) addFiles(e.target.files);
          e.target.value = "";
        }}
      />

      <div className="mt-2 p-4 rounded-xl bg-slate-950 border border-slate-900">
        <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2.5">
          How naming works
        </h3>
        <ul className="text-sm text-slate-500 space-y-2">
          <li className="flex gap-2">
            <span className="text-violet-400">✓</span>
            <span>AI names each item from what it sees in the photo</span>
          </li>
          <li className="flex gap-2">
            <span className="text-violet-400">✓</span>
            <span>Clear filenames help identification only (not used as the title)</span>
          </li>
          <li className="flex gap-2">
            <span className="text-violet-400">✓</span>
            <span>Non-clothing photos are flagged for you to confirm or remove</span>
          </li>
        </ul>
      </div>
    </div>
  );
}
