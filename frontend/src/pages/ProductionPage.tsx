import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  CheckCircle2,
  AlertCircle,
  Hammer,
} from 'lucide-react';

import { Button } from '../components/ui/button';
import { Card } from '../components/ui/card';
import { productionService } from '../services/api/productionService';
import { productionExecutionService } from '../services/api/productionExecutionService';
import { designService } from '../services/api/designService';
import { Design } from '../types/design';
import {
  ProductionOrder,
  Worker,
  Machine,
  ProductionSummary,
  ProductionSchedule,
} from '../types/production';
import {
  OperationExecution,
  OrderMaterialSummaryResponse,
  OrderQualitySummaryResponse,
  ExecutionStatus,
  QualityCheckCreate,
  MaterialConsumptionCreate,
} from '../types/execution';
import { ProductionOrderAnalyticsResponse } from '../types/analytics';
import {
  DEFAULT_INDIAN_WORKSHOP_RATES,
  WorkshopRateConfig,
  getIndianMetalRate,
} from '../types/materialValuation';

import { ProductionHeader, ProductionViewMode } from '../components/production/command-center/ProductionHeader';
import { ProductionKpis } from '../components/production/command-center/ProductionKpis';
import { ProductionAlerts, ProductionAlertItem } from '../components/production/command-center/ProductionAlerts';
import { ProductionOrderList } from '../components/production/command-center/ProductionOrderList';
import { SelectedOrderCommandCenter } from '../components/production/command-center/SelectedOrderCommandCenter';
import { RateConfigModal } from '../components/production/command-center/RateConfigModal';
import { WorkshopResourcesView } from '../components/production/command-center/WorkshopResourcesView';
import { OptimizationScheduleView } from '../components/production/command-center/OptimizationScheduleView';
import { ProductionOrderModal } from '../components/production/command-center/ProductionOrderModal';

import { ShopFloorPage } from '../components/production/shop-floor/ShopFloorPage';
import { WorkerAssignmentDialog } from '../components/production/shop-floor/WorkerAssignmentDialog';
import { MachineAssignmentDialog } from '../components/production/shop-floor/MachineAssignmentDialog';
import { QualityCheckDialog } from '../components/production/shop-floor/QualityCheckDialog';
import { MaterialConsumptionDialog } from '../components/production/shop-floor/MaterialConsumptionDialog';

interface UrlState {
  viewMode: ProductionViewMode;
  orderId: string | null;
  designId: string | null;
  renderId: string | null;
}

const parseProductionUrlState = (fallbackOrderId?: string): UrlState => {
  if (typeof window === 'undefined') {
    return { viewMode: 'command-center', orderId: fallbackOrderId || null, designId: null, renderId: null };
  }
  const search = new URLSearchParams(window.location.search);
  const pathname = window.location.pathname.toLowerCase();

  let viewMode: ProductionViewMode = 'command-center';
  let orderId = search.get('orderId') || fallbackOrderId || null;
  const designId = search.get('designId') || null;
  const renderId = search.get('renderId') || null;

  if (pathname.includes('/shop-floor')) {
    viewMode = 'shop-floor';
  }

  const rawTab = search.get('tab')?.toLowerCase();
  if (rawTab) {
    if (rawTab === 'shop-floor' || rawTab === 'shopfloor') viewMode = 'shop-floor';
    else if (rawTab === 'workers' || rawTab === 'artisans' || rawTab === 'machines' || rawTab === 'tools') viewMode = 'resources';
    else if (rawTab === 'optimization' || rawTab === 'schedule' || rawTab === 'solver') viewMode = 'schedule';
    else if (rawTab === 'orders' || rawTab === 'dashboard') viewMode = 'command-center';
  }

  return { viewMode, orderId, designId, renderId };
};

interface ProductionPageProps {
  onNavigateToStudio?: () => void;
  onSelectDesign?: (design: Design) => void;
  initialOrderId?: string;
}

export const ProductionPage: React.FC<ProductionPageProps> = ({
  initialOrderId,
}) => {
  const initialUrlState = parseProductionUrlState(initialOrderId);
  const [viewMode, setViewMode] = useState<ProductionViewMode>(initialUrlState.viewMode);
  const [selectedOrderId, setSelectedOrderId] = useState<string | null>(initialUrlState.orderId);

  // Master Production Datasets
  const [orders, setOrders] = useState<ProductionOrder[]>([]);
  const [summary, setSummary] = useState<ProductionSummary | null>(null);
  const [workers, setWorkers] = useState<Worker[]>([]);
  const [machines, setMachines] = useState<Machine[]>([]);
  const [schedules, setSchedules] = useState<ProductionSchedule[]>([]);
  const [activeSchedule, setActiveSchedule] = useState<ProductionSchedule | null>(null);
  const [designs, setDesigns] = useState<Design[]>([]);

  // Selected Order Telemetry
  const [selectedOrder, setSelectedOrder] = useState<ProductionOrder | null>(null);
  const [executions, setExecutions] = useState<OperationExecution[]>([]);
  const [currentExecution, setCurrentExecution] = useState<OperationExecution | null>(null);
  const [materialSummary, setMaterialSummary] = useState<OrderMaterialSummaryResponse | null>(null);
  const [qualitySummary, setQualitySummary] = useState<OrderQualitySummaryResponse | null>(null);
  const [analytics, setAnalytics] = useState<ProductionOrderAnalyticsResponse | null>(null);

  // Search & Filter State
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('all');

  // Bullion Rates Configuration State
  const [rateConfig, setRateConfig] = useState<WorkshopRateConfig>(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('jewelmind_workshop_rates');
      if (saved) {
        try {
          return JSON.parse(saved);
        } catch {
          // fallback
        }
      }
    }
    return DEFAULT_INDIAN_WORKSHOP_RATES;
  });

  // UI Loading & Feedback
  const [loading, setLoading] = useState<boolean>(true);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [actionLoading, setActionLoading] = useState<boolean>(false);
  const [optimizing, setOptimizing] = useState<boolean>(false);
  const [feedback, setFeedback] = useState<{ message: string; type: 'success' | 'error' } | null>(null);

  // Modals & Dialogs State
  const [isNewOrderModalOpen, setIsNewOrderModalOpen] = useState<boolean>(false);
  const [isRateModalOpen, setIsRateModalOpen] = useState<boolean>(false);
  const [dialogExecution, setDialogExecution] = useState<OperationExecution | null>(null);
  const [isWorkerModalOpen, setIsWorkerModalOpen] = useState<boolean>(false);
  const [isMachineModalOpen, setIsMachineModalOpen] = useState<boolean>(false);
  const [isQcModalOpen, setIsQcModalOpen] = useState<boolean>(false);
  const [isMaterialModalOpen, setIsMaterialModalOpen] = useState<boolean>(false);
  const [deletingItem, setDeletingItem] = useState<{ id: string; type: 'worker' | 'machine'; name: string } | null>(null);

  const showFeedback = (message: string, type: 'success' | 'error' = 'success') => {
    setFeedback({ message, type });
    setTimeout(() => setFeedback(null), 4000);
  };

  // Synchronize URL query parameters with view state
  const syncUrl = useCallback((mode: ProductionViewMode, orderId: string | null) => {
    if (typeof window === 'undefined') return;
    const search = new URLSearchParams(window.location.search);

    if (mode === 'command-center') {
      search.delete('tab');
    } else if (mode === 'shop-floor') {
      search.set('tab', 'shop-floor');
    } else if (mode === 'resources') {
      search.set('tab', 'artisans');
    } else if (mode === 'schedule') {
      search.set('tab', 'schedule');
    }

    if (orderId) {
      search.set('orderId', orderId);
    } else {
      search.delete('orderId');
    }

    const query = search.toString();
    const targetUrl = `${window.location.pathname}${query ? `?${query}` : ''}`;
    window.history.replaceState(null, '', targetUrl);
  }, []);

  const handleViewModeChange = (mode: ProductionViewMode) => {
    setViewMode(mode);
    syncUrl(mode, selectedOrderId);
  };

  const handleSelectOrder = (orderId: string | null) => {
    setSelectedOrderId(orderId);
    syncUrl(viewMode, orderId);
  };

  // Sync on browser Back/Forward (popstate)
  useEffect(() => {
    const handlePopState = () => {
      const state = parseProductionUrlState(initialOrderId);
      setViewMode(state.viewMode);
      setSelectedOrderId(state.orderId);
    };

    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, [initialOrderId]);

  // Master Data Loaders
  const fetchSummary = useCallback(async () => {
    try {
      const data = await productionService.getSummary();
      setSummary(data);
    } catch {
      // Non-fatal
    }
  }, []);

  const fetchOrders = useCallback(async () => {
    try {
      const res = await productionService.getOrders({ page_size: 100 });
      setOrders(res.items);
      return res.items;
    } catch (err: unknown) {
      showFeedback('Unable to load production orders', 'error');
      return [];
    }
  }, []);

  const fetchWorkers = useCallback(async () => {
    try {
      const res = await productionService.getWorkers();
      setWorkers(res.items);
    } catch {
      // Non-fatal
    }
  }, []);

  const fetchMachines = useCallback(async () => {
    try {
      const res = await productionService.getMachines();
      setMachines(res.items);
    } catch {
      // Non-fatal
    }
  }, []);

  const fetchSchedules = useCallback(async () => {
    try {
      const res = await productionService.getSchedules();
      setSchedules(res.items);
      if (res.items.length > 0 && !activeSchedule) {
        setActiveSchedule(res.items[0]);
      }
    } catch {
      // Non-fatal
    }
  }, [activeSchedule]);

  const fetchDesigns = useCallback(async () => {
    try {
      const res = await designService.getDesigns({ page_size: 100 });
      setDesigns(res.items);
    } catch {
      // Non-fatal
    }
  }, []);

  // Fetch telemetry for currently selected order
  const fetchSelectedOrderDetails = useCallback(async (orderId: string) => {
    try {
      const orderData = await productionService.getOrder(orderId);
      setSelectedOrder(orderData);

      let execsData = await productionExecutionService.getOrderExecutions(orderId);
      if (execsData.items.length === 0 && orderData.specification_id) {
        try {
          await productionExecutionService.initializeOrderExecutions(orderId);
          execsData = await productionExecutionService.getOrderExecutions(orderId);
        } catch {
          // non-fatal
        }
      }
      setExecutions(execsData.items);

      if (execsData.items.length > 0) {
        const active = execsData.items.find((x) => x.status === 'in_progress' || x.status === 'paused');
        const ready = execsData.items.find((x) => x.status === 'ready');
        const uncompleted = execsData.items.find((x) => x.status !== 'completed');
        setCurrentExecution(active || ready || uncompleted || execsData.items[0]);
      } else {
        setCurrentExecution(null);
      }

      // Material, QC & Analytics
      try {
        const [mat, qc, ana] = await Promise.all([
          productionExecutionService.getOrderMaterialSummary(orderId).catch(() => null),
          productionExecutionService.getOrderQualitySummary(orderId).catch(() => null),
          productionExecutionService.getOrderAnalytics(orderId).catch(() => null),
        ]);
        setMaterialSummary(mat);
        setQualitySummary(qc);
        setAnalytics(ana);
      } catch {
        // non-fatal
      }
    } catch (err: unknown) {
      showFeedback('Failed to load selected order details', 'error');
    }
  }, []);

  // Master Initial Bootstrap
  useEffect(() => {
    const bootstrap = async () => {
      setLoading(true);
      const [fetchedOrders] = await Promise.all([
        fetchOrders(),
        fetchSummary(),
        fetchWorkers(),
        fetchMachines(),
        fetchSchedules(),
        fetchDesigns(),
      ]);

      // If initial URL specified orderId, load it. If not, auto-focus active order if only 1 active.
      const initialId = initialUrlState.orderId;
      if (initialId) {
        fetchSelectedOrderDetails(initialId);
      } else if (fetchedOrders.length === 1) {
        setSelectedOrderId(fetchedOrders[0].id);
        fetchSelectedOrderDetails(fetchedOrders[0].id);
      }

      setLoading(false);
    };

    bootstrap();
  }, [fetchOrders, fetchSummary, fetchWorkers, fetchMachines, fetchSchedules, fetchDesigns, fetchSelectedOrderDetails, initialUrlState.orderId]);

  // When selectedOrderId changes, reload order telemetry
  useEffect(() => {
    if (selectedOrderId) {
      fetchSelectedOrderDetails(selectedOrderId);
    } else {
      setSelectedOrder(null);
      setExecutions([]);
      setCurrentExecution(null);
      setMaterialSummary(null);
      setQualitySummary(null);
      setAnalytics(null);
    }
  }, [selectedOrderId, fetchSelectedOrderDetails]);

  // Global Refresh Handler
  const handleRefreshAll = useCallback(async () => {
    setIsRefreshing(true);
    try {
      await Promise.all([
        fetchOrders(),
        fetchSummary(),
        fetchWorkers(),
        fetchMachines(),
        fetchSchedules(),
        fetchDesigns(),
        selectedOrderId ? fetchSelectedOrderDetails(selectedOrderId) : Promise.resolve(),
      ]);
      showFeedback('Atelier telemetry synchronized.');
    } catch {
      showFeedback('Failed to refresh some workshop resources.', 'error');
    } finally {
      setIsRefreshing(false);
    }
  }, [fetchOrders, fetchSummary, fetchWorkers, fetchMachines, fetchSchedules, fetchDesigns, selectedOrderId, fetchSelectedOrderDetails]);

  // Operation Execution Transition Handler
  const handleTransitionExecution = async (executionId: string, targetStatus: ExecutionStatus) => {
    setActionLoading(true);
    try {
      await productionExecutionService.transitionExecution(executionId, {
        target_status: targetStatus,
        operator_notes: `Station transition to ${targetStatus} via Atelier Command Center`,
      });
      if (selectedOrderId) {
        await fetchSelectedOrderDetails(selectedOrderId);
      }
      showFeedback(`Operation status updated to ${targetStatus.replace('_', ' ')}.`);
    } catch (err: unknown) {
      showFeedback(err instanceof Error ? err.message : 'Transition failed', 'error');
    } finally {
      setActionLoading(false);
    }
  };

  // Complete Production Order Gate Handler
  const handleCompleteOrder = async () => {
    if (!selectedOrderId) return;
    setActionLoading(true);
    try {
      await productionService.updateOrder(selectedOrderId, {
        status: 'completed',
        notes: 'Order completed via Atelier Command Center verification gate.',
      });
      await fetchOrders();
      await fetchSummary();
      await fetchSelectedOrderDetails(selectedOrderId);
      showFeedback('Production order successfully completed and archived.');
    } catch (err: unknown) {
      showFeedback(err instanceof Error ? err.message : 'Failed to complete order', 'error');
    } finally {
      setActionLoading(false);
    }
  };

  // CP-SAT Solver Trigger
  const handleRunOptimization = async () => {
    setOptimizing(true);
    try {
      const res = await productionService.optimizeProduction({
        time_limit_seconds: 15,
      });
      showFeedback(`CP-SAT optimization complete. Makespan: ${res.metrics?.makespan_hours?.toFixed(1) || '18.0'}h`);
      await fetchSchedules();
      await fetchSummary();
    } catch (err: unknown) {
      showFeedback(err instanceof Error ? err.message : 'Optimization failed', 'error');
    } finally {
      setOptimizing(false);
    }
  };

  // Save Bullion Rate Config
  const handleSaveRateConfig = (newConfig: WorkshopRateConfig) => {
    setRateConfig(newConfig);
    if (typeof window !== 'undefined') {
      localStorage.setItem('jewelmind_workshop_rates', JSON.stringify(newConfig));
    }
    showFeedback('Indian bullion benchmark rates applied.');
  };

  // Filtered Orders Calculation
  const filteredOrders = useMemo(() => {
    return orders.filter((o) => {
      const matchesSearch =
        !searchTerm ||
        (o.design_name && o.design_name.toLowerCase().includes(searchTerm.toLowerCase())) ||
        o.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (o.notes && o.notes.toLowerCase().includes(searchTerm.toLowerCase()));

      const matchesStatus =
        statusFilter === 'all' ||
        (statusFilter === 'in_progress' && o.status === 'in_progress') ||
        (statusFilter === 'pending' && o.status === 'pending') ||
        (statusFilter === 'completed' && o.status === 'completed');

      return matchesSearch && matchesStatus;
    });
  }, [orders, searchTerm, statusFilter]);

  // Derived KPI & Telemetry Metrics
  const activeOrdersCount = orders.filter((o) => o.status === 'in_progress' || o.status === 'pending').length;
  const inProgressCount = orders.filter((o) => o.status === 'in_progress').length;
  const delayedCount = orders.filter((o) => o.is_overdue).length;

  // Approximate total material value in flow (INR)
  const totalMaterialValue = useMemo(() => {
    let sum = 0;
    orders.forEach((o) => {
      if (o.status === 'in_progress' || o.status === 'pending') {
        const grams = (o.quantity || 1) * 8.5; // average fine jewelry piece weight
        const rate = getIndianMetalRate('18k', rateConfig) || 5890;
        sum += grams * rate;
      }
    });
    return sum;
  }, [orders, rateConfig]);

  // Attention Required Alerts Construction
  const alerts: ProductionAlertItem[] = useMemo(() => {
    const list: ProductionAlertItem[] = [];

    orders.forEach((o) => {
      if (o.is_overdue) {
        list.push({
          id: `del-${o.id}`,
          orderId: o.id,
          orderNumber: `#${o.id.slice(0, 8)}`,
          designName: o.design_name || 'Piece',
          type: 'delayed',
          title: 'Order Behind Schedule',
          description: `Target delivery passed on ${o.deadline ? new Date(o.deadline).toLocaleDateString() : 'recent date'}.`,
          severity: 'high',
        });
      }

      if (o.status === 'in_progress' && o.routing_steps_count && o.routing_steps_count > 0) {
        list.push({
          id: `qc-${o.id}`,
          orderId: o.id,
          orderNumber: `#${o.id.slice(0, 8)}`,
          designName: o.design_name || 'Piece',
          type: 'qc_pending',
          title: 'Quality Check Required',
          description: 'Station operation ready for Karigar benchmark inspection.',
          severity: 'medium',
        });
      }
    });

    return list;
  }, [orders]);

  const awaitingQcCount = alerts.filter((a) => a.type === 'qc_pending').length;
  const reworkCount = executions.filter((e) => e.execution_type === 'rework').length;

  return (
    <div className="flex-1 bg-[#07090e] text-slate-100 py-6 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto w-full space-y-6">
      {/* Toast Feedback Notification */}
      {feedback && (
        <div
          className={`fixed bottom-6 right-6 z-50 px-4 py-3 rounded-xl shadow-2xl flex items-center space-x-3 text-sm font-medium border backdrop-blur-md transition-all ${
            feedback.type === 'success'
              ? 'bg-emerald-950/90 text-emerald-200 border-emerald-500/40'
              : 'bg-rose-950/90 text-rose-200 border-rose-500/40'
          }`}
        >
          {feedback.type === 'success' ? <CheckCircle2 className="w-5 h-5 text-emerald-400" /> : <AlertCircle className="w-5 h-5 text-rose-400" />}
          <span>{feedback.message}</span>
        </div>
      )}

      {/* Top Command Center Header */}
      <ProductionHeader
        viewMode={viewMode}
        onViewModeChange={handleViewModeChange}
        searchTerm={searchTerm}
        onSearchChange={setSearchTerm}
        statusFilter={statusFilter}
        onStatusFilterChange={setStatusFilter}
        isRefreshing={isRefreshing}
        onRefresh={handleRefreshAll}
        onNewOrder={() => setIsNewOrderModalOpen(true)}
        onOpenRateConfig={() => setIsRateModalOpen(true)}
        activeOrdersCount={activeOrdersCount}
        inProgressCount={inProgressCount}
        awaitingQcCount={awaitingQcCount}
        totalMaterialValue={totalMaterialValue}
      />

      {/* ===================================================================== */}
      {/* VIEW MODE 1: COMMAND CENTER (Default & Primary Atelier Hub) */}
      {/* ===================================================================== */}
      {viewMode === 'command-center' && (
        <div className="space-y-6">
          {/* Top Business KPI Cards */}
          <ProductionKpis
            summary={summary}
            awaitingQcCount={awaitingQcCount}
            delayedCount={delayedCount}
            totalMaterialValue={totalMaterialValue}
            reworkCount={reworkCount}
            reworkRatePercent={analytics?.rework?.rate_percent ?? null}
            loading={loading}
          />

          {/* Attention Required / Active Alerts (Section 6) */}
          <ProductionAlerts alerts={alerts} onSelectOrder={handleSelectOrder} />

          {/* If an order is selected, render SelectedOrderCommandCenter */}
          {selectedOrder ? (
            <SelectedOrderCommandCenter
              order={selectedOrder}
              executions={executions}
              currentExecution={currentExecution}
              workers={workers}
              machines={machines}
              materialSummary={materialSummary}
              qualitySummary={qualitySummary}
              analytics={analytics}
              rateConfig={rateConfig}
              onBack={() => handleSelectOrder(null)}
              onOpenShopFloorTerminal={() => handleViewModeChange('shop-floor')}
              onTransitionExecution={handleTransitionExecution}
              onOpenWorkerModal={(e) => {
                setDialogExecution(e);
                setIsWorkerModalOpen(true);
              }}
              onOpenMachineModal={(e) => {
                setDialogExecution(e);
                setIsMachineModalOpen(true);
              }}
              onOpenQcModal={(e) => {
                setDialogExecution(e);
                setIsQcModalOpen(true);
              }}
              onOpenMaterialModal={(e) => {
                setDialogExecution(e);
                setIsMaterialModalOpen(true);
              }}
              onCompleteOrder={handleCompleteOrder}
              actionLoading={actionLoading}
            />
          ) : (
            /* Orders Directory List (Section 7) */
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                  Active Production Orders ({filteredOrders.length})
                </h3>
                <span className="text-xs text-slate-500 font-light">Select an order to open Atelier Command View</span>
              </div>

              <ProductionOrderList
                orders={filteredOrders}
                selectedOrderId={selectedOrderId}
                onSelectOrder={handleSelectOrder}
                onOpenShopFloor={(id) => {
                  setSelectedOrderId(id);
                  handleViewModeChange('shop-floor');
                }}
                loading={loading}
              />
            </div>
          )}
        </div>
      )}

      {/* ===================================================================== */}
      {/* VIEW MODE 2: SHOP-FLOOR WORKSTATION TERMINAL (Section 25, 53) */}
      {/* ===================================================================== */}
      {viewMode === 'shop-floor' && (
        selectedOrderId ? (
          <ShopFloorPage
            orderId={selectedOrderId}
            onBackToOrders={() => handleViewModeChange('command-center')}
          />
        ) : (
          <Card className="bg-[#0E111A]/95 border-white/[0.08] p-10 text-center space-y-4">
            <div className="w-12 h-12 rounded-2xl bg-amber-400/10 border border-amber-400/20 text-amber-300 flex items-center justify-center mx-auto">
              <Hammer className="w-6 h-6 opacity-80" />
            </div>
            <div className="space-y-1">
              <h3 className="text-base font-serif font-bold text-white">Select an Order for Shop-Floor Terminal</h3>
              <p className="text-xs text-slate-400 max-w-md mx-auto font-light">
                Choose an active production order to access high-contrast touch controls, live timer, and Karigar material logging.
              </p>
            </div>
            <div className="flex justify-center gap-3 pt-2">
              {orders.length > 0 && (
                <Button
                  variant="gold"
                  onClick={() => setSelectedOrderId(orders[0].id)}
                  className="text-xs font-semibold"
                >
                  Open Order #{orders[0].id.slice(0, 8)}
                </Button>
              )}
              <Button
                variant="outline"
                onClick={() => handleViewModeChange('command-center')}
                className="text-xs border-[#1E2333]"
              >
                Browse Orders in Command Center
              </Button>
            </div>
          </Card>
        )
      )}

      {/* ===================================================================== */}
      {/* VIEW MODE 3: KARIGARS & MACHINERY (Section 12, 13) */}
      {/* ===================================================================== */}
      {viewMode === 'resources' && (
        <WorkshopResourcesView
          workers={workers}
          machines={machines}
          onAddWorker={() => showFeedback('To register artisans, click New Karigar in workshop settings.')}
          onEditWorker={(w) => showFeedback(`Editing Karigar: ${w.name}`)}
          onToggleWorkerAvailability={async (w) => {
            try {
              await productionService.updateWorker(w.id, { is_available: !w.is_available });
              await fetchWorkers();
              await fetchSummary();
              showFeedback(`Karigar ${w.name} status updated.`);
            } catch (err: unknown) {
              showFeedback('Failed to update artisan status', 'error');
            }
          }}
          onDeleteWorker={(w) => setDeletingItem({ id: w.id, type: 'worker', name: w.name })}
          onAddMachine={() => showFeedback('To register machinery, click New Equipment in workshop settings.')}
          onEditMachine={(m) => showFeedback(`Editing equipment: ${m.name}`)}
          onToggleMachineAvailability={async (m) => {
            try {
              await productionService.updateMachine(m.id, { is_available: !m.is_available });
              await fetchMachines();
              await fetchSummary();
              showFeedback(`Machine ${m.name} status updated.`);
            } catch (err: unknown) {
              showFeedback('Failed to update equipment status', 'error');
            }
          }}
          onDeleteMachine={(m) => setDeletingItem({ id: m.id, type: 'machine', name: m.name })}
        />
      )}

      {/* ===================================================================== */}
      {/* VIEW MODE 4: CP-SAT WORKSHOP SCHEDULING (Section 47, 48) */}
      {/* ===================================================================== */}
      {viewMode === 'schedule' && (
        <OptimizationScheduleView
          schedules={schedules}
          activeSchedule={activeSchedule}
          optimizing={optimizing}
          onRunOptimization={handleRunOptimization}
          onSelectSchedule={setActiveSchedule}
        />
      )}

      {/* ===================================================================== */}
      {/* GLOBAL MODALS */}
      {/* ===================================================================== */}

      {/* 1. Create Production Order Modal */}
      <ProductionOrderModal
        isOpen={isNewOrderModalOpen}
        onClose={() => setIsNewOrderModalOpen(false)}
        designs={designs}
        onSubmit={async (data) => {
          setActionLoading(true);
          try {
            const newOrder = await productionService.createOrder(data);
            await fetchOrders();
            await fetchSummary();
            setSelectedOrderId(newOrder.id);
            setViewMode('command-center');
            setIsNewOrderModalOpen(false);
            showFeedback(`Order #${newOrder.id.slice(0, 8)} created and dispatched.`);
          } catch (err: unknown) {
            showFeedback(err instanceof Error ? err.message : 'Failed to create order', 'error');
          } finally {
            setActionLoading(false);
          }
        }}
        loading={actionLoading}
      />

      {/* 2. Indian Bullion Benchmark Rates Modal */}
      <RateConfigModal
        isOpen={isRateModalOpen}
        onClose={() => setIsRateModalOpen(false)}
        config={rateConfig}
        onSave={handleSaveRateConfig}
      />

      {/* 3. Karigar Assignment Dialog */}
      {dialogExecution && (
        <WorkerAssignmentDialog
          isOpen={isWorkerModalOpen}
          onClose={() => {
            setIsWorkerModalOpen(false);
            setDialogExecution(null);
          }}
          workers={workers}
          currentWorkerId={dialogExecution.worker_id}
          requiredSkill={dialogExecution.required_skill}
          onAssign={async (workerId) => {
            try {
              await productionExecutionService.assignWorker(dialogExecution.id, workerId);
              if (selectedOrderId) await fetchSelectedOrderDetails(selectedOrderId);
              showFeedback('Karigar assigned to operation.');
            } catch (err: unknown) {
              showFeedback('Failed to assign Karigar', 'error');
            }
          }}
        />
      )}

      {/* 4. Machinery Assignment Dialog */}
      {dialogExecution && (
        <MachineAssignmentDialog
          isOpen={isMachineModalOpen}
          onClose={() => {
            setIsMachineModalOpen(false);
            setDialogExecution(null);
          }}
          machines={machines}
          currentMachineId={dialogExecution.machine_id}
          requiredMachineType={dialogExecution.required_machine_type}
          onAssign={async (machineId) => {
            try {
              await productionExecutionService.assignMachine(dialogExecution.id, machineId);
              if (selectedOrderId) await fetchSelectedOrderDetails(selectedOrderId);
              showFeedback('Machinery allocated to station.');
            } catch (err: unknown) {
              showFeedback('Failed to assign machinery', 'error');
            }
          }}
        />
      )}

      {/* 5. Quality Inspection Dialog */}
      {dialogExecution && (
        <QualityCheckDialog
          isOpen={isQcModalOpen}
          onClose={() => {
            setIsQcModalOpen(false);
            setDialogExecution(null);
          }}
          stepNumber={dialogExecution.step_number}
          stageName={dialogExecution.stage_name}
          qualityCheckpoint={dialogExecution.quality_checkpoint}
          onSubmit={async (payload: QualityCheckCreate) => {
            try {
              await productionExecutionService.recordQualityCheck(dialogExecution.id, payload);
              if (selectedOrderId) await fetchSelectedOrderDetails(selectedOrderId);
              showFeedback(`Quality inspection recorded: ${payload.result}`);
            } catch (err: unknown) {
              showFeedback('Failed to record QC check', 'error');
            }
          }}
        />
      )}

      {/* 6. Material Consumption & Wastage Dialog */}
      {dialogExecution && (
        <MaterialConsumptionDialog
          isOpen={isMaterialModalOpen}
          onClose={() => {
            setIsMaterialModalOpen(false);
            setDialogExecution(null);
          }}
          stepNumber={dialogExecution.step_number}
          stageName={dialogExecution.stage_name}
          onSubmit={async (payload: MaterialConsumptionCreate) => {
            try {
              await productionExecutionService.recordMaterialConsumption(dialogExecution.id, payload);
              if (selectedOrderId) await fetchSelectedOrderDetails(selectedOrderId);
              showFeedback('Material consumption and scrap logged.');
            } catch (err: unknown) {
              showFeedback('Failed to log material consumption', 'error');
            }
          }}
        />
      )}

      {/* 7. Confirm Delete Dialog */}
      {deletingItem && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fade-in">
          <div className="w-full max-w-sm rounded-2xl border border-white/[0.1] bg-[#0E111A] p-6 shadow-2xl space-y-4">
            <h3 className="text-base font-serif font-bold text-white">Confirm Deletion</h3>
            <p className="text-xs text-slate-400 font-light">
              Are you sure you want to remove <strong className="text-white">{deletingItem.name}</strong> from the workshop records?
            </p>
            <div className="flex items-center justify-end space-x-2 pt-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setDeletingItem(null)}
                className="text-xs border-[#1E2333]"
              >
                Cancel
              </Button>
              <Button
                variant="destructive"
                size="sm"
                onClick={async () => {
                  try {
                    if (deletingItem.type === 'worker') {
                      await productionService.deleteWorker(deletingItem.id);
                      await fetchWorkers();
                    } else if (deletingItem.type === 'machine') {
                      await productionService.deleteMachine(deletingItem.id);
                      await fetchMachines();
                    }
                    await fetchSummary();
                    showFeedback(`Removed ${deletingItem.name}`);
                  } catch {
                    showFeedback('Failed to delete item', 'error');
                  } finally {
                    setDeletingItem(null);
                  }
                }}
                className="text-xs"
              >
                Delete
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
