import React from 'react';
import {
  Factory,
  RefreshCw,
  Plus,
  Search,
  LayoutDashboard,
  Hammer,
  Cpu,
  Calendar,
  IndianRupee,
} from 'lucide-react';
import { Button } from '../../ui/button';
import { Input } from '../../ui/input';

export type ProductionViewMode = 'command-center' | 'shop-floor' | 'resources' | 'schedule';

interface ProductionHeaderProps {
  viewMode: ProductionViewMode;
  onViewModeChange: (mode: ProductionViewMode) => void;
  searchTerm: string;
  onSearchChange: (val: string) => void;
  statusFilter: string;
  onStatusFilterChange: (val: string) => void;
  isRefreshing: boolean;
  onRefresh: () => void;
  onNewOrder: () => void;
  onOpenRateConfig: () => void;
  activeOrdersCount: number;
  inProgressCount: number;
  awaitingQcCount: number;
  totalMaterialValue: number;
}

export const ProductionHeader: React.FC<ProductionHeaderProps> = ({
  viewMode,
  onViewModeChange,
  searchTerm,
  onSearchChange,
  statusFilter,
  onStatusFilterChange,
  isRefreshing,
  onRefresh,
  onNewOrder,
  onOpenRateConfig,
  activeOrdersCount,
  inProgressCount,
  awaitingQcCount,
  totalMaterialValue,
}) => {
  const formattedVal = totalMaterialValue > 0
    ? totalMaterialValue >= 100000
      ? `₹${(totalMaterialValue / 100000).toFixed(2)}L`
      : `₹${totalMaterialValue.toLocaleString('en-IN')}`
    : '—';

  return (
    <div className="space-y-4 pb-6 border-b border-[#1E2333]/90">
      {/* Top Banner & Title */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        <div className="flex items-start sm:items-center space-x-3.5">
          <div className="w-11 h-11 rounded-2xl bg-gradient-to-tr from-amber-500/20 via-amber-400/20 to-yellow-300/10 border border-[#D4AF37]/30 flex items-center justify-center text-[#E6CA65] shadow-lg shadow-[#D4AF37]/5 shrink-0">
            <Factory className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2.5 flex-wrap">
              <h1 className="text-xl sm:text-2xl font-serif font-bold text-white tracking-wide">
                Production Command Center
              </h1>
              <span className="text-[11px] font-mono uppercase px-2.5 py-0.5 rounded-full bg-[#D4AF37]/10 text-[#E6CA65] border border-[#D4AF37]/30 font-semibold tracking-wider">
                Atelier OS
              </span>
            </div>
            {/* Live Ticker Subtitle */}
            <div className="text-xs text-slate-400 mt-1 flex items-center gap-2 flex-wrap font-light">
              <span className="text-slate-300 font-medium">{activeOrdersCount} Active Orders</span>
              <span className="text-slate-600">•</span>
              <span className="text-amber-300/90">{inProgressCount} In Progress</span>
              <span className="text-slate-600">•</span>
              <span className="text-cyan-300/90">{awaitingQcCount} Awaiting QC</span>
              <span className="text-slate-600">•</span>
              <span className="text-emerald-300/90 font-mono font-medium">{formattedVal} Material in Flow</span>
            </div>
          </div>
        </div>

        {/* Global Action Controls */}
        <div className="flex items-center gap-2.5 flex-wrap sm:flex-nowrap">
          <Button
            variant="outline"
            size="sm"
            onClick={onOpenRateConfig}
            className="border-[#1E2333] hover:bg-[#161B26] text-slate-300 text-xs h-9 px-3"
            title="Configure Indian Bullion Benchmark Rates"
          >
            <IndianRupee className="w-3.5 h-3.5 mr-1.5 text-amber-300/80" />
            <span>Bullion Rates</span>
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={onRefresh}
            disabled={isRefreshing}
            className="border-[#1E2333] hover:bg-[#161B26] text-slate-300 text-xs h-9 px-3"
          >
            <RefreshCw className={`w-3.5 h-3.5 mr-1.5 text-slate-400 ${isRefreshing ? 'animate-spin' : ''}`} />
            <span>Sync</span>
          </Button>

          <Button
            variant="gold"
            size="sm"
            onClick={onNewOrder}
            className="text-xs h-9 px-3.5 font-semibold shadow-lg shadow-[#D4AF37]/10"
          >
            <Plus className="w-3.5 h-3.5 mr-1.5" />
            <span>New Order</span>
          </Button>
        </div>
      </div>

      {/* Navigation Mode Strip & Filter Row */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 pt-1">
        {/* Mode Selector Tabs */}
        <div className="inline-flex p-1 rounded-xl bg-[#0D1017] border border-[#1E2333] overflow-x-auto max-w-full">
          <button
            type="button"
            onClick={() => onViewModeChange('command-center')}
            className={`flex items-center space-x-2 px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all whitespace-nowrap ${
              viewMode === 'command-center'
                ? 'bg-amber-400/15 text-amber-200 border border-amber-400/30 shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <LayoutDashboard className="w-3.5 h-3.5" />
            <span>Command Center</span>
          </button>

          <button
            type="button"
            onClick={() => onViewModeChange('shop-floor')}
            className={`flex items-center space-x-2 px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all whitespace-nowrap ${
              viewMode === 'shop-floor'
                ? 'bg-amber-400/15 text-amber-200 border border-amber-400/30 shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Hammer className="w-3.5 h-3.5" />
            <span>Shop-Floor Workstation</span>
          </button>

          <button
            type="button"
            onClick={() => onViewModeChange('resources')}
            className={`flex items-center space-x-2 px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all whitespace-nowrap ${
              viewMode === 'resources'
                ? 'bg-amber-400/15 text-amber-200 border border-amber-400/30 shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Cpu className="w-3.5 h-3.5" />
            <span>Karigars & Machinery</span>
          </button>

          <button
            type="button"
            onClick={() => onViewModeChange('schedule')}
            className={`flex items-center space-x-2 px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all whitespace-nowrap ${
              viewMode === 'schedule'
                ? 'bg-amber-400/15 text-amber-200 border border-amber-400/30 shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Calendar className="w-3.5 h-3.5" />
            <span>CP-SAT Optimizer</span>
          </button>
        </div>

        {/* Search & Status Quick Filter */}
        <div className="flex items-center gap-2.5">
          <div className="relative flex-1 sm:w-64">
            <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
            <Input
              type="text"
              placeholder="Search design, Karigar, ID..."
              value={searchTerm}
              onChange={(e) => onSearchChange(e.target.value)}
              className="pl-8 pr-3 h-8 text-xs bg-[#0E111A]/90 border-[#1E2333] text-slate-200 placeholder:text-slate-500 focus:border-amber-400/50"
            />
          </div>

          <div className="flex items-center space-x-1 bg-[#0E111A]/90 p-0.5 rounded-lg border border-[#1E2333]">
            {['all', 'in_progress', 'pending', 'completed'].map((st) => (
              <button
                key={st}
                type="button"
                onClick={() => onStatusFilterChange(st)}
                className={`px-2.5 py-1 rounded text-[11px] font-medium transition-colors ${
                  statusFilter === st
                    ? 'bg-[#1E2333] text-amber-300'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {st === 'all' ? 'All' : st === 'in_progress' ? 'Active' : st === 'pending' ? 'Pending' : 'Completed'}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
