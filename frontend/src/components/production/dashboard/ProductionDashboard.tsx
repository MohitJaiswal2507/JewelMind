import React, { useEffect, useState, useCallback } from 'react';
import {
  RefreshCw,
  Layers,
  Sparkles,
} from 'lucide-react';
import { Button } from '../../ui/button';
import { ProductionMetricsCards } from './ProductionMetricsCards';
import { ActiveProductionTable } from './ActiveProductionTable';

import { productionService } from '../../../services/api/productionService';
import { ProductionOrder } from '../../../types/production';

interface ProductionDashboardProps {
  onOpenShopFloor: (orderId: string) => void;
  onNavigateToTab?: (tab: 'orders' | 'workers' | 'machines' | 'optimization') => void;
}

export const ProductionDashboard: React.FC<ProductionDashboardProps> = ({
  onOpenShopFloor,
  onNavigateToTab,
}) => {
  const [orders, setOrders] = useState<ProductionOrder[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);

  const fetchDashboardOrders = useCallback(async (isInitial = false) => {
    if (isInitial) setLoading(true);
    else setRefreshing(true);

    try {
      const response = await productionService.getOrders({
        page_size: 50,
      });
      setOrders(response.items);
    } catch (err: unknown) {
      console.error('Failed to load dashboard orders:', err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchDashboardOrders(true);
  }, [fetchDashboardOrders]);

  const activeOrders = orders.filter(
    (x) => x.status === 'in_progress' || x.status === 'pending'
  );
  const completedOrders = orders.filter((x) => x.status === 'completed');

  // Estimate QC / rework counts from order statuses or notes/flags
  const ordersAwaitingQc = orders.filter(
    (x) => x.status === 'in_progress' && (x.routing_steps_count ?? 0) > 0
  ).length;
  const ordersInRework = orders.filter(
    (x) => x.notes?.toLowerCase().includes('rework')
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
      {loading ? (
        <div className="py-20 text-center text-slate-400 flex flex-col items-center justify-center">
          <RefreshCw className="w-8 h-8 animate-spin text-amber-400 mb-3" />
          <p className="text-xs">Loading production pipeline...</p>
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
