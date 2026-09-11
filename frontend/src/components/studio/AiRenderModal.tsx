import React, { useState, useEffect } from 'react';
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
  Gem,
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
  { id: '18k yellow gold', label: '18K Yellow Gold', color: 'from-amber-400 to-yellow-300' },
  { id: 'white gold', label: '18K White Gold', color: 'from-slate-200 to-slate-400' },
  { id: 'rose gold', label: '18K Rose Gold', color: 'from-rose-300 to-pink-400' },
  { id: 'platinum', label: '950 Platinum', color: 'from-slate-100 to-slate-300' },
  { id: 'sterling silver', label: '925 Sterling Silver', color: 'from-slate-300 to-slate-400' },
];

const GEMSTONES = [
  { id: 'round brilliant diamond', label: 'Brilliant Cut Diamond' },
  { id: 'blue sapphire', label: 'Royal Ceylon Sapphire' },
  { id: 'emerald', label: 'Colombian Emerald' },
  { id: 'ruby', label: 'Burmese Ruby' },
  { id: 'amethyst', label: 'Royal Purple Amethyst' },
];

const STAGES = [
  'Extracting LineArt blueprint geometry...',
  'Conditioning 1000-step ControlNet neural network...',
  'Synthesizing precious metal luster & gemstone facets...',
  'Polishing photorealistic master render...',
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
  const [renderStageIdx, setRenderStageIdx] = useState<number>(0);
  const [renderResult, setRenderResult] = useState<RenderResultResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'split' | 'rendered'>('split');

  // Progressive rendering status simulator
  useEffect(() => {
    let interval: ReturnType<typeof setInterval> | null = null;
    if (isRendering) {
      setRenderStageIdx(0);
      interval = setInterval(() => {
        setRenderStageIdx((prev) => (prev < STAGES.length - 1 ? prev + 1 : prev));
      }, 1400);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isRendering]);

  if (!isOpen) return null;

  const convertDataUrlToBlob = (dataUrl: string): Blob => {
    const parts = dataUrl.split(',');
    const mimeMatch = parts[0].match(/:(.*?);/);
    const mime = mimeMatch ? mimeMatch[1] : 'image/png';
    const binaryStr = atob(parts[1]);
    const len = binaryStr.length;
    const bytes = new Uint8Array(len);
    for (let i = 0; i < len; i++) {
      bytes[i] = binaryStr.charCodeAt(i);
    }
    return new Blob([bytes], { type: mime });
  };

  const handleRender = async () => {
    setIsRendering(true);
    setError(null);

    try {
      let fileBlob: Blob | null = null;
      if (sketchUrl.startsWith('data:')) {
        fileBlob = convertDataUrlToBlob(sketchUrl);
      }

      const options: RenderOptions = {
        category: selectedCategory,
        design_id: designId,
        sketch_url: sketchUrl,
        material,
        gemstone,
        control_type: controlType,
        control_strength: controlStrength,
        steps,
        prompt: customPrompt.trim() || undefined,
        seed: seed.trim() ? parseInt(seed.trim(), 10) : undefined,
      };

      const result = await aiRenderingService.renderSketch(fileBlob, options);
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
        if (err.message.toLowerCase().includes('failed to fetch') || err.message.toLowerCase().includes('networkerror')) {
          setError('Unable to reach the AI rendering service. Please ensure the backend server is running on port 8000.');
        } else {
          setError(err.message);
        }
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
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/85 backdrop-blur-md p-4 animate-in fade-in">
      <div className="bg-[#0E111A] border border-white/10 rounded-2xl w-full max-w-4xl max-h-[92vh] flex flex-col shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-7 py-5 border-b border-white/[0.07] bg-[#0A0C12]/70">
          <div className="flex items-center space-x-3">
            <div className="p-2.5 rounded-xl bg-amber-400/10 text-amber-300 border border-amber-400/20">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <h2 className="font-serif text-base font-medium text-white tracking-wide flex items-center space-x-2">
                <span>Atelier Generative Diffusion Suite</span>
                <Badge variant="gold" className="text-[9px]">
                  ControlNet v2
                </Badge>
              </h2>
              <p className="text-[11px] text-slate-400 font-light">
                Synthesize photorealistic precious metals & gemstones conditioned on blueprint geometry.
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
        <div className="flex-1 overflow-y-auto p-7 grid grid-cols-1 md:grid-cols-12 gap-7">
          {/* Left Column: Visual Comparison & Output */}
          <div className="md:col-span-7 flex flex-col space-y-4">
            <div className="flex items-center justify-between text-xs">
              <span className="font-medium text-slate-300 font-serif">Rendering Surface</span>
              {renderResult && (
                <div className="flex items-center space-x-1 bg-[#080A10] border border-white/10 rounded-lg p-0.5">
                  <button
                    onClick={() => setViewMode('split')}
                    className={`px-2.5 py-1 text-[10px] rounded-md font-semibold uppercase tracking-wider transition ${
                      viewMode === 'split' ? 'bg-amber-400/20 text-amber-200' : 'text-slate-400 hover:text-white'
                    }`}
                  >
                    Side-by-Side
                  </button>
                  <button
                    onClick={() => setViewMode('rendered')}
                    className={`px-2.5 py-1 text-[10px] rounded-md font-semibold uppercase tracking-wider transition ${
                      viewMode === 'rendered' ? 'bg-amber-400/20 text-amber-200' : 'text-slate-400 hover:text-white'
                    }`}
                  >
                    Render Only
                  </button>
                </div>
              )}
            </div>

            {/* Visual Display Container */}
            <div className="relative w-full bg-[#080A10] rounded-2xl border border-white/[0.07] p-4 min-h-[360px] flex items-center justify-center overflow-hidden shadow-inner">
              {isRendering ? (
                <div className="flex flex-col items-center justify-center space-y-4 text-center p-6">
                  <Loader2 className="w-10 h-10 text-amber-300 animate-spin" />
                  <div className="space-y-1.5 max-w-sm">
                    <p className="font-serif text-sm font-medium text-white">Synthesizing Diffusion Masterpiece...</p>
                    <p className="text-xs text-amber-300/90 font-mono transition-all duration-300">
                      {STAGES[renderStageIdx]}
                    </p>
                    <p className="text-[10px] text-slate-500 font-light pt-1">
                      GPU accelerated: ControlNet {controlType} conditioning active
                    </p>
                  </div>
                </div>
              ) : renderResult ? (
                viewMode === 'split' ? (
                  <div className="grid grid-cols-2 gap-3.5 w-full h-full">
                    <div className="flex flex-col items-center space-y-2">
                      <span className="text-[10px] uppercase font-semibold text-slate-400 tracking-widest">
                        Original Blueprint
                      </span>
                      <div className="bg-[#0A0C14] border border-white/5 rounded-xl p-3 w-full h-64 flex items-center justify-center">
                        <img
                          src={sketchUrl}
                          alt="Original Sketch"
                          className="max-h-full object-contain filter invert opacity-85"
                        />
                      </div>
                    </div>
                    <div className="flex flex-col items-center space-y-2">
                      <span className="text-[10px] uppercase font-semibold text-amber-300 tracking-widest flex items-center space-x-1">
                        <CheckCircle2 className="w-3 h-3 text-amber-300" />
                        <span>Photorealistic Render</span>
                      </span>
                      <div className="bg-[#0A0C14] border border-amber-400/30 rounded-xl p-3 w-full h-64 flex items-center justify-center shadow-lg">
                        <img
                          src={renderResult.output_url}
                          alt="Rendered Result"
                          className="max-h-full object-contain rounded-lg shadow-xl"
                        />
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="flex flex-col items-center space-y-2 w-full">
                    <img
                      src={renderResult.output_url}
                      alt="Rendered Jewellery"
                      className="max-h-80 object-contain rounded-xl shadow-2xl border border-white/10"
                    />
                  </div>
                )
              ) : (
                <div className="flex flex-col items-center space-y-3.5 text-center">
                  <div className="w-56 h-56 bg-[#0A0C14] border border-white/5 rounded-xl p-4 flex items-center justify-center">
                    <img
                      src={sketchUrl}
                      alt="Original Sketch Preview"
                      className="max-h-full object-contain filter invert opacity-85"
                    />
                  </div>
                  <p className="text-[11px] text-slate-400 font-light">
                    Input blueprint loaded. Configure metal alloy and gemstones, then click "Synthesize Render".
                  </p>
                </div>
              )}
            </div>

            {/* Error Message */}
            {error && (
              <div className="p-3.5 bg-rose-500/10 border border-rose-500/30 rounded-xl text-xs text-rose-300 flex items-start space-x-2">
                <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
                <span className="leading-snug">{error}</span>
              </div>
            )}

            {/* Render Metadata Box */}
            {renderResult && (
              <div className="p-3.5 bg-[#080A10] border border-white/5 rounded-xl text-[11px] space-y-1.5 font-light">
                <div className="font-medium text-slate-300 flex items-center justify-between">
                  <span className="flex items-center space-x-1.5 text-slate-400">
                    <Cpu className="w-3.5 h-3.5 text-amber-300" />
                    <span>Inference Telemetry</span>
                  </span>
                  <span className="text-amber-300 font-mono text-[10px]">
                    {(renderResult.inference_time_ms / 1000).toFixed(2)}s • {renderResult.device_used}
                  </span>
                </div>
                <div className="grid grid-cols-3 gap-2 text-slate-400 pt-1 text-[10px] font-mono">
                  <div>
                    Seed: <span className="text-white">{renderResult.seed}</span>
                  </div>
                  <div>
                    Steps: <span className="text-white">{renderResult.steps}</span>
                  </div>
                  <div>
                    Control: <span className="text-white">{renderResult.control_type}</span>
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
                <label className="font-semibold text-slate-400 uppercase tracking-widest text-[10px]">
                  Jewellery Category
                </label>
                <select
                  value={selectedCategory}
                  onChange={(e) => setSelectedCategory(e.target.value)}
                  className="w-full bg-[#080A10] border border-white/10 rounded-xl px-3.5 py-2 text-xs text-slate-200 focus:outline-none focus:border-amber-400 font-medium capitalize cursor-pointer shadow-inner"
                >
                  {CATEGORIES.map((c) => (
                    <option key={c.id} value={c.id} className="bg-[#0E111A]">
                      {c.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* Material Selection */}
              <div className="space-y-1.5">
                <label className="font-semibold text-slate-400 uppercase tracking-widest text-[10px]">
                  Precious Metal Alloy
                </label>
                <div className="grid grid-cols-1 gap-1.5">
                  {MATERIALS.map((m) => (
                    <button
                      key={m.id}
                      type="button"
                      onClick={() => setMaterial(m.id)}
                      className={`text-left px-3.5 py-2 rounded-xl text-xs font-medium border transition-all cursor-pointer flex items-center justify-between ${
                        material === m.id
                          ? 'bg-amber-400/15 border-amber-400/50 text-amber-200 shadow-sm'
                          : 'bg-[#080A10] border-white/5 text-slate-400 hover:text-slate-200 hover:border-white/15'
                      }`}
                    >
                      <span>{m.label}</span>
                      <div className={`w-3 h-3 rounded-full bg-gradient-to-r ${m.color}`} />
                    </button>
                  ))}
                </div>
              </div>

              {/* Gemstone Selection */}
              <div className="space-y-1.5">
                <label className="font-semibold text-slate-400 uppercase tracking-widest text-[10px] flex items-center justify-between">
                  <span>Gemstone Spec</span>
                  <Gem className="w-3 h-3 text-amber-300" />
                </label>
                <select
                  value={gemstone}
                  onChange={(e) => setGemstone(e.target.value)}
                  className="w-full bg-[#080A10] border border-white/10 rounded-xl px-3.5 py-2 text-xs text-slate-200 focus:outline-none focus:border-amber-400 cursor-pointer shadow-inner"
                >
                  {GEMSTONES.map((g) => (
                    <option key={g.id} value={g.id} className="bg-[#0E111A]">
                      {g.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* Conditioning Adapter */}
              <div className="space-y-1.5">
                <label className="font-semibold text-slate-400 uppercase tracking-widest text-[10px] flex items-center space-x-1.5">
                  <Layers className="w-3 h-3 text-slate-500" />
                  <span>Geometry Adapter</span>
                </label>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    type="button"
                    onClick={() => setControlType('lineart')}
                    className={`px-3 py-2 rounded-xl text-center text-xs font-semibold border transition-all cursor-pointer ${
                      controlType === 'lineart'
                        ? 'bg-amber-400/15 border-amber-400/50 text-amber-200'
                        : 'bg-[#080A10] border-white/5 text-slate-400 hover:border-white/15'
                    }`}
                  >
                    LineArt (Blueprint)
                  </button>
                  <button
                    type="button"
                    onClick={() => setControlType('canny')}
                    className={`px-3 py-2 rounded-xl text-center text-xs font-semibold border transition-all cursor-pointer ${
                      controlType === 'canny'
                        ? 'bg-amber-400/15 border-amber-400/50 text-amber-200'
                        : 'bg-[#080A10] border-white/5 text-slate-400 hover:border-white/15'
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
                  className="flex items-center space-x-1.5 text-[11px] font-semibold text-slate-400 hover:text-slate-200 transition-colors cursor-pointer"
                >
                  <Sliders className="w-3 h-3 text-amber-300" />
                  <span>{showAdvanced ? 'Hide Advanced Settings' : 'Show Advanced Settings'}</span>
                </button>

                {showAdvanced && (
                  <div className="mt-2.5 p-3.5 rounded-xl bg-[#080A10] border border-white/5 space-y-3 text-[11px]">
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
                        className="w-full accent-amber-400 cursor-pointer"
                      />
                    </div>

                    <div className="space-y-1">
                      <div className="flex justify-between text-slate-400">
                        <span>Geometry Adherence</span>
                        <span className="font-mono text-white">{controlStrength.toFixed(2)}</span>
                      </div>
                      <input
                        type="range"
                        min="0.4"
                        max="1.0"
                        step="0.05"
                        value={controlStrength}
                        onChange={(e) => setControlStrength(parseFloat(e.target.value))}
                        className="w-full accent-amber-400 cursor-pointer"
                      />
                    </div>

                    <div className="space-y-1">
                      <label className="text-slate-400">Seed (Optional)</label>
                      <input
                        type="number"
                        placeholder="Random seed (e.g. 42)"
                        value={seed}
                        onChange={(e) => setSeed(e.target.value)}
                        className="w-full bg-[#0E111A] border border-white/10 rounded-lg px-2.5 py-1.5 text-slate-200 text-xs focus:outline-none focus:border-amber-400"
                      />
                    </div>

                    <div className="space-y-1">
                      <label className="text-slate-400">Custom Lighting / Prompt Notes</label>
                      <input
                        type="text"
                        placeholder="e.g. Victorian filigree, polished bezel"
                        value={customPrompt}
                        onChange={(e) => setCustomPrompt(e.target.value)}
                        className="w-full bg-[#0E111A] border border-white/10 rounded-lg px-2.5 py-1.5 text-slate-200 text-xs focus:outline-none focus:border-amber-400"
                      />
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Actions */}
            <div className="pt-4 border-t border-white/5 space-y-2">
              <Button
                variant="gold"
                size="sm"
                className="w-full font-semibold text-xs shadow-md h-9"
                onClick={handleRender}
                disabled={isRendering}
              >
                {isRendering ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 mr-1.5 animate-spin" />
                    Synthesizing Render...
                  </>
                ) : (
                  <>
                    <Sparkles className="w-3.5 h-3.5 mr-1.5" />
                    Synthesize Render
                  </>
                )}
              </Button>

              {renderResult && (
                <Button
                  variant="secondary"
                  size="sm"
                  className="w-full text-xs font-semibold h-8 bg-[#121622] hover:bg-[#181E2E] border-white/5"
                  onClick={handleDownloadRender}
                >
                  <Download className="w-3.5 h-3.5 mr-1.5" /> Download Render (PNG)
                </Button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
