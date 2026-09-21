import React, { useState, useRef, useEffect } from 'react';
import {
  X,
  Columns,
  Sliders,
  CheckCircle2,
  Calendar,
  Layers,
  Cpu,
  Hash,
  Download,
} from 'lucide-react';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Design, DesignRender } from '../../types/design';

interface StudioComparisonModalProps {
  isOpen: boolean;
  onClose: () => void;
  design: Design;
  renders: DesignRender[];
  initialRenderIdA?: string;
  initialRenderIdB?: string;
  onApproveRender?: (renderId: string) => Promise<void>;
}

export const StudioComparisonModal: React.FC<StudioComparisonModalProps> = ({
  isOpen,
  onClose,
  design,
  renders,
  initialRenderIdA,
  initialRenderIdB,
  onApproveRender,
}) => {
  const [viewMode, setViewMode] = useState<'split' | 'side-by-side'>('side-by-side');
  const [selectedIdA, setSelectedIdA] = useState<string>(initialRenderIdA || (renders[0]?.id ?? 'blueprint'));
  const [selectedIdB, setSelectedIdB] = useState<string>(
    initialRenderIdB || (renders[renders.length - 1]?.id ?? renders[0]?.id ?? 'blueprint')
  );
  const [splitPos, setSplitPos] = useState<number>(50);
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const [isApproving, setIsApproving] = useState<boolean>(false);
  const sliderRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (initialRenderIdA) setSelectedIdA(initialRenderIdA);
    if (initialRenderIdB) setSelectedIdB(initialRenderIdB);
    else if (renders.length >= 2) {
      setSelectedIdA(renders[renders.length - 2].id);
      setSelectedIdB(renders[renders.length - 1].id);
    } else if (renders.length === 1) {
      if (design.sketch_image_url) {
        setSelectedIdA('blueprint');
        setSelectedIdB(renders[0].id);
      } else {
        setSelectedIdA(renders[0].id);
        setSelectedIdB(renders[0].id);
      }
    }
  }, [initialRenderIdA, initialRenderIdB, renders, design.sketch_image_url]);

  if (!isOpen) return null;

  // Resolve media for Side A and Side B
  const getMediaData = (id: string) => {
    if (id === 'blueprint') {
      return {
        id: 'blueprint',
        title: 'Source Blueprint / Sketch',
        versionLabel: 'Blueprint',
        imageUrl: design.sketch_image_url,
        isBlueprint: true,
        mode: 'Sketch Asset',
        prompt: design.ai_prompt || 'Initial Sketch Blueprint',
        controlType: 'Blueprint Source',
        controlStrength: 1.0,
        seed: null,
        isApproved: false,
        createdAt: design.created_at,
      };
    }
    const r = renders.find((item) => item.id === id);
    if (r) {
      return {
        id: r.id,
        title: `Render Version ${r.version_number}`,
        versionLabel: `V${r.version_number}`,
        imageUrl: r.image_url,
        isBlueprint: false,
        mode: r.render_mode === 'text' ? 'Text Guided' : r.render_mode === 'doodle' ? 'Doodle Guided' : 'Image Guided',
        prompt: r.prompt,
        controlType: r.control_type || 'none',
        controlStrength: r.control_strength,
        seed: r.seed,
        isApproved: r.is_approved_for_production,
        createdAt: r.created_at,
      };
    }
    return null;
  };

  const mediaA = getMediaData(selectedIdA);
  const mediaB = getMediaData(selectedIdB);

  // Slider Mouse/Touch dragging logic
  const handleMouseDown = () => setIsDragging(true);
  const handleMouseUp = () => setIsDragging(false);

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!isDragging || !sliderRef.current) return;
    const rect = sliderRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const clamped = Math.max(5, Math.min(95, (x / rect.width) * 100));
    setSplitPos(clamped);
  };

  const handleApprove = async (renderId: string) => {
    if (!onApproveRender || renderId === 'blueprint') return;
    setIsApproving(true);
    try {
      await onApproveRender(renderId);
    } finally {
      setIsApproving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-black/85 backdrop-blur-md animate-in fade-in select-none">
      <div className="relative w-full max-w-6xl max-h-[92vh] bg-[#0A0C13] border border-white/10 rounded-2xl shadow-2xl flex flex-col overflow-hidden">
        {/* Modal Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-white/10 bg-[#0E111A]">
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-xl bg-amber-400/10 border border-amber-400/20 text-amber-300">
              <Layers className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h2 className="text-base font-serif font-medium text-white tracking-wide">
                  Version Iteration Comparison
                </h2>
                <Badge variant="gold" className="text-[10px] font-mono">
                  {design.name}
                </Badge>
              </div>
              <p className="text-xs text-slate-400 font-light">
                Inspect photorealistic generative iterations, verify fine jewellery craftsmanship & quality
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            {/* View Mode Toggle */}
            <div className="flex items-center bg-[#08090D] p-1 rounded-xl border border-white/10 text-xs">
              <button
                onClick={() => setViewMode('side-by-side')}
                className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg font-medium transition cursor-pointer ${
                  viewMode === 'side-by-side'
                    ? 'bg-amber-400 text-slate-950 font-semibold shadow'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                <Columns className="w-3.5 h-3.5" />
                <span>Side-by-Side</span>
              </button>
              <button
                onClick={() => setViewMode('split')}
                className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg font-medium transition cursor-pointer ${
                  viewMode === 'split'
                    ? 'bg-amber-400 text-slate-950 font-semibold shadow'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                <Sliders className="w-3.5 h-3.5" />
                <span>Split Slider</span>
              </button>
            </div>

            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 text-slate-400 hover:text-white rounded-lg hover:bg-white/10"
              onClick={onClose}
              aria-label="Close modal"
            >
              <X className="w-4 h-4" />
            </Button>
          </div>
        </div>

        {/* Version Selector Bar */}
        <div className="grid grid-cols-2 gap-4 px-6 py-3 bg-[#08090E] border-b border-white/5 text-xs">
          {/* Side A Selector */}
          <div className="flex items-center space-x-2">
            <span className="font-semibold text-slate-400 font-mono text-[11px] uppercase tracking-wider">
              Left (Side A):
            </span>
            <select
              value={selectedIdA}
              onChange={(e) => setSelectedIdA(e.target.value)}
              className="bg-[#121622] border border-white/15 rounded-lg px-2.5 py-1 text-xs text-white focus:outline-none focus:ring-1 focus:ring-amber-400/50"
            >
              {design.sketch_image_url && <option value="blueprint">Source Blueprint (Sketch)</option>}
              {renders.map((r) => (
                <option key={r.id} value={r.id}>
                  V{r.version_number} — {r.render_mode.toUpperCase()} ({new Date(r.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })})
                  {r.is_approved_for_production ? ' ★ Approved' : ''}
                </option>
              ))}
            </select>
          </div>

          {/* Side B Selector */}
          <div className="flex items-center justify-end space-x-2">
            <span className="font-semibold text-slate-400 font-mono text-[11px] uppercase tracking-wider">
              Right (Side B):
            </span>
            <select
              value={selectedIdB}
              onChange={(e) => setSelectedIdB(e.target.value)}
              className="bg-[#121622] border border-white/15 rounded-lg px-2.5 py-1 text-xs text-white focus:outline-none focus:ring-1 focus:ring-amber-400/50"
            >
              {renders.map((r) => (
                <option key={r.id} value={r.id}>
                  V{r.version_number} — {r.render_mode.toUpperCase()} ({new Date(r.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })})
                  {r.is_approved_for_production ? ' ★ Approved' : ''}
                </option>
              ))}
              {design.sketch_image_url && <option value="blueprint">Source Blueprint (Sketch)</option>}
            </select>
          </div>
        </div>

        {/* Comparison Stage */}
        <div className="flex-1 overflow-y-auto p-6 bg-[#06070B] flex flex-col items-center justify-center">
          {viewMode === 'side-by-side' ? (
            /* SIDE BY SIDE VIEW */
            <div className="w-full grid grid-cols-1 md:grid-cols-2 gap-6 items-stretch">
              {/* Card A */}
              <div className="flex flex-col bg-[#0E111A] border border-white/10 rounded-2xl overflow-hidden shadow-xl">
                <div className="relative aspect-square max-h-[380px] bg-[#040508] flex items-center justify-center p-3 border-b border-white/10">
                  {mediaA?.imageUrl ? (
                    <img
                      src={mediaA.imageUrl}
                      alt={mediaA.title}
                      className={`w-full h-full object-contain ${
                        mediaA.isBlueprint ? 'filter invert opacity-80' : ''
                      }`}
                    />
                  ) : (
                    <div className="text-slate-500 text-xs">No media preview</div>
                  )}

                  {/* Version Badge */}
                  <div className="absolute top-3 left-3 px-2.5 py-1 rounded-lg bg-black/70 backdrop-blur-md text-[11px] font-mono text-amber-300 font-bold border border-white/10">
                    {mediaA?.versionLabel}
                  </div>

                  {/* Mode & Approval Badges */}
                  <div className="absolute top-3 right-3 flex items-center space-x-1.5">
                    <Badge variant="outline" className="text-[10px]">
                      {mediaA?.mode}
                    </Badge>
                    {mediaA?.isApproved && (
                      <Badge variant="gold" className="text-[10px]">
                        <CheckCircle2 className="w-3 h-3 mr-1" /> Approved
                      </Badge>
                    )}
                  </div>
                </div>

                {/* Telemetry Details */}
                <div className="p-4 space-y-2.5 text-xs font-light">
                  <div className="font-serif font-medium text-white truncate">{mediaA?.title}</div>
                  <div className="text-[11px] text-slate-300 line-clamp-2 italic bg-[#080A10] p-2.5 rounded-lg border border-white/5">
                    "{mediaA?.prompt}"
                  </div>

                  <div className="grid grid-cols-2 gap-2 text-[11px] pt-1">
                    <div className="flex items-center space-x-1.5 text-slate-400">
                      <Cpu className="w-3.5 h-3.5 text-slate-500" />
                      <span>Control: <strong className="text-slate-200 font-mono">{mediaA?.controlType}</strong></span>
                    </div>
                    <div className="flex items-center space-x-1.5 text-slate-400">
                      <Hash className="w-3.5 h-3.5 text-slate-500" />
                      <span>Seed: <strong className="text-slate-200 font-mono">{mediaA?.seed ?? 'Random'}</strong></span>
                    </div>
                    <div className="flex items-center space-x-1.5 text-slate-400">
                      <Calendar className="w-3.5 h-3.5 text-slate-500" />
                      <span className="font-mono text-[10px]">
                        {mediaA?.createdAt ? new Date(mediaA.createdAt).toLocaleDateString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : '-'}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Card B */}
              <div className="flex flex-col bg-[#0E111A] border border-white/10 rounded-2xl overflow-hidden shadow-xl">
                <div className="relative aspect-square max-h-[380px] bg-[#040508] flex items-center justify-center p-3 border-b border-white/10">
                  {mediaB?.imageUrl ? (
                    <img
                      src={mediaB.imageUrl}
                      alt={mediaB.title}
                      className={`w-full h-full object-contain ${
                        mediaB.isBlueprint ? 'filter invert opacity-80' : ''
                      }`}
                    />
                  ) : (
                    <div className="text-slate-500 text-xs">No media preview</div>
                  )}

                  {/* Version Badge */}
                  <div className="absolute top-3 left-3 px-2.5 py-1 rounded-lg bg-black/70 backdrop-blur-md text-[11px] font-mono text-amber-300 font-bold border border-white/10">
                    {mediaB?.versionLabel}
                  </div>

                  {/* Mode & Approval Badges */}
                  <div className="absolute top-3 right-3 flex items-center space-x-1.5">
                    <Badge variant="outline" className="text-[10px]">
                      {mediaB?.mode}
                    </Badge>
                    {mediaB?.isApproved && (
                      <Badge variant="gold" className="text-[10px]">
                        <CheckCircle2 className="w-3 h-3 mr-1" /> Approved
                      </Badge>
                    )}
                  </div>
                </div>

                {/* Telemetry Details */}
                <div className="p-4 space-y-2.5 text-xs font-light">
                  <div className="font-serif font-medium text-white truncate">{mediaB?.title}</div>
                  <div className="text-[11px] text-slate-300 line-clamp-2 italic bg-[#080A10] p-2.5 rounded-lg border border-white/5">
                    "{mediaB?.prompt}"
                  </div>

                  <div className="grid grid-cols-2 gap-2 text-[11px] pt-1">
                    <div className="flex items-center space-x-1.5 text-slate-400">
                      <Cpu className="w-3.5 h-3.5 text-slate-500" />
                      <span>Control: <strong className="text-slate-200 font-mono">{mediaB?.controlType}</strong></span>
                    </div>
                    <div className="flex items-center space-x-1.5 text-slate-400">
                      <Hash className="w-3.5 h-3.5 text-slate-500" />
                      <span>Seed: <strong className="text-slate-200 font-mono">{mediaB?.seed ?? 'Random'}</strong></span>
                    </div>
                    <div className="flex items-center space-x-1.5 text-slate-400">
                      <Calendar className="w-3.5 h-3.5 text-slate-500" />
                      <span className="font-mono text-[10px]">
                        {mediaB?.createdAt ? new Date(mediaB.createdAt).toLocaleDateString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : '-'}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            /* SPLIT SLIDER VIEW */
            <div
              ref={sliderRef}
              onMouseMove={handleMouseMove}
              onMouseUp={handleMouseUp}
              onMouseLeave={handleMouseUp}
              className="relative w-full max-w-3xl aspect-square max-h-[460px] bg-[#0E111A] rounded-2xl border border-white/10 overflow-hidden shadow-2xl select-none cursor-ew-resize"
            >
              {/* Left Side: Version A */}
              <div className="absolute inset-0 flex items-center justify-center bg-[#05060A]">
                {mediaA?.imageUrl ? (
                  <img
                    src={mediaA.imageUrl}
                    alt={mediaA.title}
                    className={`w-full h-full object-contain ${
                      mediaA.isBlueprint ? 'filter invert opacity-80' : ''
                    }`}
                  />
                ) : (
                  <div className="text-slate-500 text-xs">No media preview</div>
                )}
                <div className="absolute top-4 left-4 px-2.5 py-1 rounded-lg bg-black/75 backdrop-blur-md text-[11px] text-amber-300 font-mono border border-white/10">
                  {mediaA?.versionLabel} ({mediaA?.mode})
                </div>
              </div>

              {/* Right Side: Version B (Clipped by splitPos) */}
              <div
                className="absolute inset-0 overflow-hidden bg-[#05060A]"
                style={{ clipPath: `polygon(${splitPos}% 0, 100% 0, 100% 100%, ${splitPos}% 100%)` }}
              >
                {mediaB?.imageUrl ? (
                  <img
                    src={mediaB.imageUrl}
                    alt={mediaB.title}
                    className={`w-full h-full object-contain bg-[#05060A] ${
                      mediaB.isBlueprint ? 'filter invert opacity-80' : ''
                    }`}
                  />
                ) : (
                  <div className="text-slate-500 text-xs">No media preview</div>
                )}
                <div className="absolute top-4 right-4 px-2.5 py-1 rounded-lg bg-amber-400 text-slate-950 font-bold text-[11px] shadow">
                  {mediaB?.versionLabel} ({mediaB?.mode})
                </div>
              </div>

              {/* Draggable Divider Handle */}
              <div
                className="absolute top-0 bottom-0 w-0.5 bg-amber-400 z-20 cursor-ew-resize flex items-center justify-center"
                style={{ left: `${splitPos}%` }}
                onMouseDown={handleMouseDown}
              >
                <div className="w-7 h-7 -ml-3.25 rounded-full bg-amber-400 text-slate-950 flex items-center justify-center shadow-lg border-2 border-slate-950">
                  <Sliders className="w-3.5 h-3.5 rotate-90" />
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="flex items-center justify-between px-6 py-3.5 bg-[#0E111A] border-t border-white/10 text-xs">
          <div className="flex items-center space-x-2 text-slate-400">
            <span>Comparing</span>
            <strong className="text-amber-300 font-mono">{mediaA?.versionLabel}</strong>
            <span>with</span>
            <strong className="text-amber-300 font-mono">{mediaB?.versionLabel}</strong>
          </div>

          <div className="flex items-center space-x-3">
            {mediaB && !mediaB.isBlueprint && !mediaB.isApproved && onApproveRender && (
              <Button
                variant="gold"
                size="sm"
                className="font-semibold text-xs shadow-md"
                onClick={() => handleApprove(mediaB.id)}
                disabled={isApproving}
              >
                <CheckCircle2 className="w-3.5 h-3.5 mr-1.5" />
                {isApproving ? 'Approving...' : `Approve ${mediaB.versionLabel} for Production`}
              </Button>
            )}

            {mediaB?.imageUrl && (
              <Button
                variant="secondary"
                size="sm"
                className="text-xs bg-[#121622] hover:bg-[#181E2E] border-white/5"
                onClick={() => {
                  const a = document.createElement('a');
                  a.href = mediaB.imageUrl!;
                  a.download = `${design.name.toLowerCase().replace(/[^a-z0-9]+/g, '-')}-${mediaB.versionLabel}.png`;
                  a.target = '_blank';
                  document.body.appendChild(a);
                  a.click();
                  document.body.removeChild(a);
                }}
              >
                <Download className="w-3.5 h-3.5 mr-1.5" /> Download {mediaB.versionLabel}
              </Button>
            )}

            <Button
              variant="outline"
              size="sm"
              className="text-xs border-white/10"
              onClick={onClose}
            >
              Close
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};
export default StudioComparisonModal;
