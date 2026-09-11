import React, { useState } from 'react';
import {
  Sparkles,
  Layers,
  ArrowRight,
  ExternalLink,
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { DashboardRecentAsset } from '../../types/dashboard';

interface DashboardRecentRendersProps {
  renders: DashboardRecentAsset[];
  onNavigateToStudio: () => void;
  onSelectDesign: (designId: string) => void;
  onOpenRenderModal: (sketchUrl?: string, designName?: string) => void;
}

export const DashboardRecentRenders: React.FC<DashboardRecentRendersProps> = ({
  renders,
  onNavigateToStudio,
  onSelectDesign,
  onOpenRenderModal,
}) => {
  const [selectedAsset, setSelectedAsset] = useState<DashboardRecentAsset | null>(
    renders.length > 0 ? renders[0] : null
  );

  return (
    <Card className="bg-[#0E111A]/90 border-white/[0.07] shadow-2xl overflow-hidden">
      <CardHeader className="p-6 sm:p-7 pb-4 border-b border-white/[0.06] bg-[#0A0C12]/50">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center space-x-2 text-amber-300">
              <Sparkles className="w-5 h-5" />
              <CardTitle className="text-lg font-serif font-medium">
                Recent Diffusion Masterpieces
              </CardTitle>
            </div>
            <CardDescription className="text-xs text-slate-400 font-light">
              Conditioned on lineart blueprint geometry with 1000-step ControlNet refinement
            </CardDescription>
          </div>
          <div className="flex items-center space-x-2.5">
            <Button
              variant="gold"
              size="sm"
              onClick={() => onOpenRenderModal()}
              className="text-xs font-semibold shadow-sm"
            >
              <Sparkles className="w-3.5 h-3.5 mr-1.5" />
              New AI Render
            </Button>
            <Button
              variant="secondary"
              size="sm"
              onClick={onNavigateToStudio}
              className="text-xs font-medium"
            >
              <span>Explore Studio</span>
              <ArrowRight className="w-3.5 h-3.5 ml-1.5" />
            </Button>
          </div>
        </div>
      </CardHeader>

      <CardContent className="p-6 sm:p-7">
        {renders.length === 0 ? (
          <div className="py-14 px-6 rounded-2xl bg-[#0A0C12]/40 border border-dashed border-white/10 text-center space-y-4">
            <div className="w-12 h-12 rounded-2xl bg-amber-400/10 text-amber-300 border border-amber-400/20 flex items-center justify-center mx-auto">
              <Sparkles className="w-6 h-6" />
            </div>
            <div className="space-y-1.5 max-w-sm mx-auto">
              <h3 className="text-base font-serif font-medium text-white">No Renders in Studio Yet</h3>
              <p className="text-xs text-slate-400 font-light leading-relaxed">
                Draw or upload a jewellery blueprint to synthesize photorealistic 18K gold and precious gemstone prototypes.
              </p>
            </div>
            <Button
              variant="gold"
              size="sm"
              onClick={() => onOpenRenderModal()}
              className="text-xs font-semibold"
            >
              <Sparkles className="w-3.5 h-3.5 mr-1.5" />
              Synthesize First Render
            </Button>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Left/Main: Dual Canvas Blueprint vs Photorealistic Render */}
            <div className="lg:col-span-2 space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2.5">
                  <span className="text-sm font-serif font-medium text-white">
                    {selectedAsset?.name || 'Selected Prototype'}
                  </span>
                  <Badge variant="gold" className="text-[10px]">
                    {selectedAsset?.category || 'Jewellery'}
                  </Badge>
                </div>
                {selectedAsset && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => onSelectDesign(selectedAsset.id)}
                    className="h-7 text-xs text-amber-300 hover:text-amber-200 flex items-center gap-1"
                  >
                    <span>Inspect Prototype</span>
                    <ExternalLink className="w-3 h-3" />
                  </Button>
                )}
              </div>

              {/* Side-by-Side Container */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {/* Blueprint Sketch Box */}
                <div className="rounded-2xl bg-[#080A10] border border-white/[0.07] p-4 space-y-3 flex flex-col justify-between">
                  <div className="flex items-center justify-between text-[11px] text-slate-400 font-medium">
                    <span className="flex items-center gap-1.5">
                      <Layers className="w-3.5 h-3.5 text-slate-400" />
                      Blueprint Geometry
                    </span>
                    <Badge variant="outline" className="text-[9px]">
                      Conditioning Input
                    </Badge>
                  </div>
                  <div className="w-full h-52 sm:h-60 rounded-xl bg-[#06070A] flex items-center justify-center overflow-hidden border border-white/5 p-3">
                    {selectedAsset?.sketch_image_url ? (
                      <img
                        src={selectedAsset.sketch_image_url}
                        alt="Sketch blueprint"
                        className="max-h-full max-w-full object-contain filter invert opacity-85"
                      />
                    ) : (
                      <div className="text-center text-slate-500 text-xs font-light">
                        No sketch uploaded
                      </div>
                    )}
                  </div>
                  <div className="text-[10px] text-slate-500 font-mono truncate">
                    {selectedAsset?.sketch_image_url ? 'Cloud storage active' : 'Draft blueprint'}
                  </div>
                </div>

                {/* AI Rendered Box */}
                <div className="rounded-2xl bg-[#080A10] border border-amber-400/30 p-4 space-y-3 flex flex-col justify-between">
                  <div className="flex items-center justify-between text-[11px] text-amber-300 font-medium">
                    <span className="flex items-center gap-1.5">
                      <Sparkles className="w-3.5 h-3.5 text-amber-300" />
                      Photorealistic Render
                    </span>
                    <Badge variant="gold" className="text-[9px]">
                      Diffusion Output
                    </Badge>
                  </div>
                  <div className="w-full h-52 sm:h-60 rounded-xl bg-[#06070A] flex items-center justify-center overflow-hidden border border-white/5 p-3">
                    {selectedAsset?.rendered_image_url ? (
                      <img
                        src={selectedAsset.rendered_image_url}
                        alt="AI Render"
                        className="max-h-full max-w-full object-contain rounded-lg shadow-lg"
                      />
                    ) : (
                      <div className="text-center p-4 space-y-2.5">
                        <Sparkles className="w-6 h-6 text-slate-600 mx-auto" />
                        <p className="text-xs text-slate-400 font-light">Render not synthesized yet</p>
                        {selectedAsset?.sketch_image_url && (
                          <Button
                            variant="gold"
                            size="sm"
                            onClick={() =>
                              onOpenRenderModal(
                                selectedAsset.sketch_image_url || undefined,
                                selectedAsset.name
                              )
                            }
                            className="h-7 text-[11px] font-semibold"
                          >
                            Render Blueprint
                          </Button>
                        )}
                      </div>
                    )}
                  </div>
                  <div className="text-[10px] text-amber-300/80 font-mono truncate">
                    {selectedAsset?.rendered_image_url
                      ? 'Local RTX 4060 Diffusion complete'
                      : 'Awaiting diffusion synthesis'}
                  </div>
                </div>
              </div>
            </div>

            {/* Right: Quick Selection List */}
            <div className="space-y-3">
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-widest block">
                Atelier Gallery ({renders.length})
              </span>
              <div className="space-y-2 max-h-[380px] overflow-y-auto pr-1">
                {renders.map((item) => {
                  const isSelected = selectedAsset?.id === item.id;
                  const thumb = item.rendered_image_url || item.sketch_image_url;
                  return (
                    <div
                      key={item.id}
                      onClick={() => setSelectedAsset(item)}
                      className={`p-3 rounded-xl border transition-all duration-200 cursor-pointer flex items-center gap-3.5 ${
                        isSelected
                          ? 'bg-amber-400/10 border-amber-400/40 shadow-lg'
                          : 'bg-[#080A10] border-white/5 hover:border-white/15 hover:bg-[#0D101A]'
                      }`}
                    >
                      <div className="w-13 h-13 rounded-xl bg-[#06070A] border border-white/10 shrink-0 flex items-center justify-center overflow-hidden p-1">
                        {thumb ? (
                          <img
                            src={thumb}
                            alt={item.name}
                            className={`max-h-full max-w-full object-contain ${
                              !item.rendered_image_url && item.sketch_image_url ? 'filter invert' : ''
                            }`}
                          />
                        ) : (
                          <Layers className="w-4 h-4 text-slate-600" />
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="text-xs font-semibold text-white truncate">
                          {item.name}
                        </div>
                        <div className="flex items-center gap-1.5 text-[10px] text-slate-400 mt-1">
                          <span className="text-amber-300 font-medium">{item.category}</span>
                          <span>•</span>
                          <span className="font-light">{item.rendered_image_url ? 'Rendered' : 'Blueprint'}</span>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};
