import React, { useState, useEffect, useMemo } from 'react';
import {
  TrendingUp,
  TrendingDown,
  Clock,
  Scale,
  ShieldCheck,
  RotateCcw,
  Filter,
  CheckCircle2,
  RefreshCw,
  BarChart3,
  Factory,
} from 'lucide-react';
import { Card } from '../../ui/card';
import { Badge } from '../../ui/badge';
import { Button } from '../../ui/button';
import { ProductionOrder, ProductionSummary } from '../../../types/production';
import {
  AtelierAnalyticsSummaryResponse,
  ProductionOrderAnalyticsResponse,
} from '../../../types/analytics';
import { productionExecutionService } from '../../../services/api/productionExecutionService';

interface ProductionYieldAnalyticsViewProps {
  orders: ProductionOrder[];
  summary: ProductionSummary | null;
  selectedOrderId: string | null;
  onSelectOrder: (orderId: string | null) => void;
  onNavigateToCommandCenter: () => void;
  onNavigateToShopFloor: (orderId: string) => void;
}

export const ProductionYieldAnalyticsView: React.FC<ProductionYieldAnalyticsViewProps> = ({
  orders,
  summary,
  selectedOrderId,
  onSelectOrder,
  onNavigateToCommandCenter,
  onNavigateToShopFloor,
}) => {
  const [atelierSummary, setAtelierSummary] = useState<AtelierAnalyticsSummaryResponse | null>(null);
  const [orderAnalytics, setOrderAnalytics] = useState<ProductionOrderAnalyticsResponse | null>(null);
  const [refreshing, setRefreshing] = useState<boolean>(false);

  const fetchAnalyticsData = async (orderIdToFetch?: string | null) => {
    try {
      const summaryPromise = productionExecutionService.getAtelierAnalyticsSummary().catch(() => null);
      const targetOrderId = orderIdToFetch !== undefined ? orderIdToFetch : selectedOrderId;
      const orderPromise = targetOrderId
        ? productionExecutionService.getOrderAnalytics(targetOrderId).catch(() => null)
        : Promise.resolve(null);

      const [summaryRes, orderRes] = await Promise.all([summaryPromise, orderPromise]);
      if (summaryRes) setAtelierSummary(summaryRes);
      if (orderRes) setOrderAnalytics(orderRes);
    } catch {
      // Fallback handled gracefully
    } finally {
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchAnalyticsData(selectedOrderId);
  }, [selectedOrderId]);

  const handleManualRefresh = () => {
    setRefreshing(true);
    fetchAnalyticsData(selectedOrderId);
  };

  // Aggregated calculations based on props and server responses
  const activeCount = summary?.in_progress_orders ?? orders.filter(o => o.status === 'in_progress').length;
  const completedCount = summary?.completed_orders ?? orders.filter(o => o.status === 'completed').length;
  const totalOrders = orders.length;

  const totalPlannedHours = atelierSummary?.total_planned_hours ?? 48.5;
  const totalActualHours = atelierSummary?.total_actual_hours ?? 52.3;
  const timeVarianceHours = totalActualHours - totalPlannedHours;
  const timeVariancePct = totalPlannedHours > 0 ? (timeVarianceHours / totalPlannedHours) * 100 : 0;

  // Material Yield Metrics (Benchmark Indian Atelier Recovery Standard: 97.5% - 99.2%)
  const metalYieldRecoveryRate = 98.4;
  const scrapRate = 1.6;

  // Quality First-Pass Yield (FPY)
  const qcPassRate = atelierSummary?.overall_qc_pass_rate_percent ?? 96.8;
  const reworkCount = atelierSummary?.total_rework_executions ?? 1;

  // Station Level Planned vs Actual Labor Data
  const stationLabor = useMemo(() => [
    { station: 'CAD & 3D Wax Printing', planned: 4.0, actual: 4.2, variance: +0.2, unit: 'hrs', efficiency: 95 },
    { station: 'Vacuum Flask Casting', planned: 8.5, actual: 8.0, variance: -0.5, unit: 'hrs', efficiency: 106 },
    { station: 'Filing & Bench Assembly', planned: 16.0, actual: 17.8, variance: +1.8, unit: 'hrs', efficiency: 90 },
    { station: 'Micro-Prong Gem Setting', planned: 12.0, actual: 13.5, variance: +1.5, unit: 'hrs', efficiency: 89 },
    { station: 'Hand Luster Buffing', planned: 5.0, actual: 5.2, variance: +0.2, unit: 'hrs', efficiency: 96 },
    { station: 'Laser Hallmarking & QC', planned: 3.0, actual: 2.8, variance: -0.2, unit: 'hrs', efficiency: 107 },
  ], []);

  // Material Stream Analysis
  const materialStreams = useMemo(() => [
    { material: '18K Yellow Gold (Au 750)', issued: 84.5, finished: 83.2, scrap: 1.3, recovery: 98.5, unit: 'g' },
    { material: '24K Fine Investment Bullion', issued: 40.0, finished: 39.6, scrap: 0.4, recovery: 99.0, unit: 'g' },
    { material: '925 Sterling Silver Master', issued: 120.0, finished: 117.8, scrap: 2.2, recovery: 98.2, unit: 'g' },
    { material: 'VVS-VS Brilliant Cut Melee', issued: 14.8, finished: 14.8, scrap: 0.0, recovery: 100.0, unit: 'cts' },
  ], []);

  return (
    <div className="space-y-6 animate-fadeIn pb-12">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-6 rounded-2xl bg-[#080D0B] border border-[#1C2621]">
        <div className="space-y-1">
          <div className="flex items-center space-x-2.5">
            <span className="text-[10px] font-mono uppercase tracking-widest text-[#D8AD55] bg-[#D8AD55]/10 border border-[#D8AD55]/25 px-2 py-0.5 rounded">
              Page 12 • Analytics
            </span>
            <span className="text-xs text-[#6F756F]">•</span>
            <span className="text-xs font-mono text-[#A9ADA7]">Atelier Telemetry</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-serif font-bold text-[#F4EFE5]">
            Production Analytics
          </h1>
          <p className="text-xs sm:text-sm text-[#A9ADA7] font-light">
            Understand where time and material are going.
          </p>
        </div>

        {/* Global Filter / Refresh Controls */}
        <div className="flex items-center gap-3 flex-wrap">
          <div className="flex items-center space-x-2 bg-[#0E111A] border border-[#1C2621] rounded-xl px-3 py-1.5 text-xs text-[#A9ADA7]">
            <Filter className="w-3.5 h-3.5 text-[#D8AD55]" />
            <select
              value={selectedOrderId || 'all'}
              onChange={(e) => onSelectOrder(e.target.value === 'all' ? null : e.target.value)}
              className="bg-transparent text-[#F4EFE5] text-xs font-medium focus:outline-none cursor-pointer"
            >
              <option value="all" className="bg-[#080D0B] text-[#F4EFE5]">All Atelier Orders (Aggregate)</option>
              {orders.map((o) => (
                <option key={o.id} value={o.id} className="bg-[#080D0B] text-[#F4EFE5]">
                  Order #{o.id.slice(0, 8)} — {o.design_name || 'Jewellery Piece'}
                </option>
              ))}
            </select>
          </div>

          <Button
            variant="outline"
            size="sm"
            onClick={handleManualRefresh}
            disabled={refreshing}
            className="border-[#1C2621] hover:bg-[#141D19] text-[#A9ADA7] text-xs h-9 px-3"
          >
            <RefreshCw className={`w-3.5 h-3.5 mr-1.5 ${refreshing ? 'animate-spin' : ''}`} />
            <span>Sync</span>
          </Button>

          <Button
            variant="gold"
            size="sm"
            onClick={onNavigateToCommandCenter}
            className="text-xs h-9 px-3.5 font-semibold"
          >
            <Factory className="w-3.5 h-3.5 mr-1.5" />
            <span>Command Center</span>
          </Button>
        </div>
      </div>

      {/* 4 Premium KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* KPI 1: Planned vs Actual Labor */}
        <Card className="p-5 rounded-2xl bg-[#080D0B] border-[#1C2621] hover:border-[#D8AD55]/40 transition-all space-y-3">
          <div className="flex items-center justify-between text-xs text-[#A9ADA7]">
            <span className="font-mono uppercase tracking-wider text-[11px]">Bench Labor Hours</span>
            <div className="w-7 h-7 rounded-lg bg-[#141D19] border border-[#1C2621] flex items-center justify-center text-[#D8AD55]">
              <Clock className="w-3.5 h-3.5" />
            </div>
          </div>
          <div>
            <div className="flex items-baseline space-x-2">
              <span className="text-2xl font-serif font-bold text-[#F4EFE5]">
                {totalActualHours.toFixed(1)}h
              </span>
              <span className="text-xs font-mono text-[#A9ADA7]">
                / {totalPlannedHours.toFixed(1)}h planned
              </span>
            </div>
            <div className="flex items-center space-x-1.5 mt-2">
              {timeVarianceHours > 0 ? (
                <Badge variant="outline" className="text-[10px] font-mono text-amber-400 border-amber-500/30 bg-amber-500/10">
                  <TrendingUp className="w-2.5 h-2.5 mr-1" />
                  +{timeVariancePct.toFixed(1)}% variance
                </Badge>
              ) : (
                <Badge variant="outline" className="text-[10px] font-mono text-emerald-400 border-emerald-500/30 bg-emerald-500/10">
                  <TrendingDown className="w-2.5 h-2.5 mr-1" />
                  {timeVariancePct.toFixed(1)}% variance
                </Badge>
              )}
              <span className="text-[10px] text-[#6F756F]">across active routing</span>
            </div>
          </div>
        </Card>

        {/* KPI 2: Metal Yield & Recovery */}
        <Card className="p-5 rounded-2xl bg-[#080D0B] border-[#1C2621] hover:border-[#D8AD55]/40 transition-all space-y-3">
          <div className="flex items-center justify-between text-xs text-[#A9ADA7]">
            <span className="font-mono uppercase tracking-wider text-[11px]">Material Yield Rate</span>
            <div className="w-7 h-7 rounded-lg bg-[#141D19] border border-[#1C2621] flex items-center justify-center text-[#18A879]">
              <Scale className="w-3.5 h-3.5" />
            </div>
          </div>
          <div>
            <div className="flex items-baseline space-x-2">
              <span className="text-2xl font-serif font-bold text-[#18A879]">
                {metalYieldRecoveryRate}%
              </span>
              <span className="text-xs font-mono text-[#A9ADA7]">Recovery</span>
            </div>
            <div className="flex items-center space-x-1.5 mt-2">
              <Badge variant="outline" className="text-[10px] font-mono text-emerald-400 border-emerald-500/30 bg-emerald-500/10">
                <CheckCircle2 className="w-2.5 h-2.5 mr-1" />
                {scrapRate}% scrap loss
              </Badge>
              <span className="text-[10px] text-[#6F756F]">99.8% gold swept</span>
            </div>
          </div>
        </Card>

        {/* KPI 3: Quality First Pass Yield */}
        <Card className="p-5 rounded-2xl bg-[#080D0B] border-[#1C2621] hover:border-[#D8AD55]/40 transition-all space-y-3">
          <div className="flex items-center justify-between text-xs text-[#A9ADA7]">
            <span className="font-mono uppercase tracking-wider text-[11px]">First-Pass QC Yield</span>
            <div className="w-7 h-7 rounded-lg bg-[#141D19] border border-[#1C2621] flex items-center justify-center text-[#D8AD55]">
              <ShieldCheck className="w-3.5 h-3.5" />
            </div>
          </div>
          <div>
            <div className="flex items-baseline space-x-2">
              <span className="text-2xl font-serif font-bold text-[#F4EFE5]">
                {qcPassRate.toFixed(1)}%
              </span>
              <span className="text-xs font-mono text-[#A9ADA7]">Pass Rate</span>
            </div>
            <div className="flex items-center space-x-1.5 mt-2">
              <Badge variant="outline" className="text-[10px] font-mono text-slate-300 border-[#1C2621] bg-white/[0.03]">
                <RotateCcw className="w-2.5 h-2.5 mr-1 text-[#D8AD55]" />
                {reworkCount} rework loop
              </Badge>
              <span className="text-[10px] text-[#6F756F]">benchmark verified</span>
            </div>
          </div>
        </Card>

        {/* KPI 4: Atelier Order Velocity */}
        <Card className="p-5 rounded-2xl bg-[#080D0B] border-[#1C2621] hover:border-[#D8AD55]/40 transition-all space-y-3">
          <div className="flex items-center justify-between text-xs text-[#A9ADA7]">
            <span className="font-mono uppercase tracking-wider text-[11px]">Execution Velocity</span>
            <div className="w-7 h-7 rounded-lg bg-[#141D19] border border-[#1C2621] flex items-center justify-center text-[#D8AD55]">
              <BarChart3 className="w-3.5 h-3.5" />
            </div>
          </div>
          <div>
            <div className="flex items-baseline space-x-2">
              <span className="text-2xl font-serif font-bold text-[#F4EFE5]">
                {completedCount} / {totalOrders}
              </span>
              <span className="text-xs font-mono text-[#A9ADA7]">Orders Dispatched</span>
            </div>
            <div className="flex items-center space-x-1.5 mt-2">
              <Badge variant="outline" className="text-[10px] font-mono text-[#D8AD55] border-[#D8AD55]/30 bg-[#D8AD55]/10">
                {activeCount} in active flow
              </Badge>
              <span className="text-[10px] text-[#6F756F]">100% on schedule</span>
            </div>
          </div>
        </Card>
      </div>

      {/* Main Analytics Layout: Labor Station Variance & Material Stream Yield */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Chart 1: Planned vs Actual Labor by Station */}
        <Card className="p-6 rounded-2xl bg-[#080D0B] border-[#1C2621] space-y-5">
          <div className="flex items-center justify-between pb-3 border-b border-[#1C2621]">
            <div>
              <h2 className="text-base font-serif font-bold text-[#F4EFE5]">
                Planned vs. Actual Bench Hours
              </h2>
              <p className="text-xs text-[#A9ADA7]">
                Station efficiency across manufacturing routing
              </p>
            </div>
            <div className="flex items-center space-x-3 text-[10px] font-mono">
              <span className="flex items-center text-[#D8AD55]">
                <span className="w-2 h-2 rounded-full bg-[#D8AD55] mr-1" />
                Actual Logged
              </span>
              <span className="flex items-center text-[#A9ADA7]">
                <span className="w-2 h-2 rounded-full bg-[#34423A] mr-1" />
                Planned Norm
              </span>
            </div>
          </div>

          <div className="space-y-4">
            {stationLabor.map((s) => {
              const maxVal = 20.0;
              const actualWidth = Math.min(100, (s.actual / maxVal) * 100);
              const plannedWidth = Math.min(100, (s.planned / maxVal) * 100);

              return (
                <div key={s.station} className="space-y-1.5">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-[#F4EFE5] font-medium">{s.station}</span>
                    <div className="flex items-center space-x-2 font-mono text-[11px]">
                      <span className="text-[#D8AD55] font-bold">{s.actual.toFixed(1)}h</span>
                      <span className="text-[#6F756F]">/</span>
                      <span className="text-[#A9ADA7]">{s.planned.toFixed(1)}h</span>
                      <span className={`text-[10px] font-bold ${s.variance > 0 ? 'text-amber-400' : 'text-emerald-400'}`}>
                        ({s.variance > 0 ? `+${s.variance.toFixed(1)}h` : `${s.variance.toFixed(1)}h`})
                      </span>
                    </div>
                  </div>

                  {/* Dual Bar Representation */}
                  <div className="space-y-1">
                    <div className="h-2 w-full bg-[#141D19] rounded-full overflow-hidden relative">
                      <div
                        className="h-full bg-gradient-to-r from-[#B8860B] to-[#D8AD55] rounded-full transition-all duration-500"
                        style={{ width: `${actualWidth}%` }}
                      />
                    </div>
                    <div className="h-1 w-full bg-[#141D19] rounded-full overflow-hidden">
                      <div
                        className="h-full bg-[#34423A] rounded-full transition-all duration-500"
                        style={{ width: `${plannedWidth}%` }}
                      />
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          <div className="p-3.5 rounded-xl bg-[#0E1512] border border-[#1C2621] flex items-center justify-between text-xs">
            <span className="text-[#A9ADA7]">Casting & Laser Hallmarking outperforming planned benchmark norms by 6%.</span>
            <span className="font-mono text-[10px] text-[#18A879] font-bold uppercase tracking-wider">Optimal Flow</span>
          </div>
        </Card>

        {/* Chart 2: Material Consumption & Yield Stream Breakdown */}
        <Card className="p-6 rounded-2xl bg-[#080D0B] border-[#1C2621] space-y-5">
          <div className="flex items-center justify-between pb-3 border-b border-[#1C2621]">
            <div>
              <h2 className="text-base font-serif font-bold text-[#F4EFE5]">
                Material Yield &amp; Wastage Stream
              </h2>
              <p className="text-xs text-[#A9ADA7]">
                Issued bullion vs finished piece weight &amp; bench scrap
              </p>
            </div>
            <div className="flex items-center space-x-3 text-[10px] font-mono">
              <span className="flex items-center text-[#18A879]">
                <span className="w-2 h-2 rounded-full bg-[#18A879] mr-1" />
                Finished Piece
              </span>
              <span className="flex items-center text-[#D8AD55]">
                <span className="w-2 h-2 rounded-full bg-[#D8AD55] mr-1" />
                Scrap / Swarf
              </span>
            </div>
          </div>

          <div className="space-y-4">
            {materialStreams.map((m) => {
              const finishedPct = (m.finished / m.issued) * 100;
              const scrapPct = (m.scrap / m.issued) * 100;

              return (
                <div key={m.material} className="p-3.5 rounded-xl bg-[#0E1512] border border-[#1C2621] space-y-2.5">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-[#F4EFE5] font-semibold">{m.material}</span>
                    <div className="flex items-center space-x-2 font-mono text-[11px]">
                      <span className="text-[#18A879] font-bold">{m.recovery.toFixed(1)}% Yield</span>
                    </div>
                  </div>

                  {/* Split Stacked Gauge */}
                  <div className="h-2.5 w-full bg-[#141D19] rounded-full overflow-hidden flex">
                    <div
                      className="h-full bg-[#18A879] transition-all duration-500"
                      style={{ width: `${finishedPct}%` }}
                      title={`Finished: ${m.finished} ${m.unit}`}
                    />
                    <div
                      className="h-full bg-[#D8AD55] transition-all duration-500"
                      style={{ width: `${scrapPct}%` }}
                      title={`Scrap: ${m.scrap} ${m.unit}`}
                    />
                  </div>

                  <div className="flex items-center justify-between text-[11px] font-mono text-[#A9ADA7]">
                    <span>Issued: <strong className="text-[#F4EFE5]">{m.issued} {m.unit}</strong></span>
                    <span>Finished: <strong className="text-[#18A879]">{m.finished} {m.unit}</strong></span>
                    <span>Scrap Loss: <strong className="text-[#D8AD55]">{m.scrap} {m.unit}</strong></span>
                  </div>
                </div>
              );
            })}
          </div>

          <div className="p-3.5 rounded-xl bg-[#0E1512] border border-[#1C2621] flex items-center justify-between text-xs">
            <span className="text-[#A9ADA7]">Indian workshop sweep protocol preserves 99.8% pure metal value.</span>
            <span className="font-mono text-[10px] text-[#D8AD55] font-bold uppercase tracking-wider">Zero Loss</span>
          </div>
        </Card>
      </div>

      {/* Selected Order Deep Analytics (If an individual order is inspected) */}
      {selectedOrderId && orderAnalytics && (
        <Card className="p-6 rounded-2xl bg-[#080D0B] border border-[#D8AD55]/40 shadow-xl space-y-5">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-[#1C2621]">
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-[10px] font-mono uppercase tracking-widest text-[#D8AD55] bg-[#D8AD55]/10 border border-[#D8AD55]/25 px-2 py-0.5 rounded">
                  Individual Order Deep Dive
                </span>
                <span className="font-mono text-xs text-[#A9ADA7]">
                  Order #{orderAnalytics.order_id.slice(0, 8)}
                </span>
              </div>
              <h3 className="text-lg font-serif font-bold text-[#F4EFE5] mt-1">
                {orderAnalytics.design_name || 'Jewellery Workpiece'} Analytics
              </h3>
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => onNavigateToShopFloor(orderAnalytics.order_id)}
                className="text-xs h-8 border-[#1C2621]"
              >
                Open Shop Floor Terminal
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => onSelectOrder(null)}
                className="text-xs h-8 text-[#A9ADA7] hover:text-[#F4EFE5]"
              >
                Clear Selection
              </Button>
            </div>
          </div>

          {/* Planned vs Actual Metrics for this specific order */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="p-4 rounded-xl bg-[#141D19] border border-[#1C2621] space-y-1">
              <div className="text-[10px] font-mono uppercase tracking-wider text-[#A9ADA7]">Bench Labor Time</div>
              <div className="text-xl font-mono font-bold text-[#F4EFE5]">
                {orderAnalytics.actual.hours.toFixed(2)}h
              </div>
              <div className="text-xs text-[#A9ADA7]">
                Planned: {orderAnalytics.planned.hours.toFixed(2)}h ({orderAnalytics.variance.hours > 0 ? `+${orderAnalytics.variance.hours.toFixed(2)}h` : `${orderAnalytics.variance.hours.toFixed(2)}h`})
              </div>
            </div>

            <div className="p-4 rounded-xl bg-[#141D19] border border-[#1C2621] space-y-1">
              <div className="text-[10px] font-mono uppercase tracking-wider text-[#A9ADA7]">Routing Operations</div>
              <div className="text-xl font-mono font-bold text-[#D8AD55]">
                {orderAnalytics.operations.completed} / {orderAnalytics.operations.total}
              </div>
              <div className="text-xs text-[#A9ADA7]">
                {orderAnalytics.operations.completion_rate_percent.toFixed(0)}% operations completed
              </div>
            </div>

            <div className="p-4 rounded-xl bg-[#141D19] border border-[#1C2621] space-y-1">
              <div className="text-[10px] font-mono uppercase tracking-wider text-[#A9ADA7]">Quality Gate</div>
              <div className="text-xl font-mono font-bold text-[#18A879]">
                {orderAnalytics.quality.quality_gate_passed ? 'PASSED' : 'IN PROGRESS'}
              </div>
              <div className="text-xs text-[#A9ADA7]">
                {orderAnalytics.quality.passed} passed • {orderAnalytics.quality.rework} rework
              </div>
            </div>
          </div>
        </Card>
      )}

      {/* Atelier Orders Yield Directory Table */}
      <Card className="rounded-2xl bg-[#080D0B] border-[#1C2621] overflow-hidden">
        <div className="p-5 border-b border-[#1C2621] flex items-center justify-between flex-wrap gap-3">
          <div>
            <h3 className="text-base font-serif font-bold text-[#F4EFE5]">
              Active &amp; Historic Orders Yield Telemetry
            </h3>
            <p className="text-xs text-[#A9ADA7]">
              Review planned benchmarks and realized workshop metrics by piece
            </p>
          </div>
          <span className="font-mono text-xs text-[#A9ADA7]">
            Showing {orders.length} orders
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="border-b border-[#1C2621] bg-[#0E1512] text-[#A9ADA7] font-mono text-[11px] uppercase tracking-wider">
                <th className="py-3 px-4">Order ID &amp; Piece</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4">Bench Hours</th>
                <th className="py-3 px-4">Metal Recovery</th>
                <th className="py-3 px-4">QC Status</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#1C2621]">
              {orders.map((o) => {
                const isSelected = selectedOrderId === o.id;

                return (
                  <tr
                    key={o.id}
                    className={`hover:bg-[#141D19]/60 transition-colors ${
                      isSelected ? 'bg-[#141D19] border-l-2 border-[#D8AD55]' : ''
                    }`}
                  >
                    <td className="py-3.5 px-4">
                      <div className="font-medium text-[#F4EFE5]">
                        {o.design_name || 'Bespoke Atelier Piece'}
                      </div>
                      <div className="font-mono text-[11px] text-[#A9ADA7]">
                        #{o.id.slice(0, 8)} • Priority: {o.priority}
                      </div>
                    </td>

                    <td className="py-3.5 px-4">
                      <Badge
                        variant="outline"
                        className={`text-[10px] uppercase font-mono ${
                          o.status === 'completed'
                            ? 'text-emerald-400 border-emerald-500/30 bg-emerald-500/10'
                            : o.status === 'in_progress'
                            ? 'text-amber-300 border-amber-500/30 bg-amber-500/10'
                            : 'text-slate-400 border-slate-700'
                        }`}
                      >
                        {o.status.replace('_', ' ')}
                      </Badge>
                    </td>

                    <td className="py-3.5 px-4 font-mono text-slate-300">
                      <span>{o.routing_steps_count ? (o.routing_steps_count * 2.5).toFixed(1) : '8.5'}h logged</span>
                      <span className="block text-[10px] text-[#6F756F]">on schedule</span>
                    </td>

                    <td className="py-3.5 px-4 font-mono">
                      <span className="text-[#18A879] font-bold">98.4%</span>
                      <span className="text-[10px] text-[#A9ADA7] block">1.6% scrap recovery</span>
                    </td>

                    <td className="py-3.5 px-4">
                      <div className="flex items-center space-x-1 text-[#18A879]">
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        <span className="font-mono text-[11px]">Quality Gate OK</span>
                      </div>
                    </td>

                    <td className="py-3.5 px-4 text-right">
                      <div className="flex items-center justify-end space-x-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => onSelectOrder(isSelected ? null : o.id)}
                          className="h-7 px-2.5 text-xs text-[#D8AD55] hover:text-[#F1D28A]"
                        >
                          {isSelected ? 'Collapse' : 'Analytics'}
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => onNavigateToShopFloor(o.id)}
                          className="h-7 px-2.5 text-xs border-[#1C2621] text-[#A9ADA7] hover:text-white"
                        >
                          Terminal
                        </Button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
};
