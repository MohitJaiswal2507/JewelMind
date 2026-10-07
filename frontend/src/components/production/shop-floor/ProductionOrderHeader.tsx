import React from 'react';
import { ArrowLeft, Clock, ShieldCheck, Layers } from 'lucide-react';
import { Button } from '../../ui/button';
import { Badge } from '../../ui/badge';
import { ProductionOrder } from '../../../types/production';

interface ProductionOrderHeaderProps {
  order: ProductionOrder;
  currentStepNumber?: number | null;
  totalSteps?: number;
  qualityGatePassed?: boolean;
  onBack?: () => void;
  onRefresh?: () => void;
  isRefreshing?: boolean;
}

export const ProductionOrderHeader: React.FC<ProductionOrderHeaderProps> = ({
  order,
  currentStepNumber,
  totalSteps = 0,
  qualityGatePassed,
  onBack,
  onRefresh,
  isRefreshing = false,
}) => {
  const getStatusBadge = (status: string) => {
    switch (status.toLowerCase()) {
      case 'completed':
        return <Badge variant="success">Completed</Badge>;
      case 'in_progress':
        return <Badge variant="gold">In Progress</Badge>;
      case 'pending':
        return <Badge variant="secondary">Pending</Badge>;
      case 'cancelled':
        return <Badge variant="destructive">Cancelled</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  const getPriorityBadge = (priority: string) => {
    switch (priority.toLowerCase()) {
      case 'urgent':
        return <Badge variant="destructive" className="font-mono">Urgent</Badge>;
      case 'high':
        return <Badge className="bg-amber-500/20 text-amber-300 border-amber-500/30 font-mono">High</Badge>;
      case 'medium':
        return <Badge variant="secondary" className="font-mono">Medium</Badge>;
      default:
        return <Badge variant="outline" className="font-mono">{priority}</Badge>;
    }
  };

  const formattedDeadline = order.deadline
    ? new Date(order.deadline).toLocaleDateString(undefined, {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
      })
    : 'No deadline';

  return (
    <div className="rounded-2xl border border-[#1C2621] bg-[#0B1210]/95 p-5 sm:p-6 shadow-xl mb-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        {/* Left: Back Button & Order ID / Design Info */}
        <div className="flex items-start space-x-3.5">
          {onBack && (
            <Button
              variant="outline"
              size="sm"
              onClick={onBack}
              className="mt-1 h-9 w-9 p-0 rounded-xl border-[#1C2621] hover:border-[#D8AD55]/40 text-[#A9ADA7]"
              title="Return to order list"
            >
              <ArrowLeft className="w-4 h-4" />
            </Button>
          )}

          <div>
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-mono text-xs text-amber-300/80 uppercase tracking-widest font-semibold">
                Shop Floor Station
              </span>
              <span className="text-white/20">&bull;</span>
              <span className="font-mono text-xs text-slate-400 font-medium">
                #{order.id.slice(0, 8)}
              </span>
              {getStatusBadge(order.status)}
              {getPriorityBadge(order.priority)}
              {qualityGatePassed && (
                <Badge variant="success" className="flex items-center space-x-1">
                  <ShieldCheck className="w-3 h-3 mr-1" />
                  QC Gate Passed
                </Badge>
              )}
            </div>

            <h1 className="text-xl sm:text-2xl font-serif font-bold text-white mt-1">
              {order.design_name || 'Bespoke Jewellery Piece'}
            </h1>

            <div className="flex flex-wrap items-center gap-3 text-xs text-slate-400 mt-1.5 font-light">
              <span>Qty: <strong className="text-amber-200 font-mono">{order.quantity} units</strong></span>
              <span>&bull;</span>
              <span>Category: <strong className="text-slate-200">{order.design_category || order.specification_category || 'Jewellery'}</strong></span>
              <span>&bull;</span>
              <span className="flex items-center space-x-1">
                <Clock className="w-3.5 h-3.5 text-slate-500 inline mr-1" />
                Due: <span className={order.is_overdue ? 'text-rose-400 font-semibold' : 'text-slate-300'}>{formattedDeadline}</span>
                {order.is_overdue && (
                  <Badge variant="destructive" className="ml-1 text-[9px] py-0 px-1">OVERDUE</Badge>
                )}
              </span>
              {order.specification_id && (
                <>
                  <span>&bull;</span>
                  <span className="text-amber-300/80 font-mono text-[11px] bg-amber-400/10 px-2 py-0.5 rounded border border-amber-400/20">
                    Spec v{order.specification_version || 1}
                  </span>
                </>
              )}
            </div>
          </div>
        </div>

        {/* Right: Step Counter & Action Controls */}
        <div className="flex items-center gap-3 self-end md:self-center">
          <div className="text-right px-4 py-2 rounded-xl bg-white/[0.03] border border-white/[0.06]">
            <p className="text-[10px] uppercase tracking-wider text-slate-400 font-semibold">
              Routing Progress
            </p>
            <div className="flex items-center space-x-1.5 justify-end mt-0.5">
              <Layers className="w-3.5 h-3.5 text-amber-300" />
              <span className="font-mono text-sm font-bold text-white">
                Step {currentStepNumber ?? '-'}{' '}
                <span className="text-slate-500 font-normal">/ {totalSteps}</span>
              </span>
            </div>
          </div>

          {onRefresh && (
            <Button
              variant="outline"
              size="sm"
              onClick={onRefresh}
              disabled={isRefreshing}
              className="h-10 px-3.5 rounded-xl border-white/10 hover:border-amber-400/40 text-slate-200"
            >
              {isRefreshing ? 'Syncing...' : 'Sync Station'}
            </Button>
          )}
        </div>
      </div>
    </div>
  );
};
