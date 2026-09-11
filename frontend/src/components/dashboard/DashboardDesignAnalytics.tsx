import React from 'react';
import {
  Layers,
  BarChart3,
  TrendingUp,
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../ui/card';
import { DistributionItem } from '../../types/dashboard';

interface DashboardDesignAnalyticsProps {
  categories: DistributionItem[];
  statuses: DistributionItem[];
  priorities: DistributionItem[];
}

const CATEGORY_GRADIENTS = [
  'bg-gradient-to-r from-amber-400 to-yellow-200',
  'bg-gradient-to-r from-slate-300 to-slate-100',
  'bg-gradient-to-r from-amber-600 to-amber-400',
  'bg-gradient-to-r from-emerald-400 to-teal-200',
  'bg-gradient-to-r from-purple-400 to-pink-300',
  'bg-gradient-to-r from-sky-400 to-cyan-200',
];

const PRIORITY_GRADIENTS: Record<string, string> = {
  Urgent: 'bg-gradient-to-r from-rose-500 to-red-400',
  High: 'bg-gradient-to-r from-amber-500 to-yellow-400',
  Medium: 'bg-gradient-to-r from-amber-400 to-yellow-200',
  Low: 'bg-gradient-to-r from-slate-400 to-slate-200',
};

export const DashboardDesignAnalytics: React.FC<DashboardDesignAnalyticsProps> = ({
  categories,
  statuses,
  priorities,
}) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {/* Category Distribution */}
      <Card className="bg-[#0E111A]/90 border-white/[0.07] shadow-2xl flex flex-col justify-between">
        <CardHeader className="p-6 sm:p-7 pb-3 border-b border-white/[0.06] bg-[#0A0C12]/50">
          <div className="flex items-center space-x-2 text-amber-300">
            <Layers className="w-5 h-5" />
            <CardTitle className="text-base font-serif font-medium">Jewellery Categories</CardTitle>
          </div>
          <CardDescription className="text-xs text-slate-400 font-light">
            Portfolio product distribution
          </CardDescription>
        </CardHeader>

        <CardContent className="p-6 sm:p-7 space-y-4 flex-1">
          {categories.length === 0 ? (
            <div className="text-center py-6 text-slate-500 text-xs font-light">
              No categories recorded yet.
            </div>
          ) : (
            <div className="space-y-3.5">
              {categories.map((item, idx) => {
                const gradientClass = CATEGORY_GRADIENTS[idx % CATEGORY_GRADIENTS.length];
                return (
                  <div key={item.name} className="space-y-1.5">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-medium text-white">{item.name}</span>
                      <span className="font-mono text-slate-400 font-light text-[11px]">
                        {item.count} ({item.percentage}%)
                      </span>
                    </div>
                    <div className="w-full bg-[#080A10] rounded-full h-1.5 overflow-hidden">
                      <div
                        className={`h-1.5 rounded-full ${gradientClass}`}
                        style={{ width: `${Math.max(4, item.percentage)}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Order Priority Distribution */}
      <Card className="bg-[#0E111A]/90 border-white/[0.07] shadow-2xl flex flex-col justify-between">
        <CardHeader className="p-6 sm:p-7 pb-3 border-b border-white/[0.06] bg-[#0A0C12]/50">
          <div className="flex items-center space-x-2 text-slate-300">
            <BarChart3 className="w-5 h-5" />
            <CardTitle className="text-base font-serif font-medium">Order Priority Spectrum</CardTitle>
          </div>
          <CardDescription className="text-xs text-slate-400 font-light">
            Workshop dispatch urgency tiers
          </CardDescription>
        </CardHeader>

        <CardContent className="p-6 sm:p-7 space-y-4 flex-1">
          {priorities.length === 0 ? (
            <div className="text-center py-6 text-slate-500 text-xs font-light">
              No production orders created yet.
            </div>
          ) : (
            <div className="space-y-3.5">
              {priorities.map((item) => {
                const gradientClass = PRIORITY_GRADIENTS[item.name] || 'bg-gradient-to-r from-slate-500 to-slate-300';
                return (
                  <div key={item.name} className="space-y-1.5">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-medium text-white">{item.name}</span>
                      <span className="font-mono text-slate-400 font-light text-[11px]">
                        {item.count} ({item.percentage}%)
                      </span>
                    </div>
                    <div className="w-full bg-[#080A10] rounded-full h-1.5 overflow-hidden">
                      <div
                        className={`h-1.5 rounded-full ${gradientClass}`}
                        style={{ width: `${Math.max(4, item.percentage)}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Design Lifecycle Status */}
      <Card className="bg-[#0E111A]/90 border-white/[0.07] shadow-2xl flex flex-col justify-between md:col-span-2 lg:col-span-1">
        <CardHeader className="p-6 sm:p-7 pb-3 border-b border-white/[0.06] bg-[#0A0C12]/50">
          <div className="flex items-center space-x-2 text-amber-300">
            <TrendingUp className="w-5 h-5" />
            <CardTitle className="text-base font-serif font-medium">Design Pipeline Health</CardTitle>
          </div>
          <CardDescription className="text-xs text-slate-400 font-light">
            Lifecycle progression breakdown
          </CardDescription>
        </CardHeader>

        <CardContent className="p-6 sm:p-7 space-y-4 flex-1">
          {statuses.length === 0 ? (
            <div className="text-center py-6 text-slate-500 text-xs font-light">
              No designs registered yet.
            </div>
          ) : (
            <div className="space-y-3.5">
              {statuses.map((item) => (
                <div key={item.name} className="space-y-1.5">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-medium text-white capitalize">{item.name}</span>
                    <span className="font-mono text-slate-400 font-light text-[11px]">
                      {item.count} ({item.percentage}%)
                    </span>
                  </div>
                  <div className="w-full bg-[#080A10] rounded-full h-1.5 overflow-hidden">
                    <div
                      className="h-1.5 rounded-full bg-gradient-to-r from-amber-400 to-yellow-200"
                      style={{ width: `${Math.max(4, item.percentage)}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};
