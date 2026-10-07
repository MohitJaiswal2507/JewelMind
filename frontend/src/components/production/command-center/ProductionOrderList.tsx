import React from 'react';
import {
  Layers,
  Hammer,
  Eye,
  Calendar,
  Sparkles,
} from 'lucide-react';
import { Button } from '../../ui/button';
import { Badge } from '../../ui/badge';
import { ProductionOrder, ORDER_PRIORITIES, ORDER_STATUSES } from '../../../types/production';
import { formatINR } from '../../../types/materialValuation';

interface ProductionOrderListProps {
  orders: ProductionOrder[];
  selectedOrderId: string | null;
  onSelectOrder: (orderId: string) => void;
  onOpenShopFloor: (orderId: string) => void;
  loading?: boolean;
}

export const ProductionOrderList: React.FC<ProductionOrderListProps> = ({
  orders,
  selectedOrderId,
  onSelectOrder,
  onOpenShopFloor,
  loading = false,
}) => {
  if (loading) {
    return (
      <div className="space-y-3">
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-24 rounded-2xl bg-[#0B1210] border border-[#1C2621] animate-pulse" />
        ))}
      </div>
    );
  }

  if (orders.length === 0) {
    return (
      <div className="p-12 text-center rounded-2xl bg-[#0B1210] border border-[#1C2621] space-y-4">
        <div className="w-12 h-12 rounded-2xl bg-[#141D19] border border-[#D8AD55]/20 text-[#D8AD55] flex items-center justify-center mx-auto">
          <Layers className="w-6 h-6 opacity-80" />
        </div>
        <div className="space-y-1">
          <h3 className="text-base font-serif font-medium text-[#F4EFE5]">No Active Production Orders</h3>
          <p className="text-xs text-[#A9ADA7] max-w-sm mx-auto font-light">
            There are no production orders matching your filter. Send an approved specification from the Studio or create a new order to begin.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {orders.map((order) => {
        const isSelected = order.id === selectedOrderId;
        const priorityConfig = ORDER_PRIORITIES.find((p) => p.value === order.priority);
        const statusConfig = ORDER_STATUSES.find((s) => s.value === order.status);

        // Approximate material valuation (e.g. 18K gold ~ 20-30g or spec BOM)
        const estimatedGoldGrams = order.specification_category ? 8.5 * order.quantity : 12.0;
        const approxValue = estimatedGoldGrams * 5890;

        return (
          <div
            key={order.id}
            onClick={() => onSelectOrder(order.id)}
            className={`p-4 rounded-2xl border transition-all duration-200 cursor-pointer relative group ${
              isSelected
                ? 'bg-[#141D19] border-[#D8AD55]/60 shadow-xl shadow-[#D8AD55]/5 ring-1 ring-[#D8AD55]/30'
                : 'bg-[#0B1210]/95 border-[#1C2621] hover:border-[#D8AD55]/30 hover:bg-[#0F1714]'
            }`}
          >
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
              {/* Product Info & Thumbnail */}
              <div className="flex items-center space-x-3.5 min-w-0 flex-1">
                <div className="w-14 h-14 rounded-xl bg-[#161B26] border border-white/[0.08] overflow-hidden shrink-0 relative flex items-center justify-center">
                  {order.design_thumbnail_url ? (
                    <img
                      src={order.design_thumbnail_url}
                      alt={order.design_name || 'Jewellery piece'}
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                    />
                  ) : (
                    <Sparkles className="w-5 h-5 text-amber-300/40" />
                  )}
                  {order.is_overdue && (
                    <span className="absolute top-1 right-1 w-2.5 h-2.5 rounded-full bg-rose-500 ring-2 ring-[#0E111A]" title="Overdue order" />
                  )}
                </div>

                <div className="space-y-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-sm font-serif font-medium text-white truncate">
                      {order.design_name || 'Bespoke Atelier Order'}
                    </span>
                    <span className="text-[11px] font-mono text-slate-400 px-2 py-0.5 rounded bg-white/[0.04]">
                      #{order.id.slice(0, 8)}
                    </span>
                    {order.specification_version && (
                      <span className="text-[10px] font-mono text-amber-300/80 px-1.5 py-0.5 rounded bg-amber-400/10 border border-amber-400/20">
                        Spec v{order.specification_version}
                      </span>
                    )}
                  </div>

                  <div className="flex items-center gap-3 text-xs text-slate-400 font-light flex-wrap">
                    <span className="text-slate-300 font-medium capitalize">
                      {order.design_category || 'Fine Jewellery'}
                    </span>
                    <span className="text-slate-600">•</span>
                    <span>Qty: <strong className="text-white font-medium">{order.quantity}</strong></span>
                    <span className="text-slate-600">•</span>
                    <span className="flex items-center gap-1">
                      <Calendar className="w-3 h-3 text-slate-500" />
                      Due: {order.deadline ? new Date(order.deadline).toLocaleDateString() : 'Flexible'}
                    </span>
                  </div>
                </div>
              </div>

              {/* Progress & Telemetry */}
              <div className="flex items-center gap-6 sm:gap-8 justify-between md:justify-end flex-wrap">
                {/* Routing Steps Progress */}
                <div className="space-y-1 min-w-[120px]">
                  <div className="flex items-center justify-between text-[11px]">
                    <span className="text-slate-400 font-light">Routing Steps</span>
                    <span className="text-amber-300 font-mono font-medium">
                      {order.routing_steps_count ? `${order.routing_steps_count} stages` : 'Spec routing'}
                    </span>
                  </div>
                  <div className="w-full bg-[#1A1F2C] h-1.5 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all duration-500 ${
                        order.status === 'completed'
                          ? 'w-full bg-emerald-400'
                          : order.status === 'in_progress'
                          ? 'w-2/3 bg-gradient-to-r from-amber-400 to-yellow-300'
                          : 'w-1/6 bg-blue-400'
                      }`}
                    />
                  </div>
                </div>

                {/* Material Estimated Value */}
                <div className="text-right hidden lg:block">
                  <div className="text-xs text-slate-400 font-light">Material Value</div>
                  <div className="text-sm font-serif font-medium text-emerald-300">
                    {formatINR(approxValue)}
                  </div>
                </div>

                {/* Priority & Status Badges */}
                <div className="flex items-center gap-2">
                  {priorityConfig && (
                    <Badge variant="outline" className={`text-[10px] capitalize ${priorityConfig.color}`}>
                      {priorityConfig.label}
                    </Badge>
                  )}
                  {statusConfig && (
                    <Badge variant="outline" className={`text-[10px] capitalize font-medium ${statusConfig.color}`}>
                      {statusConfig.label}
                    </Badge>
                  )}
                </div>

                {/* Action Buttons */}
                <div className="flex items-center gap-2" onClick={(e) => e.stopPropagation()}>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => onSelectOrder(order.id)}
                    className="h-8 text-xs border-[#1E2333] hover:border-amber-400/50 hover:bg-[#161B26] text-slate-200"
                  >
                    <Eye className="w-3.5 h-3.5 mr-1 text-amber-300/80" />
                    <span>Command</span>
                  </Button>

                  <Button
                    variant="gold"
                    size="sm"
                    onClick={() => onOpenShopFloor(order.id)}
                    className="h-8 text-xs font-medium"
                    title="Open Shop-Floor Terminal for this order"
                  >
                    <Hammer className="w-3.5 h-3.5 mr-1" />
                    <span>Shop Floor</span>
                  </Button>
                </div>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
};
