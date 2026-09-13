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
  Undo2,
  Wand2,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Textarea } from '../ui/textarea';
import {
  aiRenderingService,
  RenderResultResponse,
  RenderOptions,
} from '../../services/api/aiRenderingService';
import { geminiDesignService } from '../../services/api/geminiDesignService';
import { designService } from '../../services/api/designService';
import { ApiClientError } from '../../services/api/client';
import {
  GeminiStatus,
  StructuredDesignUnderstanding,
} from '../../types/ai';
import { GeminiDesignUnderstandingCard } from './GeminiDesignUnderstandingCard';

interface AiRenderModalProps {
  isOpen: boolean;
  onClose: () => void;
  sketchUrl: string;
  designTitle: string;
  category?: string;
  designId?: string;
  verifiedYoloCategory?: string | null;
  verifiedYoloConfidence?: number | null;
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
  verifiedYoloCategory = null,
  verifiedYoloConfidence = null,
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

  // Gemini State Management (Phase B UI Integration)
  const [userPromptInput, setUserPromptInput] = useState<string>('');
  const [originalUserPrompt, setOriginalUserPrompt] = useState<string>('');
  const [finalEditablePrompt, setFinalEditablePrompt] = useState<string>('');
  const [negativePrompt, setNegativePrompt] = useState<string>('');
  const [designUnderstanding, setDesignUnderstanding] = useState<StructuredDesignUnderstanding | null>(null);
  const [geminiStatus, setGeminiStatus] = useState<GeminiStatus>('idle');
  const [geminiError, setGeminiError] = useState<string | null>(null);
  const [isPromptEnhanced, setIsPromptEnhanced] = useState<boolean>(false);
  const [isPromptAnalyzedFromSketch, setIsPromptAnalyzedFromSketch] = useState<boolean>(false);
  const [userManuallyEdited, setUserManuallyEdited] = useState<boolean>(false);
  const [resolvedCategory, setResolvedCategory] = useState<string>(initialCategory.toLowerCase());
  const [yoloCategory, setYoloCategory] = useState<string | null>(verifiedYoloCategory);
  const [geminiCategory, setGeminiCategory] = useState<string | null>(null);
  const [categoryConflict, setCategoryConflict] = useState<boolean>(false);
  const [fallbackApplied, setFallbackApplied] = useState<boolean>(false);
  const [geminiWarnings, setGeminiWarnings] = useState<string[]>([]);
  const [showNegativePrompt, setShowNegativePrompt] = useState<boolean>(false);

  // Execution states for rendering
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

  /**
   * Flow A: Enhance artisan prompt with Gemini AI
   * Correction 2: Use only verified YOLO V2 category when available; never invent or pass selectedCategory as YOLO.
   * Correction 1: Semantic priority is applied, but prompt remains 100% user-editable.
   */
  const handleEnhancePrompt = async () => {
    const trimmed = userPromptInput.trim();
    if (!trimmed) {
      setGeminiError('Please enter a prompt description before enhancing with AI.');
      return;
    }

    if (geminiStatus === 'enhancing' || geminiStatus === 'analyzing') {
      return;
    }

    setGeminiStatus('enhancing');
    setGeminiError(null);

    try {
      setOriginalUserPrompt(trimmed);

      let imageBase64: string | null = null;
      let imageUrl: string | null = null;
      if (sketchUrl.startsWith('data:')) {
        imageBase64 = sketchUrl;
      } else if (sketchUrl.startsWith('http://') || sketchUrl.startsWith('https://')) {
        imageUrl = sketchUrl;
      }

      const res = await geminiDesignService.enhancePrompt({
        user_prompt: trimmed,
        image_base64: imageBase64,
        image_url: imageUrl,
        // Only pass YOLO context if actually verified; otherwise undefined
        yolo_category: verifiedYoloCategory || undefined,
        yolo_confidence: verifiedYoloConfidence !== null ? verifiedYoloConfidence : undefined,
      });

      setDesignUnderstanding(res.design_understanding);
      setResolvedCategory(res.resolved_category);
      setYoloCategory(res.yolo_category || null);
      setGeminiCategory(res.gemini_category || null);
      setCategoryConflict(res.category_conflict);
      setFallbackApplied(res.fallback_applied);
      setGeminiWarnings(res.warnings || []);

      // Put compiled renderer prompt into the editable field
      setFinalEditablePrompt(res.renderer_prompt);
      setNegativePrompt(res.negative_prompt);
      setIsPromptEnhanced(true);
      setIsPromptAnalyzedFromSketch(false);
      setUserManuallyEdited(false);
      setGeminiStatus('success');
    } catch (err: unknown) {
      setGeminiStatus('error');
      if (err instanceof ApiClientError) {
        if (err.status === 503) {
          setGeminiError('Gemini AI service is temporarily unavailable. You can continue using your prompt.');
        } else if (err.status === 422) {
          setGeminiError('Unable to process prompt. Please refine your design description.');
        } else {
          setGeminiError(err.message || 'Gemini prompt enhancement failed. Your prompt is preserved.');
        }
      } else if (err instanceof Error) {
        setGeminiError(err.message || 'Network error communicating with Gemini service.');
      } else {
        setGeminiError('Prompt enhancement encountered an unexpected issue.');
      }
    }
  };

  /**
   * Flow B: Multimodal image/sketch analysis when prompt is empty or on demand
   * Correction 2: Use only verified YOLO category if available, never invent one.
   */
  const handleAnalyzeSketch = async () => {
    if (!sketchUrl) {
      setGeminiError('No sketch or blueprint image available to analyze.');
      return;
    }

    if (geminiStatus === 'enhancing' || geminiStatus === 'analyzing') {
      return;
    }

    setGeminiStatus('analyzing');
    setGeminiError(null);

    try {
      let fileBlob: Blob | null = null;
      let imageBase64: string | undefined = undefined;
      let imageUrl: string | undefined = undefined;

      if (sketchUrl.startsWith('data:')) {
        fileBlob = convertDataUrlToBlob(sketchUrl);
      } else if (sketchUrl.startsWith('http://') || sketchUrl.startsWith('https://')) {
        imageUrl = sketchUrl;
      }

      const res = await geminiDesignService.analyzeDesign({
        file: fileBlob,
        imageBase64,
        imageUrl,
        userPrompt: userPromptInput.trim() || undefined,
        // Only pass YOLO context if actually verified; otherwise undefined
        yoloCategory: verifiedYoloCategory || undefined,
        yoloConfidence: verifiedYoloConfidence !== null ? verifiedYoloConfidence : undefined,
      });

      setDesignUnderstanding(res.design_understanding);
      setResolvedCategory(res.resolved_category);
      setYoloCategory(res.yolo_category || null);
      setGeminiCategory(res.gemini_category || null);
      setCategoryConflict(res.category_conflict);
      setFallbackApplied(res.fallback_applied);
      setGeminiWarnings(res.warnings || []);

      // Populate prompt with renderer prompt
      setFinalEditablePrompt(res.renderer_prompt);
      setNegativePrompt(res.negative_prompt);
      setIsPromptAnalyzedFromSketch(true);
      setIsPromptEnhanced(false);
      setUserManuallyEdited(false);
      setGeminiStatus('success');
    } catch (err: unknown) {
      setGeminiStatus('error');
      if (err instanceof ApiClientError) {
        if (err.status === 503) {
          setGeminiError('Gemini Vision analysis is currently unavailable. Standard workflow remains active.');
        } else {
          setGeminiError(err.message || 'Design understanding service error. Standard workflow remains active.');
        }
      } else if (err instanceof Error) {
        setGeminiError(err.message || 'Network error communicating with design understanding service.');
      } else {
        setGeminiError('Sketch analysis encountered an unexpected issue.');
      }
    }
  };

  /**
   * Revert prompt to original user input
   */
  const handleRevertToOriginal = () => {
    setFinalEditablePrompt(originalUserPrompt || userPromptInput);
    setUserManuallyEdited(false);
    setIsPromptEnhanced(false);
  };

  /**
   * Phase C: GEMINI -> EXISTING RENDERER INTEGRATION
   * Submits the final user-approved prompt (with explicit user intent precedence),
   * negative prompt, category, and optional structured design context to the existing
   * ControlNet + SD1.5 + LoRA renderer.
   *
   * Rules enforced:
   * 1. Final user prompt has ultimate authority (user edits preserved).
   * 2. Zero re-invocation of Gemini during render (no duplicate calls or overwrites).
   * 3. Zero alteration of ControlNet strength or inference parameters.
   * 4. 100% fallback compatibility when Gemini is not used or unavailable.
   */
  const handleRender = async () => {
    setIsRendering(true);
    setError(null);

    try {
      let fileBlob: Blob | null = null;
      if (sketchUrl.startsWith('data:')) {
        fileBlob = convertDataUrlToBlob(sketchUrl);
      }

      // Precedence: finalEditablePrompt (user approved/edited) > customPrompt > userPromptInput
      const promptToUse =
        finalEditablePrompt.trim() ||
        customPrompt.trim() ||
        userPromptInput.trim() ||
        undefined;

      const negativePromptToUse = negativePrompt.trim() || undefined;
      const categoryToUse = resolvedCategory || selectedCategory;
      const structuredDesignJson = designUnderstanding
        ? JSON.stringify(designUnderstanding)
        : undefined;

      const options: RenderOptions = {
        category: categoryToUse,
        design_id: designId,
        sketch_url: sketchUrl,
        material,
        gemstone,
        control_type: controlType,
        control_strength: controlStrength,
        steps,
        prompt: promptToUse,
        negative_prompt: negativePromptToUse,
        structured_design: structuredDesignJson,
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

  const isGeminiLoading = geminiStatus === 'analyzing' || geminiStatus === 'enhancing';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/85 backdrop-blur-md p-4 animate-in fade-in">
      <div className="bg-[#0E111A] border border-white/10 rounded-2xl w-full max-w-5xl max-h-[94vh] flex flex-col shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-7 py-4 border-b border-white/[0.07] bg-[#0A0C12]/70">
          <div className="flex items-center space-x-3">
            <div className="p-2.5 rounded-xl bg-amber-400/10 text-amber-300 border border-amber-400/20">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <h2 className="font-serif text-base font-medium text-white tracking-wide flex items-center space-x-2">
                <span>Atelier Generative Diffusion & Design Intelligence Suite</span>
                <Badge variant="gold" className="text-[9px]">
                  Gemini + ControlNet
                </Badge>
              </h2>
              <p className="text-[11px] text-slate-400 font-light">
                Multimodal design understanding and photorealistic jewellery diffusion rendering.
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
          {/* Left Column: Visual Canvas & Design Understanding Output */}
          <div className="md:col-span-6 flex flex-col space-y-4">
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
            <div className="relative w-full bg-[#080A10] rounded-2xl border border-white/[0.07] p-4 min-h-[300px] flex items-center justify-center overflow-hidden shadow-inner">
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
                  <div className="w-52 h-52 bg-[#0A0C14] border border-white/5 rounded-xl p-4 flex items-center justify-center">
                    <img
                      src={sketchUrl}
                      alt="Original Sketch Preview"
                      className="max-h-full object-contain filter invert opacity-85"
                    />
                  </div>
                  <p className="text-[11px] text-slate-400 font-light">
                    Input blueprint loaded. Use Gemini AI to understand the design or refine your prompt.
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

            {/* Structured Design Understanding Card */}
            {designUnderstanding && (
              <GeminiDesignUnderstandingCard
                understanding={designUnderstanding}
                resolvedCategory={resolvedCategory}
                yoloCategory={yoloCategory}
                geminiCategory={geminiCategory}
                categoryConflict={categoryConflict}
                fallbackApplied={fallbackApplied}
                warnings={geminiWarnings}
                isEnhancedPrompt={isPromptEnhanced}
              />
            )}
          </div>

          {/* Right Column: AI Prompting, Design Understanding & Diffusion Controls */}
          <div className="md:col-span-6 flex flex-col justify-between space-y-5">
            <div className="space-y-4 text-xs">
              {/* SECTION: Gemini Multimodal Prompting */}
              <div className="p-4 rounded-2xl bg-[#080A10] border border-white/10 space-y-3">
                <div className="flex items-center justify-between">
                  <label className="font-semibold text-slate-300 uppercase tracking-widest text-[10px] flex items-center space-x-1.5">
                    <Wand2 className="w-3.5 h-3.5 text-amber-300" />
                    <span>Describe Your Design (Optional)</span>
                  </label>
                  {isGeminiLoading && (
                    <span className="text-[10px] text-amber-300 flex items-center space-x-1">
                      <Loader2 className="w-3 h-3 animate-spin" />
                      <span>{geminiStatus === 'enhancing' ? 'Enhancing with AI...' : 'Analyzing sketch...'}</span>
                    </span>
                  )}
                </div>

                <div className="space-y-2">
                  <Textarea
                    value={userPromptInput}
                    onChange={(e) => setUserPromptInput(e.target.value)}
                    placeholder="e.g. platinum round brilliant diamond thin shank..."
                    className="min-h-[70px] text-xs"
                    disabled={isGeminiLoading}
                  />

                  {/* Gemini Action Buttons */}
                  <div className="flex items-center gap-2">
                    <Button
                      type="button"
                      variant="gold"
                      size="sm"
                      onClick={handleEnhancePrompt}
                      disabled={isGeminiLoading || !userPromptInput.trim()}
                      className="flex-1 text-xs font-semibold h-8"
                    >
                      {geminiStatus === 'enhancing' ? (
                        <>
                          <Loader2 className="w-3.5 h-3.5 mr-1.5 animate-spin" />
                          Enhancing with AI...
                        </>
                      ) : (
                        <>
                          <Sparkles className="w-3.5 h-3.5 mr-1.5" />
                          Enhance with AI
                        </>
                      )}
                    </Button>

                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={handleAnalyzeSketch}
                      disabled={isGeminiLoading || !sketchUrl}
                      className="flex-1 text-xs font-medium h-8 border-white/10 hover:border-amber-400/40 text-slate-300"
                    >
                      {geminiStatus === 'analyzing' ? (
                        <>
                          <Loader2 className="w-3.5 h-3.5 mr-1.5 animate-spin" />
                          Analyzing Sketch...
                        </>
                      ) : (
                        <>
                          <Layers className="w-3.5 h-3.5 mr-1.5 text-amber-300" />
                          Understand Sketch
                        </>
                      )}
                    </Button>
                  </div>
                </div>

                {/* Friendly Gemini Error Message (Non-blocking) */}
                {geminiError && (
                  <div className="p-2.5 rounded-xl bg-amber-500/10 border border-amber-500/20 text-[11px] text-amber-200 flex items-start space-x-2">
                    <AlertCircle className="w-3.5 h-3.5 text-amber-400 shrink-0 mt-0.5" />
                    <span className="leading-snug">{geminiError}</span>
                  </div>
                )}

                {/* Editable Final Rendering Prompt (Result from AI or User Edit) */}
                {(finalEditablePrompt || isPromptEnhanced || isPromptAnalyzedFromSketch) && (
                  <div className="pt-2 border-t border-white/5 space-y-2">
                    <div className="flex items-center justify-between text-[10px]">
                      <span className="font-semibold text-amber-300 uppercase tracking-wider flex items-center space-x-1.5">
                        <CheckCircle2 className="w-3 h-3 text-amber-300" />
                        <span>
                          {userManuallyEdited
                            ? 'Editable Final Prompt (User Modified)'
                            : isPromptEnhanced
                            ? 'Enhanced Prompt (Fully Editable)'
                            : 'Interpreted Prompt (Fully Editable)'}
                        </span>
                      </span>

                      {originalUserPrompt && (
                        <button
                          type="button"
                          onClick={handleRevertToOriginal}
                          className="text-slate-400 hover:text-white flex items-center space-x-1 text-[10px] transition cursor-pointer"
                        >
                          <Undo2 className="w-2.5 h-2.5" />
                          <span>Revert</span>
                        </button>
                      )}
                    </div>

                    <Textarea
                      value={finalEditablePrompt}
                      onChange={(e) => {
                        setFinalEditablePrompt(e.target.value);
                        setUserManuallyEdited(true);
                      }}
                      className="min-h-[80px] text-xs font-mono bg-[#0A0C14] border-amber-400/30 text-amber-100"
                    />

                    {/* Phase C: Connected to Existing Renderer */}
                    <div className="p-2 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-[10px] text-emerald-300 flex items-center justify-between">
                      <span className="flex items-center space-x-1 font-mono">
                        <CheckCircle2 className="w-3 h-3 text-emerald-400 shrink-0" />
                        <span>Active Rendering Conditioning (Phase C Connected)</span>
                      </span>
                      <Badge variant="outline" className="text-[9px] border-emerald-500/40 text-emerald-300">
                        Renderer Active
                      </Badge>
                    </div>

                    {/* Negative Prompt Collapsible Toggle */}
                    <div className="pt-1">
                      <button
                        type="button"
                        onClick={() => setShowNegativePrompt(!showNegativePrompt)}
                        className="flex items-center space-x-1.5 text-[10px] text-slate-400 hover:text-slate-200 transition cursor-pointer"
                      >
                        {showNegativePrompt ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                        <span>{showNegativePrompt ? 'Hide Negative Prompt' : 'Review Negative Prompt'}</span>
                      </button>

                      {showNegativePrompt && (
                        <div className="mt-2 space-y-1">
                          <label className="text-[10px] text-slate-400 uppercase tracking-widest font-semibold">
                            Negative Conditioning Anchors (Editable)
                          </label>
                          <Textarea
                            value={negativePrompt}
                            onChange={(e) => setNegativePrompt(e.target.value)}
                            className="min-h-[60px] text-[11px] font-mono text-slate-400 bg-[#0A0C14]"
                          />
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>

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
                      <label className="text-slate-400">Custom Lighting / Prompt Notes (Renderer Parameter)</label>
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
                disabled={isRendering || isGeminiLoading}
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

export default AiRenderModal;
