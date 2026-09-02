import React, { useState, useEffect, useRef, useCallback } from 'react';
import { ArrowLeft, Loader2, AlertCircle, CheckCircle2 } from 'lucide-react';
import { Button } from '../components/ui/button';
import { CanvasToolbar, CanvasTool } from '../components/canvas/CanvasToolbar';
import { DrawingCanvas, DrawingCanvasHandle } from '../components/canvas/DrawingCanvas';
import { ClearCanvasModal } from '../components/canvas/ClearCanvasModal';
import { DesignChatPanel } from '../components/chat/DesignChatPanel';
import { designService } from '../services/api/designService';
import { Design } from '../types/design';

interface DesignWorkspacePageProps {
  designId: string;
  onBack: () => void;
}

export const DesignWorkspacePage: React.FC<DesignWorkspacePageProps> = ({
  designId,
  onBack,
}) => {
  const canvasRef = useRef<DrawingCanvasHandle | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  // Design state
  const [design, setDesign] = useState<Design | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

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
  const [feedback, setFeedback] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  // AI & Chat state
  const [prompt, setPrompt] = useState<string>('');
  const [canvasInfluence, setCanvasInfluence] = useState<number>(60);

  const fetchDesign = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await designService.getDesign(designId);
      setDesign(data);
      setPrompt(data.ai_prompt || '');
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
    if (!design || !canvasRef.current) return;
    setIsSaving(true);
    try {
      const blob = await canvasRef.current.exportPngBlob();
      if (!blob) throw new Error('Could not serialize canvas artwork.');

      const cleanName = design.name.toLowerCase().replace(/[^a-z0-9]/g, '_');
      const file = new File([blob], `${cleanName}_sketch.png`, { type: 'image/png' });

      // Upload to Supabase Storage
      const updatedDesign = await designService.uploadSketch(design.id, file);

      // Save prompt if updated
      if (prompt !== design.ai_prompt) {
        await designService.updateDesign(design.id, { ai_prompt: prompt });
      }

      setDesign(updatedDesign);
      setFeedback({ type: 'success', message: 'Sketch blueprint saved to Supabase Storage successfully.' });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to save sketch.';
      setFeedback({ type: 'error', message: msg });
    } finally {
      setIsSaving(false);
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
      const filename = `${design.name.toLowerCase().replace(/[^a-z0-9]+/g, '-')}-sketch.png`;
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      setFeedback({ type: 'success', message: `Exported clean sketch as ${filename}` });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to export sketch.';
      setFeedback({ type: 'error', message: msg });
    }
  };

  // File Upload Reference Handler
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file && canvasRef.current) {
      canvasRef.current.loadFile(file);
      setFeedback({ type: 'success', message: `Loaded reference image "${file.name}" onto canvas.` });
    }
  };

  // Global Workspace Keyboard Shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ignore if typing inside text input/textarea
      const tag = (e.target as HTMLElement)?.tagName?.toLowerCase();
      if (tag === 'input' || tag === 'textarea') return;

      if ((e.ctrlKey || e.metaKey) && e.key === 'z') {
        e.preventDefault();
        if (e.shiftKey) {
          handleRedo();
        } else {
          handleUndo();
        }
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
      } else if (e.key === 'h' || e.key === 'H') {
        setActiveTool('hand');
      } else if (e.key === 'v' || e.key === 'V') {
        setActiveTool('select');
      } else if (e.key === 'l' || e.key === 'L') {
        setActiveTool('line');
      } else if (e.key === 'r' || e.key === 'R') {
        setActiveTool('rectangle');
      } else if (e.key === 'o' || e.key === 'O') {
        setActiveTool('ellipse');
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleUndo, handleRedo, handleSaveSketch]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-[calc(100vh-80px)] space-y-4 text-slate-400">
        <Loader2 className="w-8 h-8 animate-spin text-amber-400" />
        <span className="text-xs">Initializing jewellery design canvas...</span>
      </div>
    );
  }

  if (error || !design) {
    return (
      <div className="max-w-xl mx-auto py-16 space-y-4">
        <Button variant="outline" size="sm" onClick={onBack}>
          <ArrowLeft className="w-4 h-4 mr-2" /> Back to Designs
        </Button>
        <div className="p-5 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center space-x-2.5">
          <AlertCircle className="w-5 h-5 shrink-0" />
          <span>{error || 'Design record not found.'}</span>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 top-[65px] z-40 bg-[#050811] flex flex-col overflow-hidden">
      {/* Hidden File Picker */}
      <input
        ref={fileInputRef}
        type="file"
        accept="image/png,image/jpeg,image/webp"
        onChange={handleFileChange}
        className="hidden"
      />

      {/* Top Creative Toolbar */}
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

      {/* Feedback Toast */}
      {feedback && (
        <div
          className={`absolute top-14 left-1/2 -translate-x-1/2 z-50 px-4 py-2 rounded-xl text-xs font-semibold shadow-2xl flex items-center space-x-2 animate-in fade-in slide-in-from-top-2 duration-150 ${
            feedback.type === 'success'
              ? 'bg-emerald-500 text-slate-950 border border-emerald-300'
              : 'bg-rose-600 text-white border border-rose-400'
          }`}
        >
          {feedback.type === 'success' ? <CheckCircle2 className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
          <span>{feedback.message}</span>
        </div>
      )}

      {/* Main Workspace Body: Split between Canvas (75%) and Chat Panel (25%) */}
      <div className="flex-1 flex flex-col md:flex-row overflow-hidden relative">
        {/* Drawing Surface Area */}
        <div className="flex-1 h-full relative overflow-hidden">
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
        </div>

        {/* Right-Side Chat & Diffusion Studio Panel */}
        <div className="w-full md:w-[320px] lg:w-[380px] h-[340px] md:h-full shrink-0 shadow-2xl border-t md:border-t-0 border-slate-800">
          <DesignChatPanel
            initialPrompt={prompt}
            onPromptChange={setPrompt}
            canvasInfluence={canvasInfluence}
            onCanvasInfluenceChange={setCanvasInfluence}
            designName={design.name}
            designCategory={design.category}
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
