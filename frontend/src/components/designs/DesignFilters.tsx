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
    <div className="space-y-4 bg-gradient-to-br from-slate-900/90 to-[#0b0e17] p-4 sm:p-5 rounded-2xl border border-slate-800 shadow-md">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
        {/* Search input */}
        <div className="relative flex-1">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
          <Input
            value={search}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder="Search jewellery designs by title, description or stone..."
            className="pl-10 h-10 bg-slate-950/70 border-slate-800 focus-visible:ring-amber-400"
          />
        </div>

        {/* Status Dropdown & Reset */}
        <div className="flex items-center space-x-2.5">
          <div className="flex items-center space-x-2">
            <Filter className="w-4 h-4 text-slate-400 hidden sm:block" />
            <select
              value={selectedStatus}
              onChange={(e) => onStatusChange(e.target.value as DesignStatus | '')}
              className="h-10 rounded-md border border-slate-700 bg-slate-950/70 px-3 text-xs text-slate-200 focus:outline-none focus:ring-1 focus:ring-amber-400 cursor-pointer"
            >
              <option value="">All Statuses</option>
              {DESIGN_STATUSES.map((st) => (
                <option key={st.value} value={st.value}>
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
              className="h-10 text-xs border-slate-700 hover:text-amber-300 hover:border-amber-500/50"
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
          className={`px-3 py-1.5 rounded-full text-xs font-semibold whitespace-nowrap transition ${
            selectedCategory === ''
              ? 'bg-amber-400 text-slate-950 shadow-sm shadow-amber-500/20'
              : 'bg-slate-800/80 text-slate-300 hover:bg-slate-700/80'
          }`}
        >
          All Categories
        </button>

        {DESIGN_CATEGORIES.map((cat) => (
          <button
            key={cat}
            type="button"
            onClick={() => onCategoryChange(cat)}
            className={`px-3 py-1.5 rounded-full text-xs font-semibold whitespace-nowrap transition ${
              selectedCategory === cat
                ? 'bg-amber-400 text-slate-950 shadow-sm shadow-amber-500/20'
                : 'bg-slate-800/80 text-slate-300 hover:bg-slate-700/80'
            }`}
          >
            {cat}
          </button>
        ))}
      </div>
    </div>
  );
};
