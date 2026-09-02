import React from 'react';
import { Sparkles, Layers, Image as ImageIcon, Calendar } from 'lucide-react';
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
}

interface StudioMediaCardProps {
  item: StudioMediaItem;
  isSelected: boolean;
  onSelect: (item: StudioMediaItem) => void;
}

const getStatusBadge = (status: DesignStatus) => {
  switch (status) {
    case 'ready':
      return <Badge variant="success">Approved</Badge>;
    case 'rendering':
      return (
        <Badge variant="gold" className="animate-pulse">
          <Sparkles className="w-3 h-3 mr-1" /> Rendering
        </Badge>
      );
    case 'rendered':
      return (
        <Badge variant="gold">
          <Sparkles className="w-3 h-3 mr-1" /> Rendered
        </Badge>
      );
    case 'archived':
      return <Badge variant="secondary">Archived</Badge>;
    case 'draft':
    default:
      return <Badge variant="outline">Draft</Badge>;
  }
};

export const StudioMediaCard: React.FC<StudioMediaCardProps> = ({
  item,
  isSelected,
  onSelect,
}) => {
  return (
    <div
      onClick={() => onSelect(item)}
      className={`group relative rounded-2xl bg-[#0b0e17] border transition-all duration-200 cursor-pointer overflow-hidden flex flex-col justify-between ${
        isSelected
          ? 'border-amber-400 ring-2 ring-amber-400/20 bg-slate-900/90 shadow-xl'
          : 'border-slate-800/90 hover:border-amber-500/40 hover:bg-slate-900/60 shadow-md'
      }`}
    >
      {/* Top Image Preview Box */}
      <div className="relative w-full h-44 bg-slate-950/90 border-b border-slate-800/80 flex items-center justify-center p-3 overflow-hidden">
        {item.thumbnailUrl ? (
          <img
            src={item.thumbnailUrl}
            alt={item.title}
            className="w-full h-full object-contain filter invert opacity-90 group-hover:scale-105 transition-transform duration-300"
          />
        ) : (
          <div className="flex flex-col items-center space-y-1.5 text-slate-600">
            <ImageIcon className="w-8 h-8" />
            <span className="text-[10px] font-mono">No Preview</span>
          </div>
        )}

        {/* Media Type Overlay Pill */}
        <div className="absolute top-2.5 left-2.5 px-2 py-0.5 rounded-md bg-slate-950/80 backdrop-blur-sm border border-slate-800 text-[10px] font-medium text-slate-300 flex items-center space-x-1">
          <Layers className="w-3 h-3 text-amber-400" />
          <span>{item.mediaType}</span>
        </div>

        {/* Status Badge */}
        <div className="absolute top-2.5 right-2.5">
          {getStatusBadge(item.status)}
        </div>
      </div>

      {/* Card Metadata Footer */}
      <div className="p-3.5 space-y-2">
        <div>
          <div className="text-xs font-bold text-white truncate group-hover:text-amber-300 transition">
            {item.title}
          </div>
          <div className="text-[11px] font-mono text-amber-400/90 pt-0.5">
            {item.sku}
          </div>
        </div>

        <div className="flex items-center justify-between text-[10px] text-slate-400 pt-1 border-t border-slate-800/80">
          <span className="truncate">{item.category}</span>
          <div className="flex items-center space-x-1 font-mono">
            <Calendar className="w-3 h-3 text-slate-500" />
            <span>{new Date(item.createdAt).toLocaleDateString([], { month: 'short', day: 'numeric' })}</span>
          </div>
        </div>
      </div>
    </div>
  );
};
