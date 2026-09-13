import React from 'react';
import {
  Sparkles,
  ShieldCheck,
  Gem,
  Layers,
  AlertTriangle,
  Info,
  CheckCircle2,
} from 'lucide-react';
import { Badge } from '../ui/badge';
import { StructuredDesignUnderstanding } from '../../types/ai';

interface GeminiDesignUnderstandingCardProps {
  understanding: StructuredDesignUnderstanding;
  resolvedCategory?: string;
  yoloCategory?: string | null;
  geminiCategory?: string | null;
  categoryConflict?: boolean;
  fallbackApplied?: boolean;
  warnings?: string[];
  isEnhancedPrompt?: boolean;
}

export const GeminiDesignUnderstandingCard: React.FC<GeminiDesignUnderstandingCardProps> = ({
  understanding,
  resolvedCategory,
  yoloCategory,
  geminiCategory,
  categoryConflict = false,
  fallbackApplied = false,
  warnings = [],
  isEnhancedPrompt = false,
}) => {
  const categoryLabel = resolvedCategory || understanding.jewellery_category;

  return (
    <div className="bg-[#0A0C14] border border-amber-400/20 rounded-2xl p-4 space-y-3.5 shadow-xl animate-in fade-in duration-200">
      {/* Header Banner */}
      <div className="flex items-center justify-between border-b border-white/[0.07] pb-3">
        <div className="flex items-center space-x-2">
          <div className="p-1.5 rounded-lg bg-amber-400/10 text-amber-300 border border-amber-400/20">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <h4 className="text-xs font-semibold text-white font-serif tracking-wide flex items-center space-x-2">
              <span>{isEnhancedPrompt ? 'JewelMind Enhanced Understanding' : 'JewelMind Understood Your Design'}</span>
            </h4>
            <p className="text-[10px] text-slate-400 font-light">
              Multimodal semantic breakdown synthesized for precision atelier diffusion.
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-1.5">
          {fallbackApplied ? (
            <Badge variant="outline" className="text-[9px] border-amber-500/40 text-amber-300">
              Heuristic Fallback
            </Badge>
          ) : (
            <Badge variant="gold" className="text-[9px]">
              Gemini Vision
            </Badge>
          )}
        </div>
      </div>

      {/* Summary statement */}
      {understanding.design_summary && (
        <div className="p-2.5 rounded-xl bg-[#0E111A] border border-white/5 text-[11px] text-slate-300 leading-relaxed font-light">
          <span className="text-amber-300 font-medium font-serif mr-1">Interpretation:</span>
          {understanding.design_summary}
        </div>
      )}

      {/* Structured Grid Attributes */}
      <div className="grid grid-cols-2 gap-2 text-xs">
        {/* Jewellery Type */}
        <div className="bg-[#080A10] border border-white/5 rounded-xl p-2.5 space-y-1">
          <span className="text-[10px] uppercase font-semibold text-slate-400 tracking-wider flex items-center space-x-1">
            <Layers className="w-3 h-3 text-amber-300" />
            <span>Jewellery Type</span>
          </span>
          <p className="text-xs font-medium text-white capitalize">{categoryLabel}</p>
          {yoloCategory ? (
            <p className="text-[9px] text-slate-400 font-mono">
              Grounded by YOLO V2: <span className="text-slate-300 capitalize">{yoloCategory}</span>
            </p>
          ) : (
            <p className="text-[9px] text-slate-500 font-mono">
              Category: <span className="text-slate-400 capitalize">{categoryLabel}</span>
            </p>
          )}
        </div>

        {/* Precious Metal Alloy */}
        <div className="bg-[#080A10] border border-white/5 rounded-xl p-2.5 space-y-1">
          <span className="text-[10px] uppercase font-semibold text-slate-400 tracking-wider flex items-center space-x-1">
            <span className="w-2 h-2 rounded-full bg-amber-400" />
            <span>Precious Metal</span>
          </span>
          <p className="text-xs font-medium text-white capitalize">{understanding.material.primary_metal}</p>
          <p className="text-[9px] text-slate-400 capitalize">{understanding.material.finish}</p>
        </div>

        {/* Gemstones */}
        <div className="bg-[#080A10] border border-white/5 rounded-xl p-2.5 space-y-1">
          <span className="text-[10px] uppercase font-semibold text-slate-400 tracking-wider flex items-center space-x-1">
            <Gem className="w-3 h-3 text-amber-300" />
            <span>Gemstone Spec</span>
          </span>
          {understanding.gemstones.has_gemstones && understanding.gemstones.primary_gemstone ? (
            <div>
              <p className="text-xs font-medium text-white capitalize">
                {understanding.gemstones.primary_gemstone.gemstone_type}
              </p>
              <p className="text-[9px] text-slate-400 capitalize">
                Cut: {understanding.gemstones.primary_gemstone.cut} • Setting: {understanding.gemstones.primary_gemstone.setting_type}
              </p>
            </div>
          ) : (
            <p className="text-xs text-slate-400">All-metal silhouette (No stones)</p>
          )}
        </div>

        {/* Architecture & Geometry */}
        <div className="bg-[#080A10] border border-white/5 rounded-xl p-2.5 space-y-1">
          <span className="text-[10px] uppercase font-semibold text-slate-400 tracking-wider flex items-center space-x-1">
            <Info className="w-3 h-3 text-amber-300" />
            <span>Geometry & Shank</span>
          </span>
          <p className="text-xs font-medium text-white capitalize">
            {understanding.structure.band_or_body_structure || understanding.structure.silhouette}
          </p>
          <p className="text-[9px] text-slate-400 capitalize">
            {understanding.structure.setting_style || understanding.structure.stone_arrangement}
          </p>
        </div>
      </div>

      {/* Motifs and Aesthetic Influences */}
      {understanding.design_motifs && understanding.design_motifs.length > 0 && (
        <div className="space-y-1">
          <span className="text-[10px] uppercase font-semibold text-slate-400 tracking-wider">
            Design Motifs
          </span>
          <div className="flex flex-wrap gap-1.5 pt-0.5">
            {understanding.design_motifs.map((motif, i) => (
              <span
                key={i}
                className="px-2 py-0.5 rounded-md bg-[#0E111A] border border-white/10 text-[10px] text-slate-300"
              >
                {motif}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* User Intent Preserved Indicator (Semantic Priority) */}
      {understanding.user_constraints_applied && understanding.user_constraints_applied.length > 0 && (
        <div className="p-2.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-xs text-emerald-300 flex items-start space-x-2">
          <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
          <div className="space-y-1 text-[11px] leading-tight">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-emerald-300">
                Explicit User Requirements (Semantic Priority):
              </span>
              <span className="text-[10px] text-emerald-400/80 font-mono">Tier 1 Precedence</span>
            </div>
            <p className="text-[10px] text-emerald-300/80 font-light">
              Explicit user constraints take precedence over AI suggestions. The final prompt remains fully editable below.
            </p>
            <div className="flex flex-wrap gap-1 pt-0.5">
              {understanding.user_constraints_applied.map((constraint, idx) => (
                <span
                  key={idx}
                  className="inline-flex items-center px-2 py-0.5 rounded bg-emerald-400/20 text-emerald-200 text-[10px] font-mono"
                >
                  <CheckCircle2 className="w-2.5 h-2.5 mr-1 text-emerald-400" />
                  {constraint}
                </span>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Conflict or Diagnostic Warnings */}
      {categoryConflict && yoloCategory && (
        <div className="p-2.5 rounded-xl bg-amber-500/10 border border-amber-500/30 text-xs text-amber-300 flex items-start space-x-2">
          <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
          <div className="text-[10px] leading-snug">
            <span className="font-semibold">Category Discrepancy:</span> Verified YOLO V2 detected{' '}
            <span className="font-mono">{yoloCategory}</span> while visual analysis suggested{' '}
            <span className="font-mono">{geminiCategory}</span>. The final prompt is grounded on{' '}
            <span className="font-semibold capitalize">{categoryLabel}</span>.
          </div>
        </div>
      )}

      {warnings && warnings.length > 0 && (
        <div className="space-y-1">
          {warnings.map((w, idx) => (
            <p key={idx} className="text-[10px] text-amber-400/80 font-light flex items-center space-x-1">
              <Info className="w-3 h-3 text-amber-400 shrink-0" />
              <span>{w}</span>
            </p>
          ))}
        </div>
      )}
    </div>
  );
};

export default GeminiDesignUnderstandingCard;
