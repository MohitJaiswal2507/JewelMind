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
    <div className="flex-1 flex flex-col h-full overflow-hidden bg-[#08090D] p-5 sm:p-7 space-y-6">
      {/* Top Search & Filter Bar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 pb-3 border-b border-white/[0.07]">
        {/* Search Field */}
        <div className="relative flex-1 max-w-md">
          <Search className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <Input
            type="text"
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder="Search lookbook by title, category, or SKU..."
            className="pl-9.5 bg-[#0E111A] border-white/10 text-xs text-white placeholder:text-slate-500 rounded-xl focus-visible:ring-amber-400/50"
          />
        </div>

        {/* Category Filter Pills */}
        <div className="flex items-center space-x-1.5 overflow-x-auto pb-1 sm:pb-0 scrollbar-none">
          {CATEGORIES.map((cat) => (
            <button
              key={cat}
              onClick={() => onSelectCategory(cat)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition cursor-pointer ${
                selectedCategory === cat
                  ? 'bg-amber-400/20 text-amber-200 border border-amber-400/40 shadow-sm'
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
          Atelier Lookbook <span className="text-amber-300 font-mono text-xs font-normal">({items.length} Assets)</span>
        </h2>
        <span className="text-[11px] text-slate-400 font-light">Fine jewellery blueprints & photorealistic prototypes</span>
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
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 xl:grid-cols-3 gap-5 pb-8">
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
