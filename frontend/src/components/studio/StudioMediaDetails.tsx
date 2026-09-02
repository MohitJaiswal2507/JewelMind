import React, { useState } from 'react';
import {
  X,
  Download,
  Trash2,
  Brush,
  Calendar,
  Layers,
  User,
  AlertTriangle,
  Loader2,
  HardDrive
} from 'lucide-react';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Separator } from '../ui/separator';
import { StudioMediaItem } from './StudioMediaCard';

interface StudioMediaDetailsProps {
  item: StudioMediaItem | null;
  onClose: () => void;
  onOpenCanvas: (designId: string) => void;
  onDeleteMedia: (item: StudioMediaItem) => Promise<void>;
}

export const StudioMediaDetails: React.FC<StudioMediaDetailsProps> = ({
  item,
  onClose,
  onOpenCanvas,
  onDeleteMedia,
}) => {
  const [isDeleting, setIsDeleting] = useState<boolean>(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  if (!item) return null;

  const handleDownload = () => {
    if (!item.thumbnailUrl) return;
    const a = document.createElement('a');
    a.href = item.thumbnailUrl;
    a.download = `${item.title.toLowerCase().replace(/[^a-z0-9]+/g, '-')}-${item.sku.toLowerCase().replace(/[^a-z0-9]+/g, '-')}.png`;
    a.target = '_blank';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  const handleDeleteConfirm = async () => {
    setIsDeleting(true);
    setError(null);
    try {
      await onDeleteMedia(item);
      setShowDeleteConfirm(false);
      onClose();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to delete media asset.';
      setError(msg);
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <aside className="w-full lg:w-80 xl:w-96 bg-[#070a12] border-l border-slate-800/90 flex flex-col justify-between select-none p-5 text-slate-300 overflow-y-auto">
      <div className="space-y-5">
        {/* Header */}
        <div className="flex items-center justify-between pb-2 border-b border-slate-800/80">
          <h3 className="text-xs font-bold text-white uppercase tracking-wider">Media Details</h3>
          <Button
            variant="ghost"
            size="icon"
            className="h-7 w-7 rounded-lg text-slate-400 hover:text-white"
            onClick={onClose}
            aria-label="Close details"
          >
            <X className="w-4 h-4" />
          </Button>
        </div>

        {/* Large Media Preview */}
        <div className="w-full bg-slate-950/90 rounded-2xl border border-slate-800/90 p-4 flex items-center justify-center min-h-[220px] overflow-hidden group relative">
          {item.thumbnailUrl ? (
            <img
              src={item.thumbnailUrl}
              alt={item.title}
              className="max-h-52 object-contain filter invert opacity-95 rounded-lg group-hover:scale-105 transition-transform duration-200"
            />
          ) : (
            <div className="text-center p-4 text-slate-500 text-xs">No media preview available</div>
          )}
        </div>

        {/* Title & SKU Header */}
        <div className="space-y-1">
          <h2 className="text-base font-extrabold text-white tracking-tight leading-snug">
            {item.title}
          </h2>
          <div className="text-xs font-mono font-semibold text-amber-400">
            {item.sku}
          </div>
          <div className="text-[11px] text-slate-400">
            {item.mediaType} • {item.category}
          </div>
        </div>

        <Separator />

        {/* Metadata Specification Table */}
        <div className="space-y-3 text-xs">
          <div className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">
            Asset Metadata
          </div>

          <div className="space-y-2.5">
            <div className="flex items-center justify-between">
              <span className="text-slate-400 flex items-center space-x-1.5">
                <User className="w-3.5 h-3.5 text-slate-500" />
                <span>Creator</span>
              </span>
              <span className="font-semibold text-white truncate max-w-[140px]">{item.creatorName}</span>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-slate-400 flex items-center space-x-1.5">
                <Calendar className="w-3.5 h-3.5 text-slate-500" />
                <span>Creation Date</span>
              </span>
              <span className="font-mono text-slate-300">
                {new Date(item.createdAt).toLocaleDateString([], {
                  month: 'short',
                  day: 'numeric',
                  year: 'numeric',
                })}
              </span>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-slate-400 flex items-center space-x-1.5">
                <HardDrive className="w-3.5 h-3.5 text-slate-500" />
                <span>Asset Size</span>
              </span>
              <span className="font-mono text-slate-300">{item.fileSize}</span>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-slate-400 flex items-center space-x-1.5">
                <Layers className="w-3.5 h-3.5 text-slate-500" />
                <span>Status</span>
              </span>
              <Badge variant={item.status === 'ready' ? 'success' : 'outline'} className="text-[10px]">
                {item.status.toUpperCase()}
              </Badge>
            </div>
          </div>
        </div>

        {/* Design Description if present */}
        {item.design.description && (
          <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 text-xs space-y-1">
            <div className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">Artisan Notes</div>
            <p className="text-slate-300 leading-relaxed text-[11px]">{item.design.description}</p>
          </div>
        )}
      </div>

      {/* Action Footer */}
      <div className="pt-4 border-t border-slate-800/80 space-y-2">
        {/* Open in Interactive Canvas */}
        <Button
          variant="gold"
          size="sm"
          className="w-full font-bold text-xs shadow-md"
          onClick={() => onOpenCanvas(item.designId)}
        >
          <Brush className="w-3.5 h-3.5 mr-1.5" /> Open in Sketch Canvas
        </Button>

        {/* Download & Delete Buttons */}
        <div className="grid grid-cols-2 gap-2">
          <Button
            variant="secondary"
            size="sm"
            className="text-xs font-semibold"
            onClick={handleDownload}
            disabled={!item.thumbnailUrl}
          >
            <Download className="w-3.5 h-3.5 mr-1.5" /> Download
          </Button>

          <Button
            variant="outline"
            size="sm"
            className="text-xs border-slate-700 hover:border-rose-500 hover:text-rose-400 hover:bg-rose-500/10"
            onClick={() => setShowDeleteConfirm(true)}
          >
            <Trash2 className="w-3.5 h-3.5 mr-1.5" /> Delete
          </Button>
        </div>

        {/* Delete Confirmation Sub-Dialog */}
        {showDeleteConfirm && (
          <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-xs space-y-2 animate-in fade-in">
            <div className="flex items-center space-x-1.5 font-bold text-rose-300">
              <AlertTriangle className="w-4 h-4 text-rose-400" />
              <span>Confirm Delete?</span>
            </div>
            <p className="text-[11px] text-rose-300">
              Are you sure you want to permanently delete this media file from Supabase Storage?
            </p>
            {error && <p className="text-[10px] text-rose-400 font-semibold">{error}</p>}
            <div className="flex items-center space-x-2 pt-1">
              <Button
                variant="outline"
                size="sm"
                className="h-7 text-[11px] border-slate-700"
                onClick={() => setShowDeleteConfirm(false)}
                disabled={isDeleting}
              >
                Cancel
              </Button>
              <Button
                variant="destructive"
                size="sm"
                className="h-7 text-[11px] font-bold"
                onClick={handleDeleteConfirm}
                disabled={isDeleting}
              >
                {isDeleting ? <Loader2 className="w-3 h-3 animate-spin mr-1" /> : null}
                Yes, Delete
              </Button>
            </div>
          </div>
        )}
      </div>
    </aside>
  );
};
