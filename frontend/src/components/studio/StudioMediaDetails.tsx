import React, { useState, useEffect } from 'react';
import {
  X,
  Download,
  Trash2,
  PenTool,
  Calendar,
  Layers,
  User,
  AlertTriangle,
  Loader2,
  HardDrive,
  Sparkles,
  CheckCircle2,
  Columns,
  Factory,
  Check,
  ShieldCheck,
} from 'lucide-react';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Separator } from '../ui/separator';
import { StudioMediaItem } from './StudioMediaCard';
import { Design, DesignRender } from '../../types/design';
import { designService } from '../../services/api/designService';
import { ProductionSpecificationReviewModal } from '../production/ProductionSpecificationReviewModal';

interface StudioMediaDetailsProps {
  item: StudioMediaItem | null;
  onClose: () => void;
  onOpenCanvas: (designId: string) => void;
  onDeleteMedia: (item: StudioMediaItem) => Promise<void>;
  onApproveRender?: (designId: string, renderId: string) => Promise<void>;
  onDeleteRender?: (designId: string, renderId: string) => Promise<void>;
  onCompareVersions?: (design: Design, renders: DesignRender[], renderAId?: string, renderBId?: string) => void;
  onSendToProduction?: (designId: string, renderId?: string) => void;
}

export const StudioMediaDetails: React.FC<StudioMediaDetailsProps> = ({
  item,
  onClose,
  onOpenCanvas,
  onDeleteMedia,
  onApproveRender,
  onDeleteRender,
  onCompareVersions,
  onSendToProduction,
}) => {
  const [renders, setRenders] = useState<DesignRender[]>(item?.design.renders || []);
  const [selectedRenderId, setSelectedRenderId] = useState<string | null>(item?.renderId || null);
  const [loadingRenders, setLoadingRenders] = useState<boolean>(false);
  const [isApproving, setIsApproving] = useState<boolean>(false);
  const [isDeleting, setIsDeleting] = useState<boolean>(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState<boolean>(false);
  const [deleteTargetType, setDeleteTargetType] = useState<'asset' | 'render'>('render');
  const [error, setError] = useState<string | null>(null);
  const [showSpecReview, setShowSpecReview] = useState<boolean>(false);

  // Sync / fetch renders when item changes
  useEffect(() => {
    if (!item) return;
    if (item.design.renders && item.design.renders.length > 0) {
      setRenders(item.design.renders);
      setSelectedRenderId(item.renderId || item.design.renders[item.design.renders.length - 1].id);
    } else {
      // Fetch fresh renders from API
      const loadRenders = async () => {
        setLoadingRenders(true);
        try {
          const res = await designService.getDesignRenders(item.designId);
          setRenders(res.renders);
          if (res.renders.length > 0) {
            setSelectedRenderId(item.renderId || res.renders[res.renders.length - 1].id);
          }
        } catch {
          // fallback to empty
        } finally {
          setLoadingRenders(false);
        }
      };
      loadRenders();
    }
  }, [item]);

  if (!item) return null;

  // Active displayed render (if inspecting a render, otherwise blueprint)
  const activeRender = renders.find((r) => r.id === selectedRenderId) || null;
  const currentPreviewUrl = activeRender ? activeRender.image_url : item.thumbnailUrl;
  const isViewingSketch = !activeRender && item.mediaType === 'PNG Sketch';

  const getFallbackImage = () => {
    const cat = item.category?.toLowerCase() || '';
    if (cat.includes('necklace') || cat.includes('choker')) return '/assets/emerald-necklace.jpg';
    if (cat.includes('ring')) return '/assets/diamond-ring.jpg';
    if (cat.includes('earring') || cat.includes('jhumka')) return '/assets/jhumka-earrings.jpg';
    if (cat.includes('pendant')) return '/assets/real-pendant.jpg';
    if (cat.includes('bracelet') || cat.includes('bangle')) return '/assets/design-sapphire-bracelet.png';
    if (item.mediaType === 'PNG Sketch') return '/assets/real-sketch.jpg';
    return '/assets/met-emerald-necklace.jpg';
  };

  const [imgSrc, setImgSrc] = useState<string>(currentPreviewUrl || '');
  const [imgError, setImgError] = useState<boolean>(false);

  useEffect(() => {
    setImgSrc(currentPreviewUrl || '');
    setImgError(false);
  }, [currentPreviewUrl]);

  // Close on Escape key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  const handleDownload = () => {
    const downloadUrl = imgSrc || currentPreviewUrl;
    if (!downloadUrl) return;
    const a = document.createElement('a');
    a.href = downloadUrl;
    const label = activeRender ? `V${activeRender.version_number}` : 'sketch';
    a.download = `${item.title.toLowerCase().replace(/[^a-z0-9]+/g, '-')}-${label}.png`;
    a.target = '_blank';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  const handleApprove = async () => {
    if (!activeRender || !onApproveRender) return;
    setIsApproving(true);
    setError(null);
    try {
      await onApproveRender(item.designId, activeRender.id);
      // Update local render list approval state
      setRenders((prev) =>
        prev.map((r) => ({
          ...r,
          is_approved_for_production: r.id === activeRender.id,
        }))
      );
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to approve render.';
      setError(msg);
    } finally {
      setIsApproving(false);
    }
  };

  const handleDeleteRenderConfirm = async () => {
    if (!activeRender || !onDeleteRender) return;
    setIsDeleting(true);
    setError(null);
    try {
      await onDeleteRender(item.designId, activeRender.id);
      setRenders((prev) => prev.filter((r) => r.id !== activeRender.id));
      setSelectedRenderId(null);
      setShowDeleteConfirm(false);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to delete render version.';
      setError(msg);
    } finally {
      setIsDeleting(false);
    }
  };

  const handleDeleteAssetConfirm = async () => {
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
    <aside className="w-full h-full bg-[#0A0C12] border-l border-white/[0.08] flex flex-col select-none text-slate-300 overflow-hidden shadow-2xl">
      {/* Sticky Top Header */}
      <div className="sticky top-0 z-30 bg-[#0A0C12]/95 backdrop-blur-md px-5 py-4 border-b border-white/[0.08] flex items-center justify-between shrink-0">
        <div className="flex items-center space-x-2">
          <Sparkles className="w-4 h-4 text-[#D8AD55]" />
          <h3 className="text-xs font-serif font-medium text-white tracking-wider flex items-center space-x-1.5 uppercase">
            <span>Asset Inspector</span>
          </h3>
          {activeRender && (
            <Badge variant="gold" className="text-[10px] font-mono px-1.5 py-0">
              V{activeRender.version_number}
            </Badge>
          )}
        </div>
        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8 rounded-lg text-slate-400 hover:text-white hover:bg-white/10 transition-colors"
          onClick={onClose}
          aria-label="Close details"
        >
          <X className="w-4 h-4" />
        </Button>
      </div>

      {/* Scrollable Inspector Body */}
      <div className="flex-1 overflow-y-auto p-5 space-y-5">
        {/* Large Media Preview */}
        <div className="w-full bg-[#080A10] rounded-2xl border border-white/[0.07] p-3 flex items-center justify-center min-h-[200px] max-h-[260px] overflow-hidden group relative">
          <img
            src={imgSrc || getFallbackImage()}
            alt={item.title}
            onError={() => {
              if (!imgError) {
                setImgError(true);
                setImgSrc(getFallbackImage());
              }
            }}
            className={`max-h-56 object-contain rounded-lg group-hover:scale-105 transition-transform duration-300 ${
              isViewingSketch ? 'filter invert opacity-90' : 'shadow-xl'
            }`}
          />

          {activeRender?.is_approved_for_production && (
            <div className="absolute top-2.5 right-2.5 px-2.5 py-1 rounded-lg bg-emerald-500/90 text-white font-semibold text-[10px] flex items-center space-x-1 shadow-lg backdrop-blur-sm border border-emerald-400/30">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-200" />
              <span>Approved for Production</span>
            </div>
          )}
        </div>

        {/* Title & SKU Header */}
        <div className="space-y-1">
          <h2 className="font-serif text-base text-white font-normal tracking-tight leading-snug">
            {item.title}
          </h2>
          <div className="text-xs font-mono font-semibold text-amber-300">
            {item.sku}
          </div>
          <div className="text-[11px] text-slate-400 font-light flex items-center space-x-2">
            <span>{item.category}</span>
            <span>•</span>
            <span className="capitalize">{activeRender ? `${activeRender.render_mode} Guided` : item.mediaType}</span>
          </div>
        </div>

        {/* Phase H: Render Version History List */}
        <div className="space-y-2 pt-2 border-t border-white/5">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider flex items-center space-x-1">
              <Layers className="w-3 h-3 text-amber-300" />
              <span>Version History ({renders.length})</span>
            </span>
            {renders.length >= 2 && onCompareVersions && (
              <button
                onClick={() => onCompareVersions(item.design, renders, renders[0]?.id, renders[renders.length - 1]?.id)}
                className="text-[10px] text-amber-300 hover:text-amber-200 flex items-center space-x-1 font-medium transition cursor-pointer"
              >
                <Columns className="w-3 h-3" />
                <span>Compare</span>
              </button>
            )}
          </div>

          {loadingRenders ? (
            <div className="flex items-center space-x-2 text-xs text-slate-500 py-2">
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
              <span>Loading versions...</span>
            </div>
          ) : renders.length === 0 ? (
            <div className="text-xs text-slate-500 italic py-1">No render versions yet. Synthesize in workspace.</div>
          ) : (
            <div className="flex items-center space-x-2 overflow-x-auto pb-1.5 scrollbar-thin">
              {renders.map((r) => {
                const isSelected = selectedRenderId === r.id;
                return (
                  <button
                    key={r.id}
                    onClick={() => setSelectedRenderId(r.id)}
                    className={`relative shrink-0 w-16 h-16 rounded-xl border p-1 overflow-hidden transition cursor-pointer ${
                      isSelected
                        ? 'border-amber-400 ring-2 ring-amber-400/30 bg-[#141824]'
                        : 'border-white/10 hover:border-white/25 bg-[#0E111A]'
                    }`}
                  >
                    <img
                      src={r.thumbnail_url || r.image_url}
                      alt={`Version ${r.version_number}`}
                      className="w-full h-full object-cover rounded-lg"
                    />
                    <div className="absolute top-1 left-1 px-1 py-0.2 rounded bg-black/80 text-[9px] font-mono text-amber-300 font-bold">
                      V{r.version_number}
                    </div>
                    {r.is_approved_for_production && (
                      <div className="absolute bottom-1 right-1 p-0.5 rounded-full bg-amber-400 text-slate-950">
                        <Check className="w-2.5 h-2.5 stroke-[3]" />
                      </div>
                    )}
                  </button>
                );
              })}
            </div>
          )}
        </div>

        <Separator />

        {/* Metadata Specification Table */}
        <div className="space-y-2.5 text-xs font-light">
          <div className="text-[10px] font-semibold text-slate-500 uppercase tracking-widest">
            Render Telemetry
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-slate-400 flex items-center space-x-1.5">
                <User className="w-3.5 h-3.5 text-slate-500" />
                <span>Creator</span>
              </span>
              <span className="font-medium text-white truncate max-w-[140px] font-sans">{item.creatorName}</span>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-slate-400 flex items-center space-x-1.5">
                <Calendar className="w-3.5 h-3.5 text-slate-500" />
                <span>Created</span>
              </span>
              <span className="font-mono text-slate-300 text-[11px]">
                {new Date(activeRender?.created_at || item.createdAt).toLocaleDateString([], {
                  month: 'short',
                  day: 'numeric',
                  hour: '2-digit',
                  minute: '2-digit',
                })}
              </span>
            </div>

            {activeRender && (
              <>
                <div className="flex items-center justify-between">
                  <span className="text-slate-400 flex items-center space-x-1.5">
                    <Sparkles className="w-3.5 h-3.5 text-slate-500" />
                    <span>Control Type</span>
                  </span>
                  <span className="font-mono text-slate-200 text-[11px]">{activeRender.control_type} ({activeRender.control_strength.toFixed(2)})</span>
                </div>

                {activeRender.seed && (
                  <div className="flex items-center justify-between">
                    <span className="text-slate-400">Seed</span>
                    <span className="font-mono text-slate-300 text-[11px]">{activeRender.seed}</span>
                  </div>
                )}
              </>
            )}

            <div className="flex items-center justify-between">
              <span className="text-slate-400 flex items-center space-x-1.5">
                <HardDrive className="w-3.5 h-3.5 text-slate-500" />
                <span>Asset Size</span>
              </span>
              <span className="font-mono text-slate-300 text-[11px]">{item.fileSize}</span>
            </div>
          </div>

          {activeRender?.prompt && (
            <div className="p-3 rounded-xl bg-[#0E111A] border border-white/5 space-y-1">
              <div className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">Active Prompt</div>
              <p className="text-slate-300 leading-relaxed text-[11px] font-light line-clamp-3">"{activeRender.prompt}"</p>
            </div>
          )}
        </div>
      </div>

      {/* Action Footer */}
      <div className="pt-4 border-t border-white/5 space-y-2">
        {/* Approve for Production Button */}
        {activeRender && (
          <Button
            variant={activeRender.is_approved_for_production ? 'outline' : 'gold'}
            size="sm"
            className="w-full font-semibold text-xs shadow-md"
            onClick={handleApprove}
            disabled={isApproving || activeRender.is_approved_for_production}
          >
            {isApproving ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin mr-1.5" />
            ) : activeRender.is_approved_for_production ? (
              <CheckCircle2 className="w-3.5 h-3.5 mr-1.5 text-amber-400" />
            ) : (
              <CheckCircle2 className="w-3.5 h-3.5 mr-1.5" />
            )}
            {activeRender.is_approved_for_production
              ? `V${activeRender.version_number} Approved for Production`
              : `Approve V${activeRender.version_number} for Production`}
          </Button>
        )}

        {/* Review Production Specification Button */}
        {activeRender?.is_approved_for_production && (
          <Button
            variant="gold"
            size="sm"
            className="w-full font-semibold text-xs shadow-md"
            onClick={() => setShowSpecReview(true)}
            data-testid="open-spec-review-btn"
          >
            <ShieldCheck className="w-3.5 h-3.5 mr-1.5" /> Review Production Specification
          </Button>
        )}

        {/* Send to Production Button */}
        {onSendToProduction && activeRender?.is_approved_for_production && (
          <Button
            variant="secondary"
            size="sm"
            className="w-full font-semibold text-xs bg-[#161B2C] hover:bg-[#1E263E] text-amber-300 border border-amber-400/20"
            onClick={() => onSendToProduction(item.designId, activeRender.id)}
          >
            <Factory className="w-3.5 h-3.5 mr-1.5" /> Send V{activeRender.version_number} to Production
          </Button>
        )}

        {/* Compare Versions Button */}
        {renders.length >= 2 && onCompareVersions && (
          <Button
            variant="secondary"
            size="sm"
            className="w-full font-medium text-xs bg-[#121622] hover:bg-[#181E2E] border-white/5"
            onClick={() => onCompareVersions(item.design, renders, renders[0]?.id, activeRender?.id || renders[renders.length - 1]?.id)}
          >
            <Columns className="w-3.5 h-3.5 mr-1.5" /> Compare Iterations
          </Button>
        )}

        {/* Open in Interactive Canvas */}
        <Button
          variant="secondary"
          size="sm"
          className="w-full font-semibold text-xs bg-[#161B2C] hover:bg-[#1E263E] text-[#D8AD55] hover:text-[#F1D28A] border border-[#D8AD55]/30 flex items-center justify-center transition-all shadow-sm"
          onClick={() => onOpenCanvas(item.designId)}
        >
          <PenTool className="w-3.5 h-3.5 mr-1.5 text-[#D8AD55]" /> Open in Canvas
        </Button>

        {/* Download & Delete Buttons */}
        <div className="grid grid-cols-2 gap-2">
          <Button
            variant="secondary"
            size="sm"
            className="text-xs font-medium bg-[#121622] hover:bg-[#181E2E] border-white/5"
            onClick={handleDownload}
            disabled={!currentPreviewUrl}
          >
            <Download className="w-3.5 h-3.5 mr-1.5" /> Download
          </Button>

          <Button
            variant="outline"
            size="sm"
            className="text-xs border-white/10 hover:border-rose-500/40 hover:text-rose-300"
            onClick={() => {
              setDeleteTargetType(activeRender ? 'render' : 'asset');
              setShowDeleteConfirm(true);
            }}
          >
            <Trash2 className="w-3.5 h-3.5 mr-1.5" /> {activeRender ? `Delete V${activeRender.version_number}` : 'Delete'}
          </Button>
        </div>

        {/* Delete Confirmation Sub-Dialog */}
        {showDeleteConfirm && (
          <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-xs space-y-2 animate-in fade-in">
            <div className="flex items-center space-x-1.5 font-semibold text-rose-300">
              <AlertTriangle className="w-4 h-4 text-rose-400" />
              <span>Confirm Delete {deleteTargetType === 'render' ? `Version V${activeRender?.version_number}` : 'Media'}?</span>
            </div>
            <p className="text-[11px] text-rose-300 font-light">
              {deleteTargetType === 'render'
                ? 'Permanently delete this render iteration? If assigned to a production order, deletion will be blocked.'
                : 'Permanently delete this sketch asset from cloud storage?'}
            </p>
            {error && <p className="text-[10px] text-rose-400 font-semibold">{error}</p>}
            <div className="flex items-center space-x-2 pt-1">
              <Button
                variant="outline"
                size="sm"
                className="h-7 text-[11px] border-white/10"
                onClick={() => {
                  setShowDeleteConfirm(false);
                  setError(null);
                }}
                disabled={isDeleting}
              >
                Cancel
              </Button>
              <Button
                variant="destructive"
                size="sm"
                className="h-7 text-[11px] font-semibold"
                onClick={deleteTargetType === 'render' ? handleDeleteRenderConfirm : handleDeleteAssetConfirm}
                disabled={isDeleting}
              >
                {isDeleting ? <Loader2 className="w-3 h-3 animate-spin mr-1" /> : null}
                Yes, Delete
              </Button>
            </div>
          </div>
        )}

        {/* Production Specification Review Modal */}
        {showSpecReview && activeRender && (
          <ProductionSpecificationReviewModal
            isOpen={showSpecReview}
            onClose={() => setShowSpecReview(false)}
            renderId={activeRender.id}
            renderThumbnailUrl={activeRender.thumbnail_url || activeRender.image_url}
            renderVersion={activeRender.version_number}
            designCategory={item?.design?.category}
          />
        )}
      </div>
    </aside>
  );
};
export default StudioMediaDetails;
