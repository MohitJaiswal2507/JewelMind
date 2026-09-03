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
} from '../types/production';

type ActiveTab = 'orders' | 'workers' | 'machines';

interface ProductionPageProps {
  onNavigateToStudio?: () => void;
  onSelectDesign?: (design: Design) => void;
}

export const ProductionPage: React.FC<ProductionPageProps> = () => {
  const [activeTab, setActiveTab] = useState<ActiveTab>('orders');
  const [summary, setSummary] = useState<ProductionSummary | null>(null);

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
  // Modals
  // -------------------------------------------------------------------------
  const [isOrderModalOpen, setIsOrderModalOpen] = useState<boolean>(false);
  const [editingOrder, setEditingOrder] = useState<ProductionOrder | null>(null);

  const [isWorkerModalOpen, setIsWorkerModalOpen] = useState<boolean>(false);
  const [editingWorker, setEditingWorker] = useState<Worker | null>(null);

  const [isMachineModalOpen, setIsMachineModalOpen] = useState<boolean>(false);
  const [editingMachine, setEditingMachine] = useState<Machine | null>(null);

  const [deletingItem, setDeletingItem] = useState<{ type: 'order' | 'worker' | 'machine'; id: string; name: string } | null>(null);

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

  useEffect(() => {
    fetchSummary();
    fetchOrders();
    fetchWorkers();
    fetchMachines();
    fetchUserDesigns();
  }, [fetchSummary, fetchOrders, fetchWorkers, fetchMachines, fetchUserDesigns]);

  // -------------------------------------------------------------------------
  // Order Handlers
  // -------------------------------------------------------------------------
  const handleSaveOrder = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    const design_id = formData.get('design_id') as string;
    const quantity = parseInt(formData.get('quantity') as string, 10);
    const priority = formData.get('priority') as OrderPriority;
    const status = formData.get('status') as OrderStatus;
    const deadlineInput = formData.get('deadline') as string;
    const notes = formData.get('notes') as string;

    if (!design_id && !editingOrder) {
      showFeedback('Please select a jewellery design.', 'error');
      return;
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
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-slate-800">
        <div>
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-amber-500/20 via-amber-400/20 to-yellow-300/10 border border-amber-500/30 flex items-center justify-center text-amber-400">
              <Factory className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
                Production Management
                <Badge variant="outline" className="text-xs bg-amber-500/10 text-amber-400 border-amber-500/30 font-semibold">
                  Phase 11
                </Badge>
              </h1>
              <p className="text-sm text-slate-400">
                Manufacturing orders, workshop artisans, equipment capacity & deadline tracking.
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              fetchSummary();
              fetchOrders();
              fetchWorkers();
              fetchMachines();
            }}
            className="border-slate-800 hover:bg-slate-800/60 text-slate-300"
          >
            <RefreshCw className="w-4 h-4 mr-1.5" />
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
              className="font-semibold shadow-lg shadow-amber-500/10"
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
              className="font-semibold shadow-lg shadow-amber-500/10"
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
              className="font-semibold shadow-lg shadow-amber-500/10"
            >
              <Plus className="w-4 h-4 mr-1.5" />
              Add Machine
            </Button>
          )}
        </div>
      </div>

      {/* KPI Metrics Dashboard Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 my-6">
        <Card className="bg-[#0b0e17]/80 border-slate-800/80 backdrop-blur">
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
            <div className="w-10 h-10 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400">
              <TrendingUp className="w-5 h-5" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-[#0b0e17]/80 border-slate-800/80 backdrop-blur">
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
            <div className={`w-10 h-10 rounded-xl border flex items-center justify-center ${summary && summary.overdue_orders > 0 ? 'bg-rose-500/10 border-rose-500/30 text-rose-400' : 'bg-slate-800/50 border-slate-700/50 text-slate-400'}`}>
              <AlertTriangle className="w-5 h-5" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-[#0b0e17]/80 border-slate-800/80 backdrop-blur">
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

        <Card className="bg-[#0b0e17]/80 border-slate-800/80 backdrop-blur">
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
      <div className="flex space-x-1 border-b border-slate-800 my-6">
        <button
          onClick={() => setActiveTab('orders')}
          className={`flex items-center space-x-2 py-3 px-5 border-b-2 font-medium text-sm transition-colors ${
            activeTab === 'orders'
              ? 'border-amber-400 text-amber-400 bg-amber-400/5'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <Factory className="w-4 h-4" />
          <span>Production Orders</span>
          <Badge variant="secondary" className="text-[10px] ml-1 bg-slate-800">
            {totalOrders}
          </Badge>
        </button>

        <button
          onClick={() => setActiveTab('workers')}
          className={`flex items-center space-x-2 py-3 px-5 border-b-2 font-medium text-sm transition-colors ${
            activeTab === 'workers'
              ? 'border-amber-400 text-amber-400 bg-amber-400/5'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <Users className="w-4 h-4" />
          <span>Workshop Artisans</span>
          <Badge variant="secondary" className="text-[10px] ml-1 bg-slate-800">
            {workers.length}
          </Badge>
        </button>

        <button
          onClick={() => setActiveTab('machines')}
          className={`flex items-center space-x-2 py-3 px-5 border-b-2 font-medium text-sm transition-colors ${
            activeTab === 'machines'
              ? 'border-amber-400 text-amber-400 bg-amber-400/5'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <Cpu className="w-4 h-4" />
          <span>Machinery & Tools</span>
          <Badge variant="secondary" className="text-[10px] ml-1 bg-slate-800">
            {machines.length}
          </Badge>
        </button>
      </div>

      {/* ===================================================================== */}
      {/* TAB 1: PRODUCTION ORDERS */}
      {/* ===================================================================== */}
      {activeTab === 'orders' && (
        <div>
          {/* Filters Bar */}
          <div className="flex flex-col sm:flex-row gap-3 items-center justify-between bg-[#0b0e17]/80 p-3 rounded-xl border border-slate-800/80 mb-6">
            <div className="relative w-full sm:w-80">
              <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
              <Input
                placeholder="Search design name or notes..."
                value={orderSearch}
                onChange={(e) => {
                  setOrderSearch(e.target.value);
                  setOrderPage(1);
                }}
                className="pl-9 bg-[#111625] border-slate-800 text-sm h-9"
              />
            </div>

            <div className="flex items-center space-x-2 w-full sm:w-auto">
              <select
                value={statusFilter}
                onChange={(e) => {
                  setStatusFilter(e.target.value as OrderStatus | '');
                  setOrderPage(1);
                }}
                className="bg-[#111625] border border-slate-800 text-slate-300 text-xs rounded-lg px-3 py-2 outline-none focus:border-amber-500"
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
                className="bg-[#111625] border border-slate-800 text-slate-300 text-xs rounded-lg px-3 py-2 outline-none focus:border-amber-500"
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
              <RefreshCw className="w-8 h-8 animate-spin text-amber-400 mb-3" />
              <p className="text-sm">Loading production orders...</p>
            </div>
          ) : orders.length === 0 ? (
            <div className="py-20 text-center bg-[#0b0e17]/50 rounded-2xl border border-slate-800/80 p-8">
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
            <div className="overflow-x-auto rounded-xl border border-slate-800/80 bg-[#0b0e17]/80 backdrop-blur">
              <table className="w-full text-left border-collapse text-sm">
                <thead>
                  <tr className="border-b border-slate-800 text-xs uppercase tracking-wider text-slate-400 bg-slate-900/40">
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
                      <tr key={order.id} className="hover:bg-slate-800/30 transition-colors">
                        <td className="py-3.5 px-4 font-medium text-white flex items-center space-x-3">
                          <div className="w-10 h-10 rounded-lg bg-slate-900 border border-slate-800 overflow-hidden shrink-0 flex items-center justify-center">
                            {order.design_thumbnail_url ? (
                              <img
                                src={order.design_thumbnail_url}
                                alt={order.design_name || 'Design'}
                                className="w-full h-full object-cover"
                              />
                            ) : (
                              <Layers className="w-5 h-5 text-slate-600" />
                            )}
                          </div>
                          <div>
                            <p className="font-semibold text-white leading-snug">
                              {order.design_name || 'Jewellery Design'}
                            </p>
                            <p className="text-xs text-slate-500">{order.design_category || 'Custom Item'}</p>
                          </div>
                        </td>

                        <td className="py-3.5 px-4">
                          <span className="font-bold text-amber-300">{order.quantity}</span>{' '}
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
                              variant="ghost"
                              size="sm"
                              onClick={() => {
                                setEditingOrder(order);
                                setIsOrderModalOpen(true);
                              }}
                              className="h-8 w-8 p-0 text-slate-400 hover:text-amber-400"
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
              <RefreshCw className="w-8 h-8 animate-spin text-amber-400 mb-3" />
              <p className="text-sm">Loading artisan roster...</p>
            </div>
          ) : workers.length === 0 ? (
            <div className="py-20 text-center bg-[#0b0e17]/50 rounded-2xl border border-slate-800/80 p-8">
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
                  <Card key={worker.id} className="bg-[#0b0e17]/80 border-slate-800 hover:border-slate-700 transition-all">
                    <CardHeader className="p-4 pb-2 flex flex-row items-start justify-between space-y-0">
                      <div className="flex items-center space-x-3">
                        <div className="w-10 h-10 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400 font-bold">
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
                          className="h-8 w-8 p-0 text-slate-400 hover:text-amber-400"
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
                      <div className="bg-slate-900/60 rounded-lg p-3 my-2 border border-slate-800/80 flex items-center justify-between">
                        <div>
                          <p className="text-[11px] text-slate-500 uppercase tracking-wider">Productive Capacity</p>
                          <p className="text-base font-bold text-amber-300 mt-0.5">
                            {worker.capacity_hours_per_day}{' '}
                            <span className="text-xs font-normal text-slate-400">hours / day</span>
                          </p>
                        </div>

                        <button
                          onClick={() => handleToggleWorkerAvailability(worker)}
                          className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-full text-xs font-semibold border transition-all ${
                            worker.is_available
                              ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30 hover:bg-emerald-500/20'
                              : 'bg-slate-800 text-slate-400 border-slate-700 hover:bg-slate-700'
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
            <div className="py-20 text-center bg-[#0b0e17]/50 rounded-2xl border border-slate-800/80 p-8">
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
                  <Card key={machine.id} className="bg-[#0b0e17]/80 border-slate-800 hover:border-slate-700 transition-all">
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
                      <div className="bg-slate-900/60 rounded-lg p-3 my-2 border border-slate-800/80 flex items-center justify-between">
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
      {/* MODAL: CREATE / EDIT PRODUCTION ORDER */}
      {/* ===================================================================== */}
      {isOrderModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
          <div className="bg-[#0b0e17] border border-slate-800 rounded-2xl w-full max-w-lg overflow-hidden shadow-2xl">
            <div className="p-5 border-b border-slate-800 flex items-center justify-between">
              <h3 className="text-lg font-bold text-white flex items-center gap-2">
                <Factory className="w-5 h-5 text-amber-400" />
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
                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
                    Associated Jewellery Design <span className="text-rose-400">*</span>
                  </label>
                  {userDesigns.length === 0 ? (
                    <div className="bg-amber-500/10 border border-amber-500/30 rounded-lg p-3 text-xs text-amber-300">
                      No saved designs found. Please create a design in the Studio first.
                    </div>
                  ) : (
                    <select
                      name="design_id"
                      required
                      className="w-full bg-[#111625] border border-slate-800 text-slate-200 text-sm rounded-lg px-3 py-2.5 outline-none focus:border-amber-500"
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
                    className="bg-[#111625] border-slate-800"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
                    Priority Level <span className="text-rose-400">*</span>
                  </label>
                  <select
                    name="priority"
                    defaultValue={editingOrder?.priority ?? 'medium'}
                    className="w-full bg-[#111625] border border-slate-800 text-slate-200 text-sm rounded-lg px-3 py-2 outline-none focus:border-amber-500 h-10"
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
                    className="w-full bg-[#111625] border border-slate-800 text-slate-200 text-sm rounded-lg px-3 py-2 outline-none focus:border-amber-500 h-10"
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
                    className="bg-[#111625] border-slate-800 text-sm"
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
                  className="bg-[#111625] border-slate-800 text-sm"
                />
              </div>

              <div className="flex justify-end space-x-3 pt-4 border-t border-slate-800">
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
          <div className="bg-[#0b0e17] border border-slate-800 rounded-2xl w-full max-w-md overflow-hidden shadow-2xl">
            <div className="p-5 border-b border-slate-800 flex items-center justify-between">
              <h3 className="text-lg font-bold text-white flex items-center gap-2">
                <Users className="w-5 h-5 text-amber-400" />
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
                  className="bg-[#111625] border-slate-800"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
                  Craft Specialization <span className="text-rose-400">*</span>
                </label>
                <select
                  name="skill"
                  defaultValue={editingWorker?.skill ?? 'stone_setting'}
                  className="w-full bg-[#111625] border border-slate-800 text-slate-200 text-sm rounded-lg px-3 py-2 outline-none focus:border-amber-500 h-10"
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
                  className="bg-[#111625] border-slate-800"
                />
              </div>

              <div className="flex items-center space-x-2 pt-2">
                <input
                  type="checkbox"
                  id="worker_available"
                  name="is_available"
                  defaultChecked={editingWorker?.is_available ?? true}
                  className="w-4 h-4 rounded border-slate-700 bg-slate-900 text-amber-500 focus:ring-amber-500"
                />
                <label htmlFor="worker_available" className="text-sm font-medium text-slate-300">
                  Currently active and present in workshop
                </label>
              </div>

              <div className="flex justify-end space-x-3 pt-4 border-t border-slate-800">
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
          <div className="bg-[#0b0e17] border border-slate-800 rounded-2xl w-full max-w-md overflow-hidden shadow-2xl">
            <div className="p-5 border-b border-slate-800 flex items-center justify-between">
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
                  className="bg-[#111625] border-slate-800"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
                  Equipment Category <span className="text-rose-400">*</span>
                </label>
                <select
                  name="machine_type"
                  defaultValue={editingMachine?.machine_type ?? 'laser_engraver'}
                  className="w-full bg-[#111625] border border-slate-800 text-slate-200 text-sm rounded-lg px-3 py-2 outline-none focus:border-amber-500 h-10"
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
                  className="bg-[#111625] border-slate-800"
                />
              </div>

              <div className="flex items-center space-x-2 pt-2">
                <input
                  type="checkbox"
                  id="machine_available"
                  name="is_available"
                  defaultChecked={editingMachine?.is_available ?? true}
                  className="w-4 h-4 rounded border-slate-700 bg-slate-900 text-purple-500 focus:ring-purple-500"
                />
                <label htmlFor="machine_available" className="text-sm font-medium text-slate-300">
                  Operational and ready for manufacturing runs
                </label>
              </div>

              <div className="flex justify-end space-x-3 pt-4 border-t border-slate-800">
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
          <div className="bg-[#0b0e17] border border-rose-900/50 rounded-2xl w-full max-w-sm overflow-hidden shadow-2xl p-6 text-center">
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
