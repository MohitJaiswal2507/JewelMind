import React from 'react';
import {
  Factory,
  ArrowRight,
  Clock,
} from 'lucide-react';
import { Button } from '../../ui/button';
import { Badge } from '../../ui/badge';
import { ProductionOrder } from '../../../types/production';

interface ActiveProductionTableProps {
  orders: ProductionOrder[];
  onOpenShopFloor: (orderId: string) => void;
}

export const ActiveProductionTable: React.FC<ActiveProductionTableProps> = ({
  orders,
  onOpenShopFloor,
}) => {
  if (orders.length === 0) {
    return (
      <div className="rounded-2xl border border-white/[0.08] bg-[#0E111A]/90 p-8 text-center">
        <Factory className="w-10 h-10 text-slate-600 mx-auto mb-2" />
        <h3 className="text-sm font-semibold text-white">No Active Orders</h3>
        <p className="text-xs text-slate-400 mt-1">
          Create or schedule a production order to launch shop-floor operations.
        </p>
      </div>
    );
  }

  return (
    <div className="rounded-2xl border border-white/[0.08] bg-[#0E111A]/90 backdrop-blur-md shadow-xl overflow-hidden">
      <div className="p-5 border-b border-white/[0.06] flex items-center justify-between">
        <div>
          <h2 className="text-base font-serif font-bold text-white">Active Shop-Floor Orders</h2>
          <p className="text-xs text-slate-400 font-light">
            Live routing and execution tracking across workshop stations
          </p>
        </div>
        <span className="text-xs font-mono text-amber-300/80 bg-amber-400/10 px-2.5 py-1 rounded-full border border-amber-400/20">
          {orders.length} in production
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs text-slate-300">
          <thead className="bg-white/[0.02] border-b border-white/[0.05] text-[10px] uppercase tracking-wider text-slate-400 font-semibold">
            <tr>
              <th className="py-3 px-4">Order & Design</th>
              <th className="py-3 px-4">Quantity</th>
              <th className="py-3 px-4">Priority</th>
              <th className="py-3 px-4">Status</th>
              <th className="py-3 px-4">Target Due</th>
              <th className="py-3 px-4 text-right">Workstation Terminal</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/[0.04]">
            {orders.map((order) => {
              const formattedDeadline = order.deadline
                ? new Date(order.deadline).toLocaleDateString(undefined, {
                    month: 'short',
                    day: 'numeric',
                  })
                : 'No deadline';

              return (
                <tr key={order.id} className="hover:bg-white/[0.02] transition-colors">
                  <td className="py-3 px-4">
                    <div className="flex items-center space-x-2.5">
                      <div className="w-8 h-8 rounded-lg bg-amber-400/10 border border-amber-400/20 flex items-center justify-center text-amber-300 font-mono text-xs font-bold shrink-0">
                        #{order.id.slice(0, 4)}
                      </div>
                      <div>
                        <div className="flex items-center space-x-1.5">
                          <span className="font-semibold text-white">
                            {order.design_name || 'Bespoke Jewellery'}
                          </span>
                          {order.specification_id && (
                            <Badge
                              variant="outline"
                              className="text-[9px] py-0 px-1 font-mono bg-amber-500/10 text-amber-300 border-amber-500/30"
                            >
                              v{order.specification_version || 1}
                            </Badge>
                          )}
                        </div>
                        <span className="text-[11px] text-slate-500">
                          {order.design_category || order.specification_category || 'Piece'}
                        </span>
                      </div>
                    </div>
                  </td>

                  <td className="py-3 px-4 font-mono font-bold text-amber-200">
                    {order.quantity} pcs
                  </td>

                  <td className="py-3 px-4">
                    <Badge
                      variant="outline"
                      className={`text-[9px] uppercase font-mono ${
                        order.priority === 'urgent'
                          ? 'bg-rose-500/15 text-rose-300 border-rose-500/30'
                          : order.priority === 'high'
                          ? 'bg-amber-500/15 text-amber-300 border-amber-500/30'
                          : 'bg-white/[0.04] text-slate-300'
                      }`}
                    >
                      {order.priority}
                    </Badge>
                  </td>

                  <td className="py-3 px-4">
                    <Badge
                      variant="outline"
                      className={`text-[9px] uppercase ${
                        order.status === 'completed'
                          ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                          : order.status === 'in_progress'
                          ? 'bg-amber-500/10 text-amber-300 border-amber-500/30'
                          : 'bg-slate-500/10 text-slate-400'
                      }`}
                    >
                      {order.status.replace('_', ' ')}
                    </Badge>
                  </td>

                  <td className="py-3 px-4">
                    <div className="flex items-center space-x-1">
                      <Clock className="w-3.5 h-3.5 text-slate-500" />
                      <span className={order.is_overdue ? 'text-rose-400 font-bold' : 'text-slate-300'}>
                        {formattedDeadline}
                      </span>
                    </div>
                  </td>

                  <td className="py-3 px-4 text-right">
                    <Button
                      variant="atelier"
                      size="sm"
                      onClick={() => onOpenShopFloor(order.id)}
                      className="text-xs font-semibold"
                    >
                      <span>Open Station</span>
                      <ArrowRight className="w-3.5 h-3.5 ml-1.5 text-amber-300" />
                    </Button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
