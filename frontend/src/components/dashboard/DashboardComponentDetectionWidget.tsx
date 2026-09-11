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
    { name: 'Gemstones', count: 'Solitaire, Pave, Baguettes', icon: Gem, color: 'text-amber-300 bg-amber-400/10 border-amber-400/20' },
    { name: 'Clasps & Mounts', count: 'Lobster, Toggle, Bezels', icon: Scan, color: 'text-slate-300 bg-white/5 border-white/10' },
    { name: 'Shanks & Bodies', count: 'Cathedral, Tension, Halos', icon: Layers, color: 'text-amber-200 bg-amber-400/10 border-amber-400/20' },
    { name: 'Connectors', count: 'Jump Rings, Bails, Hinges', icon: Cpu, color: 'text-slate-300 bg-white/5 border-white/10' },
  ];

  return (
    <Card className="bg-[#0E111A]/90 border-white/[0.07] shadow-2xl overflow-hidden flex flex-col justify-between">
      <CardHeader className="p-6 sm:p-7 pb-4 border-b border-white/[0.06] bg-[#0A0C12]/50">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center space-x-2 text-amber-300">
              <Cpu className="w-5 h-5" />
              <CardTitle className="text-lg font-serif font-medium">
                YOLO Computer Vision Component Scanner
              </CardTitle>
            </div>
            <CardDescription className="text-xs text-slate-400 font-light">
              Automated instance segmentation for structural jewellery decomposition
            </CardDescription>
          </div>

          <Button
            variant="atelier"
            size="sm"
            onClick={onOpenDetectionModal}
            className="text-xs font-semibold"
          >
            <Scan className="w-3.5 h-3.5 mr-1.5 text-amber-300" />
            Inspect Blueprint Components
          </Button>
        </div>
      </CardHeader>

      <CardContent className="p-6 sm:p-7 space-y-6">
        {/* Component Taxonomy Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5">
          {componentClasses.map((item, idx) => {
            const Icon = item.icon;
            return (
              <div
                key={idx}
                className="p-4 rounded-xl bg-[#080A10] border border-white/5 space-y-2 hover:border-amber-400/20 transition-all duration-200"
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-medium text-white">{item.name}</span>
                  <div className={`p-1.5 rounded-lg border ${item.color}`}>
                    <Icon className="w-3.5 h-3.5" />
                  </div>
                </div>
                <p className="text-[11px] text-slate-400/90 font-light leading-snug">{item.count}</p>
              </div>
            );
          })}
        </div>

        {/* Informational banner */}
        <div className="p-4.5 rounded-xl bg-[#0A0C14] border border-white/[0.06] flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center space-x-3.5">
            <div className="p-2 rounded-xl bg-amber-400/10 text-amber-300 border border-amber-400/20 shrink-0">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <div className="text-xs font-semibold text-white">
                Downstream ML Feature Feeder
              </div>
              <p className="text-[11px] text-slate-400 font-light mt-0.5">
                Component counts and geometric areas feed directly into cost, precious metal wastage, and bench-hour estimation models.
              </p>
            </div>
          </div>

          <Button
            variant="secondary"
            size="sm"
            onClick={onOpenDetectionModal}
            className="text-xs font-medium shrink-0 bg-[#121622] hover:bg-[#181E2E] border-white/5"
          >
            <span>Run Scanner</span>
            <ArrowRight className="w-3.5 h-3.5 ml-1.5" />
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};
