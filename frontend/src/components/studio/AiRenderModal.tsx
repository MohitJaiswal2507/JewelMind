import React, { useState } from 'react';
import {
  X,
  Sparkles,
  Loader2,
  AlertCircle,
  Download,
  Cpu,
  Layers,
  Sliders,
  CheckCircle2,
} from 'lucide-react';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import {
  aiRenderingService,
  RenderResultResponse,
  RenderOptions,
} from '../../services/api/aiRenderingService';
import { designService } from '../../services/api/designService';
import { ApiClientError } from '../../services/api/client';

interface AiRenderModalProps {
  isOpen: boolean;
  onClose: () => void;
  sketchUrl: string;
  designTitle: string;
  category?: string;
  designId?: string;
  onSuccess?: (renderedUrl: string) => void;
}

const CATEGORIES = [
  { id: 'ring', label: 'Ring' },
  { id: 'earring', label: 'Earring' },
  { id: 'pendant', label: 'Pendant' },
  { id: 'necklace', label: 'Necklace' },
  { id: 'bracelet', label: 'Bracelet' },
  { id: 'bangle', label: 'Bangle' },
  { id: 'brooch', label: 'Brooch' },
  { id: 'other', label: 'Other Jewellery' },
];

const MATERIALS = [
  { id: '18k yellow gold', label: '18K Yellow Gold' },
  { id: 'white gold', label: '18K White Gold' },
  { id: 'rose gold', label: '18K Rose Gold' },
  { id: 'platinum', label: '950 Platinum' },
  { id: 'sterling silver', label: '925 Sterling Silver' },
];

const GEMSTONES = [
  { id: 'round brilliant diamond', label: 'Brilliant Diamond' },
  { id: 'blue sapphire', label: 'Royal Blue Sapphire' },
  { id: 'emerald', label: 'Colombian Emerald' },
  { id: 'ruby', label: 'Burmese Ruby' },
  { id: 'amethyst', label: 'Royal Amethyst' },
];

export const AiRenderModal: React.FC<AiRenderModalProps> = ({
  isOpen,
  onClose,
  sketchUrl,
  designTitle,
  category: initialCategory = 'ring',
  designId,
  onSuccess,
}) => {
  const [selectedCategory, setSelectedCategory] = useState<string>(initialCategory.toLowerCase());
  const [material, setMaterial] = useState<string>('18k yellow gold');
  const [gemstone, setGemstone] = useState<string>('round brilliant diamond');
  const [controlType, setControlType] = useState<'lineart' | 'canny'>('lineart');
  const [controlStrength, setControlStrength] = useState<number>(1.0);
  const [steps, setSteps] = useState<number>(20);
  const [seed, setSeed] = useState<string>('');
  const [customPrompt, setCustomPrompt] = useState<string>('');
  const [showAdvanced, setShowAdvanced] = useState<boolean>(false);

  // Execution states
  const [isRendering, setIsRendering] = useState<boolean>(false);
  const [renderResult, setRenderResult] = useState<RenderResultResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'split' | 'rendered'>('split');

  if (!isOpen) return null;

  const handleRender = async () => {
    setIsRendering(true);
    setError(null);

    try {
      // Fetch the sketch image blob from the sketch URL
      const response = await fetch(sketchUrl);
      if (!response.ok) {
        throw new Error('Failed to load jewellery sketch image.');
      }
      const blob = await response.blob();

      const options: RenderOptions = {
        category: selectedCategory,
        design_id: designId,
        material,
        gemstone,
        control_type: controlType,
        control_strength: controlStrength,
        steps,
        prompt: customPrompt.trim() || undefined,
        seed: seed.trim() ? parseInt(seed.trim(), 10) : undefined,
      };

      const result = await aiRenderingService.renderSketch(blob, options);
      setRenderResult(result);

      if (designId) {
        try {
          await designService.updateDesign(designId, {
            rendered_image_url: result.output_url,
            status: 'ready',
          });
          if (onSuccess) {
            onSuccess(result.output_url);
          }
        } catch (saveErr) {
          console.warn('Design persistence warning:', saveErr);
        }
      }
    } catch (err: unknown) {
      if (err instanceof ApiClientError) {
        if (err.status === 507) {
          setError(
            'Rendering exceeded available GPU memory. Try a lower resolution or wait for the current GPU job to finish.'
          );
        } else if (err.status === 503) {
          setError('AI rendering worker is offline. Start the local RTX 4060 worker.');
        } else if (err.status === 422) {
          setError('Please upload a valid jewellery sketch.');
        } else {
          setError(err.message || 'AI rendering worker is offline. Start the local RTX 4060 worker.');
        }
      } else if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('AI rendering worker is offline. Start the local RTX 4060 worker.');
      }
    } finally {
      setIsRendering(false);
    }
  };

  const handleDownloadRender = () => {
    if (!renderResult) return;
    const a = document.createElement('a');
    a.href = renderResult.output_url;
    a.download = `render-${designTitle.toLowerCase().replace(/[^a-z0-9]+/g, '-')}-${renderResult.seed}.png`;
    a.target = '_blank';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md p-4 animate-in fade-in">
      <div className="bg-[#0b0f19] border border-slate-800 rounded-2xl w-full max-w-4xl max-h-[90vh] flex flex-col shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800/80 bg-slate-950/60">
          <div className="flex items-center space-x-2.5">
            <div className="p-2 rounded-xl bg-amber-500/10 text-amber-400 border border-amber-500/20">
              <Sparkles className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-white tracking-wide flex items-center space-x-2">
                <span>AI Jewellery Generative Rendering</span>
                <Badge variant="outline" className="text-[10px] text-emerald-400 border-emerald-500/30">
                  RTX 4060 ControlNet Diffusion
                </Badge>
              </h2>
              <p className="text-[11px] text-slate-400">
                Transforms sketch contours into photorealistic precious metals and gemstones using ControlNet.
              </p>
            </div>
          </div>
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8 rounded-lg text-slate-400 hover:text-white"
            onClick={onClose}
          >
            <X className="w-4 h-4" />
          </Button>
        </div>

        {/* Modal Body */}
        <div className="flex-1 overflow-y-auto p-6 grid grid-cols-1 md:grid-cols-12 gap-6">
          {/* Left Column: Visual Comparison & Output */}
          <div className="md:col-span-7 flex flex-col space-y-4">
            <div className="flex items-center justify-between text-xs">
              <span className="font-semibold text-slate-300">Rendering Canvas</span>
              {renderResult && (
                <div className="flex items-center space-x-1 bg-slate-900 border border-slate-800 rounded-lg p-0.5">
                  <button
                    onClick={() => setViewMode('split')}
                    className={`px-2 py-1 text-[11px] rounded font-medium transition-colors ${
                      viewMode === 'split' ? 'bg-amber-500/20 text-amber-300' : 'text-slate-400 hover:text-white'
                    }`}
                  >
                    Side-by-Side
                  </button>
                  <button
                    onClick={() => setViewMode('rendered')}
                    className={`px-2 py-1 text-[11px] rounded font-medium transition-colors ${
                      viewMode === 'rendered' ? 'bg-amber-500/20 text-amber-300' : 'text-slate-400 hover:text-white'
                    }`}
                  >
                    Render Only
                  </button>
                </div>
              )}
            </div>

            {/* Visual Display Container */}
            <div className="relative w-full bg-slate-950 rounded-2xl border border-slate-800/80 p-4 min-h-[340px] flex items-center justify-center overflow-hidden">
              {isRendering ? (
                <div className="flex flex-col items-center justify-center space-y-3 text-center p-6">
                  <Loader2 className="w-10 h-10 text-amber-400 animate-spin" />
                  <div className="space-y-1">
                    <p className="text-xs font-semibold text-white">Rendering jewellery...</p>
                    <p className="text-[11px] text-slate-400 max-w-xs">
                      Local GPU active: conditioning geometry with ControlNet {controlType} & generating photorealistic materials.
                    </p>
                  </div>
                </div>
              ) : renderResult ? (
                viewMode === 'split' ? (
                  <div className="grid grid-cols-2 gap-3 w-full h-full">
                    <div className="flex flex-col items-center space-y-1.5">
                      <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">
                        Original Blueprint
                      </span>
                      <div className="bg-white/5 border border-slate-800 rounded-xl p-2 w-full h-64 flex items-center justify-center">
                        <img
                          src={sketchUrl}
                          alt="Original Sketch"
                          className="max-h-full object-contain filter invert opacity-90"
                        />
                      </div>
                    </div>
                    <div className="flex flex-col items-center space-y-1.5">
                      <span className="text-[10px] uppercase font-bold text-amber-400 tracking-wider flex items-center space-x-1">
                        <CheckCircle2 className="w-3 h-3 text-amber-400" />
                        <span>Photorealistic Render</span>
                      </span>
                      <div className="bg-slate-900 border border-amber-500/30 rounded-xl p-2 w-full h-64 flex items-center justify-center shadow-inner">
                        <img
                          src={renderResult.output_url}
                          alt="Rendered Result"
                          className="max-h-full object-contain rounded-lg shadow-lg"
                        />
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="flex flex-col items-center space-y-2 w-full">
                    <img
                      src={renderResult.output_url}
                      alt="Rendered Jewellery"
                      className="max-h-80 object-contain rounded-xl shadow-2xl border border-slate-800"
                    />
                  </div>
                )
              ) : (
                <div className="flex flex-col items-center space-y-3 text-center">
                  <div className="w-56 h-56 bg-white/5 border border-slate-800/80 rounded-xl p-3 flex items-center justify-center">
                    <img
                      src={sketchUrl}
                      alt="Original Sketch Preview"
                      className="max-h-full object-contain filter invert opacity-85"
                    />
                  </div>
                  <p className="text-[11px] text-slate-500">
                    Input sketch ready. Adjust precious materials and click "Render Jewellery".
                  </p>
                </div>
              )}
            </div>

            {/* Error Message */}
            {error && (
              <div className="p-3 bg-rose-500/10 border border-rose-500/30 rounded-xl text-xs text-rose-300 flex items-start space-x-2">
                <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
                <span className="leading-snug">{error}</span>
              </div>
            )}

            {/* Render Metadata Box */}
            {renderResult && (
              <div className="p-3 bg-slate-900/60 border border-slate-800 rounded-xl text-[11px] space-y-1.5">
                <div className="font-semibold text-slate-300 flex items-center justify-between">
                  <span className="flex items-center space-x-1.5 text-slate-400">
                    <Cpu className="w-3.5 h-3.5 text-amber-400" />
                    <span>Inference Telemetry</span>
                  </span>
                  <span className="text-amber-400 font-mono">
                    {(renderResult.inference_time_ms / 1000).toFixed(2)}s • {renderResult.device_used}
                  </span>
                </div>
                <div className="grid grid-cols-3 gap-2 text-slate-400 pt-1">
                  <div>
                    Seed: <span className="font-mono text-white">{renderResult.seed}</span>
                  </div>
                  <div>
                    Steps: <span className="font-mono text-white">{renderResult.steps}</span>
                  </div>
                  <div>
                    Control: <span className="font-mono text-white">{renderResult.control_type}</span>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Right Column: Parameters & Controls */}
          <div className="md:col-span-5 flex flex-col justify-between space-y-5">
            <div className="space-y-4 text-xs">
              {/* Category Selection */}
              <div className="space-y-1.5">
                <label className="font-bold text-slate-300 uppercase tracking-wider text-[10px]">
                  Jewellery Category
                </label>
                <select
                  value={selectedCategory}
                  onChange={(e) => setSelectedCategory(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-amber-500 font-medium capitalize"
                >
                  {CATEGORIES.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* Material Selection */}
              <div className="space-y-1.5">
                <label className="font-bold text-slate-300 uppercase tracking-wider text-[10px]">
                  Precious Metal Finish
                </label>
                <div className="grid grid-cols-1 gap-1.5">
                  {MATERIALS.map((m) => (
                    <button
                      key={m.id}
                      type="button"
                      onClick={() => setMaterial(m.id)}
                      className={`text-left px-3 py-2 rounded-xl text-xs font-medium border transition-all ${
                        material === m.id
                          ? 'bg-amber-500/15 border-amber-500/50 text-amber-300 shadow-sm'
                          : 'bg-slate-900/40 border-slate-800 text-slate-400 hover:text-slate-200 hover:border-slate-700'
                      }`}
                    >
                      {m.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Gemstone Selection */}
              <div className="space-y-1.5">
                <label className="font-bold text-slate-300 uppercase tracking-wider text-[10px]">
                  Gemstone Embellishment
                </label>
                <select
                  value={gemstone}
                  onChange={(e) => setGemstone(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-amber-500"
                >
                  {GEMSTONES.map((g) => (
                    <option key={g.id} value={g.id}>
                      {g.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* Conditioning Adapter */}
              <div className="space-y-1.5">
                <label className="font-bold text-slate-300 uppercase tracking-wider text-[10px] flex items-center space-x-1.5">
                  <Layers className="w-3.5 h-3.5 text-slate-500" />
                  <span>ControlNet Adapter</span>
                </label>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    type="button"
                    onClick={() => setControlType('lineart')}
                    className={`px-3 py-2 rounded-xl text-center text-xs font-semibold border transition-all ${
                      controlType === 'lineart'
                        ? 'bg-blue-500/15 border-blue-500/50 text-blue-300'
                        : 'bg-slate-900/40 border-slate-800 text-slate-400'
                    }`}
                  >
                    LineArt (Blueprint)
                  </button>
                  <button
                    type="button"
                    onClick={() => setControlType('canny')}
                    className={`px-3 py-2 rounded-xl text-center text-xs font-semibold border transition-all ${
                      controlType === 'canny'
                        ? 'bg-blue-500/15 border-blue-500/50 text-blue-300'
                        : 'bg-slate-900/40 border-slate-800 text-slate-400'
                    }`}
                  >
                    Canny Edge
                  </button>
                </div>
              </div>

              {/* Advanced Settings Toggle */}
              <div>
                <button
                  type="button"
                  onClick={() => setShowAdvanced(!showAdvanced)}
                  className="flex items-center space-x-1.5 text-[11px] font-semibold text-slate-400 hover:text-slate-200 transition-colors"
                >
                  <Sliders className="w-3 h-3 text-amber-400" />
                  <span>{showAdvanced ? 'Hide Advanced Options' : 'Show Advanced Options'}</span>
                </button>

                {showAdvanced && (
                  <div className="mt-2.5 p-3 rounded-xl bg-slate-950/70 border border-slate-800 space-y-2.5 text-[11px]">
                    <div className="space-y-1">
                      <div className="flex justify-between text-slate-400">
                        <span>Denoising Steps</span>
                        <span className="font-mono text-white">{steps}</span>
                      </div>
                      <input
                        type="range"
                        min="10"
                        max="30"
                        value={steps}
                        onChange={(e) => setSteps(parseInt(e.target.value, 10))}
                        className="w-full accent-amber-500 cursor-pointer"
                      />
                    </div>

                    <div className="space-y-1">
                      <div className="flex justify-between text-slate-400">
                        <span>Geometry Adherence Scale</span>
                        <span className="font-mono text-white">{controlStrength.toFixed(2)}</span>
                      </div>
                      <input
                        type="range"
                        min="0.4"
                        max="1.0"
                        step="0.05"
                        value={controlStrength}
                        onChange={(e) => setControlStrength(parseFloat(e.target.value))}
                        className="w-full accent-amber-500 cursor-pointer"
                      />
                    </div>

                    <div className="space-y-1">
                      <label className="text-slate-400">Fixed Seed (Optional)</label>
                      <input
                        type="number"
                        placeholder="Random seed (e.g. 42)"
                        value={seed}
                        onChange={(e) => setSeed(e.target.value)}
                        className="w-full bg-slate-900 border border-slate-800 rounded-lg px-2.5 py-1.5 text-slate-200 text-xs focus:outline-none focus:border-amber-500"
                      />
                    </div>

                    <div className="space-y-1">
                      <label className="text-slate-400">Style Prompt Notes</label>
                      <input
                        type="text"
                        placeholder="e.g. Victorian filigree, polished bezel"
                        value={customPrompt}
                        onChange={(e) => setCustomPrompt(e.target.value)}
                        className="w-full bg-slate-900 border border-slate-800 rounded-lg px-2.5 py-1.5 text-slate-200 text-xs focus:outline-none focus:border-amber-500"
                      />
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Actions */}
            <div className="pt-4 border-t border-slate-800/80 space-y-2">
              <Button
                variant="gold"
                size="sm"
                className="w-full font-bold text-xs shadow-md h-9"
                onClick={handleRender}
                disabled={isRendering}
              >
                {isRendering ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 mr-1.5 animate-spin" />
                    Rendering jewellery...
                  </>
                ) : (
                  <>
                    <Sparkles className="w-3.5 h-3.5 mr-1.5" />
                    Render Jewellery
                  </>
                )}
              </Button>

              {renderResult && (
                <Button
                  variant="secondary"
                  size="sm"
                  className="w-full text-xs font-semibold h-8"
                  onClick={handleDownloadRender}
                >
                  <Download className="w-3.5 h-3.5 mr-1.5" /> Download Rendered Image
                </Button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
