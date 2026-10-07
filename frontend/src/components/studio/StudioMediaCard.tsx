import React, { useState, useEffect } from 'react';
import { Layers, Image as ImageIcon, Calendar, CheckCircle2, PenTool, ExternalLink } from 'lucide-react';
import { Badge } from '../ui/badge';
import { Design, DesignStatus } from '../../types/design';

export interface StudioMediaItem {
  id: string;
  designId: string;
  title: string;
  sku: string;
  mediaType: 'PNG Sketch' | 'Photorealistic Render' | 'Vector Blueprint';
  thumbnailUrl: string;
  category: string;
  status: DesignStatus;
  createdAt: string;
  creatorName: string;
  fileSize: string;
  design: Design;
  versionNumber?: number;
  renderId?: string;
  renderMode?: string;
  isApprovedForProduction?: boolean;
  totalVersionsCount?: number;
}

interface StudioMediaCardProps {
  item: StudioMediaItem;
  isSelected: boolean;
  onSelect: (item: StudioMediaItem) => void;
  onOpenCanvas?: (designId: string) => void;
}

export const StudioMediaCard: React.FC<StudioMediaCardProps> = ({
  item,
  isSelected,
  onSelect,
  onOpenCanvas,
}) => {
  const [imgSrc, setImgSrc] = useState<string>(item.thumbnailUrl || '');
  const [imgError, setImgError] = useState<boolean>(false);

  useEffect(() => {
    setImgSrc(item.thumbnailUrl || '');
    setImgError(false);
  }, [item.thumbnailUrl]);

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

  const getGuidanceLabel = () => {
    if (item.mediaType === 'PNG Sketch') return 'Sketch Blueprint';
    if (item.renderMode === 'text') return 'Text Guided';
    if (item.renderMode === 'doodle') return 'Doodle Guided';
    if (item.renderMode === 'image') return 'Image Guided';
    return 'Generative Render';
  };

  return (
    <div
      onClick={() => onSelect(item)}
      className={`group relative rounded-2xl bg-[#0E111A]/90 border transition-all duration-300 cursor-pointer overflow-hidden flex flex-col justify-between ${
        isSelected
          ? 'border-[#D8AD55] ring-2 ring-[#D8AD55]/30 bg-[#141824] shadow-[0_12px_40px_rgba(216,173,85,0.18)]'
          : 'border-white/[0.08] hover:border-[#D8AD55]/40 hover:bg-[#121622] shadow-xl hover:shadow-[0_10px_35px_rgba(216,173,85,0.1)]'
      }`}
    >
      {/* Top Image Preview Box with Luxury Presentation */}
      <div className="relative w-full aspect-[4/3] bg-gradient-to-b from-[#141D19] to-[#080A10] border-b border-white/[0.06] flex items-center justify-center p-3 overflow-hidden">
        {imgSrc ? (
          <img
            src={imgSrc}
            alt={item.title}
            onError={() => {
              if (!imgError) {
                setImgError(true);
                setImgSrc(getFallbackImage());
              }
            }}
            className={`w-full h-full object-contain group-hover:scale-105 transition-transform duration-500 ease-out ${
              item.mediaType === 'PNG Sketch' && !imgError ? 'filter invert opacity-85' : 'rounded-lg'
            }`}
          />
        ) : (
          <div className="flex flex-col items-center space-y-2 text-slate-500">
            <ImageIcon className="w-8 h-8 text-[#D8AD55]/60" />
            <span className="text-[10px] font-mono">No Preview</span>
          </div>
        )}

        {/* Top-Left: Version Pill & Guidance Badge */}
        <div className="absolute top-3 left-3 flex items-center space-x-1.5 z-10">
          {item.versionNumber ? (
            <div className="px-2 py-0.5 rounded-md bg-[#0B1210]/90 border border-[#D8AD55]/50 text-[#F1D28A] font-mono font-bold text-[10px] shadow backdrop-blur-md">
              V{item.versionNumber}
            </div>
          ) : (
            <div className="px-2 py-0.5 rounded-md bg-[#0B1210]/90 text-slate-300 font-mono text-[10px] border border-white/10 backdrop-blur-md">
              Sketch
            </div>
          )}
          <div className="px-2 py-0.5 rounded-md bg-[#080A10]/85 backdrop-blur-md border border-white/10 text-[10px] font-medium text-slate-300 flex items-center space-x-1">
            <Layers className="w-3 h-3 text-[#D8AD55]" />
            <span>{getGuidanceLabel()}</span>
          </div>
        </div>

        {/* Top-Right: Approval Badge or Ready State */}
        <div className="absolute top-3 right-3 flex items-center space-x-1.5 z-10">
          {item.isApprovedForProduction ? (
            <Badge variant="gold" className="text-[10px] font-semibold shadow-md">
              <CheckCircle2 className="w-3 h-3 mr-1" /> Approved
            </Badge>
          ) : item.status === 'ready' ? (
            <Badge variant="success" className="text-[10px]">Ready</Badge>
          ) : null}
        </div>

        {/* Bottom-Right within thumbnail: Versions Count Pill */}
        {item.totalVersionsCount && item.totalVersionsCount > 1 ? (
          <div className="absolute bottom-2.5 right-2.5 px-2 py-0.5 rounded-md bg-black/80 backdrop-blur-md border border-white/15 text-[10px] font-mono text-slate-300 z-10">
            {item.totalVersionsCount} versions
          </div>
        ) : null}

        {/* Quick Action Overlay on Hover */}
        <div className="absolute inset-0 bg-black/40 backdrop-blur-[2px] opacity-0 group-hover:opacity-100 transition-opacity duration-200 flex items-center justify-center gap-2 z-20">
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              onSelect(item);
            }}
            className="px-3 py-1.5 rounded-lg bg-[#0B1210]/90 border border-white/20 text-white hover:text-[#F1D28A] hover:border-[#D8AD55] text-xs font-medium flex items-center space-x-1 transition cursor-pointer shadow-lg"
          >
            <ExternalLink className="w-3.5 h-3.5 mr-1 text-[#D8AD55]" />
            <span>Inspect</span>
          </button>

          {onOpenCanvas && (
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                onOpenCanvas(item.designId);
              }}
              className="px-3 py-1.5 rounded-lg bg-[#141D19] border border-[#D8AD55]/60 text-[#F1D28A] hover:bg-[#D8AD55] hover:text-[#050806] text-xs font-semibold flex items-center space-x-1 transition cursor-pointer shadow-lg"
              title="Open in CAD Canvas"
            >
              <PenTool className="w-3.5 h-3.5 mr-1" />
              <span>Canvas</span>
            </button>
          )}
        </div>
      </div>

      {/* Card Metadata Footer */}
      <div className="p-4 space-y-2.5">
        <div>
          <div className="text-sm font-serif font-medium text-[#F4EFE5] truncate group-hover:text-[#F1D28A] transition-colors">
            {item.title}
          </div>
          <div className="text-[10px] font-mono text-[#D8AD55]/90 pt-0.5 font-medium tracking-wide">
            {item.sku}
          </div>
        </div>

        <div className="flex items-center justify-between text-[11px] text-slate-400 pt-2 border-t border-white/5 font-light">
          <span className="truncate text-slate-300 font-medium">{item.category}</span>
          <div className="flex items-center space-x-1 font-mono text-[10px] text-slate-400">
            <Calendar className="w-3 h-3 text-[#D8AD55]/70" />
            <span>{new Date(item.createdAt).toLocaleDateString([], { month: 'short', day: 'numeric' })}</span>
          </div>
        </div>
      </div>
    </div>
  );
};

