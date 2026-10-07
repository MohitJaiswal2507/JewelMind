import React from 'react';
import { Search, ImageOff, CheckCircle2, Sparkles, Brush, Layers, Image as ImageIcon } from 'lucide-react';
import { Input } from '../ui/input';
import { StudioMediaCard, StudioMediaItem } from './StudioMediaCard';

interface StudioMediaGridProps {
  items: StudioMediaItem[];
  selectedItem: StudioMediaItem | null;
  onSelectItem: (item: StudioMediaItem) => void;
  onOpenCanvas?: (designId: string) => void;
  searchQuery: string;
  onSearchChange: (q: string) => void;
  selectedCategory: string;
  onSelectCategory: (cat: string) => void;
  selectedCollection?: string | null;
  onSelectCollection?: (col: string | null) => void;
}

const CATEGORIES = ['All', 'Ring', 'Necklace', 'Earrings', 'Bracelet', 'Bangle', 'Pendant', 'Brooch', 'Other'];

const SCOPE_FILTERS = [
  { id: null, label: 'All Media' },
  { id: 'approved', label: 'Approved Only', icon: CheckCircle2 },
  { id: 'text', label: 'Text Guided', icon: Sparkles },
  { id: 'doodle', label: 'Doodle Guided', icon: Brush },
  { id: 'image', label: 'Image Guided', icon: ImageIcon },
  { id: 'sketches', label: 'Sketches', icon: Layers },
];

export const StudioMediaGrid: React.FC<StudioMediaGridProps> = ({
  items,
  selectedItem,
  onSelectItem,
  onOpenCanvas,
  searchQuery,
  onSearchChange,
  selectedCategory,
  onSelectCategory,
  selectedCollection = null,
  onSelectCollection,
}) => {
  return (
    <div className="flex-1 flex flex-col h-full bg-[#08090D] p-5 sm:p-7 space-y-6">
      {/* Top Search & Filter Bar */}
      <div className="flex flex-col gap-4 pb-4 border-b border-white/[0.08]">
        {/* Row 1: Search + Curation Scope Filter */}
        <div className="flex flex-col lg:flex-row items-stretch lg:items-center justify-between gap-3">
          {/* Search Field */}
          <div className="relative flex-1 max-w-md">
            <Search className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <Input
              type="text"
              value={searchQuery}
              onChange={(e) => onSearchChange(e.target.value)}
              placeholder="Search lookbook by title, category, or SKU..."
              className="pl-9.5 bg-[#0E111A] border-white/10 text-xs text-white placeholder:text-slate-500 rounded-xl focus-visible:ring-[#D8AD55]/40"
            />
          </div>

          {/* Curation Scope Filters */}
          {onSelectCollection && (
            <div className="flex items-center space-x-1.5 overflow-x-auto pb-1 lg:pb-0 scrollbar-none">
              {SCOPE_FILTERS.map((scope) => {
                const Icon = scope.icon;
                const active = selectedCollection === scope.id;
                return (
                  <button
                    key={scope.label}
                    onClick={() => onSelectCollection(scope.id)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition cursor-pointer flex items-center space-x-1.5 ${
                      active
                        ? 'bg-[#141D19] text-[#F1D28A] border border-[#D8AD55]/40 shadow-sm font-semibold'
                        : 'bg-[#0E111A] text-slate-400 border border-white/5 hover:text-white hover:bg-white/[0.03]'
                    }`}
                  >
                    {Icon && <Icon className={`w-3.5 h-3.5 ${active ? 'text-[#D8AD55]' : 'text-slate-500'}`} />}
                    <span>{scope.label}</span>
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {/* Row 2: Category Filter Pills */}
        <div className="flex items-center space-x-1.5 overflow-x-auto pb-1 scrollbar-none">
          {CATEGORIES.map((cat) => (
            <button
              key={cat}
              onClick={() => onSelectCategory(cat)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition cursor-pointer ${
                selectedCategory === cat
                  ? 'bg-[#D8AD55]/20 text-[#F1D28A] border border-[#D8AD55]/50 shadow-sm'
                  : 'bg-[#0E111A] text-slate-400 border border-white/5 hover:text-white hover:border-white/15'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {/* Dynamic Header & Count */}
      <div className="flex items-center justify-between">
        <h2 className="text-base font-serif font-medium text-white tracking-wide">
          Studio Lookbook <span className="text-[#D8AD55] font-mono text-xs font-normal">({items.length} Assets)</span>
        </h2>
        <span className="text-[11px] text-slate-400 font-light hidden sm:inline">Fine jewellery blueprints &amp; photorealistic prototypes</span>
      </div>

      {/* Media Grid Stream */}
      <div className="flex-1 overflow-y-auto pr-1">
        {items.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-24 space-y-3 text-slate-500">
            <ImageOff className="w-12 h-12 text-slate-600" />
            <div className="text-sm font-serif font-medium text-slate-300">No Studio Media Found</div>
            <p className="text-xs text-slate-500 max-w-sm text-center font-light">
              No matching jewellery media assets found for your search filters. Upload or draw a sketch to populate your Studio.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-3 2xl:grid-cols-4 gap-6 pb-8">
            {items.map((item) => (
              <StudioMediaCard
                key={item.id}
                item={item}
                isSelected={selectedItem?.id === item.id}
                onSelect={onSelectItem}
                onOpenCanvas={onOpenCanvas}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
