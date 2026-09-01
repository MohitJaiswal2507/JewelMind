import React, { useRef, useEffect, useState, useCallback, useImperativeHandle, forwardRef } from 'react';
import { CanvasTool } from './CanvasToolbar';

export interface DrawingCanvasHandle {
  undo: () => void;
  redo: () => void;
  canUndo: () => boolean;
  canRedo: () => boolean;
  clear: () => void;
  exportPngBlob: () => Promise<Blob | null>;
  loadFromUrl: (url: string) => Promise<void>;
  loadFile: (file: File) => Promise<void>;
}

interface DrawingCanvasProps {
  activeTool: CanvasTool;
  strokeColor: string;
  strokeWidth: number;
  eraserWidth: number;
  gridEnabled: boolean;
  symmetryEnabled: boolean;
  zoom: number;
  panOffset: { x: number; y: number };
  onPanChange: (newOffset: { x: number; y: number }) => void;
  onHistoryChange: (canUndo: boolean, canRedo: boolean) => void;
  initialImageUrl?: string | null;
}

const CANVAS_WIDTH = 1400;
const CANVAS_HEIGHT = 1000;
const MAX_HISTORY = 30;

export const DrawingCanvas = forwardRef<DrawingCanvasHandle, DrawingCanvasProps>(({
  activeTool,
  strokeColor,
  strokeWidth,
  eraserWidth,
  gridEnabled,
  symmetryEnabled,
  zoom,
  panOffset,
  onPanChange,
  onHistoryChange,
  initialImageUrl,
}, ref) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const overlayCanvasRef = useRef<HTMLCanvasElement | null>(null);

  // Drawing state
  const isDrawingRef = useRef<boolean>(false);
  const startPosRef = useRef<{ x: number; y: number }>({ x: 0, y: 0 });
  const lastPosRef = useRef<{ x: number; y: number }>({ x: 0, y: 0 });

  // Pan interaction
  const isPanningRef = useRef<boolean>(false);
  const panStartRef = useRef<{ x: number; y: number }>({ x: 0, y: 0 });

  // History stack
  const undoStackRef = useRef<ImageData[]>([]);
  const redoStackRef = useRef<ImageData[]>([]);

  // Annotations
  const [annotations, setAnnotations] = useState<Array<{ x: number; y: number; text: string }>>([]);

  const notifyHistory = useCallback(() => {
    onHistoryChange(undoStackRef.current.length > 0, redoStackRef.current.length > 0);
  }, [onHistoryChange]);

  const saveHistorySnapshot = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
    undoStackRef.current.push(imageData);
    if (undoStackRef.current.length > MAX_HISTORY) {
      undoStackRef.current.shift();
    }
    // Clear redo stack on new action
    redoStackRef.current = [];
    notifyHistory();
  }, [notifyHistory]);

  const undo = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas || undoStackRef.current.length === 0) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const currentSnapshot = ctx.getImageData(0, 0, canvas.width, canvas.height);
    redoStackRef.current.push(currentSnapshot);

    const previousSnapshot = undoStackRef.current.pop();
    if (previousSnapshot) {
      ctx.putImageData(previousSnapshot, 0, 0);
    }
    notifyHistory();
  }, [notifyHistory]);

  const redo = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas || redoStackRef.current.length === 0) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const currentSnapshot = ctx.getImageData(0, 0, canvas.width, canvas.height);
    undoStackRef.current.push(currentSnapshot);

    const nextSnapshot = redoStackRef.current.pop();
    if (nextSnapshot) {
      ctx.putImageData(nextSnapshot, 0, 0);
    }
    notifyHistory();
  }, [notifyHistory]);

  const clear = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    saveHistorySnapshot();
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    setAnnotations([]);
  }, [saveHistorySnapshot]);

  const loadFromUrl = useCallback(async (url: string) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const img = new Image();
    img.crossOrigin = 'anonymous';
    img.onload = () => {
      ctx.fillStyle = '#ffffff';
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      // Scale to fit canvas nicely while maintaining aspect ratio
      const hRatio = canvas.width / img.width;
      const vRatio = canvas.height / img.height;
      const ratio = Math.min(hRatio, vRatio, 1);
      const centerShiftX = (canvas.width - img.width * ratio) / 2;
      const centerShiftY = (canvas.height - img.height * ratio) / 2;

      ctx.drawImage(img, 0, 0, img.width, img.height, centerShiftX, centerShiftY, img.width * ratio, img.height * ratio);
      saveHistorySnapshot();
    };
    img.src = url;
  }, [saveHistorySnapshot]);

  const loadFile = useCallback(async (file: File) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      if (typeof e.target?.result === 'string') {
        loadFromUrl(e.target.result);
      }
    };
    reader.readAsDataURL(file);
  }, [loadFromUrl]);

  const exportPngBlob = useCallback(async (): Promise<Blob | null> => {
    const canvas = canvasRef.current;
    if (!canvas) return null;
    return new Promise((resolve) => {
      canvas.toBlob((blob) => resolve(blob), 'image/png');
    });
  }, []);

  useImperativeHandle(ref, () => ({
    undo,
    redo,
    canUndo: () => undoStackRef.current.length > 0,
    canRedo: () => redoStackRef.current.length > 0,
    clear,
    exportPngBlob,
    loadFromUrl,
    loadFile,
  }), [undo, redo, clear, exportPngBlob, loadFromUrl, loadFile]);

  // Canvas Initialization
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    canvas.width = CANVAS_WIDTH;
    canvas.height = CANVAS_HEIGHT;

    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT);

    if (initialImageUrl) {
      loadFromUrl(initialImageUrl);
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Overlay Canvas sizing (for rubberband previews, grid, symmetry)
  useEffect(() => {
    const overlay = overlayCanvasRef.current;
    if (!overlay) return;
    overlay.width = CANVAS_WIDTH;
    overlay.height = CANVAS_HEIGHT;
  }, []);

  // Draw Grid and Symmetry onto Overlay Canvas
  const renderOverlayGuides = useCallback(() => {
    const overlay = overlayCanvasRef.current;
    if (!overlay) return;
    const ctx = overlay.getContext('2d');
    if (!ctx) return;

    ctx.clearRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT);

    // 1. Grid
    if (gridEnabled) {
      ctx.save();
      ctx.strokeStyle = 'rgba(203, 213, 225, 0.4)';
      ctx.lineWidth = 1;
      const gridSize = 40;

      ctx.beginPath();
      for (let x = 0; x < CANVAS_WIDTH; x += gridSize) {
        ctx.moveTo(x, 0);
        ctx.lineTo(x, CANVAS_HEIGHT);
      }
      for (let y = 0; y < CANVAS_HEIGHT; y += gridSize) {
        ctx.moveTo(0, y);
        ctx.lineTo(CANVAS_WIDTH, y);
      }
      ctx.stroke();
      ctx.restore();
    }

    // 2. Symmetry Guide Line
    if (symmetryEnabled) {
      ctx.save();
      ctx.strokeStyle = 'rgba(217, 119, 6, 0.7)';
      ctx.lineWidth = 1.5;
      ctx.setLineDash([6, 6]);
      const centerX = CANVAS_WIDTH / 2;

      ctx.beginPath();
      ctx.moveTo(centerX, 0);
      ctx.lineTo(centerX, CANVAS_HEIGHT);
      ctx.stroke();

      // Top & bottom indicator diamonds
      ctx.setLineDash([]);
      ctx.fillStyle = '#d97706';
      ctx.beginPath();
      ctx.arc(centerX, 15, 4, 0, Math.PI * 2);
      ctx.arc(centerX, CANVAS_HEIGHT - 15, 4, 0, Math.PI * 2);
      ctx.fill();
      ctx.restore();
    }
  }, [gridEnabled, symmetryEnabled]);

  useEffect(() => {
    renderOverlayGuides();
  }, [renderOverlayGuides]);

  // Coordinate conversion taking into account zoom, pan, and canvas rect
  const getCanvasCoordinates = (e: React.MouseEvent<HTMLDivElement>): { x: number; y: number } | null => {
    const canvas = canvasRef.current;
    if (!canvas) return null;
    const rect = canvas.getBoundingClientRect();
    const scaleX = CANVAS_WIDTH / rect.width;
    const scaleY = CANVAS_HEIGHT / rect.height;

    const clientX = e.clientX - rect.left;
    const clientY = e.clientY - rect.top;

    return {
      x: clientX * scaleX,
      y: clientY * scaleY,
    };
  };

  const handleMouseDown = (e: React.MouseEvent<HTMLDivElement>) => {
    if (e.button !== 0) return; // Left click only

    // Hand tool handles panning
    if (activeTool === 'hand' || e.altKey) {
      isPanningRef.current = true;
      panStartRef.current = { x: e.clientX - panOffset.x, y: e.clientY - panOffset.y };
      return;
    }

    const pos = getCanvasCoordinates(e);
    if (!pos) return;

    if (activeTool === 'comment') {
      const note = prompt('Enter design annotation note:');
      if (note && note.trim()) {
        setAnnotations((prev) => [...prev, { x: pos.x, y: pos.y, text: note.trim() }]);
      }
      return;
    }

    isDrawingRef.current = true;
    startPosRef.current = pos;
    lastPosRef.current = pos;

    // Save snapshot before drawing
    saveHistorySnapshot();

    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    if (activeTool === 'brush') {
      ctx.beginPath();
      ctx.arc(pos.x, pos.y, strokeWidth / 2, 0, Math.PI * 2);
      ctx.fillStyle = strokeColor;
      ctx.fill();

      if (symmetryEnabled) {
        const mirrorX = CANVAS_WIDTH - pos.x;
        ctx.beginPath();
        ctx.arc(mirrorX, pos.y, strokeWidth / 2, 0, Math.PI * 2);
        ctx.fillStyle = strokeColor;
        ctx.fill();
      }
    } else if (activeTool === 'eraser') {
      ctx.save();
      ctx.fillStyle = '#ffffff';
      ctx.beginPath();
      ctx.arc(pos.x, pos.y, eraserWidth / 2, 0, Math.PI * 2);
      ctx.fill();
      ctx.restore();
    }
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    // Handle Pan
    if (isPanningRef.current) {
      const newX = e.clientX - panStartRef.current.x;
      const newY = e.clientY - panStartRef.current.y;
      onPanChange({ x: newX, y: newY });
      return;
    }

    if (!isDrawingRef.current) return;

    const pos = getCanvasCoordinates(e);
    if (!pos) return;

    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const overlay = overlayCanvasRef.current;
    const overlayCtx = overlay?.getContext('2d');

    if (activeTool === 'brush') {
      ctx.strokeStyle = strokeColor;
      ctx.lineWidth = strokeWidth;
      ctx.lineCap = 'round';
      ctx.lineJoin = 'round';

      ctx.beginPath();
      ctx.moveTo(lastPosRef.current.x, lastPosRef.current.y);
      ctx.lineTo(pos.x, pos.y);
      ctx.stroke();

      if (symmetryEnabled) {
        const mirrorLastX = CANVAS_WIDTH - lastPosRef.current.x;
        const mirrorX = CANVAS_WIDTH - pos.x;
        ctx.beginPath();
        ctx.moveTo(mirrorLastX, lastPosRef.current.y);
        ctx.lineTo(mirrorX, pos.y);
        ctx.stroke();
      }

      lastPosRef.current = pos;
    } else if (activeTool === 'eraser') {
      ctx.strokeStyle = '#ffffff';
      ctx.lineWidth = eraserWidth;
      ctx.lineCap = 'round';
      ctx.lineJoin = 'round';

      ctx.beginPath();
      ctx.moveTo(lastPosRef.current.x, lastPosRef.current.y);
      ctx.lineTo(pos.x, pos.y);
      ctx.stroke();

      lastPosRef.current = pos;
    } else if (['line', 'rectangle', 'ellipse'].includes(activeTool) && overlayCtx) {
      // Rubberband shape preview on overlay canvas
      renderOverlayGuides();

      overlayCtx.save();
      overlayCtx.strokeStyle = strokeColor;
      overlayCtx.lineWidth = strokeWidth;
      overlayCtx.lineCap = 'round';
      overlayCtx.lineJoin = 'round';

      const start = startPosRef.current;

      if (activeTool === 'line') {
        overlayCtx.beginPath();
        overlayCtx.moveTo(start.x, start.y);
        overlayCtx.lineTo(pos.x, pos.y);
        overlayCtx.stroke();

        if (symmetryEnabled) {
          overlayCtx.beginPath();
          overlayCtx.moveTo(CANVAS_WIDTH - start.x, start.y);
          overlayCtx.lineTo(CANVAS_WIDTH - pos.x, pos.y);
          overlayCtx.stroke();
        }
      } else if (activeTool === 'rectangle') {
        const w = pos.x - start.x;
        const h = pos.y - start.y;
        overlayCtx.strokeRect(start.x, start.y, w, h);

        if (symmetryEnabled) {
          overlayCtx.strokeRect(CANVAS_WIDTH - start.x - w, start.y, w, h);
        }
      } else if (activeTool === 'ellipse') {
        const radiusX = Math.abs(pos.x - start.x) / 2;
        const radiusY = Math.abs(pos.y - start.y) / 2;
        const centerX = (start.x + pos.x) / 2;
        const centerY = (start.y + pos.y) / 2;

        overlayCtx.beginPath();
        overlayCtx.ellipse(centerX, centerY, radiusX, radiusY, 0, 0, Math.PI * 2);
        overlayCtx.stroke();

        if (symmetryEnabled) {
          overlayCtx.beginPath();
          overlayCtx.ellipse(CANVAS_WIDTH - centerX, centerY, radiusX, radiusY, 0, 0, Math.PI * 2);
          overlayCtx.stroke();
        }
      }
      overlayCtx.restore();
    }
  };

  const handleMouseUp = (e: React.MouseEvent<HTMLDivElement>) => {
    if (isPanningRef.current) {
      isPanningRef.current = false;
      return;
    }

    if (!isDrawingRef.current) return;
    isDrawingRef.current = false;

    const pos = getCanvasCoordinates(e);
    if (!pos) return;

    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const start = startPosRef.current;

    // Rasterize geometric shapes permanently onto main drawing canvas
    if (['line', 'rectangle', 'ellipse'].includes(activeTool)) {
      ctx.save();
      ctx.strokeStyle = strokeColor;
      ctx.lineWidth = strokeWidth;
      ctx.lineCap = 'round';
      ctx.lineJoin = 'round';

      if (activeTool === 'line') {
        ctx.beginPath();
        ctx.moveTo(start.x, start.y);
        ctx.lineTo(pos.x, pos.y);
        ctx.stroke();

        if (symmetryEnabled) {
          ctx.beginPath();
          ctx.moveTo(CANVAS_WIDTH - start.x, start.y);
          ctx.lineTo(CANVAS_WIDTH - pos.x, pos.y);
          ctx.stroke();
        }
      } else if (activeTool === 'rectangle') {
        const w = pos.x - start.x;
        const h = pos.y - start.y;
        ctx.strokeRect(start.x, start.y, w, h);

        if (symmetryEnabled) {
          ctx.strokeRect(CANVAS_WIDTH - start.x - w, start.y, w, h);
        }
      } else if (activeTool === 'ellipse') {
        const radiusX = Math.abs(pos.x - start.x) / 2;
        const radiusY = Math.abs(pos.y - start.y) / 2;
        const centerX = (start.x + pos.x) / 2;
        const centerY = (start.y + pos.y) / 2;

        ctx.beginPath();
        ctx.ellipse(centerX, centerY, radiusX, radiusY, 0, 0, Math.PI * 2);
        ctx.stroke();

        if (symmetryEnabled) {
          ctx.beginPath();
          ctx.ellipse(CANVAS_WIDTH - centerX, centerY, radiusX, radiusY, 0, 0, Math.PI * 2);
          ctx.stroke();
        }
      }
      ctx.restore();
      renderOverlayGuides();
    }
  };

  const getCursorStyle = () => {
    switch (activeTool) {
      case 'hand':
        return isPanningRef.current ? 'cursor-grabbing' : 'cursor-grab';
      case 'brush':
        return 'cursor-crosshair';
      case 'eraser':
        return 'cursor-cell';
      case 'line':
      case 'rectangle':
      case 'ellipse':
        return 'cursor-crosshair';
      case 'comment':
        return 'cursor-help';
      case 'select':
      default:
        return 'cursor-default';
    }
  };

  return (
    <div
      className={`relative w-full h-full bg-[#050811] overflow-hidden flex items-center justify-center select-none ${getCursorStyle()}`}
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
    >
      {/* Pan & Zoom Canvas Wrapper */}
      <div
        className="relative shadow-2xl rounded-2xl overflow-hidden border border-slate-700/60 transition-transform duration-75"
        style={{
          width: `${CANVAS_WIDTH}px`,
          height: `${CANVAS_HEIGHT}px`,
          transform: `translate(${panOffset.x}px, ${panOffset.y}px) scale(${zoom})`,
          transformOrigin: 'center center',
        }}
      >
        {/* Main Drawing Canvas */}
        <canvas
          ref={canvasRef}
          className="absolute inset-0 w-full h-full bg-white block"
        />

        {/* Dynamic Overlay Canvas (Guides, Symmetry, Shape Previews) */}
        <canvas
          ref={overlayCanvasRef}
          className="absolute inset-0 w-full h-full pointer-events-none block"
        />

        {/* Annotations Marker Overlay */}
        {annotations.map((ann, idx) => (
          <div
            key={idx}
            className="absolute z-20 -translate-x-1/2 -translate-y-1/2 p-2 bg-amber-500 text-slate-950 font-bold text-xs rounded-lg shadow-xl border border-amber-300 max-w-[200px] animate-in zoom-in-75"
            style={{ left: `${ann.x}px`, top: `${ann.y}px` }}
          >
            <div className="text-[10px] uppercase tracking-wider text-amber-950">Note #{idx + 1}</div>
            <div className="font-normal text-slate-900">{ann.text}</div>
          </div>
        ))}
      </div>
    </div>
  );
});

DrawingCanvas.displayName = 'DrawingCanvas';
