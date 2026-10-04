import React, { useState, useEffect, useCallback } from 'react';
import {
  RefreshCw,
  Layers,
  Sparkles,
  AlertCircle,
} from 'lucide-react';
import { Button } from '../../ui/button';
import { ProductionMetricsCards } from './ProductionMetricsCards';
import { ActiveProductionTable } from './ActiveProductionTable';

import { productionService } from '../../../services/api/productionService';
import { ProductionOrder } from '../../../types/production';

interface ProductionDashboardProps {
  onOpenShopFloor: (orderId: string) => void;
  onNavigateToTab?: (tab: 'orders' | 'workers' | 'machines' | 'optimization') => void;
  orders?: ProductionOrder[];
  loading?: boolean;
  onRefresh?: () => void;
}

export const ProductionDashboard: React.FC<ProductionDashboardProps> = ({
  onOpenShopFloor,
  onNavigateToTab,
  orders: propOrders,
  loading: propLoading,
  onRefresh: propOnRefresh,
}) => {
  const [internalOrders, setInternalOrders] = useState<ProductionOrder[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const isControlled = propOrders !== undefined;
  const orders = isControlled ? propOrders : internalOrders;
  const isLoading = propLoading !== undefined ? propLoading : loading;

  const fetchDashboardOrders = useCallback(async (isInitial = false) => {
    if (propOnRefresh) {
      setRefreshing(true);
      setError(null);
      try {
        await propOnRefresh();
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : 'Failed to refresh orders');
      } finally {
        setRefreshing(false);
      }
      return;
    }

    if (isInitial) setLoading(true);
    else setRefreshing(true);
    setError(null);

    try {
      const response = await productionService.getOrders({
        page_size: 50,
      });
      setInternalOrders(response.items);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to load dashboard orders';
      setError(msg);
      console.error('Failed to load dashboard orders:', err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [propOnRefresh]);

  useEffect(() => {
    if (!isControlled) {
      fetchDashboardOrders(true);
    }
  }, [isControlled, fetchDashboardOrders]);

  const activeOrders = orders.filter(
    (x: ProductionOrder) => x.status === 'in_progress' || x.status === 'pending'
  );
  const completedOrders = orders.filter((x: ProductionOrder) => x.status === 'completed');

  // Estimate QC / rework counts from order statuses or notes/flags
  const ordersAwaitingQc = orders.filter(
    (x: ProductionOrder) => x.status === 'in_progress' && (x.routing_steps_count ?? 0) > 0
  ).length;
  const ordersInRework = orders.filter(
    (x: ProductionOrder) => Boolean(x.notes?.toLowerCase().includes('rework'))
  ).length;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Top Controls Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-serif font-bold text-white flex items-center space-x-2">
            <span>Atelier Workshop Operations</span>
          </h1>
          <p className="text-xs text-slate-400 font-light mt-0.5">
            Production flow, active workstation terminals, and routing quality
          </p>
        </div>

        <div className="flex items-center space-x-2.5">
          <Button
            variant="outline"
            size="sm"
            onClick={() => fetchDashboardOrders(false)}
            disabled={refreshing}
            className="border-white/10 text-slate-300 hover:border-amber-400/30"
          >
            <RefreshCw className={`w-3.5 h-3.5 mr-1.5 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh
          </Button>

          {onNavigateToTab && (
            <>
              <Button
                variant="secondary"
                size="sm"
                onClick={() => onNavigateToTab('orders')}
                className="text-xs"
              >
                <Layers className="w-3.5 h-3.5 mr-1.5" />
                Orders List
              </Button>

              <Button
                variant="gold"
                size="sm"
                onClick={() => onNavigateToTab('optimization')}
                className="text-xs font-semibold shadow-md shadow-amber-500/10"
              >
                <Sparkles className="w-3.5 h-3.5 mr-1.5" />
                CP-SAT Solver
              </Button>
            </>
          )}
        </div>
      </div>

      {/* KPI Metrics */}
      <ProductionMetricsCards
        activeOrders={activeOrders.length}
        completedOrders={completedOrders.length}
        ordersAwaitingQc={ordersAwaitingQc}
        ordersInRework={ordersInRework}
      />

      {/* Active Orders Workstation Grid */}
      {isLoading ? (
        <div className="py-20 text-center text-slate-400 flex flex-col items-center justify-center">
          <RefreshCw className="w-8 h-8 animate-spin text-amber-400 mb-3" />
          <p className="text-xs">Loading production pipeline...</p>
        </div>
      ) : error ? (
        <div className="rounded-2xl border border-rose-500/20 bg-rose-500/10 p-8 text-center">
          <AlertCircle className="w-10 h-10 text-rose-400 mx-auto mb-2" />
          <h3 className="text-sm font-semibold text-white">Unable to load production data</h3>
          <p className="text-xs text-rose-300 mt-1 max-w-md mx-auto">{error}</p>
          <Button
            variant="outline"
            size="sm"
            onClick={() => fetchDashboardOrders(false)}
            className="mt-4 border-rose-500/30 text-rose-300 hover:bg-rose-500/20"
          >
            <RefreshCw className="w-3.5 h-3.5 mr-1.5" /> Retry
          </Button>
        </div>
      ) : (
        <ActiveProductionTable
          orders={activeOrders}
          onOpenShopFloor={onOpenShopFloor}
        />
      )}
    </div>
  );
};
