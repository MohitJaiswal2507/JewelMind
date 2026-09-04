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
    <Card className="bg-[#0b0f19] border-slate-800 shadow-xl overflow-hidden">
      <CardHeader className="p-6 pb-4 border-b border-slate-800/80 bg-slate-950/40">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center space-x-2 text-amber-400">
              <Sparkles className="w-5 h-5" />
              <CardTitle className="text-base sm:text-lg">
                Generative AI Renderings & Blueprints
              </CardTitle>
            </div>
            <CardDescription className="text-xs">
              Sketch blueprint conditioning & ControlNet photorealistic metallic previews
            </CardDescription>
          </div>
          <div className="flex items-center space-x-2.5">
            <Button
              variant="gold"
              size="sm"
              onClick={() => onOpenRenderModal()}
              className="text-xs font-bold shadow-sm"
            >
              <Sparkles className="w-3.5 h-3.5 mr-1.5" />
              New AI Render
            </Button>
            <Button
              variant="secondary"
              size="sm"
              onClick={onNavigateToStudio}
              className="text-xs font-semibold"
            >
              <span>View All in Studio</span>
              <ArrowRight className="w-3.5 h-3.5 ml-1.5" />
            </Button>
          </div>
        </div>
      </CardHeader>

      <CardContent className="p-6">
        {renders.length === 0 ? (
          <div className="py-12 px-6 rounded-2xl bg-slate-950/40 border border-dashed border-slate-800 text-center space-y-4">
            <div className="w-12 h-12 rounded-2xl bg-amber-500/10 text-amber-400 border border-amber-500/20 flex items-center justify-center mx-auto">
              <Sparkles className="w-6 h-6" />
            </div>
            <div className="space-y-1 max-w-sm mx-auto">
              <h3 className="text-sm font-bold text-white">No AI Renders Generated Yet</h3>
              <p className="text-xs text-slate-400">
                Upload or draw a jewellery sketch blueprint and run ControlNet generative diffusion to produce photorealistic gold and gemstone previews.
              </p>
            </div>
            <Button
              variant="gold"
              size="sm"
              onClick={() => onOpenRenderModal()}
              className="text-xs font-bold"
            >
              <Sparkles className="w-3.5 h-3.5 mr-1.5" />
              Start First AI Render
            </Button>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Left/Main: Side-by-Side Blueprint vs Photorealistic Render for Selected Asset */}
            <div className="lg:col-span-2 space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <span className="text-xs font-bold text-white uppercase tracking-wider">
                    {selectedAsset?.name || 'Selected Design'}
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
                    className="h-7 text-xs text-amber-400 hover:text-amber-300 flex items-center gap-1"
                  >
                    <span>Inspect Details</span>
                    <ExternalLink className="w-3 h-3" />
                  </Button>
                )}
              </div>

              {/* Side-by-Side Container */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {/* Blueprint Sketch Box */}
                <div className="rounded-xl bg-slate-950/80 border border-slate-800 p-3 space-y-2 flex flex-col justify-between">
                  <div className="flex items-center justify-between text-[11px] text-slate-400 font-semibold">
                    <span className="flex items-center gap-1">
                      <Layers className="w-3 h-3 text-slate-400" />
                      Sketch Blueprint
                    </span>
                    <Badge variant="outline" className="text-[9px]">
                      Conditioning Input
                    </Badge>
                  </div>
                  <div className="w-full h-48 sm:h-56 rounded-lg bg-slate-900/60 flex items-center justify-center overflow-hidden border border-slate-800/60 p-2">
                    {selectedAsset?.sketch_image_url ? (
                      <img
                        src={selectedAsset.sketch_image_url}
                        alt="Sketch blueprint"
                        className="max-h-full max-w-full object-contain filter invert opacity-90"
                      />
                    ) : (
                      <div className="text-center text-slate-500 text-xs">
                        No sketch uploaded
                      </div>
                    )}
                  </div>
                  <div className="text-[10px] text-slate-500 font-mono truncate">
                    {selectedAsset?.sketch_image_url ? 'Stored in Supabase bucket' : 'Draft blueprint'}
                  </div>
                </div>

                {/* AI Rendered Box */}
                <div className="rounded-xl bg-slate-950/80 border border-amber-500/30 p-3 space-y-2 flex flex-col justify-between">
                  <div className="flex items-center justify-between text-[11px] text-amber-300 font-semibold">
                    <span className="flex items-center gap-1">
                      <Sparkles className="w-3 h-3 text-amber-400" />
                      Photorealistic Render
                    </span>
                    <Badge variant="gold" className="text-[9px]">
                      ControlNet Output
                    </Badge>
                  </div>
                  <div className="w-full h-48 sm:h-56 rounded-lg bg-slate-900/60 flex items-center justify-center overflow-hidden border border-slate-800/60 p-2">
                    {selectedAsset?.rendered_image_url ? (
                      <img
                        src={selectedAsset.rendered_image_url}
                        alt="AI Render"
                        className="max-h-full max-w-full object-contain rounded"
                      />
                    ) : (
                      <div className="text-center p-4 space-y-2">
                        <Sparkles className="w-6 h-6 text-slate-600 mx-auto" />
                        <p className="text-[11px] text-slate-400">Render not generated yet</p>
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
                            className="h-7 text-[10px] font-bold"
                          >
                            Render This Sketch
                          </Button>
                        )}
                      </div>
                    )}
                  </div>
                  <div className="text-[10px] text-amber-400/80 font-mono truncate">
                    {selectedAsset?.rendered_image_url
                      ? 'Local RTX 4060 Diffusion complete'
                      : 'Awaiting diffusion inference'}
                  </div>
                </div>
              </div>
            </div>

            {/* Right: Quick Selection List */}
            <div className="space-y-3">
              <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block">
                Recent AI Gallery ({renders.length})
              </span>
              <div className="space-y-2 max-h-[340px] overflow-y-auto pr-1">
                {renders.map((item) => {
                  const isSelected = selectedAsset?.id === item.id;
                  const thumb = item.rendered_image_url || item.sketch_image_url;
                  return (
                    <div
                      key={item.id}
                      onClick={() => setSelectedAsset(item)}
                      className={`p-3 rounded-xl border transition-all cursor-pointer flex items-center gap-3 ${
                        isSelected
                          ? 'bg-amber-500/10 border-amber-500/50 shadow-md'
                          : 'bg-slate-950/40 border-slate-800/80 hover:border-slate-700 hover:bg-slate-900/40'
                      }`}
                    >
                      <div className="w-12 h-12 rounded-lg bg-slate-900 border border-slate-800 shrink-0 flex items-center justify-center overflow-hidden p-1">
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
                        <div className="text-xs font-bold text-white truncate">
                          {item.name}
                        </div>
                        <div className="flex items-center gap-1.5 text-[10px] text-slate-400 mt-0.5">
                          <span className="text-amber-400 font-semibold">{item.category}</span>
                          <span>•</span>
                          <span>{item.rendered_image_url ? 'Rendered' : 'Sketch Only'}</span>
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
