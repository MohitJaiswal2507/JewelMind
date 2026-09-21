import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  ArrowLeft,
  Loader2,
  AlertCircle,
  CheckCircle2,
  Sparkles,
  Layers,
  FileText,
  Image as ImageIcon,
  Brush,
  Split,
  Download,
  Save,
  ExternalLink,
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { CanvasToolbar, CanvasTool } from '../components/canvas/CanvasToolbar';
import { DrawingCanvas, DrawingCanvasHandle } from '../components/canvas/DrawingCanvas';
import { ClearCanvasModal } from '../components/canvas/ClearCanvasModal';
import { DesignChatPanel } from '../components/chat/DesignChatPanel';
import { designService } from '../services/api/designService';
import { aiRenderingService } from '../services/api/aiRenderingService';
import { ApiClientError } from '../services/api/client';
import { Design } from '../types/design';
import { DesignState } from '../types/ai';

interface DesignWorkspacePageProps {
  designId: string;
  onBack: () => void;
}

type WorkspaceMode = 'doodle' | 'text' | 'image';
type WorkspaceView = 'canvas' | 'comparison' | 'render';

export const DesignWorkspacePage: React.FC<DesignWorkspacePageProps> = ({
  designId,
  onBack,
}) => {
  const canvasRef = useRef<DrawingCanvasHandle | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const imageUploadRef = useRef<HTMLInputElement | null>(null);

  // Design state
  const [design, setDesign] = useState<Design | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Workspace modes & views
  const [workspaceMode, setWorkspaceMode] = useState<WorkspaceMode>('doodle');
  const [workspaceView, setWorkspaceView] = useState<WorkspaceView>('canvas');
  const [splitPosition, setSplitPosition] = useState<number>(50);

  // Conversational Design State
  const [designState, setDesignState] = useState<DesignState>({
    category: null,
    primary_metal: null,
    metal_finish: 'polished',
    accent_metal: null,
    has_gemstones: null,
    gemstone_type: null,
    gemstone_cut: null,
    gemstone_color: null,
    gemstone_count: null,
    setting_type: null,
    accent_stones: null,
    style_aesthetic: 'modern luxury',
    silhouette: null,
    engraving_or_details: null,
    current_prompt: '',
    renderer_prompt: null,
    negative_prompt: null,
  });

  // Creative Tools state
  const [activeTool, setActiveTool] = useState<CanvasTool>('brush');
  const [strokeColor, setStrokeColor] = useState<string>('#1e293b');
  const [strokeWidth, setStrokeWidth] = useState<number>(4);
  const [eraserWidth, setEraserWidth] = useState<number>(24);
  const [gridEnabled, setGridEnabled] = useState<boolean>(false);
  const [symmetryEnabled, setSymmetryEnabled] = useState<boolean>(false);

  // View state
  const [zoom, setZoom] = useState<number>(1);
  const [panOffset, setPanOffset] = useState<{ x: number; y: number }>({ x: 0, y: 0 });

  // History state
  const [canUndo, setCanUndo] = useState<boolean>(false);
  const [canRedo, setCanRedo] = useState<boolean>(false);

  // Modals & UI Feedback
  const [isClearModalOpen, setIsClearModalOpen] = useState<boolean>(false);
  const [isSaving, setIsSaving] = useState<boolean>(false);
  const [isRendering, setIsRendering] = useState<boolean>(false);
  const [isCopilotCollapsed, setIsCopilotCollapsed] = useState<boolean>(false);
  const [feedback, setFeedback] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  // Render state & Iterative Redesign
  const [renderedImageUrl, setRenderedImageUrl] = useState<string | null>(null);
  const [previousRenderUrl, setPreviousRenderUrl] = useState<string | null>(null);
  const [uploadedImageUrl, setUploadedImageUrl] = useState<string | null>(null);
  const [uploadedImageFile, setUploadedImageFile] = useState<File | null>(null);
  const [canvasInfluence, setCanvasInfluence] = useState<number>(60);

  const fetchDesign = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await designService.getDesign(designId);
      setDesign(data);
      if (data.rendered_image_url) {
        setRenderedImageUrl(data.rendered_image_url);
        setWorkspaceView('comparison');
      }

      // Initialize clean design state for loaded design
      setDesignState({
        category: data.category || null,
        primary_metal: null,
        metal_finish: 'polished',
        accent_metal: null,
        has_gemstones: null,
        gemstone_type: null,
        gemstone_cut: null,
        gemstone_color: null,
        gemstone_count: null,
        setting_type: null,
        accent_stones: null,
        style_aesthetic: 'modern luxury',
        silhouette: null,
        engraving_or_details: null,
        current_prompt: data.ai_prompt || '',
        renderer_prompt: null,
        negative_prompt: null,
      });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to load design workspace.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDesign();
  }, [designId]);

  useEffect(() => {
    if (feedback) {
      const t = setTimeout(() => setFeedback(null), 3500);
      return () => clearTimeout(t);
    }
  }, [feedback]);

  // Zoom handlers
  const handleZoomIn = () => setZoom((prev) => Math.min(3, Math.round((prev + 0.15) * 100) / 100));
  const handleZoomOut = () => setZoom((prev) => Math.max(0.4, Math.round((prev - 0.15) * 100) / 100));
  const handleResetZoom = () => {
    setZoom(1);
    setPanOffset({ x: 0, y: 0 });
  };
  const handleFitZoom = () => {
    setZoom(0.85);
    setPanOffset({ x: 0, y: 0 });
  };

  // Undo / Redo
  const handleUndo = useCallback(() => {
    canvasRef.current?.undo();
  }, []);

  const handleRedo = useCallback(() => {
    canvasRef.current?.redo();
  }, []);

  // Save to Supabase Storage & Database
  const handleSaveSketch = async () => {
    if (!design) return;
    setIsSaving(true);
    try {
      let updatedDesign = design;
      if (workspaceMode === 'doodle' && canvasRef.current) {
        const blob = await canvasRef.current.exportPngBlob();
        if (blob) {
          const cleanName = design.name.toLowerCase().replace(/[^a-z0-9]/g, '_');
          const file = new File([blob], `${cleanName}_sketch.png`, { type: 'image/png' });
          updatedDesign = await designService.uploadSketch(design.id, file);
        }
      }

      if (designState.current_prompt !== design.ai_prompt) {
        updatedDesign = await designService.updateDesign(design.id, {
          ai_prompt: designState.current_prompt,
          category: designState.category as any,
        });
      }

      setDesign(updatedDesign);
      setFeedback({ type: 'success', message: 'Design workspace & prompt saved successfully.' });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to save design.';
      setFeedback({ type: 'error', message: msg });
    } finally {
      setIsSaving(false);
    }
  };

  // Handle Photo/CAD file selection for Mode 3
  const handlePhotoUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploadedImageFile(file);
    const objectUrl = URL.createObjectURL(file);
    setUploadedImageUrl(objectUrl);
    setFeedback({ type: 'success', message: `Loaded blueprint photo "${file.name}".` });
  };

  // Central Generative Render Execution
  const handleExecuteRender = async () => {
    if (!design) return;
    setIsRendering(true);
    try {
      // Store current render as previous render for iterative comparison & Canny conditioning
      if (renderedImageUrl) {
        setPreviousRenderUrl(renderedImageUrl);
      }

      const categoryValue = (designState.category || design.category || 'other_jewellery').toLowerCase();
      const materialValue = designState.primary_metal || undefined;
      const gemstoneValue = designState.has_gemstones === false ? undefined : (designState.gemstone_type || undefined);
      const activePrompt = designState.renderer_prompt || designState.current_prompt || design.ai_prompt || `${materialValue ? materialValue + ' ' : ''}${categoryValue}`;
      const controlStrengthValue = Math.max(0.0, Math.min(1.0, canvasInfluence / 100));

      let res;
      if (workspaceMode === 'text') {
        // Mode 1: Pure Text -> Render
        res = await aiRenderingService.renderSketch(null, {
          category: categoryValue,
          source_blueprint_category: design.category.toLowerCase(),
          prompt: activePrompt,
          negative_prompt: designState.negative_prompt || undefined,
          material: materialValue,
          gemstone: gemstoneValue,
          control_strength: previousRenderUrl ? 0.65 : 0.0,
          control_type: previousRenderUrl ? 'canny' : 'lineart',
          previous_render_url: previousRenderUrl || undefined,
          design_id: design.id,
        });
      } else if (workspaceMode === 'doodle') {
        // Mode 2: Canvas Doodle -> Render
        let blob: Blob | null = null;
        if (canvasRef.current) {
          blob = await canvasRef.current.exportPngBlob();
        }
        res = await aiRenderingService.renderSketch(blob, {
          category: categoryValue,
          source_blueprint_category: design.category.toLowerCase(),
          prompt: activePrompt,
          negative_prompt: designState.negative_prompt || undefined,
          material: materialValue,
          gemstone: gemstoneValue,
          control_strength: controlStrengthValue,
          control_type: 'lineart',
          design_id: design.id,
        });
      } else {
        // Mode 3: Image Blueprint -> Render
        res = await aiRenderingService.renderSketch(uploadedImageFile, {
          category: categoryValue,
          source_blueprint_category: design.category.toLowerCase(),
          prompt: activePrompt,
          negative_prompt: designState.negative_prompt || undefined,
          material: materialValue,
          gemstone: gemstoneValue,
          control_strength: controlStrengthValue,
          control_type: 'canny',
          sketch_url: uploadedImageUrl || design.sketch_image_url || undefined,
          design_id: design.id,
        });
      }

      if (res && res.output_url) {
        if (renderedImageUrl && renderedImageUrl !== res.output_url) {
          setPreviousRenderUrl(renderedImageUrl);
        }
        setRenderedImageUrl(res.output_url);
        setWorkspaceView('comparison');
        setFeedback({ type: 'success', message: 'Photorealistic fine jewellery render synthesized successfully!' });
      }
    } catch (err: unknown) {
      if (err instanceof ApiClientError) {
        if (err.status === 422) {
          setFeedback({ type: 'error', message: `Validation Error: ${err.message}` });
        } else if (err.status === 409) {
          setFeedback({ type: 'error', message: `Category Conflict: ${err.message}` });
        } else if (err.status === 503) {
          setFeedback({ type: 'error', message: 'AI Rendering worker is offline. Start the local RTX 4060 worker.' });
        } else if (err.status === 507) {
          setFeedback({ type: 'error', message: 'GPU out of memory. Try reducing render steps or image resolution.' });
        } else {
          setFeedback({ type: 'error', message: err.message || 'AI Rendering failed.' });
        }
      } else {
        const msg = err instanceof Error ? err.message : 'AI Rendering failed.';
        setFeedback({ type: 'error', message: msg });
      }
    } finally {
      setIsRendering(false);
    }
  };

  // Export clean PNG
  const handleExportPng = async () => {
    if (!canvasRef.current || !design) return;
    try {
      const blob = await canvasRef.current.exportPngBlob();
      if (!blob) throw new Error('Canvas export failed.');

      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      const filename = `${design.name.toLowerCase().replace(/[^a-z0-9]+/g, '-')}-blueprint.png`;
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      setFeedback({ type: 'success', message: `Exported clean blueprint as ${filename}` });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to export sketch.';
      setFeedback({ type: 'error', message: msg });
    }
  };

  // Global Workspace Keyboard Shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const tag = (e.target as HTMLElement)?.tagName?.toLowerCase();
      if (tag === 'input' || tag === 'textarea') return;

      if ((e.ctrlKey || e.metaKey) && e.key === 'z') {
        e.preventDefault();
        if (e.shiftKey) handleRedo();
        else handleUndo();
      } else if ((e.ctrlKey || e.metaKey) && e.key === 'y') {
        e.preventDefault();
        handleRedo();
      } else if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        e.preventDefault();
        handleSaveSketch();
      } else if (e.key === 'b' || e.key === 'B') {
        setActiveTool('brush');
      } else if (e.key === 'e' || e.key === 'E') {
        setActiveTool('eraser');
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleUndo, handleRedo, handleSaveSketch]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-[calc(100vh-80px)] space-y-4 text-slate-400">
        <Loader2 className="w-8 h-8 animate-spin text-amber-300" />
        <span className="text-xs font-light">Initializing Canva AI Jewellery Atelier...</span>
      </div>
    );
  }

  if (error || !design) {
    return (
      <div className="max-w-xl mx-auto py-16 space-y-4">
        <Button variant="outline" size="sm" onClick={onBack} className="border-white/10 text-xs">
          <ArrowLeft className="w-4 h-4 mr-2" /> Back to Catalogue
        </Button>
        <div className="p-5 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center space-x-2.5">
          <AlertCircle className="w-5 h-5 shrink-0" />
          <span>{error || 'Design record not found.'}</span>
        </div>
      </div>
    );
  }

  const activeBlueprintUrl = uploadedImageUrl || design.sketch_image_url;

  return (
    <div className="fixed inset-0 top-[72px] z-40 bg-[#08090D] flex flex-col overflow-hidden">
      {/* Hidden File Picker for Canvas Reference */}
      <input
        ref={fileInputRef}
        type="file"
        accept="image/png,image/jpeg,image/webp"
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file && canvasRef.current) {
            canvasRef.current.loadFile(file);
            setFeedback({ type: 'success', message: `Loaded reference "${file.name}" onto canvas.` });
          }
        }}
        className="hidden"
      />

      {/* Hidden File Picker for Image Blueprint Mode */}
      <input
        ref={imageUploadRef}
        type="file"
        accept="image/png,image/jpeg,image/webp"
        onChange={handlePhotoUpload}
        className="hidden"
      />

      {/* Canva Top Unified Header Bar */}
      <div className="h-14 bg-[#0A0C12] border-b border-white/[0.08] px-4 sm:px-6 flex items-center justify-between z-30 select-none">
        {/* Left: Navigation & Design Info */}
        <div className="flex items-center space-x-3">
          <Button
            variant="ghost"
            size="sm"
            onClick={onBack}
            className="text-slate-300 hover:text-white px-2 text-xs"
            title="Exit Canva Workspace"
          >
            <ArrowLeft className="w-4 h-4 mr-1.5" />
            Back
          </Button>

          <div className="h-4 w-[1px] bg-white/10" />

          <div className="flex items-center space-x-2">
            <span className="font-serif text-sm font-medium text-white truncate max-w-[140px] sm:max-w-[220px]">
              {design.name}
            </span>
            <Badge variant="gold" className="text-[10px] py-0 px-2">
              {designState.category}
            </Badge>
          </div>
        </div>

        {/* Center: Creation Mode Selector Tabs */}
        <div className="hidden md:flex items-center bg-[#121622] p-1 rounded-xl border border-white/5 space-x-1">
          <button
            onClick={() => setWorkspaceMode('doodle')}
            className={`flex items-center space-x-1.5 px-3 py-1 rounded-lg text-xs font-medium transition cursor-pointer ${
              workspaceMode === 'doodle'
                ? 'bg-amber-400 text-slate-950 font-semibold shadow'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <Brush className="w-3.5 h-3.5" />
            <span>Sketch Canvas</span>
          </button>
          <button
            onClick={() => setWorkspaceMode('text')}
            className={`flex items-center space-x-1.5 px-3 py-1 rounded-lg text-xs font-medium transition cursor-pointer ${
              workspaceMode === 'text'
                ? 'bg-amber-400 text-slate-950 font-semibold shadow'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <FileText className="w-3.5 h-3.5" />
            <span>Text → Render</span>
          </button>
          <button
            onClick={() => setWorkspaceMode('image')}
            className={`flex items-center space-x-1.5 px-3 py-1 rounded-lg text-xs font-medium transition cursor-pointer ${
              workspaceMode === 'image'
                ? 'bg-amber-400 text-slate-950 font-semibold shadow'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <ImageIcon className="w-3.5 h-3.5" />
            <span>Image Blueprint</span>
          </button>
        </div>

        {/* Right: Render Controls & View Toggles */}
        <div className="flex items-center space-x-2.5">
          {renderedImageUrl && (
            <div className="hidden lg:flex items-center bg-[#121622] p-1 rounded-xl border border-white/5 space-x-1 text-xs">
              <button
                onClick={() => setWorkspaceView('canvas')}
                className={`px-2.5 py-1 rounded-lg font-medium transition cursor-pointer ${
                  workspaceView === 'canvas' ? 'bg-white/10 text-white' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Canvas
              </button>
              <button
                onClick={() => setWorkspaceView('comparison')}
                className={`px-2.5 py-1 rounded-lg font-medium transition cursor-pointer flex items-center space-x-1 ${
                  workspaceView === 'comparison' ? 'bg-white/10 text-white' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                <Split className="w-3 h-3" />
                <span>Comparison</span>
              </button>
              <button
                onClick={() => setWorkspaceView('render')}
                className={`px-2.5 py-1 rounded-lg font-medium transition cursor-pointer ${
                  workspaceView === 'render' ? 'bg-white/10 text-white' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Render Only
              </button>
            </div>
          )}

          <Button
            variant="outline"
            size="sm"
            onClick={handleSaveSketch}
            disabled={isSaving}
            className="text-xs border-white/10 hover:bg-white/5 text-slate-300"
          >
            {isSaving ? <Loader2 className="w-3.5 h-3.5 animate-spin mr-1" /> : <Save className="w-3.5 h-3.5 mr-1" />}
            Save
          </Button>

          <Button
            variant="gold"
            size="sm"
            onClick={handleExecuteRender}
            disabled={isRendering}
            className="text-xs font-semibold shadow-lg shadow-amber-500/10 flex items-center space-x-1.5"
          >
            {isRendering ? (
              <>
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                <span>Rendering...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-3.5 h-3.5" />
                <span>Render Visuals</span>
              </>
            )}
          </Button>
        </div>
      </div>

      {/* Secondary Doodle Toolbar (Active only in Sketch Canvas Mode & Canvas view) */}
      {workspaceMode === 'doodle' && workspaceView === 'canvas' && (
        <CanvasToolbar
          activeTool={activeTool}
          onSelectTool={setActiveTool}
          strokeColor={strokeColor}
          onChangeStrokeColor={setStrokeColor}
          strokeWidth={strokeWidth}
          onChangeStrokeWidth={setStrokeWidth}
          eraserWidth={eraserWidth}
          onChangeEraserWidth={setEraserWidth}
          gridEnabled={gridEnabled}
          onToggleGrid={() => setGridEnabled(!gridEnabled)}
          symmetryEnabled={symmetryEnabled}
          onToggleSymmetry={() => setSymmetryEnabled(!symmetryEnabled)}
          canUndo={canUndo}
          onUndo={handleUndo}
          canRedo={canRedo}
          onRedo={handleRedo}
          onClearCanvas={() => setIsClearModalOpen(true)}
          zoom={zoom}
          onZoomIn={handleZoomIn}
          onZoomOut={handleZoomOut}
          onResetZoom={handleResetZoom}
          onFitZoom={handleFitZoom}
          onSave={handleSaveSketch}
          isSaving={isSaving}
          onExportPng={handleExportPng}
          onTriggerUpload={() => fileInputRef.current?.click()}
          designName={design.name}
          designCategory={design.category}
        />
      )}

      {/* Toast Feedback */}
      {feedback && (
        <div
          className={`absolute top-20 left-1/2 -translate-x-1/2 z-50 px-4 py-2.5 rounded-xl text-xs font-semibold shadow-2xl flex items-center space-x-2 animate-in fade-in slide-in-from-top-2 duration-150 ${
            feedback.type === 'success'
              ? 'bg-amber-400 text-slate-950 border border-amber-300'
              : 'bg-rose-600 text-white border border-rose-400'
          }`}
        >
          {feedback.type === 'success' ? <CheckCircle2 className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
          <span>{feedback.message}</span>
        </div>
      )}

      {/* Main Workspace Body */}
      <div className="flex-1 flex flex-col md:flex-row overflow-hidden relative">
        {/* Central Workspace Stage */}
        <div className="flex-1 h-full relative overflow-hidden bg-[#08090E] flex flex-col">
          {/* Comparison View (Split Slider) */}
          {workspaceView === 'comparison' && renderedImageUrl && (
            <div className="flex-1 h-full relative overflow-hidden flex flex-col items-center justify-center p-4">
              <div className="relative w-full max-w-4xl h-[80vh] max-h-[600px] bg-[#0E111A] rounded-2xl border border-white/10 overflow-hidden shadow-2xl select-none">
                {/* Left Side: Original Blueprint or Previous Render */}
                <div className="absolute inset-0 flex items-center justify-center bg-[#08090D]">
                  {previousRenderUrl ? (
                    <img
                      src={previousRenderUrl}
                      alt="Previous Render Iteration"
                      className="w-full h-full object-contain"
                    />
                  ) : activeBlueprintUrl ? (
                    <img
                      src={activeBlueprintUrl}
                      alt="Source Blueprint"
                      className="w-full h-full object-contain filter invert opacity-80"
                    />
                  ) : (
                    <div className="text-center p-6 space-y-2 text-slate-500">
                      <Layers className="w-8 h-8 mx-auto" />
                      <div className="text-xs">Original Conceptual Prompt</div>
                    </div>
                  )}
                  <div className="absolute top-4 left-4 px-2.5 py-1 rounded-lg bg-black/60 backdrop-blur-md text-[11px] text-slate-300 font-mono border border-white/10">
                    {previousRenderUrl ? 'Previous Iteration' : 'Source Blueprint'}
                  </div>
                </div>

                {/* Right Side: Rendered Image (Clipped by splitPosition) */}
                <div
                  className="absolute inset-0 overflow-hidden"
                  style={{ clipPath: `polygon(${splitPosition}% 0, 100% 0, 100% 100%, ${splitPosition}% 100%)` }}
                >
                  <img
                    src={renderedImageUrl}
                    alt="AI Photorealistic Render"
                    className="w-full h-full object-contain bg-[#0E111A]"
                  />
                  <div className="absolute top-4 right-4 px-2.5 py-1 rounded-lg bg-amber-400/90 text-slate-950 font-semibold text-[11px] shadow">
                    ✨ Generative AI Output
                  </div>
                </div>

                {/* Split Divider Handle */}
                <div
                  className="absolute top-0 bottom-0 w-1 bg-amber-400 shadow-xl cursor-ew-resize flex items-center justify-center"
                  style={{ left: `${splitPosition}%` }}
                >
                  <div className="w-7 h-7 rounded-full bg-amber-400 text-slate-950 flex items-center justify-center shadow-lg text-[10px] font-bold">
                    ⇆
                  </div>
                </div>

                {/* Interactive Slider Input */}
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={splitPosition}
                  onChange={(e) => setSplitPosition(Number(e.target.value))}
                  className="absolute inset-0 opacity-0 cursor-ew-resize w-full h-full"
                />
              </div>

              {/* Slider instruction */}
              <div className="text-[11px] text-slate-500 mt-2 flex items-center space-x-2">
                <span>Drag slider to compare Blueprint ↔ Photorealistic AI synthesis</span>
              </div>
            </div>
          )}

          {/* Full Render View */}
          {workspaceView === 'render' && renderedImageUrl && (
            <div className="flex-1 h-full flex flex-col items-center justify-center p-6 bg-[#08090D] overflow-auto">
              <div className="relative max-w-3xl max-h-[80vh] rounded-2xl overflow-hidden border border-white/10 shadow-2xl bg-[#0E111A]">
                <img
                  src={renderedImageUrl}
                  alt="High-Res Fine Jewellery Render"
                  className="w-full h-full object-contain rounded-2xl"
                />
                <div className="absolute bottom-4 right-4 flex items-center space-x-2">
                  <a
                    href={renderedImageUrl}
                    download={`${design.name}-render.png`}
                    target="_blank"
                    rel="noreferrer"
                  >
                    <Button variant="gold" size="sm" className="text-xs font-semibold shadow">
                      <Download className="w-3.5 h-3.5 mr-1.5" /> Download 4K Asset
                    </Button>
                  </a>
                </div>
              </div>
            </div>
          )}

          {/* Canvas & Mode Editors (When in Canvas View) */}
          {workspaceView === 'canvas' && (
            <>
              {/* Mode 1: Doodle Sketch Canvas */}
              {workspaceMode === 'doodle' && (
                <DrawingCanvas
                  ref={canvasRef}
                  activeTool={activeTool}
                  strokeColor={strokeColor}
                  strokeWidth={strokeWidth}
                  eraserWidth={eraserWidth}
                  gridEnabled={gridEnabled}
                  symmetryEnabled={symmetryEnabled}
                  zoom={zoom}
                  panOffset={panOffset}
                  onPanChange={setPanOffset}
                  onHistoryChange={(undoable, redoable) => {
                    setCanUndo(undoable);
                    setCanRedo(redoable);
                  }}
                  initialImageUrl={design.sketch_image_url}
                />
              )}

              {/* Mode 2: Pure Text -> Render Studio */}
              {workspaceMode === 'text' && (
                <div className="flex-1 h-full flex flex-col items-center justify-center p-8 space-y-6 max-w-2xl mx-auto text-center">
                  <div className="p-4 rounded-3xl bg-amber-400/10 text-amber-300 border border-amber-400/20 shadow-xl">
                    <Sparkles className="w-10 h-10" />
                  </div>
                  <div className="space-y-2">
                    <h2 className="font-serif text-2xl text-white font-medium">Text-to-Fine-Jewellery Studio</h2>
                    <p className="text-xs text-slate-400 leading-relaxed font-light max-w-md mx-auto">
                      Generate bespoke fine jewellery directly from natural language. No drawing required. The atelier diffusion pipeline synthesizes photorealistic specular gold, platinum, and gemstones based strictly on your prompt specifications.
                    </p>
                  </div>

                  {renderedImageUrl ? (
                    <div className="relative w-72 h-72 rounded-2xl overflow-hidden border border-white/10 shadow-2xl bg-[#0E111A]">
                      <img
                        src={renderedImageUrl}
                        alt="Current Render"
                        className="w-full h-full object-contain rounded-2xl"
                      />
                      <div className="absolute bottom-2 right-2">
                        <Button
                          variant="secondary"
                          size="sm"
                          onClick={() => setWorkspaceView('render')}
                          className="text-[10px] h-7 bg-black/60 backdrop-blur-md"
                        >
                          <ExternalLink className="w-3 h-3 mr-1" /> View Full
                        </Button>
                      </div>
                    </div>
                  ) : (
                    <div className="p-6 rounded-2xl bg-[#0E111A]/90 border border-white/10 w-full text-left space-y-3">
                      <div className="flex items-center justify-between text-xs text-slate-400">
                        <span className="font-medium text-slate-200">Active Design State</span>
                        <Badge variant="gold" className="text-[10px]">{designState.category}</Badge>
                      </div>
                      <div className="text-xs text-slate-300 font-mono bg-[#08090D] p-3.5 rounded-xl border border-white/5 leading-relaxed">
                        {designState.current_prompt || 'Use the AI Copilot on the right to instruct metals, gemstones, or aesthetic styles.'}
                      </div>
                      <Button
                        variant="gold"
                        size="sm"
                        onClick={handleExecuteRender}
                        disabled={isRendering}
                        className="w-full text-xs font-semibold shadow"
                      >
                        {isRendering ? <Loader2 className="w-3.5 h-3.5 animate-spin mr-1.5" /> : <Sparkles className="w-3.5 h-3.5 mr-1.5" />}
                        Generate Visuals from Text
                      </Button>
                    </div>
                  )}
                </div>
              )}

              {/* Mode 3: Image Blueprint Mode */}
              {workspaceMode === 'image' && (
                <div className="flex-1 h-full flex flex-col items-center justify-center p-8 space-y-6 max-w-xl mx-auto text-center">
                  <div className="p-4 rounded-3xl bg-amber-400/10 text-amber-300 border border-amber-400/20 shadow-xl">
                    <ImageIcon className="w-10 h-10" />
                  </div>
                  <div className="space-y-2">
                    <h2 className="font-serif text-2xl text-white font-medium">CAD Blueprint & Photo Conditioning</h2>
                    <p className="text-xs text-slate-400 leading-relaxed font-light">
                      Upload a CAD drawing, artisan sketch, or jewellery photo. ControlNet will condition on the geometry with Canny edge structural synthesis.
                    </p>
                  </div>

                  {activeBlueprintUrl ? (
                    <div className="relative w-80 max-h-72 rounded-2xl overflow-hidden border border-white/10 shadow-2xl bg-[#0E111A] p-2">
                      <img
                        src={activeBlueprintUrl}
                        alt="Loaded Blueprint"
                        className="w-full max-h-64 object-contain rounded-xl filter invert opacity-90"
                      />
                      <div className="absolute top-4 right-4">
                        <Button
                          variant="secondary"
                          size="sm"
                          onClick={() => imageUploadRef.current?.click()}
                          className="text-[10px] h-7 bg-black/70 backdrop-blur-md text-amber-300"
                        >
                          Replace
                        </Button>
                      </div>
                    </div>
                  ) : (
                    <div
                      onClick={() => imageUploadRef.current?.click()}
                      className="w-full p-8 border-2 border-dashed border-white/10 hover:border-amber-400/50 rounded-2xl bg-[#0E111A]/60 cursor-pointer transition flex flex-col items-center space-y-3"
                    >
                      <ImageIcon className="w-8 h-8 text-amber-400" />
                      <div className="text-xs font-semibold text-white">Click to Upload Blueprint Photo</div>
                      <div className="text-[11px] text-slate-500">Supports PNG, JPG, WEBP CAD blueprints</div>
                    </div>
                  )}
                </div>
              )}
            </>
          )}
        </div>

        {/* Right-Side Conversational Copilot & State Panel */}
        <div
          className={`${
            isCopilotCollapsed ? 'w-12' : 'w-full md:w-[320px] lg:w-[380px]'
          } h-[360px] md:h-full shrink-0 shadow-2xl border-t md:border-t-0 border-white/[0.07] transition-all duration-300 relative z-20`}
        >
          <DesignChatPanel
            initialPrompt={designState.current_prompt}
            onPromptChange={(newPrompt) => {
              setDesignState((prev) => ({ ...prev, current_prompt: newPrompt }));
            }}
            designState={designState}
            onDesignStateChange={setDesignState}
            canvasInfluence={canvasInfluence}
            onCanvasInfluenceChange={setCanvasInfluence}
            designName={design.name}
            designCategory={design.category}
            onTriggerRender={handleExecuteRender}
            isRendering={isRendering}
            isCollapsed={isCopilotCollapsed}
            onToggleCollapse={() => setIsCopilotCollapsed(!isCopilotCollapsed)}
          />
        </div>
      </div>

      {/* Clear Canvas Confirmation Modal */}
      <ClearCanvasModal
        isOpen={isClearModalOpen}
        onClose={() => setIsClearModalOpen(false)}
        onConfirm={() => {
          canvasRef.current?.clear();
          setFeedback({ type: 'success', message: 'Canvas cleared. You can use Undo (Ctrl+Z) to restore.' });
        }}
      />
    </div>
  );
};

export default DesignWorkspacePage;
