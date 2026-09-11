import React, { useEffect, useState, useCallback } from 'react';
import {
  Layers,
  LogOut,
  RefreshCw,
  Loader2,
  AlertCircle,
  Gem,
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { useAuth } from '../hooks/useAuth';
import { dashboardService } from '../services/api/dashboardService';
import { DashboardOverviewResponse } from '../types/dashboard';
import { Design } from '../types/design';
import { DashboardKpiCards } from '../components/dashboard/DashboardKpiCards';
import { DashboardQuickActions } from '../components/dashboard/DashboardQuickActions';
import { DashboardRecentRenders } from '../components/dashboard/DashboardRecentRenders';
import { DashboardComponentDetectionWidget } from '../components/dashboard/DashboardComponentDetectionWidget';
import { ComponentDetectionModal } from '../components/dashboard/ComponentDetectionModal';
import { DashboardProductionOverview } from '../components/dashboard/DashboardProductionOverview';
import { DashboardDesignAnalytics } from '../components/dashboard/DashboardDesignAnalytics';
import { AiRenderModal } from '../components/studio/AiRenderModal';

interface DashboardPageProps {
  onLogout: () => void;
  onNavigateToDesigns: () => void;
  onSelectDesign?: (design: Design | { id: string; name?: string }) => void;
  onNavigateToStudio?: () => void;
  onNavigateToProduction?: (tab?: string) => void;
  onOpenCanvas?: (designId?: string) => void;
}

export const DashboardPage: React.FC<DashboardPageProps> = ({
  onLogout,
  onNavigateToDesigns,
  onSelectDesign,
  onNavigateToStudio = () => {},
  onNavigateToProduction = () => {},
  onOpenCanvas = () => {},
}) => {
  const { logout, user } = useAuth();
  const [data, setData] = useState<DashboardOverviewResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Modals state
  const [isRenderModalOpen, setIsRenderModalOpen] = useState<boolean>(false);
  const [renderSketchUrl, setRenderSketchUrl] = useState<string>('');
  const [renderDesignTitle, setRenderDesignTitle] = useState<string>('Jewellery Sketch');

  const [isDetectionModalOpen, setIsDetectionModalOpen] = useState<boolean>(false);
  const [detectionImageUrl, setDetectionImageUrl] = useState<string | null>(null);
  const [detectionDesignTitle, setDetectionDesignTitle] = useState<string>('Jewellery Blueprint');

  const fetchDashboardData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await dashboardService.getOverview();
      setData(res);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to load atelier overview.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDashboardData();
  }, [fetchDashboardData]);

  const handleLogout = async () => {
    await logout();
    onLogout();
  };

  const handleOpenRenderModalWithAsset = (sketchUrl?: string, title?: string) => {
    if (sketchUrl) {
      setRenderSketchUrl(sketchUrl);
      setRenderDesignTitle(title || 'Jewellery Sketch');
    } else if (data?.recent_renders && data.recent_renders.length > 0 && data.recent_renders[0].sketch_image_url) {
      setRenderSketchUrl(data.recent_renders[0].sketch_image_url);
      setRenderDesignTitle(data.recent_renders[0].name);
    } else {
      setRenderSketchUrl('');
      setRenderDesignTitle('Jewellery Sketch');
    }
    setIsRenderModalOpen(true);
  };

  const handleOpenDetectionModalWithAsset = (imageUrl?: string | null, title?: string) => {
    if (imageUrl) {
      setDetectionImageUrl(imageUrl);
      setDetectionDesignTitle(title || 'Jewellery Blueprint');
    } else if (data?.recent_designs && data.recent_designs.length > 0) {
      const firstWithSketch = data.recent_designs.find((d) => d.sketch_image_url || d.rendered_image_url);
      if (firstWithSketch) {
        setDetectionImageUrl(firstWithSketch.sketch_image_url || firstWithSketch.rendered_image_url);
        setDetectionDesignTitle(firstWithSketch.name);
      }
    }
    setIsDetectionModalOpen(true);
  };

  const handleSelectDesignById = (designId: string) => {
    if (onSelectDesign) {
      onSelectDesign({ id: designId });
    } else {
      onNavigateToDesigns();
    }
  };

  if (loading && !data) {
    return (
      <div className="flex flex-col items-center justify-center py-32 space-y-4 text-slate-400">
        <Loader2 className="w-8 h-8 animate-spin text-amber-300" />
        <span className="text-xs font-light tracking-wide">Synthesizing Atelier Workshop Intelligence...</span>
      </div>
    );
  }

  if (error && !data) {
    return (
      <div className="max-w-2xl mx-auto py-16 space-y-6">
        <div className="p-6 rounded-2xl bg-rose-500/10 border border-rose-500/30 text-rose-300 space-y-3">
          <div className="flex items-center space-x-2 font-medium">
            <AlertCircle className="w-5 h-5" />
            <span>Atelier Intelligence Error</span>
          </div>
          <p className="text-xs text-rose-300/80">{error}</p>
          <Button variant="outline" size="sm" onClick={fetchDashboardData} className="border-rose-500/40 text-xs">
            <RefreshCw className="w-3.5 h-3.5 mr-1.5" /> Reconnect
          </Button>
        </div>
      </div>
    );
  }

  const userName = data?.user.full_name || user?.full_name || 'Designer';

  return (
    <div className="space-y-10 max-w-7xl mx-auto py-2 sm:py-4">
      {/* 1. Header Banner & Executive Atelier Greeting */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 p-7 sm:p-9 rounded-2xl bg-[#0E111A]/90 border border-white/[0.07] shadow-2xl relative overflow-hidden">
        {/* Subtle background luxury glow */}
        <div className="absolute top-0 right-0 w-96 h-96 bg-amber-400/[0.03] rounded-full blur-3xl pointer-events-none" />

        <div className="flex items-start sm:items-center space-x-4 z-10">
          <div className="w-13 h-13 rounded-2xl bg-gradient-to-tr from-amber-400/20 via-yellow-400/10 to-transparent border border-amber-400/30 flex items-center justify-center shadow-lg shadow-amber-500/5 shrink-0">
            <Gem className="w-6 h-6 text-amber-300" />
          </div>
          <div>
            <div className="flex flex-wrap items-center gap-2.5">
              <h1 className="font-serif text-2xl sm:text-3xl text-white font-normal tracking-tight">
                Welcome to the Atelier, {userName}
              </h1>
              <Badge variant="gold" className="text-[10px]">
                {data?.user.role || 'Principal Artisan'}
              </Badge>
            </div>
            <p className="text-xs sm:text-sm text-slate-400/90 mt-1 font-light max-w-xl">
              Curate bespoke fine jewellery blueprints, generate diffusion prototypes, and orchestrate workshop manufacturing.
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2.5 z-10">
          <Button
            variant="outline"
            size="sm"
            onClick={fetchDashboardData}
            disabled={loading}
            className="h-8.5 px-3.5 text-xs text-slate-300"
          >
            <RefreshCw className={`w-3.5 h-3.5 mr-1.5 ${loading ? 'animate-spin' : ''}`} />
            Sync
          </Button>

          <Button
            variant="gold"
            size="sm"
            onClick={onNavigateToDesigns}
            className="h-8.5 px-4 font-semibold text-xs shadow-md shadow-amber-500/10"
          >
            <Layers className="w-3.5 h-3.5 mr-1.5" />
            Catalogue ({data?.kpis.total_designs || 0})
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={handleLogout}
            className="h-8.5 px-3.5 text-xs text-slate-400 hover:text-rose-300 hover:border-rose-500/30"
          >
            <LogOut className="w-3.5 h-3.5 mr-1.5" />
            Sign Out
          </Button>
        </div>
      </div>

      {/* 2. Executive Atelier KPI Strip */}
      {data && (
        <DashboardKpiCards
          kpis={data.kpis}
          onNavigateToDesigns={onNavigateToDesigns}
          onNavigateToProduction={onNavigateToProduction}
        />
      )}

      {/* 3. Visual Creative Launchpad */}
      <DashboardQuickActions
        onOpenCanvas={() => onOpenCanvas()}
        onNavigateToDesigns={onNavigateToDesigns}
        onNavigateToStudio={onNavigateToStudio}
        onOpenRenderModal={() => handleOpenRenderModalWithAsset()}
        onOpenDetectionModal={() => handleOpenDetectionModalWithAsset()}
        onOpenNewOrderModal={() => onNavigateToProduction('orders')}
        onNavigateToOptimization={() => onNavigateToProduction('optimization')}
      />

      {/* 4. AI Renderings & Blueprint Showcase */}
      {data && (
        <DashboardRecentRenders
          renders={data.recent_renders}
          onNavigateToStudio={onNavigateToStudio}
          onSelectDesign={handleSelectDesignById}
          onOpenRenderModal={handleOpenRenderModalWithAsset}
        />
      )}

      {/* 5. YOLO Component Detection Widget */}
      <DashboardComponentDetectionWidget
        onOpenDetectionModal={() => handleOpenDetectionModalWithAsset()}
        recentSketchUrl={data?.recent_designs[0]?.sketch_image_url}
        recentDesignName={data?.recent_designs[0]?.name}
      />

      {/* 6. Workshop Operations & CP-SAT Schedule Overview */}
      {data && (
        <DashboardProductionOverview
          kpis={data.kpis}
          deadlines={data.upcoming_deadlines}
          latestSchedule={data.latest_schedule}
          onNavigateToProduction={onNavigateToProduction}
          onSelectDesign={handleSelectDesignById}
        />
      )}

      {/* 7. Category & Distribution Analytics */}
      {data && (
        <DashboardDesignAnalytics
          categories={data.categories}
          statuses={data.statuses}
          priorities={data.priorities}
        />
      )}

      {/* Modals */}
      {isRenderModalOpen && (
        <AiRenderModal
          isOpen={isRenderModalOpen}
          onClose={() => setIsRenderModalOpen(false)}
          sketchUrl={renderSketchUrl}
          designTitle={renderDesignTitle}
        />
      )}

      {isDetectionModalOpen && (
        <ComponentDetectionModal
          isOpen={isDetectionModalOpen}
          onClose={() => setIsDetectionModalOpen(false)}
          initialImageUrl={detectionImageUrl}
          designTitle={detectionDesignTitle}
        />
      )}
    </div>
  );
};

export default DashboardPage;
