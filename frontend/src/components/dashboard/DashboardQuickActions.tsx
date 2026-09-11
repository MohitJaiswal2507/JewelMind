import React from 'react';
import {
  Brush,
  Sparkles,
  Cpu,
  Sliders,
  ArrowUpRight,
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../ui/card';
import { Button } from '../ui/button';

interface DashboardQuickActionsProps {
  onOpenCanvas: () => void;
  onNavigateToDesigns: () => void;
  onNavigateToStudio: () => void;
  onOpenRenderModal: () => void;
  onOpenDetectionModal: () => void;
  onOpenNewOrderModal: () => void;
  onNavigateToOptimization: () => void;
}

export const DashboardQuickActions: React.FC<DashboardQuickActionsProps> = ({
  onOpenCanvas,
  onOpenRenderModal,
  onOpenDetectionModal,
  onNavigateToOptimization,
}) => {
  const actions = [
    {
      title: 'Blueprint Drawing Desk',
      desc: 'Precision freehand sketching with symmetry, grid guides & PNG lineart export',
      icon: Brush,
      action: onOpenCanvas,
      btnLabel: 'Open Canvas',
    },
    {
      title: 'AI Generative Studio',
      desc: 'ControlNet diffusion synthesizing 18K gold, platinum & precious gemstones',
      icon: Sparkles,
      action: onOpenRenderModal,
      btnLabel: 'Synthesize Render',
    },
    {
      title: 'YOLO Component Scanner',
      desc: 'Instance segmentation extracting gemstones, clasps, mounts & shanks',
      icon: Cpu,
      action: onOpenDetectionModal,
      btnLabel: 'Scan Blueprint',
    },
    {
      title: 'Workshop CP-SAT Solver',
      desc: 'Constraint-based scheduler balancing artisan workbenches & machine runs',
      icon: Sliders,
      action: onNavigateToOptimization,
      btnLabel: 'Solve Schedule',
    },
  ];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="font-serif text-xl sm:text-2xl font-normal text-white tracking-tight">
            Creative Launchpad
          </h2>
          <p className="text-xs text-slate-400 font-light mt-0.5">
            Direct access to sketching, generative diffusion, computer vision, and manufacturing
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {actions.map((act, idx) => {
          const Icon = act.icon;
          return (
            <Card
              key={idx}
              className="bg-[#0E111A]/90 border-white/[0.07] hover:border-amber-400/30 transition-all duration-300 group flex flex-col justify-between shadow-xl"
            >
              <CardHeader className="p-6 pb-3 space-y-3">
                <div className="flex items-center justify-between">
                  <div
                    className="p-2.5 rounded-xl bg-white/[0.04] border border-white/[0.06] text-amber-300 group-hover:scale-105 group-hover:bg-amber-400/10 transition-all duration-300"
                  >
                    <Icon className="w-5 h-5" />
                  </div>
                  <span className="text-[10px] font-mono text-slate-500 font-semibold uppercase tracking-widest">
                    0{idx + 1}
                  </span>
                </div>
                <CardTitle className="text-base font-serif font-medium text-white group-hover:text-amber-200 transition-colors">
                  {act.title}
                </CardTitle>
                <CardDescription className="text-xs leading-relaxed text-slate-400/90 font-light">
                  {act.desc}
                </CardDescription>
              </CardHeader>
              <CardContent className="p-6 pt-0">
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={act.action}
                  className="w-full text-xs font-semibold justify-between bg-[#121622] hover:bg-[#181E2E] border-white/5 group-hover:border-amber-400/20"
                >
                  <span>{act.btnLabel}</span>
                  <ArrowUpRight className="w-3.5 h-3.5 text-slate-400 group-hover:text-amber-300 transition-colors" />
                </Button>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
};
