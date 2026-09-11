import React, { useState, useRef } from 'react';
import { UploadCloud, FileImage, AlertCircle, Loader2, CheckCircle2 } from 'lucide-react';
import { Button } from '../ui/button';

interface SketchUploadDropzoneProps {
  onUpload: (file: File) => Promise<void>;
  isReplacing?: boolean;
}

const ALLOWED_TYPES = ['image/png', 'image/jpeg', 'image/jpg', 'image/webp'];
const MAX_SIZE_BYTES = 10 * 1024 * 1024; // 10MB

export const SketchUploadDropzone: React.FC<SketchUploadDropzoneProps> = ({
  onUpload,
  isReplacing = false,
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const [uploading, setUploading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<boolean>(false);

  const handleProcessFile = async (file: File) => {
    setError(null);
    setSuccess(false);

    if (!ALLOWED_TYPES.includes(file.type.toLowerCase())) {
      setError('Unsupported file type. Please upload a PNG, JPEG, or WEBP image.');
      return;
    }

    if (file.size > MAX_SIZE_BYTES) {
      const actualMb = (file.size / (1024 * 1024)).toFixed(2);
      setError(`File size (${actualMb} MB) exceeds maximum allowed limit of 10 MB.`);
      return;
    }

    if (file.size === 0) {
      setError('The selected file is empty.');
      return;
    }

    setUploading(true);
    try {
      await onUpload(file);
      setSuccess(true);
      setTimeout(() => setSuccess(false), 3000);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to upload sketch asset.';
      setError(msg);
    } finally {
      setUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      handleProcessFile(file);
    }
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    const file = e.dataTransfer.files?.[0];
    if (file) {
      handleProcessFile(file);
    }
  };

  return (
    <div className="w-full space-y-3">
      {/* Hidden File Input */}
      <input
        ref={fileInputRef}
        type="file"
        accept="image/png,image/jpeg,image/webp"
        onChange={handleFileChange}
        className="hidden"
        disabled={uploading}
      />

      {/* Drop Area */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => !uploading && fileInputRef.current?.click()}
        className={`relative border-2 border-dashed rounded-2xl p-6 sm:p-8 flex flex-col items-center justify-center text-center cursor-pointer transition-all duration-300 ${
          isDragging
            ? 'border-amber-400 bg-amber-400/10 scale-[0.99]'
            : 'border-white/10 bg-[#080A10] hover:border-amber-400/30 hover:bg-[#0C0F18]'
        } ${uploading ? 'cursor-wait opacity-80' : ''}`}
      >
        {uploading ? (
          <div className="space-y-3 flex flex-col items-center">
            <Loader2 className="w-8 h-8 animate-spin text-amber-300" />
            <div className="text-xs font-medium text-slate-200">
              {isReplacing ? 'Replacing blueprint in cloud storage...' : 'Syncing blueprint to cloud storage...'}
            </div>
            <p className="text-[11px] text-slate-500 font-light">Atomic serialization & cryptographic ownership verification</p>
          </div>
        ) : success ? (
          <div className="space-y-2 flex flex-col items-center text-emerald-400">
            <CheckCircle2 className="w-8 h-8" />
            <div className="text-xs font-semibold">Blueprint synced successfully!</div>
          </div>
        ) : (
          <div className="space-y-3 flex flex-col items-center">
            <div className="p-3.5 rounded-2xl bg-[#121622] border border-white/10 text-amber-300 shadow-inner">
              <UploadCloud className="w-7 h-7" />
            </div>

            <div className="space-y-1">
              <div className="text-sm font-serif font-medium text-white flex items-center justify-center gap-1.5">
                <span>{isReplacing ? 'Click or drag to replace blueprint' : 'Upload Jewellery Blueprint'}</span>
              </div>
              <p className="text-xs text-slate-400 font-light max-w-sm">
                Drag and drop your hand-drawn sketch, digital LineArt, or CAD blueprint
              </p>
            </div>

            <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-[#121622] border border-white/5 text-[10px] text-slate-400 font-mono">
              <FileImage className="w-3.5 h-3.5 text-amber-300" />
              <span>PNG, JPG, WEBP • Max 10 MB</span>
            </div>

            <Button
              type="button"
              variant="gold"
              size="sm"
              className="mt-1 font-semibold text-xs"
              onClick={(e) => {
                e.stopPropagation();
                fileInputRef.current?.click();
              }}
            >
              Select File
            </Button>
          </div>
        )}
      </div>

      {/* Error Message */}
      {error && (
        <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/30 flex items-start space-x-2.5 text-rose-300 text-xs animate-in fade-in">
          <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
          <div className="flex-1">
            <span className="font-semibold">Upload Error: </span>
            <span>{error}</span>
          </div>
        </div>
      )}
    </div>
  );
};
