import React, { useState } from 'react';
import {
  MousePointer,
  Hand,
  Brush,
  Eraser,
  Minus,
  Square,
  Circle,
  MessageSquare,
  Palette,
  RotateCcw,
  RotateCw,
  Grid,
  Columns,
  Trash2,
  ZoomIn,
  ZoomOut,
  Maximize2,
  Download,
  Save,
  Upload,
  Loader2,
  ChevronDown
} from 'lucide-react';
import { Button } from '../ui/button';
import { Tooltip } from '../ui/tooltip';
import { Slider } from '../ui/slider';

export type CanvasTool = 'select' | 'hand' | 'brush' | 'eraser' | 'line' | 'rectangle' | 'ellipse' | 'comment';

interface CanvasToolbarProps {
  activeTool: CanvasTool;
  onSelectTool: (tool: CanvasTool) => void;
  strokeColor: string;
  onChangeStrokeColor: (color: string) => void;
  strokeWidth: number;
  onChangeStrokeWidth: (width: number) => void;
  eraserWidth: number;
  onChangeEraserWidth: (width: number) => void;
  gridEnabled: boolean;
  onToggleGrid: () => void;
  symmetryEnabled: boolean;
  onToggleSymmetry: () => void;
  canUndo: boolean;
  onUndo: () => void;
  canRedo: boolean;
  onRedo: () => void;
  onClearCanvas: () => void;
  zoom: number;
  onZoomIn: () => void;
  onZoomOut: () => void;
  onResetZoom: () => void;
  onFitZoom: () => void;
  onSave: () => void;
  isSaving: boolean;
  onExportPng: () => void;
  onTriggerUpload: () => void;
  designName?: string;
  designCategory?: string;
}

const PRESET_COLORS = [
  { name: 'Charcoal Noir', value: '#1e293b' },
  { name: '18K Yellow Gold', value: '#d4af37' },
  { name: 'Rose Gold', value: '#f43f5e' },
  { name: 'Platinum Silver', value: '#94a3b8' },
  { name: 'Colombian Emerald', value: '#059669' },
  { name: 'Royal Ceylon Sapphire', value: '#2563eb' },
  { name: 'Burmese Ruby', value: '#dc2626' },
  { name: 'Deep Onyx', value: '#0f172a' },
];

export const CanvasToolbar: React.FC<CanvasToolbarProps> = ({
  activeTool,
  onSelectTool,
  strokeColor,
  onChangeStrokeColor,
  strokeWidth,
  onChangeStrokeWidth,
  eraserWidth,
  onChangeEraserWidth,
  gridEnabled,
  onToggleGrid,
  symmetryEnabled,
  onToggleSymmetry,
  canUndo,
  onUndo,
  canRedo,
  onRedo,
  onClearCanvas,
  zoom,
  onZoomIn,
  onZoomOut,
  onResetZoom,
  onFitZoom,
  onSave,
  isSaving,
  onExportPng,
  onTriggerUpload,
  designName,
  designCategory,
}) => {
  const [showColorPopover, setShowColorPopover] = useState(false);
  const [showBrushSizePopover, setShowBrushSizePopover] = useState(false);

  return (
    <div className="w-full bg-[#0A0C12] border-b border-white/[0.07] px-3.5 py-2 flex flex-wrap items-center justify-between gap-3 text-slate-200 select-none shadow-xl">
      {/* Left Side: Creative Tools */}
      <div className="flex items-center space-x-1 sm:space-x-1.5 flex-wrap">
        {/* Selection / Cursor */}
        <Tooltip content="Selection Tool (V)">
          <Button
            variant={activeTool === 'select' ? 'gold' : 'ghost'}
            size="icon"
            className="h-8 w-8 rounded-lg"
            onClick={() => onSelectTool('select')}
            aria-label="Selection Tool"
          >
            <MousePointer className="w-4 h-4" />
          </Button>
        </Tooltip>

        {/* Hand / Pan */}
        <Tooltip content="Hand / Pan Canvas (H)">
          <Button
            variant={activeTool === 'hand' ? 'gold' : 'ghost'}
            size="icon"
            className="h-8 w-8 rounded-lg"
            onClick={() => onSelectTool('hand')}
            aria-label="Hand Tool"
          >
            <Hand className="w-4 h-4" />
          </Button>
        </Tooltip>

        <div className="w-px h-5 bg-white/10 mx-1" />

        {/* Brush */}
        <Tooltip content="Freehand Brush (B)">
          <Button
            variant={activeTool === 'brush' ? 'gold' : 'ghost'}
            size="icon"
            className="h-8 w-8 rounded-lg"
            onClick={() => onSelectTool('brush')}
            aria-label="Brush Tool"
          >
            <Brush className="w-4 h-4" />
          </Button>
        </Tooltip>

        {/* Eraser */}
        <Tooltip content="Precision Eraser (E)">
          <Button
            variant={activeTool === 'eraser' ? 'gold' : 'ghost'}
            size="icon"
            className="h-8 w-8 rounded-lg"
            onClick={() => onSelectTool('eraser')}
            aria-label="Eraser Tool"
          >
            <Eraser className="w-4 h-4" />
          </Button>
        </Tooltip>

        {/* Line */}
        <Tooltip content="Straight Line (L)">
          <Button
            variant={activeTool === 'line' ? 'gold' : 'ghost'}
            size="icon"
            className="h-8 w-8 rounded-lg"
            onClick={() => onSelectTool('line')}
            aria-label="Line Tool"
          >
            <Minus className="w-4 h-4" />
          </Button>
        </Tooltip>

        {/* Rectangle */}
        <Tooltip content="Rectangle / Mount (R)">
          <Button
            variant={activeTool === 'rectangle' ? 'gold' : 'ghost'}
            size="icon"
            className="h-8 w-8 rounded-lg"
            onClick={() => onSelectTool('rectangle')}
            aria-label="Rectangle Tool"
          >
            <Square className="w-4 h-4" />
          </Button>
        </Tooltip>

        {/* Ellipse */}
        <Tooltip content="Ellipse / Cabochon / Shank (O)">
          <Button
            variant={activeTool === 'ellipse' ? 'gold' : 'ghost'}
            size="icon"
            className="h-8 w-8 rounded-lg"
            onClick={() => onSelectTool('ellipse')}
            aria-label="Ellipse Tool"
          >
            <Circle className="w-4 h-4" />
          </Button>
        </Tooltip>

        {/* Comment / Annotation */}
        <Tooltip content="Canvas Note / Comment (C)">
          <Button
            variant={activeTool === 'comment' ? 'gold' : 'ghost'}
            size="icon"
            className="h-8 w-8 rounded-lg"
            onClick={() => onSelectTool('comment')}
            aria-label="Comment Tool"
          >
            <MessageSquare className="w-4 h-4" />
          </Button>
        </Tooltip>

        <div className="w-px h-5 bg-white/10 mx-1" />

        {/* Color Popover */}
        <div className="relative">
          <Tooltip content="Stroke Color">
            <button
              onClick={() => {
                setShowColorPopover(!showColorPopover);
                setShowBrushSizePopover(false);
              }}
              className="flex items-center space-x-1.5 px-2 py-1 h-8 rounded-lg bg-[#0E111A] border border-white/10 hover:border-amber-400/30 transition cursor-pointer"
              aria-label="Color Palette"
            >
              <div
                className="w-4 h-4 rounded-full border border-white/20 shadow-inner"
                style={{ backgroundColor: strokeColor }}
              />
              <Palette className="w-3.5 h-3.5 text-slate-400" />
            </button>
          </Tooltip>

          {showColorPopover && (
            <div className="absolute left-0 top-10 z-50 p-3.5 bg-[#0E111A] border border-white/10 rounded-xl shadow-2xl space-y-2.5 w-56 animate-in fade-in zoom-in-95 backdrop-blur-xl">
              <div className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">Jewellery Palette</div>
              <div className="grid grid-cols-4 gap-2">
                {PRESET_COLORS.map((c) => (
                  <button
                    key={c.value}
                    onClick={() => {
                      onChangeStrokeColor(c.value);
                      setShowColorPopover(false);
                    }}
                    title={c.name}
                    className={`w-8 h-8 rounded-lg border-2 transition ${
                      strokeColor === c.value ? 'border-amber-400 scale-110' : 'border-white/10 hover:scale-105'
                    }`}
                    style={{ backgroundColor: c.value }}
                  />
                ))}
              </div>
              <div className="pt-2 border-t border-white/5 flex items-center justify-between text-xs text-slate-400">
                <span>Custom:</span>
                <input
                  type="color"
                  value={strokeColor}
                  onChange={(e) => onChangeStrokeColor(e.target.value)}
                  className="w-7 h-7 bg-transparent rounded cursor-pointer"
                />
              </div>
            </div>
          )}
        </div>

        {/* Brush & Eraser Size Popover */}
        <div className="relative">
          <Tooltip content="Stroke & Eraser Width">
            <button
              onClick={() => {
                setShowBrushSizePopover(!showBrushSizePopover);
                setShowColorPopover(false);
              }}
              className="flex items-center space-x-1.5 px-2.5 py-1 h-8 rounded-lg bg-[#0E111A] border border-white/10 hover:border-amber-400/30 text-xs font-mono text-slate-300 cursor-pointer"
              aria-label="Stroke Width"
            >
              <div
                className="rounded-full bg-slate-200"
                style={{
                  width: Math.max(3, Math.min(10, activeTool === 'eraser' ? eraserWidth / 4 : strokeWidth * 2)),
                  height: Math.max(3, Math.min(10, activeTool === 'eraser' ? eraserWidth / 4 : strokeWidth * 2)),
                }}
              />
              <span>{activeTool === 'eraser' ? `${eraserWidth}px` : `${strokeWidth}px`}</span>
              <ChevronDown className="w-3 h-3 text-slate-500" />
            </button>
          </Tooltip>

          {showBrushSizePopover && (
            <div className="absolute left-0 top-10 z-50 p-4 bg-[#0E111A] border border-white/10 rounded-xl shadow-2xl space-y-3.5 w-60 animate-in fade-in zoom-in-95 backdrop-blur-xl">
              <div className="space-y-1.5">
                <div className="flex justify-between text-[11px] font-semibold text-slate-300">
                  <span>Brush Width</span>
                  <span className="font-mono text-amber-300">{strokeWidth}px</span>
                </div>
                <Slider
                  value={strokeWidth}
                  min={1}
                  max={40}
                  step={1}
                  onValueChange={onChangeStrokeWidth}
                />
              </div>

              <div className="space-y-1.5 pt-2 border-t border-white/5">
                <div className="flex justify-between text-[11px] font-semibold text-slate-300">
                  <span>Eraser Width</span>
                  <span className="font-mono text-amber-300">{eraserWidth}px</span>
                </div>
                <Slider
                  value={eraserWidth}
                  min={4}
                  max={80}
                  step={2}
                  onValueChange={onChangeEraserWidth}
                />
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Center: Design Breadcrumb */}
      <div className="hidden lg:flex items-center space-x-2 text-xs font-medium px-3.5 py-1 rounded-full bg-[#0E111A] border border-white/10 text-slate-400">
        <span className="text-amber-300 font-semibold">{designCategory || 'Jewellery'}</span>
        <span className="text-slate-600">/</span>
        <span className="text-white truncate max-w-[200px] font-serif">{designName || 'Untitled Design'}</span>
      </div>

      {/* Right Side: Canvas Aids, History & Actions */}
      <div className="flex items-center space-x-1 sm:space-x-1.5 flex-wrap">
        {/* Undo */}
        <Tooltip content="Undo (Ctrl+Z)">
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8 rounded-lg"
            onClick={onUndo}
            disabled={!canUndo}
            aria-label="Undo"
          >
            <RotateCcw className="w-4 h-4" />
          </Button>
        </Tooltip>

        {/* Redo */}
        <Tooltip content="Redo (Ctrl+Shift+Z)">
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8 rounded-lg"
            onClick={onRedo}
            disabled={!canRedo}
            aria-label="Redo"
          >
            <RotateCw className="w-4 h-4" />
          </Button>
        </Tooltip>

        <div className="w-px h-5 bg-white/10 mx-1" />

        {/* Grid Toggle */}
        <Tooltip content="Toggle Grid Guide">
          <Button
            variant={gridEnabled ? 'gold' : 'ghost'}
            size="icon"
            className="h-8 w-8 rounded-lg"
            onClick={onToggleGrid}
            aria-label="Toggle Grid"
          >
            <Grid className="w-4 h-4" />
          </Button>
        </Tooltip>

        {/* Symmetry Toggle */}
        <Tooltip content="Toggle Vertical Symmetry Mirror">
          <Button
            variant={symmetryEnabled ? 'gold' : 'ghost'}
            size="icon"
            className="h-8 w-8 rounded-lg"
            onClick={onToggleSymmetry}
            aria-label="Toggle Symmetry"
          >
            <Columns className="w-4 h-4" />
          </Button>
        </Tooltip>

        {/* Clear Canvas */}
        <Tooltip content="Clear Drawing">
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8 rounded-lg hover:text-rose-300 hover:bg-rose-500/10"
            onClick={onClearCanvas}
            aria-label="Clear Canvas"
          >
            <Trash2 className="w-4 h-4" />
          </Button>
        </Tooltip>

        <div className="w-px h-5 bg-white/10 mx-1" />

        {/* Zoom Controls */}
        <Tooltip content="Zoom Out">
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8 rounded-lg"
            onClick={onZoomOut}
            aria-label="Zoom Out"
          >
            <ZoomOut className="w-4 h-4" />
          </Button>
        </Tooltip>

        <button
          onClick={onResetZoom}
          title="Reset Zoom to 100%"
          className="px-2.5 h-8 text-[11px] font-mono text-slate-300 bg-[#0E111A] rounded-lg border border-white/10 hover:border-white/20 cursor-pointer"
        >
          {Math.round(zoom * 100)}%
        </button>

        <Tooltip content="Zoom In">
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8 rounded-lg"
            onClick={onZoomIn}
            aria-label="Zoom In"
          >
            <ZoomIn className="w-4 h-4" />
          </Button>
        </Tooltip>

        <Tooltip content="Fit Canvas (85%)">
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8 rounded-lg"
            onClick={onFitZoom}
            aria-label="Fit Canvas"
          >
            <Maximize2 className="w-4 h-4" />
          </Button>
        </Tooltip>

        <div className="w-px h-5 bg-white/10 mx-1" />

        {/* Upload Existing Reference */}
        <Tooltip content="Upload Sketch Reference">
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8 rounded-lg"
            onClick={onTriggerUpload}
            aria-label="Upload Image"
          >
            <Upload className="w-4 h-4" />
          </Button>
        </Tooltip>

        {/* Export PNG */}
        <Tooltip content="Export Clean PNG">
          <Button
            variant="secondary"
            size="sm"
            className="h-8 px-3 text-xs font-semibold bg-[#121622] hover:bg-[#181E2E] border-white/5"
            onClick={onExportPng}
            aria-label="Export PNG"
          >
            <Download className="w-3.5 h-3.5 mr-1" /> Export
          </Button>
        </Tooltip>

        {/* Save to Supabase Storage */}
        <Button
          variant="gold"
          size="sm"
          className="h-8 px-3.5 text-xs font-semibold shadow-md"
          onClick={onSave}
          disabled={isSaving}
          aria-label="Save Sketch"
        >
          {isSaving ? (
            <>
              <Loader2 className="w-3.5 h-3.5 mr-1.5 animate-spin" /> Saving...
            </>
          ) : (
            <>
              <Save className="w-3.5 h-3.5 mr-1.5" /> Save Sketch
            </>
          )}
        </Button>
      </div>
    </div>
  );
};
