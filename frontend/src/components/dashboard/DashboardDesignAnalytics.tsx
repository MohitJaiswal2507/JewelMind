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

const CATEGORY_COLORS = [
  'bg-amber-400 from-amber-400 to-yellow-300',
  'bg-sky-400 from-sky-400 to-cyan-300',
  'bg-purple-400 from-purple-400 to-indigo-300',
  'bg-emerald-400 from-emerald-400 to-teal-300',
  'bg-pink-400 from-pink-400 to-rose-300',
  'bg-orange-400 from-orange-400 to-amber-300',
];

const PRIORITY_COLORS: Record<string, string> = {
  Urgent: 'bg-rose-500 from-rose-500 to-red-400',
  High: 'bg-orange-500 from-orange-500 to-amber-400',
  Medium: 'bg-amber-400 from-amber-400 to-yellow-300',
  Low: 'bg-emerald-400 from-emerald-400 to-teal-300',
};

export const DashboardDesignAnalytics: React.FC<DashboardDesignAnalyticsProps> = ({
  categories,
  statuses,
  priorities,
}) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {/* Category Distribution */}
      <Card className="bg-[#0b0f19] border-slate-800 shadow-xl flex flex-col justify-between">
        <CardHeader className="p-6 pb-3 border-b border-slate-800/80 bg-slate-950/40">
          <div className="flex items-center space-x-2 text-amber-400">
            <Layers className="w-5 h-5" />
            <CardTitle className="text-base">Jewellery Categories</CardTitle>
          </div>
          <CardDescription className="text-xs">
            Portfolio product distribution
          </CardDescription>
        </CardHeader>

        <CardContent className="p-6 space-y-4 flex-1">
          {categories.length === 0 ? (
            <div className="text-center py-6 text-slate-500 text-xs">
              No categories recorded yet.
            </div>
          ) : (
            <div className="space-y-3">
              {categories.map((item, idx) => {
                const colorClass = CATEGORY_COLORS[idx % CATEGORY_COLORS.length];
                return (
                  <div key={item.name} className="space-y-1">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-semibold text-white">{item.name}</span>
                      <span className="font-mono text-slate-400">
                        {item.count} ({item.percentage}%)
                      </span>
                    </div>
                    <div className="w-full bg-slate-900 rounded-full h-2 overflow-hidden">
                      <div
                        className={`h-2 rounded-full bg-gradient-to-r ${colorClass}`}
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
      <Card className="bg-[#0b0f19] border-slate-800 shadow-xl flex flex-col justify-between">
        <CardHeader className="p-6 pb-3 border-b border-slate-800/80 bg-slate-950/40">
          <div className="flex items-center space-x-2 text-sky-400">
            <BarChart3 className="w-5 h-5" />
            <CardTitle className="text-base">Order Priority Spectrum</CardTitle>
          </div>
          <CardDescription className="text-xs">
            Workshop dispatch urgency tiers
          </CardDescription>
        </CardHeader>

        <CardContent className="p-6 space-y-4 flex-1">
          {priorities.length === 0 ? (
            <div className="text-center py-6 text-slate-500 text-xs">
              No production orders created yet.
            </div>
          ) : (
            <div className="space-y-3">
              {priorities.map((item) => {
                const colorClass = PRIORITY_COLORS[item.name] || 'bg-slate-400 from-slate-400 to-slate-300';
                return (
                  <div key={item.name} className="space-y-1">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-semibold text-white">{item.name}</span>
                      <span className="font-mono text-slate-400">
                        {item.count} ({item.percentage}%)
                      </span>
                    </div>
                    <div className="w-full bg-slate-900 rounded-full h-2 overflow-hidden">
                      <div
                        className={`h-2 rounded-full bg-gradient-to-r ${colorClass}`}
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
      <Card className="bg-[#0b0f19] border-slate-800 shadow-xl flex flex-col justify-between md:col-span-2 lg:col-span-1">
        <CardHeader className="p-6 pb-3 border-b border-slate-800/80 bg-slate-950/40">
          <div className="flex items-center space-x-2 text-emerald-400">
            <TrendingUp className="w-5 h-5" />
            <CardTitle className="text-base">Design Pipeline Health</CardTitle>
          </div>
          <CardDescription className="text-xs">
            Lifecycle progression breakdown
          </CardDescription>
        </CardHeader>

        <CardContent className="p-6 space-y-4 flex-1">
          {statuses.length === 0 ? (
            <div className="text-center py-6 text-slate-500 text-xs">
              No designs registered yet.
            </div>
          ) : (
            <div className="space-y-3">
              {statuses.map((item) => (
                <div key={item.name} className="space-y-1">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-semibold text-white capitalize">{item.name}</span>
                    <span className="font-mono text-slate-400">
                      {item.count} ({item.percentage}%)
                    </span>
                  </div>
                  <div className="w-full bg-slate-900 rounded-full h-2 overflow-hidden">
                    <div
                      className="h-2 rounded-full bg-gradient-to-r from-emerald-500 to-teal-400"
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
