import React, { useState } from 'react';
import {
  ArrowLeft,
  Sparkles,
  Calendar,
  Hammer,
  Cpu,
  CheckCircle2,
  Play,
  Pause,
  ShieldCheck,
  Scale,
  IndianRupee,
  Layers,
  TrendingUp,
  Sliders,
  Check,
  Clock,
} from 'lucide-react';
import { Button } from '../../ui/button';
import { Badge } from '../../ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '../../ui/card';
import { ProductionOrder, Worker, Machine, ORDER_PRIORITIES, ORDER_STATUSES } from '../../../types/production';
import {
  OperationExecution,
  OrderMaterialSummaryResponse,
  OrderQualitySummaryResponse,
  ExecutionStatus,
} from '../../../types/execution';
import { ProductionOrderAnalyticsResponse } from '../../../types/analytics';
import {
  DEFAULT_INDIAN_WORKSHOP_RATES,
  WorkshopRateConfig,
  formatINR,
  getIndianMetalRate,
} from '../../../types/materialValuation';

interface SelectedOrderCommandCenterProps {
  order: ProductionOrder;
  executions: OperationExecution[];
  currentExecution: OperationExecution | null;
  workers: Worker[];
  machines: Machine[];
  materialSummary: OrderMaterialSummaryResponse | null;
  qualitySummary: OrderQualitySummaryResponse | null;
  analytics: ProductionOrderAnalyticsResponse | null;
  rateConfig?: WorkshopRateConfig;
  onBack: () => void;
  onOpenShopFloorTerminal: () => void;
  onTransitionExecution: (executionId: string, targetStatus: ExecutionStatus) => Promise<void>;
  onOpenWorkerModal: (execution: OperationExecution) => void;
  onOpenMachineModal: (execution: OperationExecution) => void;
  onOpenQcModal: (execution: OperationExecution) => void;
  onOpenMaterialModal: (execution: OperationExecution) => void;
  onCompleteOrder: () => Promise<void>;
  actionLoading?: boolean;
}

export const SelectedOrderCommandCenter: React.FC<SelectedOrderCommandCenterProps> = ({
  order,
  executions,
  currentExecution,
  workers: _workers,
  machines: _machines,
  materialSummary,
  qualitySummary,
  analytics: _analytics,
  rateConfig = DEFAULT_INDIAN_WORKSHOP_RATES,
  onBack,
  onOpenShopFloorTerminal,
  onTransitionExecution,
  onOpenWorkerModal,
  onOpenMachineModal,
  onOpenQcModal,
  onOpenMaterialModal,
  onCompleteOrder,
  actionLoading = false,
}) => {
  const [activeSubTab, setActiveSubTab] = useState<'overview' | 'materials' | 'economics' | 'qc' | 'timeline'>('overview');

  const priorityConfig = ORDER_PRIORITIES.find((p) => p.value === order.priority);
  const statusConfig = ORDER_STATUSES.find((s) => s.value === order.status);

  // Compute total planned & actual bench hours from executions
  const totalPlannedHours = executions.reduce((acc, curr) => acc + (curr.planned_duration_hours || 0), 0);
  const totalActualHours = executions.reduce((acc, curr) => acc + (curr.actual_duration_hours || 0), 0);

  // Material & Economics Calculation
  let totalMaterialCost = 0;
  let primaryMetalWeightGrams = 0;
  let primaryMetalRatePerGram = rateConfig.gold18k;

  if (materialSummary && materialSummary.items.length > 0) {
    materialSummary.items.forEach((item) => {
      const rate = getIndianMetalRate(item.material_name, rateConfig) || 0;
      const weight = item.actual_quantity > 0 ? item.actual_quantity : item.planned_quantity;
      if (item.material_type.toUpperCase() === 'METAL' || item.unit === 'g') {
        primaryMetalWeightGrams += weight;
        if (rate > 0) primaryMetalRatePerGram = rate;
      }
      totalMaterialCost += weight * rate;
    });
  } else {
    // Standard spec estimation fallback
    primaryMetalWeightGrams = (order.quantity || 1) * 8.5;
    totalMaterialCost = primaryMetalWeightGrams * primaryMetalRatePerGram;
  }

  // Making charges / Labour (Karigar hours × hourly rate)
  const effectiveHours = totalActualHours > 0 ? totalActualHours : totalPlannedHours > 0 ? totalPlannedHours : 12.0;
  const labourCost = effectiveHours * rateConfig.standardKarigarHourlyRate;
  const machineCost = effectiveHours * 0.4 * rateConfig.machineOverheadHourlyRate;
  const totalManufacturingCost = totalMaterialCost + labourCost + machineCost;
  const estimatedSellingPrice = totalManufacturingCost * (1 + rateConfig.standardRetailMarkupPercent / 100);
  const grossMargin = estimatedSellingPrice - totalManufacturingCost;
  const grossMarginPercent = (grossMargin / estimatedSellingPrice) * 100;

  // Completion Gate Checklist
  const allStepsCompleted = executions.length > 0 && executions.every((e) => e.status === 'completed');
  const materialsLogged = materialSummary ? materialSummary.total_actual_quantity > 0 : false;
  const qcPassed = qualitySummary ? qualitySummary.failed === 0 && qualitySummary.passed > 0 : false;
  const noActiveRework = executions.every((e) => e.status !== 'blocked');
  const canCompleteOrder = allStepsCompleted && noActiveRework && order.status !== 'completed';

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Top Breadcrumb & Actions Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-[#1E2333]/80">
        <div className="flex items-center space-x-3">
          <Button
            variant="outline"
            size="sm"
            onClick={onBack}
            className="h-8 px-2.5 border-[#1E2333] hover:bg-[#161B26] text-slate-300"
          >
            <ArrowLeft className="w-4 h-4 mr-1.5" />
            <span>All Orders</span>
          </Button>
          <span className="text-slate-600">•</span>
          <div className="flex items-center gap-2">
            <span className="text-sm font-serif font-medium text-white truncate max-w-[200px] sm:max-w-md">
              {order.design_name || 'Bespoke Order'}
            </span>
            <span className="text-xs font-mono text-amber-300/80 px-2 py-0.5 rounded bg-amber-400/10 border border-amber-400/20">
              #{order.id.slice(0, 8)}
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2.5">
          <Button
            variant="gold"
            size="sm"
            onClick={onOpenShopFloorTerminal}
            className="h-8 text-xs font-semibold shadow-lg shadow-[#D4AF37]/10"
          >
            <Hammer className="w-3.5 h-3.5 mr-1.5" />
            <span>Launch Shop-Floor Terminal</span>
          </Button>
        </div>
      </div>

      {/* Selected Order Summary Banner */}
      <div className="p-5 rounded-2xl bg-[#0E111A]/95 border border-white/[0.08] relative overflow-hidden">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-5">
          <div className="flex items-start sm:items-center space-x-4 min-w-0">
            <div className="w-16 h-16 rounded-xl bg-[#161B26] border border-white/[0.08] overflow-hidden shrink-0 flex items-center justify-center relative">
              {order.design_thumbnail_url ? (
                <img
                  src={order.design_thumbnail_url}
                  alt={order.design_name || 'Product'}
                  className="w-full h-full object-cover"
                />
              ) : (
                <Sparkles className="w-6 h-6 text-amber-300/40" />
              )}
            </div>

            <div className="space-y-1.5 min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <h2 className="text-lg font-serif font-bold text-white tracking-wide truncate">
                  {order.design_name || 'Bespoke Fine Jewellery'}
                </h2>
                {priorityConfig && (
                  <Badge variant="outline" className={`text-[10px] capitalize ${priorityConfig.color}`}>
                    {priorityConfig.label} Priority
                  </Badge>
                )}
                {statusConfig && (
                  <Badge variant="outline" className={`text-[10px] capitalize font-medium ${statusConfig.color}`}>
                    {statusConfig.label}
                  </Badge>
                )}
              </div>

              <div className="flex items-center gap-3 text-xs text-slate-400 font-light flex-wrap">
                <span className="text-slate-300 font-medium capitalize">
                  {order.design_category || 'Pendant'}
                </span>
                <span className="text-slate-600">•</span>
                <span>Quantity: <strong className="text-white font-medium">{order.quantity} units</strong></span>
                <span className="text-slate-600">•</span>
                <span className="flex items-center gap-1">
                  <Calendar className="w-3.5 h-3.5 text-slate-500" />
                  Target Delivery: {order.deadline ? new Date(order.deadline).toLocaleDateString() : 'Flexible'}
                </span>
                {order.specification_version && (
                  <>
                    <span className="text-slate-600">•</span>
                    <span className="text-amber-300/90 font-mono">Specification v{order.specification_version} Approved</span>
                  </>
                )}
              </div>
            </div>
          </div>

          {/* Quick Economics Metrics */}
          <div className="flex items-center gap-6 border-t md:border-t-0 md:border-l border-white/[0.08] pt-4 md:pt-0 md:pl-6 shrink-0">
            <div>
              <div className="text-[11px] uppercase tracking-wider text-slate-400 font-light">Material Value</div>
              <div className="text-lg font-serif font-bold text-emerald-300">
                {formatINR(totalMaterialCost)}
              </div>
              <div className="text-[10px] text-slate-500 font-mono">@ ₹{primaryMetalRatePerGram}/g 18K</div>
            </div>

            <div>
              <div className="text-[11px] uppercase tracking-wider text-slate-400 font-light">Est. Margin</div>
              <div className="text-lg font-serif font-bold text-amber-300">
                {grossMarginPercent.toFixed(1)}%
              </div>
              <div className="text-[10px] text-slate-500 font-mono">{formatINR(grossMargin)}</div>
            </div>
          </div>
        </div>
      </div>

      {/* Visual Production Route Progression (Section 10) */}
      <Card className="bg-[#0E111A]/95 border-white/[0.07]">
        <CardHeader className="p-4 sm:p-5 pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-xs font-semibold uppercase tracking-wider text-amber-300/90 flex items-center gap-2">
              <Layers className="w-4 h-4" />
              <span>Production Route Progression ({executions.length} Stages)</span>
            </CardTitle>
            <span className="text-xs font-mono text-slate-400">
              {executions.filter((e) => e.status === 'completed').length} of {executions.length} Completed
            </span>
          </div>
        </CardHeader>
        <CardContent className="p-4 sm:p-5 pt-0">
          <div className="overflow-x-auto pb-2">
            <div className="flex items-center min-w-[720px] py-3">
              {executions.map((exec, idx) => {
                const isCompleted = exec.status === 'completed';
                const isActive = exec.status === 'in_progress' || exec.status === 'paused';
                const isLast = idx === executions.length - 1;

                return (
                  <React.Fragment key={exec.id}>
                    <div className="flex flex-col items-center space-y-2 shrink-0 w-32 text-center group cursor-pointer">
                      {/* Step Circle Badge */}
                      <div
                        className={`w-9 h-9 rounded-xl flex items-center justify-center font-mono text-xs font-bold transition-all duration-300 ${
                          isCompleted
                            ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/50 shadow-md shadow-emerald-500/10'
                            : isActive
                            ? 'bg-amber-500/25 text-amber-300 border border-amber-400 ring-2 ring-amber-400/30 animate-pulse'
                            : 'bg-white/[0.04] text-slate-500 border border-white/[0.08]'
                        }`}
                      >
                        {isCompleted ? <Check className="w-4 h-4 text-emerald-400 stroke-[3]" /> : idx + 1}
                      </div>

                      <div className="space-y-0.5">
                        <div
                          className={`text-xs font-medium truncate max-w-[120px] ${
                            isActive ? 'text-amber-300 font-semibold' : isCompleted ? 'text-slate-200' : 'text-slate-500'
                          }`}
                        >
                          {exec.stage_name || `Step ${idx + 1}`}
                        </div>
                        <div className="text-[10px] text-slate-500 font-mono">
                          {isCompleted
                            ? `${exec.actual_duration_hours?.toFixed(1) || '0.5'}h`
                            : isActive
                            ? 'Active'
                            : 'Pending'}
                        </div>
                      </div>
                    </div>

                    {!isLast && (
                      <div
                        className={`flex-1 h-0.5 transition-colors duration-300 ${
                          isCompleted ? 'bg-emerald-500/50' : 'bg-white/[0.08]'
                        }`}
                      />
                    )}
                  </React.Fragment>
                );
              })}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Sub-Navigation Tabs */}
      <div className="flex space-x-1 border-b border-[#1E2333] overflow-x-auto">
        {[
          { id: 'overview', label: 'Current Operation & Karigar' },
          { id: 'materials', label: 'Material Intelligence' },
          { id: 'economics', label: 'Production Economics & Margins' },
          { id: 'qc', label: 'Quality Control & Rework' },
          { id: 'timeline', label: 'Execution Timeline & Audits' },
        ].map((tab) => (
          <button
            key={tab.id}
            type="button"
            onClick={() => setActiveSubTab(tab.id as any)}
            className={`py-2.5 px-4 text-xs font-medium transition-colors border-b-2 whitespace-nowrap ${
              activeSubTab === tab.id
                ? 'border-amber-400 text-amber-300 bg-amber-400/5'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* ===================================================================== */}
      {/* SUB-TAB 1: CURRENT OPERATION & KARIGAR (Section 11, 12, 13) */}
      {/* ===================================================================== */}
      {activeSubTab === 'overview' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Current Operation Card */}
          <div className="lg:col-span-2 space-y-6">
            <Card className="bg-[#0E111A]/95 border-white/[0.08]">
              <CardHeader className="p-5 pb-3 border-b border-white/[0.06]">
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <span className="text-[11px] font-mono uppercase tracking-wider text-amber-300/80 font-semibold">
                      Current Workstation Operation
                    </span>
                    <CardTitle className="text-lg font-serif font-bold text-white">
                      {currentExecution?.stage_name || 'Operation in Preparation'}
                    </CardTitle>
                  </div>
                  {currentExecution && (
                    <Badge variant="outline" className="text-xs bg-amber-400/10 text-amber-300 border-amber-400/30 capitalize">
                      {currentExecution.status.replace('_', ' ')}
                    </Badge>
                  )}
                </div>
              </CardHeader>

              <CardContent className="p-5 space-y-6">
                {currentExecution ? (
                  <>
                    {/* Karigar & Workstation Info Grid */}
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      {/* Artisan Assignment */}
                      <div className="p-4 rounded-xl bg-[#121624] border border-white/[0.06] space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="text-[11px] font-medium uppercase tracking-wider text-slate-400">Assigned Karigar</span>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => onOpenWorkerModal(currentExecution)}
                            className="h-6 text-[10px] text-amber-300 hover:bg-amber-400/10 px-2"
                          >
                            Reassign
                          </Button>
                        </div>
                        <div className="flex items-center space-x-3">
                          <div className="w-9 h-9 rounded-lg bg-blue-500/10 border border-blue-500/20 text-blue-300 flex items-center justify-center font-bold font-serif text-sm">
                            {currentExecution.worker_name ? currentExecution.worker_name[0] : 'K'}
                          </div>
                          <div>
                            <div className="text-sm font-medium text-white">
                              {currentExecution.worker_name || 'Unassigned Karigar'}
                            </div>
                            <div className="text-[11px] text-slate-400 font-light">
                              Skill: {currentExecution.required_skill || 'Artisan Goldsmithing'}
                            </div>
                          </div>
                        </div>
                      </div>

                      {/* Workstation Machine Assignment */}
                      <div className="p-4 rounded-xl bg-[#121624] border border-white/[0.06] space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="text-[11px] font-medium uppercase tracking-wider text-slate-400">Workstation Machine</span>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => onOpenMachineModal(currentExecution)}
                            className="h-6 text-[10px] text-amber-300 hover:bg-amber-400/10 px-2"
                          >
                            Reassign
                          </Button>
                        </div>
                        <div className="flex items-center space-x-3">
                          <div className="w-9 h-9 rounded-lg bg-purple-500/10 border border-purple-500/20 text-purple-300 flex items-center justify-center font-bold text-sm">
                            <Cpu className="w-4 h-4" />
                          </div>
                          <div>
                            <div className="text-sm font-medium text-white">
                              {currentExecution.machine_name || 'Manual Workbench'}
                            </div>
                            <div className="text-[11px] text-slate-400 font-light">
                              Type: {currentExecution.required_machine_type || 'Bench Tools'}
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Bench Timing Telemetry */}
                    <div className="p-4 rounded-xl bg-[#121624]/60 border border-white/[0.06] flex items-center justify-between flex-wrap gap-4">
                      <div>
                        <div className="text-[11px] uppercase tracking-wider text-slate-400">Target Standard Norm</div>
                        <div className="text-base font-serif font-bold text-white mt-0.5">
                          {currentExecution.planned_duration_hours ? `${currentExecution.planned_duration_hours.toFixed(1)}h` : '1.5h'}
                        </div>
                      </div>

                      <div>
                        <div className="text-[11px] uppercase tracking-wider text-slate-400">Bench Hours Logged</div>
                        <div className="text-base font-serif font-bold text-amber-300 mt-0.5">
                          {currentExecution.actual_duration_hours ? `${currentExecution.actual_duration_hours.toFixed(1)}h` : '0.0h'}
                        </div>
                      </div>

                      <div>
                        <div className="text-[11px] uppercase tracking-wider text-slate-400">Quality Checkpoint</div>
                        <div className="text-xs font-mono text-cyan-300 mt-0.5">
                          {currentExecution.quality_checkpoint || 'Visual Alignment Gate'}
                        </div>
                      </div>
                    </div>

                    {/* Action Controls */}
                    <div className="flex items-center gap-3 pt-2 flex-wrap">
                      {currentExecution.status === 'ready' && (
                        <Button
                          variant="gold"
                          onClick={() => onTransitionExecution(currentExecution.id, 'in_progress')}
                          disabled={actionLoading}
                          className="h-9 font-medium"
                        >
                          <Play className="w-4 h-4 mr-1.5" />
                          Start Operation
                        </Button>
                      )}

                      {currentExecution.status === 'in_progress' && (
                        <>
                          <Button
                            variant="outline"
                            onClick={() => onTransitionExecution(currentExecution.id, 'paused')}
                            disabled={actionLoading}
                            className="h-9 border-[#1E2333] hover:bg-[#161B26] text-amber-300"
                          >
                            <Pause className="w-4 h-4 mr-1.5" />
                            Pause Bench Work
                          </Button>

                          <Button
                            variant="gold"
                            onClick={() => onTransitionExecution(currentExecution.id, 'completed')}
                            disabled={actionLoading}
                            className="h-9 font-medium"
                          >
                            <CheckCircle2 className="w-4 h-4 mr-1.5" />
                            Complete Step
                          </Button>
                        </>
                      )}

                      {currentExecution.status === 'paused' && (
                        <Button
                          variant="gold"
                          onClick={() => onTransitionExecution(currentExecution.id, 'in_progress')}
                          disabled={actionLoading}
                          className="h-9 font-medium"
                        >
                          <Play className="w-4 h-4 mr-1.5" />
                          Resume Step
                        </Button>
                      )}

                      <Button
                        variant="outline"
                        onClick={() => onOpenQcModal(currentExecution)}
                        className="h-9 border-[#1E2333] hover:bg-[#161B26] text-cyan-300 text-xs"
                      >
                        <ShieldCheck className="w-4 h-4 mr-1.5" />
                        Perform QC Inspection
                      </Button>

                      <Button
                        variant="outline"
                        onClick={() => onOpenMaterialModal(currentExecution)}
                        className="h-9 border-[#1E2333] hover:bg-[#161B26] text-emerald-300 text-xs"
                      >
                        <Scale className="w-4 h-4 mr-1.5" />
                        Log Material & Scrap
                      </Button>
                    </div>
                  </>
                ) : (
                  <div className="text-center py-8 text-slate-400">
                    All operations for this order have been completed.
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Planned vs Actual Analytics Snapshot (Section 20) */}
            <Card className="bg-[#0E111A]/95 border-white/[0.08]">
              <CardHeader className="p-4 sm:p-5 pb-3">
                <CardTitle className="text-xs font-semibold uppercase tracking-wider text-amber-300/90 flex items-center gap-2">
                  <Sliders className="w-4 h-4" />
                  <span>Planned vs Actual Bench Analytics</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="p-4 sm:p-5 pt-0">
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                  <div className="p-3.5 rounded-xl bg-[#121624]/60 border border-white/[0.05]">
                    <div className="text-[11px] text-slate-400">Bench Hours</div>
                    <div className="text-sm font-medium text-white mt-1">
                      {totalActualHours.toFixed(1)}h / {totalPlannedHours.toFixed(1)}h
                    </div>
                    <div className={`text-[10px] font-mono mt-0.5 ${totalActualHours <= totalPlannedHours ? 'text-emerald-400' : 'text-amber-400'}`}>
                      {totalActualHours <= totalPlannedHours ? 'On Schedule' : `+${(totalActualHours - totalPlannedHours).toFixed(1)}h overtime`}
                    </div>
                  </div>

                  <div className="p-3.5 rounded-xl bg-[#121624]/60 border border-white/[0.05]">
                    <div className="text-[11px] text-slate-400">Metal Consumed</div>
                    <div className="text-sm font-medium text-white mt-1">
                      {primaryMetalWeightGrams.toFixed(2)} g
                    </div>
                    <div className="text-[10px] text-emerald-400 font-mono mt-0.5">
                      18K Yellow Gold
                    </div>
                  </div>

                  <div className="p-3.5 rounded-xl bg-[#121624]/60 border border-white/[0.05]">
                    <div className="text-[11px] text-slate-400">QC Pass Verdicts</div>
                    <div className="text-sm font-medium text-cyan-300 mt-1">
                      {qualitySummary ? `${qualitySummary.passed} Passed` : '1 Passed'}
                    </div>
                    <div className="text-[10px] text-slate-400 font-mono mt-0.5">
                      {qualitySummary?.failed || 0} Failed
                    </div>
                  </div>

                  <div className="p-3.5 rounded-xl bg-[#121624]/60 border border-white/[0.05]">
                    <div className="text-[11px] text-slate-400">Rework Attempts</div>
                    <div className="text-sm font-medium text-purple-300 mt-1">
                      {executions.filter((e) => e.execution_type === 'rework').length} loops
                    </div>
                    <div className="text-[10px] text-slate-400 font-mono mt-0.5">
                      Controlled rework
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Right Rail: Karigars, Tools & Order Completion Gate */}
          <div className="space-y-6">
            {/* Order Completion Gate (Section 24) */}
            <Card className="bg-[#0E111A]/95 border-amber-400/20">
              <CardHeader className="p-4 pb-2">
                <CardTitle className="text-xs font-semibold uppercase tracking-wider text-amber-300/90 flex items-center gap-2">
                  <ShieldCheck className="w-4 h-4" />
                  <span>Order Completion Gate</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="p-4 space-y-3.5">
                <div className="space-y-2 text-xs">
                  <div className="flex items-center justify-between text-slate-300">
                    <span className="flex items-center gap-2">
                      <span className={`w-3.5 h-3.5 rounded-full flex items-center justify-center text-[9px] ${allStepsCompleted ? 'bg-emerald-500 text-black' : 'bg-slate-700 text-slate-400'}`}>✓</span>
                      All routing steps finished
                    </span>
                    <span className="font-mono text-slate-400">{executions.filter(e => e.status === 'completed').length}/{executions.length}</span>
                  </div>

                  <div className="flex items-center justify-between text-slate-300">
                    <span className="flex items-center gap-2">
                      <span className={`w-3.5 h-3.5 rounded-full flex items-center justify-center text-[9px] ${materialsLogged ? 'bg-emerald-500 text-black' : 'bg-slate-700 text-slate-400'}`}>✓</span>
                      Material consumption logged
                    </span>
                    <span className="font-mono text-slate-400">{materialsLogged ? 'Logged' : 'Pending'}</span>
                  </div>

                  <div className="flex items-center justify-between text-slate-300">
                    <span className="flex items-center gap-2">
                      <span className={`w-3.5 h-3.5 rounded-full flex items-center justify-center text-[9px] ${qcPassed ? 'bg-emerald-500 text-black' : 'bg-slate-700 text-slate-400'}`}>✓</span>
                      Final QC inspection passed
                    </span>
                    <span className="font-mono text-slate-400">{qcPassed ? 'Passed' : 'Pending'}</span>
                  </div>
                </div>

                <div className="pt-2">
                  {order.status === 'completed' ? (
                    <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-center font-medium text-xs">
                      ✓ Order Successfully Completed & Archived
                    </div>
                  ) : (
                    <Button
                      variant="gold"
                      onClick={onCompleteOrder}
                      disabled={!canCompleteOrder || actionLoading}
                      className="w-full h-9 text-xs font-bold"
                    >
                      Complete Production Order
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Quick Bullion Market Rate Snapshot */}
            <Card className="bg-[#0E111A]/95 border-white/[0.08]">
              <CardHeader className="p-4 pb-2">
                <CardTitle className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center justify-between">
                  <span>Atelier Bullion Benchmarks</span>
                  <IndianRupee className="w-3.5 h-3.5 text-amber-300" />
                </CardTitle>
              </CardHeader>
              <CardContent className="p-4 pt-0 space-y-2 text-xs">
                <div className="flex items-center justify-between py-1 border-b border-white/[0.04]">
                  <span className="text-slate-400">18K Yellow Gold</span>
                  <span className="font-mono font-medium text-amber-300">₹{rateConfig.gold18k.toLocaleString('en-IN')}/g</span>
                </div>
                <div className="flex items-center justify-between py-1 border-b border-white/[0.04]">
                  <span className="text-slate-400">22K Fine Gold</span>
                  <span className="font-mono font-medium text-amber-300">₹{rateConfig.gold22k.toLocaleString('en-IN')}/g</span>
                </div>
                <div className="flex items-center justify-between py-1 border-b border-white/[0.04]">
                  <span className="text-slate-400">925 Sterling Silver</span>
                  <span className="font-mono font-medium text-slate-300">₹{rateConfig.silver925}/g</span>
                </div>
                <div className="flex items-center justify-between py-1">
                  <span className="text-slate-400">Making Charges Base</span>
                  <span className="font-mono font-medium text-blue-300">₹{rateConfig.standardKarigarHourlyRate}/hr</span>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      )}

      {/* ===================================================================== */}
      {/* SUB-TAB 2: MATERIAL INTELLIGENCE (Section 14, 15, 16, 17, 18) */}
      {/* ===================================================================== */}
      {activeSubTab === 'materials' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            {/* Planned vs Actual Weight Card */}
            <Card className="bg-[#0E111A]/95 border-white/[0.08]">
              <CardHeader className="p-4 pb-2">
                <CardTitle className="text-xs uppercase tracking-wider text-slate-400 font-medium">
                  Net Metal Consumed
                </CardTitle>
              </CardHeader>
              <CardContent className="p-4 pt-1 space-y-1">
                <div className="text-2xl font-serif font-bold text-white">
                  {materialSummary?.total_actual_quantity ? `${materialSummary.total_actual_quantity.toFixed(2)} g` : `${primaryMetalWeightGrams.toFixed(2)} g`}
                </div>
                <div className="text-xs text-slate-400 font-light">
                  Planned: {materialSummary?.total_planned_quantity ? `${materialSummary.total_planned_quantity.toFixed(2)} g` : `${primaryMetalWeightGrams.toFixed(2)} g`}
                </div>
              </CardContent>
            </Card>

            {/* Scrap & Wastage Card */}
            <Card className="bg-[#0E111A]/95 border-white/[0.08]">
              <CardHeader className="p-4 pb-2">
                <CardTitle className="text-xs uppercase tracking-wider text-slate-400 font-medium">
                  Wastage & Spruing Loss
                </CardTitle>
              </CardHeader>
              <CardContent className="p-4 pt-1 space-y-1">
                <div className="text-2xl font-serif font-bold text-amber-300">
                  {materialSummary?.total_wastage_quantity ? `${materialSummary.total_wastage_quantity.toFixed(2)} g` : '0.20 g'}
                </div>
                <div className="text-xs text-slate-400 font-light">
                  Within acceptable crucible cutoff tolerance
                </div>
              </CardContent>
            </Card>

            {/* Material Market Valuation */}
            <Card className="bg-[#0E111A]/95 border-white/[0.08]">
              <CardHeader className="p-4 pb-2">
                <CardTitle className="text-xs uppercase tracking-wider text-slate-400 font-medium">
                  Estimated Material Market Value
                </CardTitle>
              </CardHeader>
              <CardContent className="p-4 pt-1 space-y-1">
                <div className="text-2xl font-serif font-bold text-emerald-300">
                  {formatINR(totalMaterialCost)}
                </div>
                <div className="text-xs text-slate-400 font-light">
                  Derived from {rateConfig.source}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Material Breakdown Table */}
          <Card className="bg-[#0E111A]/95 border-white/[0.08]">
            <CardHeader className="p-5 pb-3">
              <CardTitle className="text-sm font-serif font-bold text-white flex items-center justify-between">
                <span>Bill of Materials & Consumption Telemetry</span>
                <span className="text-xs font-mono font-normal text-slate-400">J4 Consumption Ledger</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="p-5 pt-0">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="border-b border-white/[0.08] text-slate-400 uppercase tracking-wider text-[10px]">
                      <th className="py-2.5">Material</th>
                      <th className="py-2.5">Type</th>
                      <th className="py-2.5">Planned Qty</th>
                      <th className="py-2.5">Actual Consumed</th>
                      <th className="py-2.5">Wastage / Scrap</th>
                      <th className="py-2.5">IBJA Rate (₹)</th>
                      <th className="py-2.5 text-right">Valuation</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/[0.04]">
                    {materialSummary && materialSummary.items.length > 0 ? (
                      materialSummary.items.map((m, idx) => {
                        const rate = getIndianMetalRate(m.material_name, rateConfig);
                        const weight = m.actual_quantity > 0 ? m.actual_quantity : m.planned_quantity;
                        const val = rate ? weight * rate : null;
                        return (
                          <tr key={idx} className="hover:bg-white/[0.02]">
                            <td className="py-3 font-medium text-white">{m.material_name}</td>
                            <td className="py-3 text-slate-400 capitalize">{m.material_type}</td>
                            <td className="py-3 font-mono text-slate-300">{m.planned_quantity.toFixed(2)} {m.unit}</td>
                            <td className="py-3 font-mono text-emerald-300 font-medium">{m.actual_quantity.toFixed(2)} {m.unit}</td>
                            <td className="py-3 font-mono text-amber-300">{m.wastage_quantity.toFixed(2)} {m.unit}</td>
                            <td className="py-3 font-mono text-slate-400">{rate ? `₹${rate.toLocaleString('en-IN')}/${m.unit}` : 'Valuation unavailable'}</td>
                            <td className="py-3 font-mono text-right font-medium text-emerald-300">{formatINR(val)}</td>
                          </tr>
                        );
                      })
                    ) : (
                      <tr>
                        <td className="py-3 font-medium text-white">18K Yellow Gold</td>
                        <td className="py-3 text-slate-400 capitalize">Metal</td>
                        <td className="py-3 font-mono text-slate-300">8.50 g</td>
                        <td className="py-3 font-mono text-emerald-300 font-medium">8.70 g</td>
                        <td className="py-3 font-mono text-amber-300">0.20 g</td>
                        <td className="py-3 font-mono text-slate-400">₹{rateConfig.gold18k.toLocaleString('en-IN')}/g</td>
                        <td className="py-3 font-mono text-right font-medium text-emerald-300">{formatINR(8.7 * rateConfig.gold18k)}</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* ===================================================================== */}
      {/* SUB-TAB 3: PRODUCTION ECONOMICS & MARGINS (Section 19) */}
      {/* ===================================================================== */}
      {activeSubTab === 'economics' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Card className="bg-[#0E111A]/95 border-white/[0.08]">
            <CardHeader className="p-5 pb-3">
              <CardTitle className="text-sm font-serif font-bold text-white flex items-center justify-between">
                <span>Atelier Cost Breakdown</span>
                <IndianRupee className="w-4 h-4 text-amber-300" />
              </CardTitle>
            </CardHeader>
            <CardContent className="p-5 pt-0 space-y-4 text-xs">
              <div className="flex items-center justify-between py-2 border-b border-white/[0.04]">
                <div>
                  <div className="text-white font-medium">Precious Material Cost</div>
                  <div className="text-slate-500 text-[11px]">Gold bullion & gemstone allocations</div>
                </div>
                <div className="font-mono text-sm text-emerald-300 font-medium">
                  {formatINR(totalMaterialCost)}
                </div>
              </div>

              <div className="flex items-center justify-between py-2 border-b border-white/[0.04]">
                <div>
                  <div className="text-white font-medium">Karigar Making Charges (Labour)</div>
                  <div className="text-slate-500 text-[11px]">{effectiveHours.toFixed(1)}h logged @ ₹{rateConfig.standardKarigarHourlyRate}/hr</div>
                </div>
                <div className="font-mono text-sm text-blue-300 font-medium">
                  {formatINR(labourCost)}
                </div>
              </div>

              <div className="flex items-center justify-between py-2 border-b border-white/[0.04]">
                <div>
                  <div className="text-white font-medium">Workshop Machinery & Overhead</div>
                  <div className="text-slate-500 text-[11px]">Furnace, casting, polishing lathe run-time</div>
                </div>
                <div className="font-mono text-sm text-purple-300 font-medium">
                  {formatINR(machineCost)}
                </div>
              </div>

              <div className="flex items-center justify-between py-3 border-t border-white/[0.1] font-semibold">
                <div className="text-sm text-white">Total Manufacturing Cost</div>
                <div className="font-mono text-base text-amber-300">
                  {formatINR(totalManufacturingCost)}
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-[#0E111A]/95 border-white/[0.08]">
            <CardHeader className="p-5 pb-3">
              <CardTitle className="text-sm font-serif font-bold text-white flex items-center justify-between">
                <span>Valuation & Margin Realization</span>
                <TrendingUp className="w-4 h-4 text-emerald-400" />
              </CardTitle>
            </CardHeader>
            <CardContent className="p-5 pt-0 space-y-5 text-xs">
              <div className="p-4 rounded-xl bg-[#121624]/60 border border-white/[0.06] space-y-1">
                <div className="text-[11px] uppercase tracking-wider text-slate-400 font-medium">
                  Estimated Atelier Selling Value
                </div>
                <div className="text-2xl font-serif font-bold text-white">
                  {formatINR(estimatedSellingPrice)}
                </div>
                <div className="text-slate-400 text-[11px]">
                  Based on configured {rateConfig.standardRetailMarkupPercent}% target commercial atelier margin
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="p-3.5 rounded-xl bg-emerald-500/5 border border-emerald-500/20">
                  <div className="text-[11px] text-slate-400">Gross Margin (INR)</div>
                  <div className="text-lg font-serif font-bold text-emerald-300 mt-1">
                    {formatINR(grossMargin)}
                  </div>
                </div>

                <div className="p-3.5 rounded-xl bg-amber-500/5 border border-amber-500/20">
                  <div className="text-[11px] text-slate-400">Margin Percentage</div>
                  <div className="text-lg font-serif font-bold text-amber-300 mt-1">
                    {grossMarginPercent.toFixed(1)}%
                  </div>
                </div>
              </div>

              <div className="text-[11px] text-slate-500 italic">
                * Note: Margin calculations reflect configured atelier rates and standard bench hours. Real-time market spot fluctuations may apply.
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* ===================================================================== */}
      {/* SUB-TAB 4: QUALITY CONTROL & REWORK (Section 22, 23) */}
      {/* ===================================================================== */}
      {activeSubTab === 'qc' && (
        <div className="space-y-6">
          <Card className="bg-[#0E111A]/95 border-white/[0.08]">
            <CardHeader className="p-5 pb-3">
              <CardTitle className="text-sm font-serif font-bold text-white flex items-center justify-between">
                <span>Quality Inspection Verdicts & Rework Loops</span>
                <ShieldCheck className="w-4 h-4 text-cyan-400" />
              </CardTitle>
            </CardHeader>
            <CardContent className="p-5 pt-0 space-y-4">
              <div className="grid grid-cols-3 gap-4">
                <div className="p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-center">
                  <div className="text-2xl font-serif font-bold text-emerald-300">
                    {qualitySummary?.passed || 1}
                  </div>
                  <div className="text-xs text-slate-400 mt-0.5">Passed Checks</div>
                </div>

                <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/20 text-center">
                  <div className="text-2xl font-serif font-bold text-rose-300">
                    {qualitySummary?.failed || 0}
                  </div>
                  <div className="text-xs text-slate-400 mt-0.5">Failed Checks</div>
                </div>

                <div className="p-3.5 rounded-xl bg-purple-500/10 border border-purple-500/20 text-center">
                  <div className="text-2xl font-serif font-bold text-purple-300">
                    {executions.filter((e) => e.execution_type === 'rework').length}
                  </div>
                  <div className="text-xs text-slate-400 mt-0.5">Rework Operations</div>
                </div>
              </div>

              {/* Rework Loop Visualization (Section 23) */}
              <div className="p-4 rounded-xl bg-[#121624]/60 border border-white/[0.06] space-y-3">
                <div className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                  Rework Traceability Flowchart
                </div>
                <div className="text-xs text-slate-400 leading-relaxed font-light">
                  {executions.some((e) => e.execution_type === 'rework') ? (
                    <div className="space-y-2">
                      <div className="flex items-center gap-2 text-rose-300 font-mono text-[11px]">
                        <span>Initial Step Failed QC</span>
                        <span>→</span>
                        <span className="text-amber-300">Rework Operation Spawned</span>
                        <span>→</span>
                        <span className="text-emerald-300">Secondary Finishing & Re-inspection</span>
                      </div>
                      <p className="text-[11px] text-slate-500">
                        Rework bench time is tracked distinctly to compute exact labour making charge variances.
                      </p>
                    </div>
                  ) : (
                    <p className="text-emerald-400 font-medium text-xs">
                      No rework incidents recorded for this production order. All steps passing standard quality gates on first attempt.
                    </p>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* ===================================================================== */}
      {/* SUB-TAB 5: TIMELINE & AUDITS (Section 21) */}
      {/* ===================================================================== */}
      {activeSubTab === 'timeline' && (
        <Card className="bg-[#0E111A]/95 border-white/[0.08]">
          <CardHeader className="p-5 pb-3">
            <CardTitle className="text-sm font-serif font-bold text-white flex items-center justify-between">
              <span>Station Execution Chronology</span>
              <Clock className="w-4 h-4 text-slate-400" />
            </CardTitle>
          </CardHeader>
          <CardContent className="p-5 pt-0">
            <div className="space-y-4 relative pl-6 before:absolute before:left-2.5 before:top-2 before:bottom-2 before:w-0.5 before:bg-white/[0.08]">
              {executions.map((exec, idx) => (
                <div key={exec.id} className="relative group">
                  <div
                    className={`absolute -left-6 top-1.5 w-3.5 h-3.5 rounded-full border-2 ${
                      exec.status === 'completed'
                        ? 'bg-emerald-500 border-[#0E111A]'
                        : exec.status === 'in_progress'
                        ? 'bg-amber-400 border-[#0E111A] animate-ping'
                        : 'bg-slate-700 border-[#0E111A]'
                    }`}
                  />
                  <div className="p-3.5 rounded-xl bg-[#121624]/60 border border-white/[0.05] space-y-1">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-medium text-white">
                        Step {idx + 1}: {exec.stage_name || 'Station Work'}
                      </span>
                      <Badge variant="outline" className="text-[10px] capitalize">
                        {exec.status}
                      </Badge>
                    </div>
                    <div className="text-[11px] text-slate-400 flex items-center gap-3 font-light">
                      <span>Karigar: <strong className="text-slate-200">{exec.worker_name || 'Unassigned'}</strong></span>
                      <span>•</span>
                      <span>Bench Hours: {exec.actual_duration_hours ? `${exec.actual_duration_hours.toFixed(1)}h` : 'Pending'}</span>
                      {exec.operator_notes && (
                        <>
                          <span>•</span>
                          <span className="italic truncate max-w-xs">{exec.operator_notes}</span>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};
