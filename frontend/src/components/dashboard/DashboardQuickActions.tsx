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
      title: 'Interactive Sketch Canvas',
      desc: 'Draw jewellery with symmetry, geometric shapes & layer guides',
      icon: Brush,
      iconColor: 'text-amber-400',
      borderColor: 'hover:border-amber-500/40',
      action: onOpenCanvas,
      btnLabel: 'Launch Canvas',
    },
    {
      title: 'AI Generative Rendering',
      desc: 'ControlNet diffusion for 18K gold, platinum & precious gemstones',
      icon: Sparkles,
      iconColor: 'text-amber-300',
      borderColor: 'hover:border-amber-400/40',
      action: onOpenRenderModal,
      btnLabel: 'Render Sketch',
    },
    {
      title: 'YOLO Component Detection',
      desc: 'Instance segmentation of gems, clasps, shanks, mounts & connectors',
      icon: Cpu,
      iconColor: 'text-cyan-400',
      borderColor: 'hover:border-cyan-500/40',
      action: onOpenDetectionModal,
      btnLabel: 'Run Detection',
    },
    {
      title: 'OR-Tools CP-SAT Optimizer',
      desc: 'Mathematical schedule solver for workshop artisans & machinery',
      icon: Sliders,
      iconColor: 'text-purple-400',
      borderColor: 'hover:border-purple-500/40',
      action: onNavigateToOptimization,
      btnLabel: 'Optimize Schedule',
    },
  ];

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-base sm:text-lg font-bold text-white tracking-tight">
            Executive Command Hub
          </h2>
          <p className="text-xs text-slate-400">
            Direct 1-click access to core AI design, computer vision, and manufacturing engines
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {actions.map((act, idx) => {
          const Icon = act.icon;
          return (
            <Card
              key={idx}
              className={`bg-[#0b0f19] border-slate-800 ${act.borderColor} transition-all duration-200 group flex flex-col justify-between shadow-md`}
            >
              <CardHeader className="p-5 pb-3 space-y-2">
                <div className="flex items-center justify-between">
                  <div
                    className={`p-2.5 rounded-xl bg-slate-900 border border-slate-800/80 ${act.iconColor} group-hover:scale-105 transition-transform`}
                  >
                    <Icon className="w-5 h-5" />
                  </div>
                  <span className="text-[10px] font-mono text-slate-500 font-bold uppercase tracking-wider">
                    0{idx + 1}
                  </span>
                </div>
                <CardTitle className="text-sm text-white font-bold group-hover:text-amber-300 transition-colors">
                  {act.title}
                </CardTitle>
                <CardDescription className="text-xs leading-relaxed text-slate-400">
                  {act.desc}
                </CardDescription>
              </CardHeader>
              <CardContent className="p-5 pt-0">
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={act.action}
                  className="w-full text-xs font-semibold justify-between border border-slate-800 hover:border-slate-700 bg-slate-900/80 hover:bg-slate-800"
                >
                  <span>{act.btnLabel}</span>
                  <ArrowUpRight className="w-3.5 h-3.5 text-slate-400 group-hover:text-amber-400 transition-colors" />
                </Button>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
};
