import React, { useEffect, useState, useCallback } from 'react';
import {
  Factory,
  RefreshCw,
  AlertTriangle,
  ArrowLeft,
} from 'lucide-react';
import { Button } from '../../ui/button';
import { ProductionOrderHeader } from './ProductionOrderHeader';
import { CurrentOperationCard } from './CurrentOperationCard';
import { OperationTimeline } from './OperationTimeline';
import { WorkerAssignmentDialog } from './WorkerAssignmentDialog';
import { MachineAssignmentDialog } from './MachineAssignmentDialog';
import { QualityCheckDialog } from './QualityCheckDialog';
import { MaterialConsumptionDialog } from './MaterialConsumptionDialog';
import { MaterialSummaryCard } from './MaterialSummaryCard';
import { ProductionProgressCard } from './ProductionProgressCard';

import { productionService } from '../../../services/api/productionService';
import { productionExecutionService } from '../../../services/api/productionExecutionService';
import { ProductionOrder, Worker, Machine } from '../../../types/production';
import {
  OperationExecution,
  OrderMaterialSummaryResponse,
  OrderQualitySummaryResponse,
  QualityCheckCreate,
  MaterialConsumptionCreate,
} from '../../../types/execution';

interface ShopFloorPageProps {
  orderId: string;
  onBackToOrders?: () => void;
}

export const ShopFloorPage: React.FC<ShopFloorPageProps> = ({
  orderId,
  onBackToOrders,
}) => {
  // Master State
  const [order, setOrder] = useState<ProductionOrder | null>(null);
  const [executions, setExecutions] = useState<OperationExecution[]>([]);
  const [currentExecution, setCurrentExecution] = useState<OperationExecution | null>(null);
  const [workers, setWorkers] = useState<Worker[]>([]);
  const [machines, setMachines] = useState<Machine[]>([]);
  const [materialSummary, setMaterialSummary] = useState<OrderMaterialSummaryResponse | null>(null);
  const [qualitySummary, setQualitySummary] = useState<OrderQualitySummaryResponse | null>(null);

  // Loading & Feedback
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [actionLoading, setActionLoading] = useState<boolean>(false);
  const [feedback, setFeedback] = useState<{ message: string; type: 'success' | 'error' } | null>(null);

  // Dialog Controls
  const [isWorkerModalOpen, setIsWorkerModalOpen] = useState<boolean>(false);
  const [isMachineModalOpen, setIsMachineModalOpen] = useState<boolean>(false);
  const [isQcModalOpen, setIsQcModalOpen] = useState<boolean>(false);
  const [isMaterialModalOpen, setIsMaterialModalOpen] = useState<boolean>(false);

  const showFeedback = (message: string, type: 'success' | 'error' = 'success') => {
    setFeedback({ message, type });
    setTimeout(() => setFeedback(null), 4000);
  };

  // Master Data Loader
  const loadStationData = useCallback(async (isInitial = false) => {
    if (isInitial) setLoading(true);
    else setRefreshing(true);

    try {
      // 1. Fetch Order Details
      const orderData = await productionService.getOrder(orderId);
      setOrder(orderData);

      // 2. Fetch Executions
      let executionData = await productionExecutionService.getOrderExecutions(orderId);

      // If empty and order is spec-backed, attempt initialization
      if (executionData.items.length === 0 && orderData.specification_id) {
        try {
          await productionExecutionService.initializeOrderExecutions(orderId);
          executionData = await productionExecutionService.getOrderExecutions(orderId);
        } catch {
          // Keep executionData empty if initialization fails or not supported
        }
      }
      setExecutions(executionData.items);

      // 3. Set Current Execution
      if (executionData.items.length > 0) {
        setCurrentExecution((prev) => {
          if (prev) {
            const found = executionData.items.find((x) => x.id === prev.id);
            if (found) return found;
          }
          // Prioritize active, ready, or first uncompleted step
          const active = executionData.items.find((x) => x.status === 'in_progress' || x.status === 'paused');
          if (active) return active;
          const ready = executionData.items.find((x) => x.status === 'ready');
          if (ready) return ready;
          const uncompleted = executionData.items.find((x) => x.status !== 'completed');
          if (uncompleted) return uncompleted;
          return executionData.items[0];
        });
      }

      // 4. Fetch Resources (Workers & Machines)
      const [workersData, machinesData] = await Promise.all([
        productionService.getWorkers(),
        productionService.getMachines(),
      ]);
      setWorkers(workersData.items);
      setMachines(machinesData.items);

      // 5. Fetch Material & QC Summaries
      try {
        const [matSum, qcSum] = await Promise.all([
          productionExecutionService.getOrderMaterialSummary(orderId),
          productionExecutionService.getOrderQualitySummary(orderId),
        ]);
        setMaterialSummary(matSum);
        setQualitySummary(qcSum);
      } catch {
        // Summaries are non-fatal
      }
    } catch (err: unknown) {
      showFeedback(err instanceof Error ? err.message : 'Failed to load shop floor data', 'error');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [orderId]);

  useEffect(() => {
    loadStationData(true);
  }, [loadStationData]);

  // Transition Handlers
  const handleTransition = async (targetStatus: 'in_progress' | 'paused' | 'completed' | 'blocked' | 'ready') => {
    if (!currentExecution) return;
    setActionLoading(true);
    try {
      const updated = await productionExecutionService.transitionExecution(currentExecution.id, {
        target_status: targetStatus,
      });
      setCurrentExecution(updated);
      showFeedback(`Operation status updated to ${targetStatus.replace('_', ' ').toUpperCase()}`);
      await loadStationData(false);
    } catch (err: unknown) {
      showFeedback(err instanceof Error ? err.message : 'State transition rejected by server', 'error');
    } finally {
      setActionLoading(false);
    }
  };

  // Resource Assignment Handlers
  const handleAssignWorker = async (workerId: string) => {
    if (!currentExecution) return;
    try {
      const updated = await productionExecutionService.assignWorker(currentExecution.id, workerId);
      setCurrentExecution(updated);
      showFeedback('Artisan assigned to operation.');
      await loadStationData(false);
    } catch (err: unknown) {
      throw err;
    }
  };

  const handleAssignMachine = async (machineId: string) => {
    if (!currentExecution) return;
    try {
      const updated = await productionExecutionService.assignMachine(currentExecution.id, machineId);
      setCurrentExecution(updated);
      showFeedback('Equipment assigned to operation.');
      await loadStationData(false);
    } catch (err: unknown) {
      throw err;
    }
  };

  // QC Submission Handler
  const handleRecordQc = async (payload: QualityCheckCreate) => {
    if (!currentExecution) return;
    try {
      await productionExecutionService.recordQualityCheck(currentExecution.id, payload);
      showFeedback(`QC inspection logged: ${payload.result}`);
      await loadStationData(false);
    } catch (err: unknown) {
      throw err;
    }
  };

  // Rework Creation Handler
  const handleCreateRework = async () => {
    if (!currentExecution) return;
    setActionLoading(true);
    try {
      const reworkExec = await productionExecutionService.createReworkExecution(currentExecution.id);
      setCurrentExecution(reworkExec);
      showFeedback(`Rework execution #${reworkExec.attempt_number || 2} authorized.`);
      await loadStationData(false);
    } catch (err: unknown) {
      showFeedback(err instanceof Error ? err.message : 'Failed to authorize rework', 'error');
    } finally {
      setActionLoading(false);
    }
  };

  // Material Consumption Handler
  const handleRecordMaterial = async (payload: MaterialConsumptionCreate) => {
    if (!currentExecution) return;
    try {
      await productionExecutionService.recordMaterialConsumption(currentExecution.id, payload);
      showFeedback('Material and wastage record logged.');
      await loadStationData(false);
    } catch (err: unknown) {
      throw err;
    }
  };

  // Final Order Completion
  const handleFinalizeOrder = async () => {
    setActionLoading(true);
    try {
      await productionExecutionService.completeOrder(orderId);
      showFeedback('Production Order marked as COMPLETED! All quality gates passed.');
      await loadStationData(false);
    } catch (err: unknown) {
      showFeedback(err instanceof Error ? err.message : 'Cannot finalize order: Unmet quality gate', 'error');
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="py-24 text-center text-slate-400 flex flex-col items-center justify-center">
        <RefreshCw className="w-9 h-9 animate-spin text-amber-400 mb-4" />
        <h2 className="text-base font-serif font-bold text-white">Opening Workstation Terminal...</h2>
        <p className="text-xs text-slate-500 mt-1">Connecting to manufacturing execution layer</p>
      </div>
    );
  }

  if (!order) {
    return (
      <div className="py-20 text-center bg-[#0E111A]/60 rounded-2xl border border-white/10 p-8">
        <AlertTriangle className="w-12 h-12 text-rose-400 mx-auto mb-3" />
        <h3 className="text-base font-bold text-white">Order Not Found</h3>
        <p className="text-sm text-slate-400 mt-1">
          The requested production order does not exist or access is restricted.
        </p>
        {onBackToOrders && (
          <Button variant="outline" size="sm" onClick={onBackToOrders} className="mt-4">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Return to Orders
          </Button>
        )}
      </div>
    );
  }

  const completedCount = executions.filter((x) => x.status === 'completed').length;
  const canComplete =
    completedCount === executions.length &&
    executions.length > 0 &&
    (qualitySummary?.quality_gate_passed ?? false);

  return (
    <div className="space-y-6 animate-fade-in pb-12">
      {/* Toast Feedback */}
      {feedback && (
        <div
          className={`p-3.5 rounded-xl border text-xs font-medium flex items-center justify-between shadow-xl backdrop-blur-md ${
            feedback.type === 'success'
              ? 'bg-emerald-500/15 border-emerald-500/30 text-emerald-200'
              : 'bg-rose-500/15 border-rose-500/30 text-rose-200'
          }`}
        >
          <span>{feedback.message}</span>
          <button onClick={() => setFeedback(null)} className="ml-2 opacity-70 hover:opacity-100">
            &times;
          </button>
        </div>
      )}

      {/* 1. Station Order Header */}
      <ProductionOrderHeader
        order={order}
        currentStepNumber={currentExecution?.step_number}
        totalSteps={executions.length}
        qualityGatePassed={qualitySummary?.quality_gate_passed}
        onBack={onBackToOrders}
        onRefresh={() => loadStationData(false)}
        isRefreshing={refreshing}
      />

      {/* 2. Main Workstation Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Current Active Operation (2 cols) */}
        <div className="lg:col-span-2 space-y-6">
          {currentExecution ? (
            <CurrentOperationCard
              execution={currentExecution}
              onAssignWorker={() => setIsWorkerModalOpen(true)}
              onAssignMachine={() => setIsMachineModalOpen(true)}
              onStart={() => handleTransition('in_progress')}
              onPause={() => handleTransition('paused')}
              onResume={() => handleTransition('in_progress')}
              onComplete={() => handleTransition('completed')}
              onBlock={() => handleTransition('blocked')}
              onMakeReady={() => handleTransition('ready')}
              onOpenQc={() => setIsQcModalOpen(true)}
              onCreateRework={handleCreateRework}
              onOpenMaterialModal={() => setIsMaterialModalOpen(true)}
              actionLoading={actionLoading}
            />
          ) : (
            <div className="rounded-2xl border border-white/[0.08] bg-[#0E111A]/90 p-8 text-center">
              <Factory className="w-10 h-10 text-slate-600 mx-auto mb-3" />
              <h3 className="text-base font-bold text-white">No Operation Selected</h3>
              <p className="text-xs text-slate-400 mt-1">
                Select an operation from the routing sequence to view execution controls.
              </p>
            </div>
          )}

          {/* Progress & Quality Gate Card */}
          <ProductionProgressCard
            totalOperations={executions.length}
            completedOperations={completedCount}
            qualitySummary={qualitySummary}
            onCompleteOrder={handleFinalizeOrder}
            canCompleteOrder={canComplete}
            completingOrder={actionLoading}
          />
        </div>

        {/* Right Column: Routing Timeline & Material Summary (1 col) */}
        <div className="space-y-6">
          <OperationTimeline
            executions={executions}
            currentExecutionId={currentExecution?.id || null}
            onSelectExecution={(exec) => setCurrentExecution(exec)}
          />

          <MaterialSummaryCard summary={materialSummary} />
        </div>
      </div>

      {/* Dialog Modals */}
      <WorkerAssignmentDialog
        isOpen={isWorkerModalOpen}
        onClose={() => setIsWorkerModalOpen(false)}
        workers={workers}
        currentWorkerId={currentExecution?.worker_id || null}
        requiredSkill={currentExecution?.required_skill}
        onAssign={handleAssignWorker}
      />

      <MachineAssignmentDialog
        isOpen={isMachineModalOpen}
        onClose={() => setIsMachineModalOpen(false)}
        machines={machines}
        currentMachineId={currentExecution?.machine_id || null}
        requiredMachineType={currentExecution?.required_machine_type}
        onAssign={handleAssignMachine}
      />

      <QualityCheckDialog
        isOpen={isQcModalOpen}
        onClose={() => setIsQcModalOpen(false)}
        stepNumber={currentExecution?.step_number}
        stageName={currentExecution?.stage_name}
        qualityCheckpoint={currentExecution?.quality_checkpoint}
        onSubmit={handleRecordQc}
      />

      <MaterialConsumptionDialog
        isOpen={isMaterialModalOpen}
        onClose={() => setIsMaterialModalOpen(false)}
        stepNumber={currentExecution?.step_number}
        stageName={currentExecution?.stage_name}
        onSubmit={handleRecordMaterial}
      />
    </div>
  );
};
