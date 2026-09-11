import React from 'react';
import { Search, Filter, RotateCcw } from 'lucide-react';
import { Input } from '../ui/input';
import { Button } from '../ui/button';
import { 
  DesignCategory, 
  DesignStatus, 
  DESIGN_CATEGORIES, 
  DESIGN_STATUSES 
} from '../../types/design';

interface DesignFiltersProps {
  search: string;
  onSearchChange: (value: string) => void;
  selectedCategory: DesignCategory | '';
  onCategoryChange: (category: DesignCategory | '') => void;
  selectedStatus: DesignStatus | '';
  onStatusChange: (status: DesignStatus | '') => void;
  onReset: () => void;
}

export const DesignFilters: React.FC<DesignFiltersProps> = ({
  search,
  onSearchChange,
  selectedCategory,
  onCategoryChange,
  selectedStatus,
  onStatusChange,
  onReset,
}) => {
  const isFiltered = Boolean(search || selectedCategory || selectedStatus);

  return (
    <div className="space-y-4 bg-[#0E111A]/90 p-5 rounded-2xl border border-white/[0.07] shadow-xl">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
        {/* Search input */}
        <div className="relative flex-1">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
          <Input
            value={search}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder="Search catalogue by name, category, or gemstone specifications..."
            className="pl-10 h-10 bg-[#080A10] border-white/10 focus-visible:ring-amber-400/50"
          />
        </div>

        {/* Status Dropdown & Reset */}
        <div className="flex items-center space-x-2.5">
          <div className="flex items-center space-x-2">
            <Filter className="w-4 h-4 text-slate-400 hidden sm:block" />
            <select
              value={selectedStatus}
              onChange={(e) => onStatusChange(e.target.value as DesignStatus | '')}
              className="h-10 rounded-xl border border-white/10 bg-[#080A10] px-3.5 text-xs text-slate-200 focus:outline-none focus:ring-1 focus:ring-amber-400/50 cursor-pointer shadow-inner"
            >
              <option value="">All Statuses</option>
              {DESIGN_STATUSES.map((st) => (
                <option key={st.value} value={st.value} className="bg-[#0E111A]">
                  {st.label}
                </option>
              ))}
            </select>
          </div>

          {isFiltered && (
            <Button
              variant="outline"
              size="sm"
              onClick={onReset}
              className="h-10 text-xs border-white/10 hover:text-amber-300 hover:border-amber-400/30"
            >
              <RotateCcw className="w-3.5 h-3.5 mr-1.5" />
              Reset
            </Button>
          )}
        </div>
      </div>

      {/* Category Pills */}
      <div className="flex items-center gap-1.5 overflow-x-auto pb-1 pt-1 no-scrollbar">
        <button
          type="button"
          onClick={() => onCategoryChange('')}
          className={`px-3.5 py-1.5 rounded-full text-xs font-semibold whitespace-nowrap transition-all duration-200 cursor-pointer ${
            selectedCategory === ''
              ? 'bg-gradient-to-r from-amber-400 to-yellow-200 text-slate-950 shadow-md shadow-amber-500/10'
              : 'bg-[#121622] text-slate-300 hover:bg-[#181E2E] border border-white/5'
          }`}
        >
          All Categories
        </button>

        {DESIGN_CATEGORIES.map((cat) => (
          <button
            key={cat}
            type="button"
            onClick={() => onCategoryChange(cat)}
            className={`px-3.5 py-1.5 rounded-full text-xs font-semibold whitespace-nowrap transition-all duration-200 cursor-pointer ${
              selectedCategory === cat
                ? 'bg-gradient-to-r from-amber-400 to-yellow-200 text-slate-950 shadow-md shadow-amber-500/10'
                : 'bg-[#121622] text-slate-300 hover:bg-[#181E2E] border border-white/5'
            }`}
          >
            {cat}
          </button>
        ))}
      </div>
    </div>
  );
};
