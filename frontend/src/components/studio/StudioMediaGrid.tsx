import React from 'react';
import { Search, ImageOff } from 'lucide-react';
import { Input } from '../ui/input';
import { StudioMediaCard, StudioMediaItem } from './StudioMediaCard';

interface StudioMediaGridProps {
  items: StudioMediaItem[];
  selectedItem: StudioMediaItem | null;
  onSelectItem: (item: StudioMediaItem) => void;
  searchQuery: string;
  onSearchChange: (q: string) => void;
  selectedCategory: string;
  onSelectCategory: (cat: string) => void;
}

const CATEGORIES = ['All', 'Ring', 'Necklace', 'Earrings', 'Bracelet', 'Bangle', 'Pendant', 'Other'];

export const StudioMediaGrid: React.FC<StudioMediaGridProps> = ({
  items,
  selectedItem,
  onSelectItem,
  searchQuery,
  onSearchChange,
  selectedCategory,
  onSelectCategory,
}) => {
  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden bg-[#050811] p-4 sm:p-6 space-y-5">
      {/* Top Search & Filter Bar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 pb-2 border-b border-slate-800/80">
        {/* Search Field */}
        <div className="relative flex-1 max-w-md">
          <Search className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <Input
            type="text"
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder="Search by title, category, or SKU..."
            className="pl-9 bg-slate-900/80 border-slate-800 text-xs text-white placeholder:text-slate-500 rounded-xl"
          />
        </div>

        {/* Category Filter Pills */}
        <div className="flex items-center space-x-1.5 overflow-x-auto pb-1 sm:pb-0 scrollbar-none">
          {CATEGORIES.map((cat) => (
            <button
              key={cat}
              onClick={() => onSelectCategory(cat)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition ${
                selectedCategory === cat
                  ? 'bg-amber-400/20 text-amber-300 border border-amber-400/40'
                  : 'bg-slate-900 text-slate-400 border border-slate-800 hover:text-white hover:border-slate-700'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {/* Dynamic Header & Count */}
      <div className="flex items-center justify-between">
        <h2 className="text-sm sm:text-base font-bold text-white tracking-tight">
          Studio Files <span className="text-amber-400 font-mono">({items.length})</span>
        </h2>
        <span className="text-[11px] text-slate-400">Showing creative media assets & sketches</span>
      </div>

      {/* Media Grid Stream */}
      <div className="flex-1 overflow-y-auto pr-1">
        {items.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-24 space-y-3 text-slate-500">
            <ImageOff className="w-12 h-12 text-slate-600" />
            <div className="text-sm font-semibold text-slate-300">No Studio Media Found</div>
            <p className="text-xs text-slate-500 max-w-sm text-center">
              No matching jewellery media assets found for your search filters. Upload or draw a sketch to populate your Studio.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 xl:grid-cols-3 gap-4 pb-8">
            {items.map((item) => (
              <StudioMediaCard
                key={item.id}
                item={item}
                isSelected={selectedItem?.id === item.id}
                onSelect={onSelectItem}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
