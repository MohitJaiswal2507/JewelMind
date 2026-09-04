import React from 'react';
import {
  Cpu,
  ArrowRight,
  ShieldCheck,
  Scan,
  Gem,
  Layers,
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../ui/card';
import { Button } from '../ui/button';

interface DashboardComponentDetectionWidgetProps {
  onOpenDetectionModal: () => void;
  recentSketchUrl?: string | null;
  recentDesignName?: string | null;
}

export const DashboardComponentDetectionWidget: React.FC<DashboardComponentDetectionWidgetProps> = ({
  onOpenDetectionModal,
}) => {
  const componentClasses = [
    { name: 'Gemstones', count: 'Solitaire, Pave, Baguettes', icon: Gem, color: 'text-sky-400 bg-sky-500/10 border-sky-500/30' },
    { name: 'Clasps & Hooks', count: 'Lobster, Toggle, Spring', icon: Scan, color: 'text-amber-400 bg-amber-500/10 border-amber-500/30' },
    { name: 'Shanks & Mounts', count: 'Cathedral, Tension, Halo', icon: Layers, color: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30' },
    { name: 'Connectors', count: 'Jump Rings, Bails, Links', icon: Cpu, color: 'text-purple-400 bg-purple-500/10 border-purple-500/30' },
  ];

  return (
    <Card className="bg-[#0b0f19] border-slate-800 shadow-xl overflow-hidden flex flex-col justify-between">
      <CardHeader className="p-6 pb-4 border-b border-slate-800/80 bg-slate-950/40">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center space-x-2 text-cyan-400">
              <Cpu className="w-5 h-5" />
              <CardTitle className="text-base sm:text-lg">
                YOLO Computer Vision Component Detection
              </CardTitle>
            </div>
            <CardDescription className="text-xs">
              Automated instance segmentation for structural jewellery decomposition
            </CardDescription>
          </div>

          <Button
            variant="gold"
            size="sm"
            onClick={onOpenDetectionModal}
            className="text-xs font-bold bg-gradient-to-r from-cyan-500 via-sky-400 to-cyan-500 text-slate-950 hover:brightness-110 shadow-sm"
          >
            <Scan className="w-3.5 h-3.5 mr-1.5" />
            Inspect Blueprint Components
          </Button>
        </div>
      </CardHeader>

      <CardContent className="p-6 space-y-5">
        {/* Component Taxonomy Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {componentClasses.map((item, idx) => {
            const Icon = item.icon;
            return (
              <div
                key={idx}
                className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-2 hover:border-slate-700 transition"
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-white">{item.name}</span>
                  <div className={`p-1.5 rounded-lg border ${item.color}`}>
                    <Icon className="w-3.5 h-3.5" />
                  </div>
                </div>
                <p className="text-[11px] text-slate-400 leading-snug">{item.count}</p>
              </div>
            );
          })}
        </div>

        {/* Informational banner */}
        <div className="p-4 rounded-xl bg-gradient-to-r from-cyan-950/30 via-slate-900/60 to-slate-950/80 border border-cyan-500/20 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-xl bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 shrink-0">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <div className="text-xs font-bold text-white">
                Downstream ML Feature Feeder
              </div>
              <p className="text-[11px] text-slate-400 mt-0.5">
                Component counts and geometric areas feed directly into cost, precious metal wastage, and labor-hour estimation models.
              </p>
            </div>
          </div>

          <Button
            variant="secondary"
            size="sm"
            onClick={onOpenDetectionModal}
            className="text-xs font-semibold shrink-0 border border-slate-700 hover:text-cyan-300"
          >
            <span>Run CV Scan</span>
            <ArrowRight className="w-3.5 h-3.5 ml-1.5" />
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};
