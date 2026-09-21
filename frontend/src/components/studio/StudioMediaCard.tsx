import React from 'react';
import { Layers, Image as ImageIcon, Calendar, CheckCircle2 } from 'lucide-react';
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
}

export const StudioMediaCard: React.FC<StudioMediaCardProps> = ({
  item,
  isSelected,
  onSelect,
}) => {
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
      className={`group relative rounded-2xl bg-[#0E111A] border transition-all duration-300 cursor-pointer overflow-hidden flex flex-col justify-between ${
        isSelected
          ? 'border-amber-400 ring-2 ring-amber-400/20 bg-[#141824] shadow-2xl'
          : 'border-white/[0.07] hover:border-amber-400/30 hover:bg-[#121622] shadow-xl'
      }`}
    >
      {/* Top Image Preview Box */}
      <div className="relative w-full h-52 bg-[#080A10] border-b border-white/[0.06] flex items-center justify-center p-3 overflow-hidden">
        {item.thumbnailUrl ? (
          <img
            src={item.thumbnailUrl}
            alt={item.title}
            className={`w-full h-full object-contain group-hover:scale-105 transition-transform duration-500 ease-out ${
              item.mediaType === 'PNG Sketch' ? 'filter invert opacity-85' : 'rounded-lg'
            }`}
          />
        ) : (
          <div className="flex flex-col items-center space-y-1.5 text-slate-600">
            <ImageIcon className="w-8 h-8" />
            <span className="text-[10px] font-mono">No Preview</span>
          </div>
        )}

        {/* Top-Left: Version Pill & Guidance Badge */}
        <div className="absolute top-3 left-3 flex items-center space-x-1.5">
          {item.versionNumber ? (
            <div className="px-2 py-0.5 rounded-lg bg-amber-400 text-slate-950 font-mono font-bold text-[10px] shadow">
              V{item.versionNumber}
            </div>
          ) : (
            <div className="px-2 py-0.5 rounded-lg bg-slate-800 text-slate-300 font-mono text-[10px] border border-white/10">
              Sketch
            </div>
          )}
          <div className="px-2 py-0.5 rounded-lg bg-[#080A10]/80 backdrop-blur-md border border-white/10 text-[10px] font-medium text-slate-300 flex items-center space-x-1">
            <Layers className="w-3 h-3 text-amber-300" />
            <span>{getGuidanceLabel()}</span>
          </div>
        </div>

        {/* Top-Right: Approval Badge or Render State */}
        <div className="absolute top-3 right-3 flex items-center space-x-1.5">
          {item.isApprovedForProduction ? (
            <Badge variant="gold" className="text-[10px] font-medium shadow-sm">
              <CheckCircle2 className="w-3 h-3 mr-1" /> Approved
            </Badge>
          ) : item.status === 'ready' ? (
            <Badge variant="success" className="text-[10px]">Ready</Badge>
          ) : null}
        </div>

        {/* Bottom-Right within thumbnail: Versions Count Pill */}
        {item.totalVersionsCount && item.totalVersionsCount > 1 ? (
          <div className="absolute bottom-2.5 right-2.5 px-2 py-0.5 rounded-md bg-black/75 backdrop-blur-md border border-white/10 text-[10px] font-mono text-slate-300">
            {item.totalVersionsCount} versions
          </div>
        ) : null}
      </div>

      {/* Card Metadata Footer */}
      <div className="p-4 space-y-2.5">
        <div>
          <div className="text-xs font-serif font-medium text-white truncate group-hover:text-amber-200 transition-colors">
            {item.title}
          </div>
          <div className="text-[11px] font-mono text-amber-300/90 pt-0.5 font-medium">
            {item.sku}
          </div>
        </div>

        <div className="flex items-center justify-between text-[11px] text-slate-400 pt-2 border-t border-white/5 font-light">
          <span className="truncate">{item.category}</span>
          <div className="flex items-center space-x-1 font-mono text-[10px]">
            <Calendar className="w-3 h-3 text-slate-500" />
            <span>{new Date(item.createdAt).toLocaleDateString([], { month: 'short', day: 'numeric' })}</span>
          </div>
        </div>
      </div>
    </div>
  );
};

