import React from 'react';
import {
  Factory,
  CheckCircle2,
  Clock,
  RotateCcw,
} from 'lucide-react';
import { Card, CardContent } from '../../ui/card';

interface ProductionMetricsCardsProps {
  activeOrders: number;
  completedOrders: number;
  ordersAwaitingQc: number;
  ordersInRework: number;
}

export const ProductionMetricsCards: React.FC<ProductionMetricsCardsProps> = ({
  activeOrders,
  completedOrders,
  ordersAwaitingQc,
  ordersInRework,
}) => {
  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {/* 1. Active Orders */}
      <Card className="bg-[#0E111A]/85 border-white/[0.08] backdrop-blur shadow-xl">
        <CardContent className="p-4 flex items-center justify-between">
          <div>
            <p className="text-xs font-medium text-slate-400">Active In-Flight</p>
            <h3 className="text-2xl font-serif font-bold text-white mt-1">
              {activeOrders}
            </h3>
            <p className="text-[11px] text-slate-500 mt-0.5">Under atelier processing</p>
          </div>
          <div className="w-10 h-10 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-300">
            <Factory className="w-5 h-5" />
          </div>
        </CardContent>
      </Card>

      {/* 2. Completed Orders */}
      <Card className="bg-[#0E111A]/85 border-white/[0.08] backdrop-blur shadow-xl">
        <CardContent className="p-4 flex items-center justify-between">
          <div>
            <p className="text-xs font-medium text-slate-400">Finalized Orders</p>
            <h3 className="text-2xl font-serif font-bold text-emerald-400 mt-1">
              {completedOrders}
            </h3>
            <p className="text-[11px] text-slate-500 mt-0.5">QC passed & completed</p>
          </div>
          <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
            <CheckCircle2 className="w-5 h-5" />
          </div>
        </CardContent>
      </Card>

      {/* 3. Orders Awaiting QC */}
      <Card className="bg-[#0E111A]/85 border-white/[0.08] backdrop-blur shadow-xl">
        <CardContent className="p-4 flex items-center justify-between">
          <div>
            <p className="text-xs font-medium text-slate-400">Awaiting Inspection</p>
            <h3 className="text-2xl font-serif font-bold text-cyan-300 mt-1">
              {ordersAwaitingQc}
            </h3>
            <p className="text-[11px] text-slate-500 mt-0.5">Pending quality verdict</p>
          </div>
          <div className="w-10 h-10 rounded-xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400">
            <Clock className="w-5 h-5" />
          </div>
        </CardContent>
      </Card>

      {/* 4. Orders in Rework */}
      <Card className="bg-[#0E111A]/85 border-white/[0.08] backdrop-blur shadow-xl">
        <CardContent className="p-4 flex items-center justify-between">
          <div>
            <p className="text-xs font-medium text-slate-400">In Controlled Rework</p>
            <h3 className="text-2xl font-serif font-bold text-purple-300 mt-1">
              {ordersInRework}
            </h3>
            <p className="text-[11px] text-slate-500 mt-0.5">Active correction loops</p>
          </div>
          <div className="w-10 h-10 rounded-xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center text-purple-300">
            <RotateCcw className="w-5 h-5" />
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
