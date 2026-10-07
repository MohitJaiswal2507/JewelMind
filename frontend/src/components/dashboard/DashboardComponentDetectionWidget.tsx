import React from 'react';
import {
  Cpu,
  ArrowRight,
  ShieldCheck,
  Scan,
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';

interface DashboardComponentDetectionWidgetProps {
  onOpenDetectionModal: () => void;
  recentSketchUrl?: string | null;
  recentDesignName?: string | null;
}

export const DashboardComponentDetectionWidget: React.FC<DashboardComponentDetectionWidgetProps> = ({
  onOpenDetectionModal,
}) => {
  const detectedComponents = [
    { name: 'Solitaire Ring Mount', confidence: 94, category: 'Ring', status: 'Optimal' },
    { name: 'Micro-Pavé Halo Accents', confidence: 91, category: 'Setting', status: 'Verified' },
    { name: 'Heritage Drop Mount', confidence: 88, category: 'Pendant', status: 'Optimal' },
    { name: 'Tapered Comfort Shank', confidence: 96, category: 'Shank', status: 'Verified' },
  ];

  return (
    <Card className="bg-[#0B1210]/95 border-[#1C2621] shadow-2xl overflow-hidden flex flex-col justify-between">
      <CardHeader className="p-6 sm:p-7 pb-4 border-b border-[#1C2621] bg-[#080D0B]/70">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center space-x-2 text-[#D8AD55]">
              <Cpu className="w-5 h-5" />
              <CardTitle className="text-lg font-serif font-medium text-[#F4EFE5]">
                AI COMPONENT SCANNER
              </CardTitle>
              <Badge variant="gold" className="text-[10px]">YOLO Vision</Badge>
            </div>
            <CardDescription className="text-xs text-[#A9ADA7] font-light">
              Automated instance segmentation for structural jewellery decomposition
            </CardDescription>
          </div>

          <Button
            variant="atelier"
            size="sm"
            onClick={onOpenDetectionModal}
            className="text-xs font-semibold"
          >
            <Scan className="w-3.5 h-3.5 mr-1.5 text-[#D8AD55]" />
            Inspect Blueprint Components
          </Button>
        </div>
      </CardHeader>

      <CardContent className="p-6 sm:p-7 space-y-6">
        {/* Component Taxonomy Detection Rows */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5">
          {detectedComponents.map((item, idx) => (
            <div
              key={idx}
              className="p-4 rounded-xl bg-[#080D0B] border border-[#1C2621] space-y-2.5 hover:border-[#D8AD55]/30 transition-all duration-200"
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-[#F4EFE5] truncate">{item.name}</span>
                <span className="text-xs font-mono font-bold text-[#D8AD55]">{item.confidence}%</span>
              </div>
              <div className="w-full bg-[#050806] rounded-full h-1.5 overflow-hidden border border-[#1C2621]">
                <div
                  className="bg-gradient-to-r from-[#D8AD55] to-[#18A879] h-full rounded-full"
                  style={{ width: `${item.confidence}%` }}
                />
              </div>
              <div className="flex items-center justify-between text-[10px] text-[#A9ADA7] font-mono">
                <span>{item.category}</span>
                <span className="text-[#18A879]">{item.status}</span>
              </div>
            </div>
          ))}
        </div>

        {/* Informational ML Feature Feeder Banner */}
        <div className="p-4 rounded-xl bg-[#080D0B] border border-[#1C2621] flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center space-x-3.5">
            <div className="p-2 rounded-xl bg-[#141D19] text-[#D8AD55] border border-[#1C2621] shrink-0">
              <ShieldCheck className="w-5 h-5 text-[#18A879]" />
            </div>
            <div>
              <div className="text-xs font-semibold text-[#F4EFE5]">
                Downstream ML Feature Feeder
              </div>
              <p className="text-[11px] text-[#A9ADA7] font-light mt-0.5">
                Component counts and geometric areas feed directly into cost, precious metal loss, and karigar bench time models.
              </p>
            </div>
          </div>

          <Button
            variant="secondary"
            size="sm"
            onClick={onOpenDetectionModal}
            className="text-xs font-medium shrink-0 bg-[#0F1714] hover:bg-[#141D19] border-[#1C2621] text-[#F4EFE5]"
          >
            Launch Scanner
            <ArrowRight className="w-3.5 h-3.5 ml-1.5 text-[#D8AD55]" />
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};
