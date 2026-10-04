import React, { useState, useEffect, useCallback } from 'react';
import {
  Factory,
  Users,
  Cpu,
  Plus,
  Search,
  AlertTriangle,
  Clock,
  CheckCircle2,
  Layers,
  Edit2,
  Trash2,
  RefreshCw,
  X,
  AlertCircle,
  TrendingUp,
  Sparkles,
  Calendar,
  Sliders,
  Timer,
  Play,
  History,
  ShieldCheck,
} from 'lucide-react';

import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Textarea } from '../components/ui/textarea';
import { productionService } from '../services/api/productionService';
import { designService } from '../services/api/designService';
import { Design } from '../types/design';
import {
  ProductionOrder,
  Worker,
  Machine,
  ProductionSummary,
  OrderPriority,
  OrderStatus,
  ORDER_PRIORITIES,
  ORDER_STATUSES,
  WORKER_SKILLS,
  MACHINE_TYPES,
  ProductionSchedule,
  ScheduledTask,
  OptimizationResponse,
} from '../types/production';

import { ShopFloorPage } from '../components/production/shop-floor/ShopFloorPage';
import { ProductionDashboard } from '../components/production/dashboard/ProductionDashboard';

type ActiveTab = 'dashboard' | 'orders' | 'shop-floor' | 'workers' | 'machines' | 'optimization';

const parseProductionUrlState = (fallbackTab: ActiveTab = 'dashboard', fallbackOrderId?: string): { tab: ActiveTab; orderId: string | null; designId: string | null; renderId: string | null } => {
  if (typeof window === 'undefined') {
    return { tab: fallbackTab, orderId: fallbackOrderId || null, designId: null, renderId: null };
  }
  const search = new URLSearchParams(window.location.search);
  const pathname = window.location.pathname.toLowerCase();

  let tab = fallbackTab;
  let orderId = search.get('orderId') || fallbackOrderId || null;
  const designId = search.get('designId') || null;
  const renderId = search.get('renderId') || null;

  if (pathname.includes('/shop-floor')) {
    tab = 'shop-floor';
  }

  const rawTab = search.get('tab');
  if (rawTab) {
    const norm = rawTab.toLowerCase();
    if (norm === 'orders') tab = 'orders';
    else if (norm === 'workers' || norm === 'artisans') tab = 'workers';
    else if (norm === 'machines' || norm === 'tools') tab = 'machines';
    else if (norm === 'optimization' || norm === 'schedule' || norm === 'solver') tab = 'optimization';
    else if (norm === 'shop-floor' || norm === 'shopfloor') tab = 'shop-floor';
    else if (norm === 'dashboard') tab = 'dashboard';
  } else if (designId) {
    // If arriving with designId from Studio, show orders tab
    tab = 'orders';
  }

  return { tab, orderId, designId, renderId };
};

interface ProductionPageProps {
  onNavigateToStudio?: () => void;
  onSelectDesign?: (design: Design) => void;
  initialTab?: ActiveTab;
  initialOrderId?: string;
}

export const ProductionPage: React.FC<ProductionPageProps> = ({
  initialTab = 'dashboard',
  initialOrderId,
}) => {
  const initialUrlState = parseProductionUrlState(initialTab, initialOrderId);
  const [activeTab, setActiveTab] = useState<ActiveTab>(initialUrlState.tab);
  const [shopFloorOrderId, setShopFloorOrderId] = useState<string | null>(initialUrlState.orderId);
  const [summary, setSummary] = useState<ProductionSummary | null>(null);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);

  // Tab switcher with URL query parameter synchronization
  const switchTab = (tab: ActiveTab, orderId?: string | null) => {
    setActiveTab(tab);
    if (orderId !== undefined) {
      setShopFloorOrderId(orderId);
    }

    if (typeof window !== 'undefined') {
      const search = new URLSearchParams(window.location.search);
      if (tab === 'dashboard') {
        search.delete('tab');
      } else {
        search.set('tab', tab);
      }

      const targetOrderId = orderId !== undefined ? orderId : shopFloorOrderId;
      if (tab === 'shop-floor' && targetOrderId) {
        search.set('orderId', targetOrderId);
      } else if (tab !== 'shop-floor') {
        search.delete('orderId');
      }

      const query = search.toString();
      const basePath = window.location.pathname.includes('/shop-floor') && tab !== 'shop-floor' ? '/production' : window.location.pathname;
      const targetUrl = `${basePath}${query ? `?${query}` : ''}`;
      window.history.replaceState(null, '', targetUrl);
    }
  };

  // Sync tab on browser Back/Forward (popstate)
  useEffect(() => {
    const handlePopState = () => {
      const { tab, orderId } = parseProductionUrlState(initialTab, initialOrderId);
      setActiveTab(tab);
      if (orderId) setShopFloorOrderId(orderId);
    };

    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, [initialTab, initialOrderId]);

  // -------------------------------------------------------------------------
  // Orders State
  // -------------------------------------------------------------------------
  const [orders, setOrders] = useState<ProductionOrder[]>([]);
  const [totalOrders, setTotalOrders] = useState<number>(0);
  const [loadingOrders, setLoadingOrders] = useState<boolean>(false);
  const [orderSearch, setOrderSearch] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<OrderStatus | ''>('');
  const [priorityFilter, setPriorityFilter] = useState<OrderPriority | ''>('');
  const [orderPage, setOrderPage] = useState<number>(1);

  // -------------------------------------------------------------------------
  // Workers State
  // -------------------------------------------------------------------------
  const [workers, setWorkers] = useState<Worker[]>([]);
  const [loadingWorkers, setLoadingWorkers] = useState<boolean>(false);

  // -------------------------------------------------------------------------
  // Machines State
  // -------------------------------------------------------------------------
  const [machines, setMachines] = useState<Machine[]>([]);
  const [loadingMachines, setLoadingMachines] = useState<boolean>(false);

  // -------------------------------------------------------------------------
  // User Designs (for Order Creation)
  // -------------------------------------------------------------------------
  const [userDesigns, setUserDesigns] = useState<Design[]>([]);

  // -------------------------------------------------------------------------
  // Optimization & Schedule State (Phase 12)
  // -------------------------------------------------------------------------
  const [schedules, setSchedules] = useState<ProductionSchedule[]>([]);
  const [activeSchedule, setActiveSchedule] = useState<ProductionSchedule | null>(null);
  const [optimizationResult, setOptimizationResult] = useState<OptimizationResponse | null>(null);
  const [optimizing, setOptimizing] = useState<boolean>(false);
  const [horizonDays, setHorizonDays] = useState<number>(14);
  const [timeLimitSec, setTimeLimitSec] = useState<number>(10);
  const [optScheduleName, setOptScheduleName] = useState<string>('');
  const [timelineGroupBy, setTimelineGroupBy] = useState<'worker' | 'machine' | 'order'>('worker');
  const [selectedTaskDetail, setSelectedTaskDetail] = useState<ScheduledTask | null>(null);

  // -------------------------------------------------------------------------
  // Modals
  // -------------------------------------------------------------------------
  const [isOrderModalOpen, setIsOrderModalOpen] = useState<boolean>(false);
  const [editingOrder, setEditingOrder] = useState<ProductionOrder | null>(null);
  const [orderCreationMode, setOrderCreationMode] = useState<'specification' | 'design'>('specification');
  const [specInputId, setSpecInputId] = useState<string>('');

  const [isWorkerModalOpen, setIsWorkerModalOpen] = useState<boolean>(false);
  const [editingWorker, setEditingWorker] = useState<Worker | null>(null);

  const [isMachineModalOpen, setIsMachineModalOpen] = useState<boolean>(false);
  const [editingMachine, setEditingMachine] = useState<Machine | null>(null);

  const [deletingItem, setDeletingItem] = useState<{ type: 'order' | 'worker' | 'machine' | 'schedule'; id: string; name: string } | null>(null);

  // Feedback notifications
  const [feedback, setFeedback] = useState<{ message: string; type: 'success' | 'error' } | null>(null);

  const showFeedback = (message: string, type: 'success' | 'error' = 'success') => {
    setFeedback({ message, type });
    setTimeout(() => setFeedback(null), 4000);
  };

  // -------------------------------------------------------------------------
  // Fetch Functions
  // -------------------------------------------------------------------------
  const fetchSummary = useCallback(async () => {
    try {
      const data = await productionService.getSummary();
      setSummary(data);
    } catch (err: unknown) {
      console.error('Failed to load production summary:', err);
    }
  }, []);

  const fetchOrders = useCallback(async () => {
    setLoadingOrders(true);
    try {
      const data = await productionService.getOrders({
        status: statusFilter || undefined,
        priority: priorityFilter || undefined,
        search: orderSearch || undefined,
        page: orderPage,
        page_size: 20,
      });
      setOrders(data.items);
      setTotalOrders(data.total);
    } catch (err: unknown) {
      showFeedback(err instanceof Error ? err.message : 'Failed to fetch production orders', 'error');
    } finally {
      setLoadingOrders(false);
    }
  }, [statusFilter, priorityFilter, orderSearch, orderPage]);

  const fetchWorkers = useCallback(async () => {
    setLoadingWorkers(true);
    try {
      const data = await productionService.getWorkers();
      setWorkers(data.items);
    } catch (err: unknown) {
      showFeedback(err instanceof Error ? err.message : 'Failed to fetch workers', 'error');
    } finally {
      setLoadingWorkers(false);
    }
  }, []);

  const fetchMachines = useCallback(async () => {
    setLoadingMachines(true);
    try {
      const data = await productionService.getMachines();
      setMachines(data.items);
    } catch (err: unknown) {
      showFeedback(err instanceof Error ? err.message : 'Failed to fetch machines', 'error');
    } finally {
      setLoadingMachines(false);
    }
  }, []);

  const fetchUserDesigns = useCallback(async () => {
    try {
      const data = await designService.getDesigns({ page_size: 100 });
      setUserDesigns(data.items);
    } catch (err: unknown) {
      console.error('Failed to load user designs for order picker:', err);
    }
  }, []);

  const fetchSchedules = useCallback(async () => {
    try {
      const data = await productionService.getSchedules(20, 0);
      setSchedules(data.items);
      if (data.items.length > 0) {
        setActiveSchedule((prev) => prev || data.items[0]);
      }
    } catch (err: unknown) {
      console.error('Failed to load saved schedules:', err);
    }
  }, []);

  useEffect(() => {
    fetchSummary();
    fetchOrders();
    fetchWorkers();
    fetchMachines();
    fetchUserDesigns();
    fetchSchedules();
  }, [fetchSummary, fetchOrders, fetchWorkers, fetchMachines, fetchUserDesigns, fetchSchedules]);

  const handleRefreshAll = useCallback(async () => {
    setIsRefreshing(true);
    try {
      await Promise.all([
        fetchSummary(),
        fetchOrders(),
        fetchWorkers(),
        fetchMachines(),
        fetchUserDesigns(),
        fetchSchedules(),
      ]);
      showFeedback('Production data synchronized.');
    } catch {
      showFeedback('Failed to refresh some workshop resources.', 'error');
    } finally {
      setIsRefreshing(false);
    }
  }, [fetchSummary, fetchOrders, fetchWorkers, fetchMachines, fetchUserDesigns, fetchSchedules]);

  const handleRunOptimization = async () => {
    setOptimizing(true);
    setOptimizationResult(null);
    try {
      const res = await productionService.optimizeProduction({
        horizon_days: horizonDays,
        time_limit_seconds: timeLimitSec,
        schedule_name: optScheduleName.trim() || undefined,
        persist_schedule: true,
      });
      setOptimizationResult(res);
      if (res.status === 'success' || res.status === 'feasible') {
        showFeedback(`Schedule generated: ${res.solver_status} (${res.metrics.makespan_hours}h makespan)`);
        await fetchSchedules();
        if (res.schedule_id) {
          const loaded = await productionService.getSchedule(res.schedule_id);
          setActiveSchedule(loaded);
        }
      } else {
        showFeedback(res.message || 'Optimization infeasible with current workshop constraints', 'error');
      }
    } catch (err: unknown) {
      showFeedback(err instanceof Error ? err.message : 'Optimization failed', 'error');
    } finally {
      setOptimizing(false);
    }
  };

  // -------------------------------------------------------------------------
  // Order Handlers
  // -------------------------------------------------------------------------
  const handleSaveOrder = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    const order_mode = (formData.get('order_mode') as string) || orderCreationMode;
    const specification_id = (formData.get('specification_id') as string)?.trim() || specInputId.trim();
    const design_id = formData.get('design_id') as string;
    const quantity = parseInt(formData.get('quantity') as string, 10);
    const priority = formData.get('priority') as OrderPriority;
    const status = formData.get('status') as OrderStatus;
    const deadlineInput = formData.get('deadline') as string;
    const notes = formData.get('notes') as string;

    if (!editingOrder) {
      if (order_mode === 'specification') {
        if (!specification_id) {
          showFeedback('Please enter an approved Production Specification ID.', 'error');
          return;
        }
      } else {
        if (!design_id) {
          showFeedback('Please select a jewellery design.', 'error');
          return;
        }
      }
    }
    if (isNaN(quantity) || quantity <= 0) {
      showFeedback('Quantity must be greater than zero.', 'error');
      return;
    }
    if (!deadlineInput) {
      showFeedback('Please specify a target delivery deadline.', 'error');
      return;
    }

    try {
      const deadlineIso = new Date(deadlineInput).toISOString();
      if (editingOrder) {
        await productionService.updateOrder(editingOrder.id, {
          quantity,
          priority,
          status,
          deadline: deadlineIso,
          notes: notes.trim() || null,
        });
        showFeedback('Production order updated successfully.');
      } else if (order_mode === 'specification') {
        await productionService.createOrderFromSpecification({
          specification_id,
          quantity,
          priority,
          deadline: deadlineIso,
          notes: notes.trim() || null,
        });
        showFeedback('Production order created from approved specification!');
      } else {
        await productionService.createOrder({
          design_id,
          quantity,
          priority,
          status,
          deadline: deadlineIso,
          notes: notes.trim() || null,
        });
        showFeedback('Production order created successfully.');
      }
      setIsOrderModalOpen(false);
      setEditingOrder(null);
      setSpecInputId('');
      fetchOrders();
      fetchSummary();
    } catch (err: unknown) {
      showFeedback(err instanceof Error ? err.message : 'Operation failed', 'error');
    }
  };

  // -------------------------------------------------------------------------
  // Worker Handlers
  // -------------------------------------------------------------------------
  const handleSaveWorker = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    const name = (formData.get('name') as string).trim();
    const skill = formData.get('skill') as string;
    const capacity = parseFloat(formData.get('capacity_hours_per_day') as string);
    const is_available = formData.get('is_available') === 'on';

    if (!name) {
      showFeedback('Artisan name is required.', 'error');
      return;
    }
    if (isNaN(capacity) || capacity < 0 || capacity > 24) {
      showFeedback('Capacity must be between 0 and 24 hours/day.', 'error');
      return;
    }

    try {
      if (editingWorker) {
        await productionService.updateWorker(editingWorker.id, {
          name,
          skill,
          capacity_hours_per_day: capacity,
          is_available,
        });
        showFeedback('Artisan profile updated.');
      } else {
        await productionService.createWorker({
          name,
          skill,
          capacity_hours_per_day: capacity,
          is_available,
        });
        showFeedback('Artisan added to workshop roster.');
      }
      setIsWorkerModalOpen(false);
      setEditingWorker(null);
      fetchWorkers();
      fetchSummary();
    } catch (err: unknown) {
      showFeedback(err instanceof Error ? err.message : 'Operation failed', 'error');
    }
  };

  const handleToggleWorkerAvailability = async (worker: Worker) => {
    try {
      await productionService.updateWorker(worker.id, {
        is_available: !worker.is_available,
      });
      fetchWorkers();
      fetchSummary();
    } catch (err: unknown) {
      showFeedback(err instanceof Error ? err.message : 'Failed to update status', 'error');
    }
  };

  // -------------------------------------------------------------------------
  // Machine Handlers
  // -------------------------------------------------------------------------
  const handleSaveMachine = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    const name = (formData.get('name') as string).trim();
    const machine_type = formData.get('machine_type') as string;
    const capacity = parseFloat(formData.get('capacity_hours_per_day') as string);
    const is_available = formData.get('is_available') === 'on';

    if (!name) {
      showFeedback('Machine identifier is required.', 'error');
      return;
    }
    if (isNaN(capacity) || capacity < 0 || capacity > 24) {
      showFeedback('Capacity must be between 0 and 24 hours/day.', 'error');
      return;
    }

    try {
      if (editingMachine) {
        await productionService.updateMachine(editingMachine.id, {
          name,
          machine_type,
          capacity_hours_per_day: capacity,
          is_available,
        });
        showFeedback('Equipment updated.');
      } else {
        await productionService.createMachine({
          name,
          machine_type,
          capacity_hours_per_day: capacity,
          is_available,
        });
        showFeedback('Equipment registered to workshop.');
      }
      setIsMachineModalOpen(false);
      setEditingMachine(null);
      fetchMachines();
      fetchSummary();
    } catch (err: unknown) {
      showFeedback(err instanceof Error ? err.message : 'Operation failed', 'error');
    }
  };

  const handleToggleMachineAvailability = async (machine: Machine) => {
    try {
      await productionService.updateMachine(machine.id, {
        is_available: !machine.is_available,
      });
      fetchMachines();
      fetchSummary();
    } catch (err: unknown) {
      showFeedback(err instanceof Error ? err.message : 'Failed to update status', 'error');
    }
  };

  // -------------------------------------------------------------------------
  // Delete Handler
  // -------------------------------------------------------------------------
  const handleConfirmDelete = async () => {
    if (!deletingItem) return;
    try {
      if (deletingItem.type === 'order') {
        await productionService.deleteOrder(deletingItem.id);
        fetchOrders();
      } else if (deletingItem.type === 'worker') {
        await productionService.deleteWorker(deletingItem.id);
        fetchWorkers();
      } else if (deletingItem.type === 'machine') {
        await productionService.deleteMachine(deletingItem.id);
        fetchMachines();
      } else if (deletingItem.type === 'schedule') {
        await productionService.deleteSchedule(deletingItem.id);
        if (activeSchedule?.id === deletingItem.id) {
          setActiveSchedule(null);
        }
        fetchSchedules();
      }
      showFeedback(`Successfully deleted ${deletingItem.name}.`);
      setDeletingItem(null);
      fetchSummary();
    } catch (err: unknown) {
      showFeedback(err instanceof Error ? err.message : 'Failed to delete item', 'error');
    }
  };

  return (
    <div className="flex-1 bg-[#07090e] text-slate-100 py-8 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto w-full">
      {/* Toast Feedback */}
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

      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-[#1E2333]">
        <div>
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-amber-500/20 via-amber-400/20 to-yellow-300/10 border border-[#D4AF37]/30 flex items-center justify-center text-[#E6CA65]">
              <Factory className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-2xl font-serif font-light tracking-wide text-[#F3F4F6] flex items-center gap-2.5">
                Production Management
                <Badge variant="outline" className="text-xs bg-[#D4AF37]/10 text-[#E6CA65] border-[#D4AF37]/30 font-semibold">
                  Phase 11
                </Badge>
              </h1>
              <p className="text-sm text-slate-400">
                Artisan allocation, precision machinery capacity, and CP-SAT mathematical makespan optimization.
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          <Button
            variant="outline"
            size="sm"
            onClick={handleRefreshAll}
            disabled={isRefreshing}
            className="border-[#1E2333] hover:bg-[#161B26]/60 text-slate-300"
          >
            <RefreshCw className={`w-4 h-4 mr-1.5 ${isRefreshing ? 'animate-spin' : ''}`} />
            Refresh
          </Button>

          {activeTab === 'orders' && (
            <Button
              variant="gold"
              size="sm"
              onClick={() => {
                setEditingOrder(null);
                setIsOrderModalOpen(true);
              }}
              className="font-semibold shadow-lg shadow-[#D4AF37]/10"
            >
              <Plus className="w-4 h-4 mr-1.5" />
              New Order
            </Button>
          )}

          {activeTab === 'workers' && (
            <Button
              variant="gold"
              size="sm"
              onClick={() => {
                setEditingWorker(null);
                setIsWorkerModalOpen(true);
              }}
              className="font-semibold shadow-lg shadow-[#D4AF37]/10"
            >
              <Plus className="w-4 h-4 mr-1.5" />
              Add Artisan
            </Button>
          )}

          {activeTab === 'machines' && (
            <Button
              variant="gold"
              size="sm"
              onClick={() => {
                setEditingMachine(null);
                setIsMachineModalOpen(true);
              }}
              className="font-semibold shadow-lg shadow-[#D4AF37]/10"
            >
              <Plus className="w-4 h-4 mr-1.5" />
              Add Machine
            </Button>
          )}

          {activeTab === 'optimization' && (
            <Button
              variant="gold"
              size="sm"
              onClick={handleRunOptimization}
              disabled={optimizing}
              className="font-semibold shadow-lg shadow-[#D4AF37]/10"
            >
              {optimizing ? (
                <>
                  <RefreshCw className="w-4 h-4 mr-1.5 animate-spin" />
                  Optimizing...
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 mr-1.5 fill-current" />
                  Run Solver
                </>
              )}
            </Button>
          )}
        </div>
      </div>

      {/* KPI Metrics Dashboard Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 my-6">
        <Card className="bg-[#0E111A]/80 border-[#1E2333]/80 backdrop-blur">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-slate-400">Active Orders</p>
              <h3 className="text-2xl font-bold text-white mt-1">
                {summary ? summary.pending_orders + summary.in_progress_orders : 0}
              </h3>
              <p className="text-[11px] text-slate-500 mt-0.5">
                {summary?.pending_orders ?? 0} Pending &bull; {summary?.in_progress_orders ?? 0} In Progress
              </p>
            </div>
            <div className="w-10 h-10 rounded-xl bg-[#D4AF37]/10 border border-[#D4AF37]/20 flex items-center justify-center text-[#E6CA65]">
              <TrendingUp className="w-5 h-5" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-[#0E111A]/80 border-[#1E2333]/80 backdrop-blur">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-slate-400">Overdue Orders</p>
              <h3 className={`text-2xl font-bold mt-1 ${summary && summary.overdue_orders > 0 ? 'text-rose-400' : 'text-slate-200'}`}>
                {summary?.overdue_orders ?? 0}
              </h3>
              <p className="text-[11px] text-slate-500 mt-0.5">
                {summary?.completed_orders ?? 0} Completed Total
              </p>
            </div>
            <div className={`w-10 h-10 rounded-xl border flex items-center justify-center ${summary && summary.overdue_orders > 0 ? 'bg-rose-500/10 border-rose-500/30 text-rose-400' : 'bg-[#161B26]/50 border-[#262C40]/50 text-slate-400'}`}>
              <AlertTriangle className="w-5 h-5" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-[#0E111A]/80 border-[#1E2333]/80 backdrop-blur">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-slate-400">Workshop Artisans</p>
              <h3 className="text-2xl font-bold text-white mt-1">
                {summary ? `${summary.available_workers}/${summary.total_workers}` : '0/0'}
              </h3>
              <p className="text-[11px] text-slate-500 mt-0.5">
                {summary?.total_worker_capacity_hours ?? 0}h Total Active Capacity
              </p>
            </div>
            <div className="w-10 h-10 rounded-xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400">
              <Users className="w-5 h-5" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-[#0E111A]/80 border-[#1E2333]/80 backdrop-blur">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-slate-400">Machinery & Tools</p>
              <h3 className="text-2xl font-bold text-white mt-1">
                {summary ? `${summary.available_machines}/${summary.total_machines}` : '0/0'}
              </h3>
              <p className="text-[11px] text-slate-500 mt-0.5">
                {summary?.total_machine_capacity_hours ?? 0}h Operational Capacity
              </p>
            </div>
            <div className="w-10 h-10 rounded-xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center text-purple-400">
              <Cpu className="w-5 h-5" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Tab Navigation */}
      <div className="flex space-x-1 border-b border-[#1E2333] my-6 overflow-x-auto">
        <button
          onClick={() => switchTab('dashboard')}
          className={`flex items-center space-x-2 py-3 px-5 border-b-2 font-medium text-sm transition-colors whitespace-nowrap ${
            activeTab === 'dashboard'
              ? 'border-[#D4AF37] text-[#E6CA65] bg-[#E6CA65]/5'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <TrendingUp className="w-4 h-4" />
          <span>Workshop Dashboard</span>
        </button>

        <button
          onClick={() => switchTab('orders')}
          className={`flex items-center space-x-2 py-3 px-5 border-b-2 font-medium text-sm transition-colors whitespace-nowrap ${
            activeTab === 'orders'
              ? 'border-[#D4AF37] text-[#E6CA65] bg-[#E6CA65]/5'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <Factory className="w-4 h-4" />
          <span>Production Orders</span>
          <Badge variant="secondary" className="text-[10px] ml-1 bg-[#161B26]">
            {totalOrders}
          </Badge>
        </button>

        <button
          onClick={() => switchTab('workers')}
          className={`flex items-center space-x-2 py-3 px-5 border-b-2 font-medium text-sm transition-colors whitespace-nowrap ${
            activeTab === 'workers'
              ? 'border-[#D4AF37] text-[#E6CA65] bg-[#E6CA65]/5'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <Users className="w-4 h-4" />
          <span>Workshop Artisans</span>
          <Badge variant="secondary" className="text-[10px] ml-1 bg-[#161B26]">
            {workers.length}
          </Badge>
        </button>

        <button
          onClick={() => switchTab('machines')}
          className={`flex items-center space-x-2 py-3 px-5 border-b-2 font-medium text-sm transition-colors whitespace-nowrap ${
            activeTab === 'machines'
              ? 'border-[#D4AF37] text-[#E6CA65] bg-[#E6CA65]/5'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <Cpu className="w-4 h-4" />
          <span>Machinery & Tools</span>
          <Badge variant="secondary" className="text-[10px] ml-1 bg-[#161B26]">
            {machines.length}
          </Badge>
        </button>

        <button
          onClick={() => switchTab('optimization')}
          className={`flex items-center space-x-2 py-3 px-5 border-b-2 font-medium text-sm transition-colors whitespace-nowrap ${
            activeTab === 'optimization'
              ? 'border-[#D4AF37] text-[#E6CA65] bg-[#E6CA65]/5'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <Sparkles className="w-4 h-4 text-[#E6CA65]" />
          <span>AI Optimization & Schedule</span>
          <Badge variant="outline" className="text-[10px] ml-1 bg-[#D4AF37]/10 text-[#F3DB7C] border-[#D4AF37]/30">
            OR-Tools
          </Badge>
        </button>

        {shopFloorOrderId && (
          <button
            onClick={() => switchTab('shop-floor')}
            className={`flex items-center space-x-2 py-3 px-5 border-b-2 font-medium text-sm transition-colors whitespace-nowrap ${
              activeTab === 'shop-floor'
                ? 'border-[#D4AF37] text-[#E6CA65] bg-[#E6CA65]/5'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Factory className="w-4 h-4 text-amber-300" />
            <span>Shop Floor Workstation</span>
            <Badge variant="outline" className="text-[9px] ml-1 font-mono bg-amber-400/10 text-amber-300 border-amber-400/30">
              #{shopFloorOrderId.slice(0, 4)}
            </Badge>
          </button>
        )}
      </div>

      {/* ===================================================================== */}
      {/* TAB 0: WORKSHOP PRODUCTION DASHBOARD */}
      {/* ===================================================================== */}
      {activeTab === 'dashboard' && (
        <ProductionDashboard
          orders={orders}
          loading={loadingOrders}
          onRefresh={handleRefreshAll}
          onOpenShopFloor={(orderId) => {
            switchTab('shop-floor', orderId);
          }}
          onNavigateToTab={(tab) => switchTab(tab)}
        />
      )}

      {/* ===================================================================== */}
      {/* TAB: SHOP-FLOOR WORKSTATION TERMINAL */}
      {/* ===================================================================== */}
      {activeTab === 'shop-floor' && shopFloorOrderId && (
        <ShopFloorPage
          orderId={shopFloorOrderId}
          onBackToOrders={() => switchTab('orders')}
        />
      )}

      {activeTab === 'shop-floor' && !shopFloorOrderId && (
        <Card className="bg-[#0E111A]/90 border-white/[0.07] p-8 text-center space-y-4">
          <Factory className="w-12 h-12 text-[#E6CA65] mx-auto opacity-80" />
          <h3 className="text-lg font-serif font-medium text-white">No Order Selected for Shop Floor</h3>
          <p className="text-sm text-slate-400 max-w-md mx-auto">
            Select an active production order to access live station routing, execution transitions, and QC inspection.
          </p>
          <div className="flex justify-center gap-3 pt-2">
            {orders.length > 0 && (
              <Button
                variant="gold"
                onClick={() => switchTab('shop-floor', orders[0].id)}
              >
                Open Order #{orders[0].id.slice(0, 8)}
              </Button>
            )}
            <Button
              variant="outline"
              onClick={() => switchTab('orders')}
            >
              Browse All Production Orders
            </Button>
          </div>
        </Card>
      )}

      {/* ===================================================================== */}
      {/* TAB 1: PRODUCTION ORDERS */}
      {/* ===================================================================== */}
      {activeTab === 'orders' && (
        <div>
          {/* Filters Bar */}
          <div className="flex flex-col sm:flex-row gap-3 items-center justify-between bg-[#0E111A]/80 p-3 rounded-xl border border-[#1E2333]/80 mb-6">
            <div className="relative w-full sm:w-80">
              <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
              <Input
                placeholder="Search design name or notes..."
                value={orderSearch}
                onChange={(e) => {
                  setOrderSearch(e.target.value);
                  setOrderPage(1);
                }}
                className="pl-9 bg-[#111625] border-[#1E2333] text-sm h-9"
              />
            </div>

            <div className="flex items-center space-x-2 w-full sm:w-auto">
              <select
                value={statusFilter}
                onChange={(e) => {
                  setStatusFilter(e.target.value as OrderStatus | '');
                  setOrderPage(1);
                }}
                className="bg-[#111625] border border-[#1E2333] text-slate-300 text-xs rounded-lg px-3 py-2 outline-none focus:border-[#D4AF37]"
              >
                <option value="">All Statuses</option>
                {ORDER_STATUSES.map((s) => (
                  <option key={s.value} value={s.value}>
                    {s.label}
                  </option>
                ))}
              </select>

              <select
                value={priorityFilter}
                onChange={(e) => {
                  setPriorityFilter(e.target.value as OrderPriority | '');
                  setOrderPage(1);
                }}
                className="bg-[#111625] border border-[#1E2333] text-slate-300 text-xs rounded-lg px-3 py-2 outline-none focus:border-[#D4AF37]"
              >
                <option value="">All Priorities</option>
                {ORDER_PRIORITIES.map((p) => (
                  <option key={p.value} value={p.value}>
                    {p.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Orders Table */}
          {loadingOrders ? (
            <div className="py-20 text-center text-slate-400 flex flex-col items-center justify-center">
              <RefreshCw className="w-8 h-8 animate-spin text-[#E6CA65] mb-3" />
              <p className="text-sm">Loading production orders...</p>
            </div>
          ) : orders.length === 0 ? (
            <div className="py-20 text-center bg-[#0E111A]/50 rounded-2xl border border-[#1E2333]/80 p-8">
              <Factory className="w-12 h-12 text-slate-600 mx-auto mb-3" />
              <h3 className="text-base font-semibold text-white">No Production Orders Found</h3>
              <p className="text-sm text-slate-400 mt-1 max-w-md mx-auto">
                {orderSearch || statusFilter || priorityFilter
                  ? 'No orders matched the selected filter criteria.'
                  : 'Start your manufacturing pipeline by creating a production batch linked to your jewellery designs.'}
              </p>
              <Button
                variant="gold"
                size="sm"
                className="mt-5"
                onClick={() => {
                  setEditingOrder(null);
                  setIsOrderModalOpen(true);
                }}
              >
                <Plus className="w-4 h-4 mr-1.5" />
                Create First Production Order
              </Button>
            </div>
          ) : (
            <div className="overflow-x-auto rounded-xl border border-[#1E2333]/80 bg-[#0E111A]/80 backdrop-blur">
              <table className="w-full text-left border-collapse text-sm">
                <thead>
                  <tr className="border-b border-[#1E2333] text-xs uppercase tracking-wider text-slate-400 bg-[#121622]/40">
                    <th className="py-3 px-4">Design Item</th>
                    <th className="py-3 px-4">Quantity</th>
                    <th className="py-3 px-4">Priority</th>
                    <th className="py-3 px-4">Status</th>
                    <th className="py-3 px-4">Target Deadline</th>
                    <th className="py-3 px-4">Notes</th>
                    <th className="py-3 px-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 text-slate-300">
                  {orders.map((order) => {
                    const statusObj = ORDER_STATUSES.find((s) => s.value === order.status);
                    const prioObj = ORDER_PRIORITIES.find((p) => p.value === order.priority);
                    const formattedDeadline = new Date(order.deadline).toLocaleDateString('en-US', {
                      month: 'short',
                      day: 'numeric',
                      year: 'numeric',
                    });

                    return (
                      <tr key={order.id} className="hover:bg-[#161B26]/30 transition-colors">
                        <td className="py-3.5 px-4 font-medium text-white flex items-center space-x-3">
                          <div className="w-10 h-10 rounded-lg bg-[#121622] border border-[#1E2333] overflow-hidden shrink-0 flex items-center justify-center relative">
                            {order.approved_render_url || order.design_thumbnail_url ? (
                              <img
                                src={(order.approved_render_url || order.design_thumbnail_url) ?? undefined}
                                alt={order.design_name || 'Design'}
                                className="w-full h-full object-cover"
                              />
                            ) : (
                              <Layers className="w-5 h-5 text-slate-600" />
                            )}
                            {order.specification_id && (
                              <span
                                title="Approved Specification & Render Lineage"
                                className="absolute top-0.5 right-0.5 w-2 h-2 rounded-full bg-emerald-400 border border-black shadow"
                              />
                            )}
                          </div>
                          <div>
                            <div className="flex items-center space-x-1.5">
                              <p className="font-semibold text-white leading-snug">
                                {order.design_name || 'Jewellery Design'}
                              </p>
                              {order.specification_id && (
                                <Badge
                                  variant="outline"
                                  className="text-[9px] py-0 px-1 bg-amber-500/10 text-amber-300 border-amber-500/30 font-mono"
                                  title={`Backed by Approved Spec v${order.specification_version || 1}`}
                                >
                                  Spec v{order.specification_version || 1}
                                </Badge>
                              )}
                            </div>
                            <div className="flex items-center space-x-2 text-xs text-slate-500 mt-0.5">
                              <span>{order.design_category || order.specification_category || 'Custom Item'}</span>
                              {order.routing_steps_count != null && order.routing_steps_count > 0 && (
                                <>
                                  <span>&bull;</span>
                                  <span className="text-cyan-400/90 font-mono text-[10px]">
                                    {order.routing_steps_count} stages
                                  </span>
                                </>
                              )}
                              {order.materials_count != null && order.materials_count > 0 && (
                                <>
                                  <span>&bull;</span>
                                  <span className="text-amber-400/80 font-mono text-[10px]">
                                    {order.materials_count} mats
                                  </span>
                                </>
                              )}
                            </div>
                          </div>
                        </td>

                        <td className="py-3.5 px-4">
                          <span className="font-bold text-[#F3DB7C]">{order.quantity}</span>{' '}
                          <span className="text-xs text-slate-500">units</span>
                        </td>

                        <td className="py-3.5 px-4">
                          <Badge variant="outline" className={`text-xs font-semibold uppercase ${prioObj?.color || ''}`}>
                            {prioObj?.label || order.priority}
                          </Badge>
                        </td>

                        <td className="py-3.5 px-4">
                          <Badge variant="outline" className={`text-xs font-semibold ${statusObj?.color || ''}`}>
                            {statusObj?.label || order.status}
                          </Badge>
                        </td>

                        <td className="py-3.5 px-4">
                          <div className="flex items-center space-x-1.5">
                            <Clock className="w-3.5 h-3.5 text-slate-500 shrink-0" />
                            <span className="text-xs">{formattedDeadline}</span>
                            {order.is_overdue && (
                              <Badge variant="destructive" className="text-[10px] py-0 px-1.5 ml-1">
                                OVERDUE
                              </Badge>
                            )}
                          </div>
                        </td>

                        <td className="py-3.5 px-4 max-w-xs truncate text-xs text-slate-400">
                          {order.notes || <span className="text-slate-600 italic">No notes</span>}
                        </td>

                        <td className="py-3.5 px-4 text-right">
                          <div className="flex items-center justify-end space-x-1">
                            <Button
                              variant="atelier"
                              size="sm"
                              onClick={() => {
                                setShopFloorOrderId(order.id);
                                setActiveTab('shop-floor');
                              }}
                              className="h-8 px-2 text-xs font-semibold"
                              title="Launch Shop Floor Workstation"
                            >
                              <Factory className="w-3.5 h-3.5 mr-1 text-amber-300" />
                              <span>Terminal</span>
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => {
                                setEditingOrder(order);
                                setIsOrderModalOpen(true);
                              }}
                              className="h-8 w-8 p-0 text-slate-400 hover:text-[#E6CA65]"
                            >
                              <Edit2 className="w-3.5 h-3.5" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() =>
                                setDeletingItem({
                                  type: 'order',
                                  id: order.id,
                                  name: `Order #${order.id.slice(0, 8)} (${order.design_name || 'Design'})`,
                                })
                              }
                              className="h-8 w-8 p-0 text-slate-400 hover:text-rose-400"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </Button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* ===================================================================== */}
      {/* TAB 2: WORKSHOP ARTISANS */}
      {/* ===================================================================== */}
      {activeTab === 'workers' && (
        <div>
          {loadingWorkers ? (
            <div className="py-20 text-center text-slate-400 flex flex-col items-center justify-center">
              <RefreshCw className="w-8 h-8 animate-spin text-[#E6CA65] mb-3" />
              <p className="text-sm">Loading artisan roster...</p>
            </div>
          ) : workers.length === 0 ? (
            <div className="py-20 text-center bg-[#0E111A]/50 rounded-2xl border border-[#1E2333]/80 p-8">
              <Users className="w-12 h-12 text-slate-600 mx-auto mb-3" />
              <h3 className="text-base font-semibold text-white">No Workshop Artisans Registered</h3>
              <p className="text-sm text-slate-400 mt-1 max-w-md mx-auto">
                Add goldsmiths, stone setters, CAD designers, and polishing specialists to manage capacity for production scheduling.
              </p>
              <Button
                variant="gold"
                size="sm"
                className="mt-5"
                onClick={() => {
                  setEditingWorker(null);
                  setIsWorkerModalOpen(true);
                }}
              >
                <Plus className="w-4 h-4 mr-1.5" />
                Add First Artisan
              </Button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {workers.map((worker) => {
                const skillObj = WORKER_SKILLS.find((s) => s.value === worker.skill);

                return (
                  <Card key={worker.id} className="bg-[#0E111A]/80 border-[#1E2333] hover:border-[#262C40] transition-all">
                    <CardHeader className="p-4 pb-2 flex flex-row items-start justify-between space-y-0">
                      <div className="flex items-center space-x-3">
                        <div className="w-10 h-10 rounded-xl bg-[#D4AF37]/10 border border-[#D4AF37]/20 flex items-center justify-center text-[#E6CA65] font-bold">
                          {worker.name.charAt(0).toUpperCase()}
                        </div>
                        <div>
                          <CardTitle className="text-base font-semibold text-white">{worker.name}</CardTitle>
                          <CardDescription className="text-xs text-slate-400">
                            {skillObj?.label || worker.skill}
                          </CardDescription>
                        </div>
                      </div>

                      <div className="flex items-center space-x-1">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => {
                            setEditingWorker(worker);
                            setIsWorkerModalOpen(true);
                          }}
                          className="h-8 w-8 p-0 text-slate-400 hover:text-[#E6CA65]"
                        >
                          <Edit2 className="w-3.5 h-3.5" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() =>
                            setDeletingItem({
                              type: 'worker',
                              id: worker.id,
                              name: worker.name,
                            })
                          }
                          className="h-8 w-8 p-0 text-slate-400 hover:text-rose-400"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </Button>
                      </div>
                    </CardHeader>

                    <CardContent className="p-4 pt-2">
                      <div className="bg-[#121622]/60 rounded-lg p-3 my-2 border border-[#1E2333]/80 flex items-center justify-between">
                        <div>
                          <p className="text-[11px] text-slate-500 uppercase tracking-wider">Productive Capacity</p>
                          <p className="text-base font-bold text-[#F3DB7C] mt-0.5">
                            {worker.capacity_hours_per_day}{' '}
                            <span className="text-xs font-normal text-slate-400">hours / day</span>
                          </p>
                        </div>

                        <button
                          onClick={() => handleToggleWorkerAvailability(worker)}
                          className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-full text-xs font-semibold border transition-all ${
                            worker.is_available
                              ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30 hover:bg-emerald-500/20'
                              : 'bg-[#161B26] text-slate-400 border-[#262C40] hover:bg-slate-700'
                          }`}
                        >
                          <span className={`w-2 h-2 rounded-full ${worker.is_available ? 'bg-emerald-400' : 'bg-slate-500'}`} />
                          <span>{worker.is_available ? 'Available' : 'Unavailable'}</span>
                        </button>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* ===================================================================== */}
      {/* TAB 3: WORKSHOP MACHINERY */}
      {/* ===================================================================== */}
      {activeTab === 'machines' && (
        <div>
          {loadingMachines ? (
            <div className="py-20 text-center text-slate-400 flex flex-col items-center justify-center">
              <RefreshCw className="w-8 h-8 animate-spin text-purple-400 mb-3" />
              <p className="text-sm">Loading equipment registry...</p>
            </div>
          ) : machines.length === 0 ? (
            <div className="py-20 text-center bg-[#0E111A]/50 rounded-2xl border border-[#1E2333]/80 p-8">
              <Cpu className="w-12 h-12 text-slate-600 mx-auto mb-3" />
              <h3 className="text-base font-semibold text-white">No Workshop Machinery Registered</h3>
              <p className="text-sm text-slate-400 mt-1 max-w-md mx-auto">
                Register laser markers, 3D printers, furnaces, and polishing equipment to calculate machine hours and avoid manufacturing bottlenecks.
              </p>
              <Button
                variant="gold"
                size="sm"
                className="mt-5"
                onClick={() => {
                  setEditingMachine(null);
                  setIsMachineModalOpen(true);
                }}
              >
                <Plus className="w-4 h-4 mr-1.5" />
                Register First Machine
              </Button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {machines.map((machine) => {
                const typeObj = MACHINE_TYPES.find((t) => t.value === machine.machine_type);

                return (
                  <Card key={machine.id} className="bg-[#0E111A]/80 border-[#1E2333] hover:border-[#262C40] transition-all">
                    <CardHeader className="p-4 pb-2 flex flex-row items-start justify-between space-y-0">
                      <div className="flex items-center space-x-3">
                        <div className="w-10 h-10 rounded-xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center text-purple-400 font-bold">
                          <Cpu className="w-5 h-5" />
                        </div>
                        <div>
                          <CardTitle className="text-base font-semibold text-white">{machine.name}</CardTitle>
                          <CardDescription className="text-xs text-slate-400">
                            {typeObj?.label || machine.machine_type}
                          </CardDescription>
                        </div>
                      </div>

                      <div className="flex items-center space-x-1">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => {
                            setEditingMachine(machine);
                            setIsMachineModalOpen(true);
                          }}
                          className="h-8 w-8 p-0 text-slate-400 hover:text-purple-400"
                        >
                          <Edit2 className="w-3.5 h-3.5" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() =>
                            setDeletingItem({
                              type: 'machine',
                              id: machine.id,
                              name: machine.name,
                            })
                          }
                          className="h-8 w-8 p-0 text-slate-400 hover:text-rose-400"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </Button>
                      </div>
                    </CardHeader>

                    <CardContent className="p-4 pt-2">
                      <div className="bg-[#121622]/60 rounded-lg p-3 my-2 border border-[#1E2333]/80 flex items-center justify-between">
                        <div>
                          <p className="text-[11px] text-slate-500 uppercase tracking-wider">Operational Capacity</p>
                          <p className="text-base font-bold text-purple-300 mt-0.5">
                            {machine.capacity_hours_per_day}{' '}
                            <span className="text-xs font-normal text-slate-400">hours / day</span>
                          </p>
                        </div>

                        <button
                          onClick={() => handleToggleMachineAvailability(machine)}
                          className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-full text-xs font-semibold border transition-all ${
                            machine.is_available
                              ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30 hover:bg-emerald-500/20'
                              : 'bg-rose-500/10 text-rose-300 border-rose-500/30 hover:bg-rose-500/20'
                          }`}
                        >
                          <span className={`w-2 h-2 rounded-full ${machine.is_available ? 'bg-emerald-400' : 'bg-rose-500'}`} />
                          <span>{machine.is_available ? 'Operational' : 'Maintenance'}</span>
                        </button>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          )}
        </div>
      )}
      {/* ===================================================================== */}
      {/* TAB 4: AI OPTIMIZATION & SCHEDULE (PHASE 12) */}
      {/* ===================================================================== */}
      {activeTab === 'optimization' && (
        <div className="space-y-6">
          {/* Optimization Controls & Schedule Selector Bar */}
          <div className="bg-[#0E111A]/80 p-5 rounded-2xl border border-[#1E2333]/80 backdrop-blur shadow-xl">
            <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-4 border-b border-[#1E2333]/80">
              <div>
                <h2 className="text-lg font-bold text-white flex items-center gap-2">
                  <Sparkles className="w-5 h-5 text-[#E6CA65]" />
                  Google OR-Tools CP-SAT Production Optimizer
                </h2>
                <p className="text-xs text-slate-400 mt-0.5">
                  Computes globally optimal, conflict-free manufacturing sequences respecting artisan skills, machine types, and delivery deadlines.
                </p>
              </div>

              {/* Saved Schedules Selector */}
              <div className="flex items-center space-x-2">
                <History className="w-4 h-4 text-slate-400 shrink-0" />
                <span className="text-xs text-slate-400 font-medium whitespace-nowrap">Saved Schedules:</span>
                <select
                  value={activeSchedule?.id || ''}
                  onChange={async (e) => {
                    const id = e.target.value;
                    if (id) {
                      try {
                        const sched = await productionService.getSchedule(id);
                        setActiveSchedule(sched);
                        setOptimizationResult(null);
                      } catch (err: unknown) {
                        showFeedback(err instanceof Error ? err.message : 'Failed to load schedule', 'error');
                      }
                    }
                  }}
                  className="bg-[#111625] border border-[#1E2333] text-slate-200 text-xs rounded-lg px-3 py-2 outline-none focus:border-[#D4AF37] max-w-xs truncate"
                >
                  {schedules.length === 0 ? (
                    <option value="">No saved schedules</option>
                  ) : (
                    schedules.map((s) => (
                      <option key={s.id} value={s.id}>
                        {s.name || `Schedule #${s.id.slice(0, 8)}`} ({s.solver_status} &bull; {new Date(s.created_at).toLocaleDateString()})
                      </option>
                    ))
                  )}
                </select>
                {activeSchedule && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                      setDeletingItem({
                        type: 'schedule',
                        id: activeSchedule.id,
                        name: activeSchedule.name || `Schedule #${activeSchedule.id.slice(0, 8)}`,
                      });
                    }}
                    className="h-8 w-8 p-0 text-slate-400 hover:text-rose-400"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </Button>
                )}
              </div>
            </div>

            {/* Parameter Inputs */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 pt-4">
              <div>
                <label className="block text-[11px] font-semibold uppercase tracking-wider text-slate-400 mb-1.5 flex items-center gap-1">
                  <Calendar className="w-3.5 h-3.5 text-[#E6CA65]" />
                  Planning Horizon (Days)
                </label>
                <select
                  value={horizonDays}
                  onChange={(e) => setHorizonDays(parseInt(e.target.value, 10))}
                  className="w-full bg-[#111625] border border-[#1E2333] text-slate-200 text-xs rounded-lg px-3 py-2.5 outline-none focus:border-[#D4AF37]"
                >
                  <option value={3}>3 Days (Express Run)</option>
                  <option value={7}>7 Days (1 Week)</option>
                  <option value={14}>14 Days (2 Weeks - Standard)</option>
                  <option value={21}>21 Days (3 Weeks)</option>
                  <option value={30}>30 Days (Full Month)</option>
                </select>
              </div>

              <div>
                <label className="block text-[11px] font-semibold uppercase tracking-wider text-slate-400 mb-1.5 flex items-center gap-1">
                  <Timer className="w-3.5 h-3.5 text-[#E6CA65]" />
                  Solver Time Limit
                </label>
                <select
                  value={timeLimitSec}
                  onChange={(e) => setTimeLimitSec(parseInt(e.target.value, 10))}
                  className="w-full bg-[#111625] border border-[#1E2333] text-slate-200 text-xs rounded-lg px-3 py-2.5 outline-none focus:border-[#D4AF37]"
                >
                  <option value={5}>5 Seconds (Fast)</option>
                  <option value={10}>10 Seconds (Recommended)</option>
                  <option value={30}>30 Seconds (Deep Search)</option>
                </select>
              </div>

              <div>
                <label className="block text-[11px] font-semibold uppercase tracking-wider text-slate-400 mb-1.5 flex items-center gap-1">
                  <Sliders className="w-3.5 h-3.5 text-[#E6CA65]" />
                  Schedule Name (Optional)
                </label>
                <Input
                  placeholder="e.g. Diwali Rush 2026 Run A"
                  value={optScheduleName}
                  onChange={(e) => setOptScheduleName(e.target.value)}
                  className="bg-[#111625] border-[#1E2333] text-xs h-9"
                />
              </div>

              <div className="flex items-end">
                <Button
                  variant="gold"
                  size="sm"
                  onClick={handleRunOptimization}
                  disabled={optimizing}
                  className="w-full h-9 font-semibold shadow-lg shadow-[#D4AF37]/20 text-xs flex items-center justify-center space-x-2"
                >
                  {optimizing ? (
                    <>
                      <RefreshCw className="w-4 h-4 animate-spin" />
                      <span>Solving CP-SAT Model...</span>
                    </>
                  ) : (
                    <>
                      <Play className="w-4 h-4 fill-current" />
                      <span>Run Production Solver</span>
                    </>
                  )}
                </Button>
              </div>
            </div>
          </div>

          {/* Infeasibility Diagnostic Box */}
          {((optimizationResult && optimizationResult.status === 'infeasible') ||
            (activeSchedule && activeSchedule.solver_status === 'INFEASIBLE')) && (
            <div className="bg-rose-950/40 border border-rose-500/40 rounded-2xl p-5 backdrop-blur">
              <div className="flex items-start space-x-3">
                <AlertTriangle className="w-6 h-6 text-rose-400 shrink-0 mt-0.5" />
                <div className="space-y-2">
                  <h3 className="text-base font-bold text-rose-300">
                    Schedule Infeasible Under Current Constraints
                  </h3>
                  <p className="text-xs text-rose-200/90 leading-relaxed">
                    The CP-SAT mathematical solver proved that no valid non-overlapping schedule exists within the specified parameters.
                  </p>
                  {optimizationResult?.infeasibility_reasons && optimizationResult.infeasibility_reasons.length > 0 && (
                    <div className="mt-3 bg-rose-950/60 rounded-xl p-3 border border-rose-900/60">
                      <p className="text-xs font-semibold text-rose-300 mb-1.5 uppercase tracking-wider">
                        Diagnostic Insights & Remediation:
                      </p>
                      <ul className="list-disc list-inside space-y-1 text-xs text-rose-200/80">
                        {optimizationResult.infeasibility_reasons.map((reason, idx) => (
                          <li key={idx}>{reason}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* KPI Dashboard for Active / Optimized Schedule */}
          {(activeSchedule || optimizationResult?.metrics) && (
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
              <Card className="bg-[#0E111A]/80 border-[#1E2333]">
                <CardContent className="p-3.5">
                  <p className="text-[11px] text-slate-400 uppercase tracking-wider font-medium">Status</p>
                  <div className="mt-1">
                    <Badge
                      variant="outline"
                      className={`text-xs font-bold uppercase ${
                        (activeSchedule?.solver_status || optimizationResult?.solver_status) === 'OPTIMAL'
                          ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                          : (activeSchedule?.solver_status || optimizationResult?.solver_status) === 'FEASIBLE'
                          ? 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30'
                          : 'bg-rose-500/10 text-rose-400 border-rose-500/30'
                      }`}
                    >
                      {activeSchedule?.solver_status || optimizationResult?.solver_status || 'UNKNOWN'}
                    </Badge>
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-[#0E111A]/80 border-[#1E2333]">
                <CardContent className="p-3.5">
                  <p className="text-[11px] text-slate-400 uppercase tracking-wider font-medium">Makespan</p>
                  <h3 className="text-lg font-bold text-[#F3DB7C] mt-1">
                    {activeSchedule?.makespan_hours ?? optimizationResult?.metrics?.makespan_hours ?? 0}h
                  </h3>
                  <p className="text-[10px] text-slate-500">
                    {(((activeSchedule?.makespan_hours ?? optimizationResult?.metrics?.makespan_hours ?? 0) / 24).toFixed(1))} days total
                  </p>
                </CardContent>
              </Card>

              <Card className="bg-[#0E111A]/80 border-[#1E2333]">
                <CardContent className="p-3.5">
                  <p className="text-[11px] text-slate-400 uppercase tracking-wider font-medium">Scheduled Tasks</p>
                  <h3 className="text-lg font-bold text-white mt-1">
                    {activeSchedule?.tasks?.length ?? optimizationResult?.schedule?.length ?? 0}
                  </h3>
                  <p className="text-[10px] text-slate-500">
                    {activeSchedule?.total_orders_scheduled ?? optimizationResult?.metrics?.total_orders_scheduled ?? 0} Orders
                  </p>
                </CardContent>
              </Card>

              <Card className="bg-[#0E111A]/80 border-[#1E2333]">
                <CardContent className="p-3.5">
                  <p className="text-[11px] text-slate-400 uppercase tracking-wider font-medium">Artisan Utilization</p>
                  <h3 className="text-lg font-bold text-blue-300 mt-1">
                    {(activeSchedule?.worker_utilization_pct ?? optimizationResult?.metrics?.worker_utilization_pct) != null
                      ? `${(activeSchedule?.worker_utilization_pct ?? optimizationResult?.metrics?.worker_utilization_pct ?? 0).toFixed(1)}%`
                      : 'Active'}
                  </h3>
                  <div className="w-full bg-[#161B26] h-1 rounded-full mt-1.5 overflow-hidden">
                    <div
                      className="bg-blue-400 h-full rounded-full transition-all"
                      style={{
                        width: `${Math.min(100, activeSchedule?.worker_utilization_pct ?? optimizationResult?.metrics?.worker_utilization_pct ?? 75)}%`,
                      }}
                    />
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-[#0E111A]/80 border-[#1E2333]">
                <CardContent className="p-3.5">
                  <p className="text-[11px] text-slate-400 uppercase tracking-wider font-medium">Machine Utilization</p>
                  <h3 className="text-lg font-bold text-purple-300 mt-1">
                    {(activeSchedule?.machine_utilization_pct ?? optimizationResult?.metrics?.machine_utilization_pct) != null
                      ? `${(activeSchedule?.machine_utilization_pct ?? optimizationResult?.metrics?.machine_utilization_pct ?? 0).toFixed(1)}%`
                      : 'Active'}
                  </h3>
                  <div className="w-full bg-[#161B26] h-1 rounded-full mt-1.5 overflow-hidden">
                    <div
                      className="bg-purple-400 h-full rounded-full transition-all"
                      style={{
                        width: `${Math.min(100, activeSchedule?.machine_utilization_pct ?? optimizationResult?.metrics?.machine_utilization_pct ?? 60)}%`,
                      }}
                    />
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-[#0E111A]/80 border-[#1E2333]">
                <CardContent className="p-3.5">
                  <p className="text-[11px] text-slate-400 uppercase tracking-wider font-medium">Solver Runtime</p>
                  <h3 className="text-lg font-bold text-slate-200 mt-1">
                    {((activeSchedule?.runtime_seconds ?? ((optimizationResult?.metrics?.solver_runtime_ms ?? 0) / 1000)) * 1000).toFixed(0)} ms
                  </h3>
                  <p className="text-[10px] text-slate-500">Google OR-Tools CP-SAT</p>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Timeline / Gantt Swimlane View */}
          {activeSchedule && activeSchedule.tasks && activeSchedule.tasks.length > 0 ? (
            <div className="bg-[#0E111A]/80 rounded-2xl border border-[#1E2333]/80 p-5 backdrop-blur shadow-2xl space-y-4">
              {/* Timeline Header & Group Controls */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-[#1E2333]">
                <div className="flex items-center space-x-2">
                  <Calendar className="w-4 h-4 text-[#E6CA65]" />
                  <h3 className="text-sm font-bold text-white">Interactive Production Timeline (Gantt)</h3>
                </div>

                <div className="flex items-center space-x-2">
                  <span className="text-xs text-slate-400">Group Swimlanes By:</span>
                  <div className="inline-flex rounded-lg bg-[#111625] p-0.5 border border-[#1E2333]">
                    <button
                      onClick={() => setTimelineGroupBy('worker')}
                      className={`px-3 py-1 text-xs font-semibold rounded-md transition-all ${
                        timelineGroupBy === 'worker' ? 'bg-[#D4AF37]/20 text-[#F3DB7C]' : 'text-slate-400 hover:text-white'
                      }`}
                    >
                      Artisans
                    </button>
                    <button
                      onClick={() => setTimelineGroupBy('machine')}
                      className={`px-3 py-1 text-xs font-semibold rounded-md transition-all ${
                        timelineGroupBy === 'machine' ? 'bg-purple-500/20 text-purple-300' : 'text-slate-400 hover:text-white'
                      }`}
                    >
                      Machinery
                    </button>
                    <button
                      onClick={() => setTimelineGroupBy('order')}
                      className={`px-3 py-1 text-xs font-semibold rounded-md transition-all ${
                        timelineGroupBy === 'order' ? 'bg-blue-500/20 text-blue-300' : 'text-slate-400 hover:text-white'
                      }`}
                    >
                      Orders
                    </button>
                  </div>
                </div>
              </div>

              {/* Gantt Matrix */}
              {(() => {
                const tasks = activeSchedule.tasks || [];
                const baseTimeMs = activeSchedule.start_date
                  ? new Date(activeSchedule.start_date).getTime()
                  : tasks.length > 0
                  ? new Date(tasks[0].start_time).getTime()
                  : Date.now();

                const getStartHour = (t: ScheduledTask): number => {
                  if (t.start_hour !== undefined) return t.start_hour;
                  return Math.max(0, (new Date(t.start_time).getTime() - baseTimeMs) / (3600 * 1000));
                };

                const getEndHour = (t: ScheduledTask): number => {
                  if (t.end_hour !== undefined) return t.end_hour;
                  return Math.max(getStartHour(t) + (t.duration_hours || 1), (new Date(t.end_time).getTime() - baseTimeMs) / (3600 * 1000));
                };

                const maxHour = Math.max(...tasks.map((t) => getEndHour(t)), 24);
                const totalDays = Math.ceil(maxHour / 24);

                // Group tasks
                const groups: { [key: string]: { label: string; sub: string; tasks: ScheduledTask[] } } = {};

                if (timelineGroupBy === 'worker') {
                  tasks.forEach((t) => {
                    const key = t.worker_id || 'unassigned';
                    if (!groups[key]) {
                      groups[key] = {
                        label: t.worker_name || 'Unassigned Artisan',
                        sub: t.operation_name,
                        tasks: [],
                      };
                    }
                    groups[key].tasks.push(t);
                  });
                } else if (timelineGroupBy === 'machine') {
                  tasks.forEach((t) => {
                    const key = t.machine_id || 'unassigned';
                    if (!groups[key]) {
                      groups[key] = {
                        label: t.machine_name || 'Manual Benchwork',
                        sub: t.operation_name,
                        tasks: [],
                      };
                    }
                    groups[key].tasks.push(t);
                  });
                } else {
                  tasks.forEach((t) => {
                    const key = t.order_id;
                    if (!groups[key]) {
                      groups[key] = {
                        label: t.design_name || `Order #${t.order_id.slice(0, 8)}`,
                        sub: `${t.quantity} units`,
                        tasks: [],
                      };
                    }
                    groups[key].tasks.push(t);
                  });
                }

                return (
                  <div className="overflow-x-auto">
                    <div className="min-w-[800px]">
                      {/* Timeline Day Header */}
                      <div className="grid grid-cols-12 gap-0 border-b border-[#1E2333] pb-2 text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                        <div className="col-span-3">Resource / Swimlane</div>
                        <div className="col-span-9 grid grid-flow-col auto-cols-fr gap-1 text-center">
                          {Array.from({ length: totalDays }).map((_, d) => (
                            <div key={d} className="bg-[#121622]/60 rounded py-1 border border-[#1E2333]/80">
                              Day {d + 1}
                              <span className="block text-[9px] text-slate-500 font-normal">
                                {d * 24}h - {(d + 1) * 24}h
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>

                      {/* Swimlane Rows */}
                      <div className="divide-y divide-slate-800/60 mt-2">
                        {Object.entries(groups).map(([groupId, group]) => (
                          <div key={groupId} className="grid grid-cols-12 gap-0 py-3 items-center hover:bg-[#121622]/30 transition-colors">
                            {/* Swimlane Label */}
                            <div className="col-span-3 pr-4">
                              <p className="text-xs font-bold text-white truncate">{group.label}</p>
                              <p className="text-[10px] text-slate-500 truncate">{group.sub}</p>
                            </div>

                            {/* Task Track */}
                            <div className="col-span-9 relative h-12 bg-slate-950/40 rounded-lg border border-[#1E2333]/50 overflow-hidden">
                              {/* Background Day Guides */}
                              <div className="absolute inset-0 grid grid-flow-col auto-cols-fr pointer-events-none divide-x divide-slate-800/20">
                                {Array.from({ length: totalDays }).map((_, d) => (
                                  <div key={d} className="h-full" />
                                ))}
                              </div>

                              {/* Task Blocks */}
                              {group.tasks.map((task) => {
                                const startH = getStartHour(task);
                                const endH = getEndHour(task);
                                const leftPct = (startH / (totalDays * 24)) * 100;
                                const widthPct = Math.max(((endH - startH) / (totalDays * 24)) * 100, 3);

                                const getOpColor = (opName: string) => {
                                  const norm = opName.toLowerCase().replace(/[\s-]+/g, '_');
                                  if (norm.includes('cad') || norm.includes('wax') || norm.includes('design'))
                                    return 'from-indigo-600/80 to-blue-500/80 border-indigo-400/50 text-indigo-100';
                                  if (norm.includes('cast'))
                                    return 'from-amber-600/80 to-amber-500/80 border-[#D4AF37]/50 text-amber-100';
                                  if (norm.includes('stone') || norm.includes('set') || norm.includes('gem'))
                                    return 'from-cyan-600/80 to-teal-500/80 border-cyan-400/50 text-cyan-100';
                                  if (norm.includes('plate') || norm.includes('dip'))
                                    return 'from-yellow-600/80 to-amber-500/80 border-yellow-400/50 text-yellow-100';
                                  if (norm.includes('polish') || norm.includes('finish') || norm.includes('buff'))
                                    return 'from-purple-600/80 to-pink-500/80 border-pink-400/50 text-pink-100';
                                  if (norm.includes('engrav'))
                                    return 'from-violet-600/80 to-purple-500/80 border-violet-400/50 text-violet-100';
                                  if (norm.includes('qa') || norm.includes('qual') || norm.includes('inspect'))
                                    return 'from-emerald-600/80 to-teal-500/80 border-emerald-400/50 text-emerald-100';
                                  return 'from-slate-700 to-slate-600 border-slate-500 text-slate-100';
                                };
                                const colorClass = getOpColor(task.operation_name);

                                return (
                                  <div
                                    key={task.id || `${task.order_id}-${task.sequence_order}`}
                                    onClick={() => setSelectedTaskDetail(task)}
                                    style={{
                                      left: `${leftPct}%`,
                                      width: `${widthPct}%`,
                                    }}
                                    className={`absolute top-1.5 bottom-1.5 rounded-md bg-gradient-to-r ${colorClass} border shadow-lg cursor-pointer px-2 py-0.5 flex items-center justify-between overflow-hidden hover:brightness-125 transition-all text-xs z-10`}
                                    title={`${task.operation_name} (${task.design_name || 'Design'}) — ${task.duration_hours}h [${startH.toFixed(1)}h -> ${endH.toFixed(1)}h]`}
                                  >
                                    <div className="truncate font-semibold text-[11px] leading-tight">
                                      <span>{task.operation_name}</span>
                                      <span className="text-[9px] opacity-80 block truncate">
                                        {task.design_name || `Qty ${task.quantity}`}
                                      </span>
                                    </div>
                                    <div className="text-[10px] font-mono shrink-0 pl-1">
                                      {task.duration_hours}h
                                    </div>
                                  </div>
                                );
                              })}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                );
              })()}
            </div>
          ) : (
            <div className="py-20 text-center bg-[#0E111A]/50 rounded-2xl border border-[#1E2333]/80 p-8">
              <Sparkles className="w-12 h-12 text-[#E6CA65]/60 mx-auto mb-3" />
              <h3 className="text-base font-semibold text-white">No Schedule Generated Yet</h3>
              <p className="text-sm text-slate-400 mt-1 max-w-md mx-auto">
                Select your planning horizon and time limit above, then click &quot;Run Production Solver&quot; to compute an optimal manufacturing schedule.
              </p>
              <Button
                variant="gold"
                size="sm"
                className="mt-5 font-semibold"
                onClick={handleRunOptimization}
                disabled={optimizing}
              >
                <Play className="w-4 h-4 mr-1.5 fill-current" />
                Run Production Optimizer Now
              </Button>
            </div>
          )}

          {/* Task Detail Modal */}
          {selectedTaskDetail && (
            <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
              <div className="bg-[#0E111A] border border-[#1E2333] rounded-2xl w-full max-w-md overflow-hidden shadow-2xl p-6 space-y-4">
                <div className="flex items-center justify-between border-b border-[#1E2333] pb-3">
                  <h3 className="text-base font-bold text-white flex items-center gap-2">
                    <Layers className="w-4 h-4 text-[#E6CA65]" />
                    Operation Details: {selectedTaskDetail.operation_name}
                  </h3>
                  <button onClick={() => setSelectedTaskDetail(null)} className="text-slate-400 hover:text-white">
                    <X className="w-5 h-5" />
                  </button>
                </div>

                <div className="space-y-3 text-xs">
                  <div className="flex justify-between py-1 border-b border-[#1E2333]/60">
                    <span className="text-slate-400">Design Item:</span>
                    <span className="font-bold text-white">{selectedTaskDetail.design_name || 'Jewellery Design'}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-[#1E2333]/60">
                    <span className="text-slate-400">Batch Quantity:</span>
                    <span className="font-bold text-[#F3DB7C]">{selectedTaskDetail.quantity} units</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-[#1E2333]/60">
                    <span className="text-slate-400">Sequence Stage:</span>
                    <span className="font-bold text-white">Step {selectedTaskDetail.sequence_order}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-[#1E2333]/60">
                    <span className="text-slate-400">Assigned Artisan:</span>
                    <span className="font-bold text-blue-300">{selectedTaskDetail.worker_name || 'Unassigned'}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-[#1E2333]/60">
                    <span className="text-slate-400">Assigned Equipment:</span>
                    <span className="font-bold text-purple-300">{selectedTaskDetail.machine_name || 'Manual Bench'}</span>
                  </div>
                  {selectedTaskDetail.specification_id && (
                    <div className="flex justify-between py-1 border-b border-[#1E2333]/60">
                      <span className="text-slate-400">Specification Lineage:</span>
                      <span className="font-mono text-amber-300">
                        Spec #{selectedTaskDetail.specification_id.slice(0, 8)}
                        {selectedTaskDetail.step_number != null && ` (Step ${selectedTaskDetail.step_number})`}
                      </span>
                    </div>
                  )}
                  {selectedTaskDetail.quality_checkpoint && (
                    <div className="flex justify-between py-1 border-b border-[#1E2333]/60">
                      <span className="text-slate-400">Quality Checkpoint:</span>
                      <Badge variant="gold" className="text-[10px] py-0">
                        {selectedTaskDetail.quality_checkpoint}
                      </Badge>
                    </div>
                  )}
                  <div className="flex justify-between py-1 border-b border-[#1E2333]/60">
                    <span className="text-slate-400">Start Time:</span>
                    <span className="font-mono text-white">
                      {new Date(selectedTaskDetail.start_time).toLocaleString()}
                    </span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-[#1E2333]/60">
                    <span className="text-slate-400">End Time:</span>
                    <span className="font-mono text-white">
                      {new Date(selectedTaskDetail.end_time).toLocaleString()}
                    </span>
                  </div>
                  <div className="flex justify-between py-1">
                    <span className="text-slate-400">Duration:</span>
                    <span className="font-bold text-[#E6CA65]">{selectedTaskDetail.duration_hours} hours</span>
                  </div>
                </div>

                <div className="pt-2 flex justify-end">
                  <Button variant="outline" size="sm" onClick={() => setSelectedTaskDetail(null)}>
                    Close
                  </Button>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ===================================================================== */}
      {/* MODAL: CREATE / EDIT PRODUCTION ORDER */}
      {/* ===================================================================== */}
      {isOrderModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
          <div className="bg-[#0E111A] border border-[#1E2333] rounded-2xl w-full max-w-lg overflow-hidden shadow-2xl">
            <div className="p-5 border-b border-[#1E2333] flex items-center justify-between">
              <h3 className="text-lg font-bold text-white flex items-center gap-2">
                <Factory className="w-5 h-5 text-[#E6CA65]" />
                {editingOrder ? 'Edit Production Order' : 'Create Production Order'}
              </h3>
              <button
                onClick={() => {
                  setIsOrderModalOpen(false);
                  setEditingOrder(null);
                }}
                className="text-slate-400 hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleSaveOrder} className="p-6 space-y-4">
              {!editingOrder && (
                <div className="space-y-3">
                  <div className="flex items-center space-x-2 p-1 bg-[#111625] rounded-xl border border-[#1E2333]">
                    <button
                      type="button"
                      onClick={() => setOrderCreationMode('specification')}
                      className={`flex-1 py-1.5 px-3 rounded-lg text-xs font-semibold transition-all flex items-center justify-center space-x-1.5 ${
                        orderCreationMode === 'specification'
                          ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40 shadow-sm'
                          : 'text-slate-400 hover:text-white'
                      }`}
                    >
                      <ShieldCheck className="w-3.5 h-3.5" />
                      <span>From Approved Spec</span>
                    </button>
                    <button
                      type="button"
                      onClick={() => setOrderCreationMode('design')}
                      className={`flex-1 py-1.5 px-3 rounded-lg text-xs font-semibold transition-all flex items-center justify-center space-x-1.5 ${
                        orderCreationMode === 'design'
                          ? 'bg-[#1E2333] text-white border border-slate-700 shadow-sm'
                          : 'text-slate-400 hover:text-white'
                      }`}
                    >
                      <Layers className="w-3.5 h-3.5" />
                      <span>Custom Design</span>
                    </button>
                  </div>

                  <input type="hidden" name="order_mode" value={orderCreationMode} />

                  {orderCreationMode === 'specification' ? (
                    <div>
                      <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
                        Approved Specification ID <span className="text-amber-400">*</span>
                      </label>
                      <Input
                        name="specification_id"
                        value={specInputId}
                        onChange={(e) => setSpecInputId(e.target.value)}
                        placeholder="e.g. 550e8400-e29b-41d4-a716-446655440000"
                        className="bg-[#111625] border-[#1E2333] font-mono text-xs text-amber-200"
                        required={orderCreationMode === 'specification'}
                      />
                      <p className="text-[11px] text-slate-500 mt-1">
                        Authoritative render, materials BOM, and manufacturing routing are automatically derived from the approved specification.
                      </p>
                    </div>
                  ) : (
                    <div>
                      <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
                        Associated Jewellery Design <span className="text-rose-400">*</span>
                      </label>
                      {userDesigns.length === 0 ? (
                        <div className="bg-[#D4AF37]/10 border border-[#D4AF37]/30 rounded-lg p-3 text-xs text-[#F3DB7C]">
                          No saved designs found. Please create a design in the Studio first.
                        </div>
                      ) : (
                        <select
                          name="design_id"
                          required={orderCreationMode === 'design'}
                          className="w-full bg-[#111625] border border-[#1E2333] text-slate-200 text-sm rounded-lg px-3 py-2.5 outline-none focus:border-[#D4AF37]"
                        >
                          <option value="">-- Choose a jewellery design --</option>
                          {userDesigns.map((d) => (
                            <option key={d.id} value={d.id}>
                              {d.name} ({d.category})
                            </option>
                          ))}
                        </select>
                      )}
                    </div>
                  )}
                </div>
              )}

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
                    Quantity (Units) <span className="text-rose-400">*</span>
                  </label>
                  <Input
                    name="quantity"
                    type="number"
                    min="1"
                    defaultValue={editingOrder?.quantity ?? 1}
                    required
                    className="bg-[#111625] border-[#1E2333]"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
                    Priority Level <span className="text-rose-400">*</span>
                  </label>
                  <select
                    name="priority"
                    defaultValue={editingOrder?.priority ?? 'medium'}
                    className="w-full bg-[#111625] border border-[#1E2333] text-slate-200 text-sm rounded-lg px-3 py-2 outline-none focus:border-[#D4AF37] h-10"
                  >
                    {ORDER_PRIORITIES.map((p) => (
                      <option key={p.value} value={p.value}>
                        {p.label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
                    Production Status <span className="text-rose-400">*</span>
                  </label>
                  <select
                    name="status"
                    defaultValue={editingOrder?.status ?? 'pending'}
                    className="w-full bg-[#111625] border border-[#1E2333] text-slate-200 text-sm rounded-lg px-3 py-2 outline-none focus:border-[#D4AF37] h-10"
                  >
                    {ORDER_STATUSES.map((s) => (
                      <option key={s.value} value={s.value}>
                        {s.label}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
                    Target Deadline <span className="text-rose-400">*</span>
                  </label>
                  <Input
                    name="deadline"
                    type="date"
                    required
                    defaultValue={
                      editingOrder
                        ? new Date(editingOrder.deadline).toISOString().split('T')[0]
                        : new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]
                    }
                    className="bg-[#111625] border-[#1E2333] text-sm"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
                  Production Notes & Instructions
                </label>
                <Textarea
                  name="notes"
                  rows={3}
                  placeholder="Special client requirements, metal alloy karatage, pavé specifications..."
                  defaultValue={editingOrder?.notes ?? ''}
                  className="bg-[#111625] border-[#1E2333] text-sm"
                />
              </div>

              <div className="flex justify-end space-x-3 pt-4 border-t border-[#1E2333]">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    setIsOrderModalOpen(false);
                    setEditingOrder(null);
                  }}
                >
                  Cancel
                </Button>
                <Button type="submit" variant="gold" size="sm" className="font-semibold">
                  {editingOrder ? 'Save Changes' : 'Create Order'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ===================================================================== */}
      {/* MODAL: ADD / EDIT WORKSHOP ARTISAN */}
      {/* ===================================================================== */}
      {isWorkerModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
          <div className="bg-[#0E111A] border border-[#1E2333] rounded-2xl w-full max-w-md overflow-hidden shadow-2xl">
            <div className="p-5 border-b border-[#1E2333] flex items-center justify-between">
              <h3 className="text-lg font-bold text-white flex items-center gap-2">
                <Users className="w-5 h-5 text-[#E6CA65]" />
                {editingWorker ? 'Edit Artisan Profile' : 'Add Workshop Artisan'}
              </h3>
              <button
                onClick={() => {
                  setIsWorkerModalOpen(false);
                  setEditingWorker(null);
                }}
                className="text-slate-400 hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleSaveWorker} className="p-6 space-y-4">
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
                  Artisan Full Name <span className="text-rose-400">*</span>
                </label>
                <Input
                  name="name"
                  placeholder="e.g. Anand Verma"
                  defaultValue={editingWorker?.name ?? ''}
                  required
                  className="bg-[#111625] border-[#1E2333]"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
                  Craft Specialization <span className="text-rose-400">*</span>
                </label>
                <select
                  name="skill"
                  defaultValue={editingWorker?.skill ?? 'stone_setting'}
                  className="w-full bg-[#111625] border border-[#1E2333] text-slate-200 text-sm rounded-lg px-3 py-2 outline-none focus:border-[#D4AF37] h-10"
                >
                  {WORKER_SKILLS.map((s) => (
                    <option key={s.value} value={s.value}>
                      {s.label}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
                  Daily Productive Capacity (Hours/Day) <span className="text-rose-400">*</span>
                </label>
                <Input
                  name="capacity_hours_per_day"
                  type="number"
                  step="0.5"
                  min="0"
                  max="24"
                  defaultValue={editingWorker?.capacity_hours_per_day ?? 8.0}
                  required
                  className="bg-[#111625] border-[#1E2333]"
                />
              </div>

              <div className="flex items-center space-x-2 pt-2">
                <input
                  type="checkbox"
                  id="worker_available"
                  name="is_available"
                  defaultChecked={editingWorker?.is_available ?? true}
                  className="w-4 h-4 rounded border-[#262C40] bg-[#121622] text-[#D4AF37] focus:ring-amber-500"
                />
                <label htmlFor="worker_available" className="text-sm font-medium text-slate-300">
                  Currently active and present in workshop
                </label>
              </div>

              <div className="flex justify-end space-x-3 pt-4 border-t border-[#1E2333]">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    setIsWorkerModalOpen(false);
                    setEditingWorker(null);
                  }}
                >
                  Cancel
                </Button>
                <Button type="submit" variant="gold" size="sm" className="font-semibold">
                  {editingWorker ? 'Save Changes' : 'Add Artisan'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ===================================================================== */}
      {/* MODAL: ADD / EDIT MACHINERY */}
      {/* ===================================================================== */}
      {isMachineModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
          <div className="bg-[#0E111A] border border-[#1E2333] rounded-2xl w-full max-w-md overflow-hidden shadow-2xl">
            <div className="p-5 border-b border-[#1E2333] flex items-center justify-between">
              <h3 className="text-lg font-bold text-white flex items-center gap-2">
                <Cpu className="w-5 h-5 text-purple-400" />
                {editingMachine ? 'Edit Machine Details' : 'Register Workshop Machine'}
              </h3>
              <button
                onClick={() => {
                  setIsMachineModalOpen(false);
                  setEditingMachine(null);
                }}
                className="text-slate-400 hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleSaveMachine} className="p-6 space-y-4">
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
                  Machine Model / ID <span className="text-rose-400">*</span>
                </label>
                <Input
                  name="name"
                  placeholder="e.g. Sisma Fiber Laser Marking System"
                  defaultValue={editingMachine?.name ?? ''}
                  required
                  className="bg-[#111625] border-[#1E2333]"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
                  Equipment Category <span className="text-rose-400">*</span>
                </label>
                <select
                  name="machine_type"
                  defaultValue={editingMachine?.machine_type ?? 'laser_engraver'}
                  className="w-full bg-[#111625] border border-[#1E2333] text-slate-200 text-sm rounded-lg px-3 py-2 outline-none focus:border-[#D4AF37] h-10"
                >
                  {MACHINE_TYPES.map((t) => (
                    <option key={t.value} value={t.value}>
                      {t.label}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
                  Daily Operational Capacity (Hours/Day) <span className="text-rose-400">*</span>
                </label>
                <Input
                  name="capacity_hours_per_day"
                  type="number"
                  step="0.5"
                  min="0"
                  max="24"
                  defaultValue={editingMachine?.capacity_hours_per_day ?? 8.0}
                  required
                  className="bg-[#111625] border-[#1E2333]"
                />
              </div>

              <div className="flex items-center space-x-2 pt-2">
                <input
                  type="checkbox"
                  id="machine_available"
                  name="is_available"
                  defaultChecked={editingMachine?.is_available ?? true}
                  className="w-4 h-4 rounded border-[#262C40] bg-[#121622] text-purple-500 focus:ring-purple-500"
                />
                <label htmlFor="machine_available" className="text-sm font-medium text-slate-300">
                  Operational and ready for manufacturing runs
                </label>
              </div>

              <div className="flex justify-end space-x-3 pt-4 border-t border-[#1E2333]">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    setIsMachineModalOpen(false);
                    setEditingMachine(null);
                  }}
                >
                  Cancel
                </Button>
                <Button type="submit" variant="gold" size="sm" className="font-semibold">
                  {editingMachine ? 'Save Changes' : 'Register Machine'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ===================================================================== */}
      {/* MODAL: DELETE CONFIRMATION */}
      {/* ===================================================================== */}
      {deletingItem && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
          <div className="bg-[#0E111A] border border-rose-900/50 rounded-2xl w-full max-w-sm overflow-hidden shadow-2xl p-6 text-center">
            <div className="w-12 h-12 rounded-full bg-rose-500/10 border border-rose-500/30 flex items-center justify-center text-rose-400 mx-auto mb-4">
              <AlertTriangle className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-white mb-1">Confirm Deletion</h3>
            <p className="text-sm text-slate-400 mb-6">
              Are you sure you want to delete <span className="text-white font-medium">{deletingItem.name}</span>? This action cannot be undone.
            </p>
            <div className="flex justify-center space-x-3">
              <Button variant="outline" size="sm" onClick={() => setDeletingItem(null)}>
                Cancel
              </Button>
              <Button variant="destructive" size="sm" onClick={handleConfirmDelete} className="font-semibold">
                Delete
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ProductionPage;
