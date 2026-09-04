import React, { useState, useRef } from 'react';
import {
  X,
  Cpu,
  Loader2,
  AlertCircle,
  UploadCloud,
  Info,
} from 'lucide-react';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Slider } from '../ui/slider';
import { aiComponentService } from '../../services/api/aiComponentService';
import { DetectionResult, ComponentDetection } from '../../types/aiComponent';
import { ApiClientError } from '../../services/api/client';

interface ComponentDetectionModalProps {
  isOpen: boolean;
  onClose: () => void;
  initialImageUrl?: string | null;
  designTitle?: string;
}

const CLASS_COLORS: Record<string, { stroke: string; fill: string; badge: string; text: string }> = {
  stone: { stroke: '#38bdf8', fill: 'rgba(56, 189, 248, 0.25)', badge: 'bg-sky-500/20 text-sky-300 border-sky-500/30', text: 'text-sky-400' },
  gemstone: { stroke: '#38bdf8', fill: 'rgba(56, 189, 248, 0.25)', badge: 'bg-sky-500/20 text-sky-300 border-sky-500/30', text: 'text-sky-400' },
  clasp: { stroke: '#fbbf24', fill: 'rgba(251, 191, 36, 0.25)', badge: 'bg-amber-500/20 text-amber-300 border-amber-500/30', text: 'text-amber-400' },
  hook: { stroke: '#f472b6', fill: 'rgba(244, 114, 182, 0.25)', badge: 'bg-pink-500/20 text-pink-300 border-pink-500/30', text: 'text-pink-400' },
  connector: { stroke: '#a855f7', fill: 'rgba(168, 85, 247, 0.25)', badge: 'bg-purple-500/20 text-purple-300 border-purple-500/30', text: 'text-purple-400' },
  ring_shank: { stroke: '#34d399', fill: 'rgba(52, 211, 153, 0.25)', badge: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30', text: 'text-emerald-400' },
  metal_body: { stroke: '#34d399', fill: 'rgba(52, 211, 153, 0.25)', badge: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30', text: 'text-emerald-400' },
  bead: { stroke: '#fb923c', fill: 'rgba(251, 146, 60, 0.25)', badge: 'bg-orange-500/20 text-orange-300 border-orange-500/30', text: 'text-orange-400' },
  pendant: { stroke: '#2dd4bf', fill: 'rgba(45, 212, 191, 0.25)', badge: 'bg-teal-500/20 text-teal-300 border-teal-500/30', text: 'text-teal-400' },
};

const getDefaultColor = (className: string) => {
  const normalized = className.toLowerCase().replace(/[\s-]+/g, '_');
  return (
    CLASS_COLORS[normalized] || {
      stroke: '#e2e8f0',
      fill: 'rgba(226, 232, 240, 0.2)',
      badge: 'bg-slate-700/50 text-slate-300 border-slate-600',
      text: 'text-slate-300',
    }
  );
};

export const ComponentDetectionModal: React.FC<ComponentDetectionModalProps> = ({
  isOpen,
  onClose,
  initialImageUrl,
  designTitle,
}) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(initialImageUrl || null);
  const [confidenceThreshold, setConfidenceThreshold] = useState<number>(0.25);
  const [isDetecting, setIsDetecting] = useState<boolean>(false);
  const [detectionResult, setDetectionResult] = useState<DetectionResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showMasks, setShowMasks] = useState<boolean>(true);
  const [showBoxes, setShowBoxes] = useState<boolean>(true);
  const [selectedComponent, setSelectedComponent] = useState<ComponentDetection | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  if (!isOpen) return null;

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
      setDetectionResult(null);
      setError(null);
    }
  };

  const handleRunDetection = async () => {
    setIsDetecting(true);
    setError(null);

    try {
      let fileBlob: Blob | File;
      if (selectedFile) {
        fileBlob = selectedFile;
      } else if (previewUrl) {
        const res = await fetch(previewUrl);
        if (!res.ok) throw new Error('Failed to fetch sketch image for detection.');
        fileBlob = await res.blob();
      } else {
        throw new Error('Please select or upload a jewellery sketch image first.');
      }

      const result = await aiComponentService.detectComponents(fileBlob, {
        conf: confidenceThreshold,
      });
      setDetectionResult(result);
    } catch (err: unknown) {
      if (err instanceof ApiClientError) {
        setError(err.message || 'Component detection service failed.');
      } else if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Detection failed. Please check backend AI vision service.');
      }
    } finally {
      setIsDetecting(false);
    }
  };

  // Group detections by class for summary
  const classCounts = detectionResult?.detections.reduce((acc, curr) => {
    acc[curr.class_name] = (acc[curr.class_name] || 0) + 1;
    return acc;
  }, {} as Record<string, number>) || {};

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md p-4 animate-in fade-in">
      <div className="bg-[#0b0f19] border border-slate-800 rounded-2xl w-full max-w-5xl max-h-[92vh] flex flex-col shadow-2xl overflow-hidden">
        {/* Modal Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-950/60">
          <div className="flex items-center space-x-2.5">
            <div className="p-2 rounded-xl bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
              <Cpu className="w-4 h-4" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h2 className="text-sm font-bold text-white tracking-wide">
                  YOLO Jewellery Component Detection
                </h2>
                <Badge variant="outline" className="text-[10px] text-cyan-400 border-cyan-500/30">
                  CV Instance Segmentation
                </Badge>
              </div>
              <p className="text-[11px] text-slate-400">
                Identify gemstones, clasps, mounts, connectors & shanks with pixel-precise contours
              </p>
            </div>
          </div>

          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8 text-slate-400 hover:text-white"
            onClick={onClose}
          >
            <X className="w-4 h-4" />
          </Button>
        </div>

        {/* Modal Body */}
        <div className="flex-1 overflow-y-auto p-6 grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left/Middle: Image Canvas with Detection Overlays */}
          <div className="lg:col-span-2 space-y-4 flex flex-col">
            <div className="flex items-center justify-between text-xs">
              <span className="font-semibold text-slate-300">
                Blueprint Inspector {designTitle ? `• ${designTitle}` : ''}
              </span>
              <div className="flex items-center space-x-3">
                <label className="flex items-center space-x-1.5 cursor-pointer text-slate-400 hover:text-white">
                  <input
                    type="checkbox"
                    checked={showMasks}
                    onChange={(e) => setShowMasks(e.target.checked)}
                    className="rounded bg-slate-900 border-slate-700 text-cyan-500 focus:ring-0"
                  />
                  <span>Masks</span>
                </label>
                <label className="flex items-center space-x-1.5 cursor-pointer text-slate-400 hover:text-white">
                  <input
                    type="checkbox"
                    checked={showBoxes}
                    onChange={(e) => setShowBoxes(e.target.checked)}
                    className="rounded bg-slate-900 border-slate-700 text-cyan-500 focus:ring-0"
                  />
                  <span>Bounding Boxes</span>
                </label>
              </div>
            </div>

            {/* Visual Canvas Container */}
            <div className="relative flex-1 min-h-[360px] max-h-[460px] bg-slate-950/90 rounded-2xl border border-slate-800 p-3 flex items-center justify-center overflow-hidden group">
              {previewUrl ? (
                <div className="relative max-h-full max-w-full flex items-center justify-center">
                  <img
                    src={previewUrl}
                    alt="Inspection blueprint"
                    className="max-h-[400px] object-contain rounded filter invert opacity-85"
                  />

                  {/* SVG Overlay for Detections */}
                  {detectionResult && detectionResult.detections.length > 0 && (
                    <svg
                      viewBox={`0 0 ${detectionResult.image_size[0]} ${detectionResult.image_size[1]}`}
                      className="absolute inset-0 w-full h-full pointer-events-auto"
                    >
                      {detectionResult.detections.map((det, idx) => {
                        const style = getDefaultColor(det.class_name);
                        const isSelected = selectedComponent === det;

                        // Polygon path if available
                        const polyPoints = det.mask && det.mask.length > 0
                          ? det.mask.map((p) => `${p[0]},${p[1]}`).join(' ')
                          : null;

                        const [x1, y1, x2, y2] = det.bbox;
                        const width = x2 - x1;
                        const height = y2 - y1;

                        return (
                          <g
                            key={idx}
                            onClick={() => setSelectedComponent(det)}
                            className="cursor-pointer transition-opacity hover:opacity-100"
                            style={{ opacity: selectedComponent && !isSelected ? 0.35 : 1 }}
                          >
                            {/* Mask Contour */}
                            {showMasks && polyPoints && (
                              <polygon
                                points={polyPoints}
                                fill={style.fill}
                                stroke={style.stroke}
                                strokeWidth={isSelected ? 3 : 1.5}
                              />
                            )}

                            {/* Bounding Box */}
                            {showBoxes && (
                              <rect
                                x={x1}
                                y={y1}
                                width={width}
                                height={height}
                                fill="none"
                                stroke={style.stroke}
                                strokeWidth={isSelected ? 2.5 : 1.2}
                                strokeDasharray={isSelected ? 'none' : '4,2'}
                              />
                            )}

                            {/* Text label */}
                            <text
                              x={x1}
                              y={Math.max(12, y1 - 4)}
                              fill={style.stroke}
                              fontSize={Math.max(10, Math.min(14, width / 6))}
                              fontWeight="bold"
                              fontFamily="sans-serif"
                            >
                              {det.class_name} ({Math.round(det.confidence * 100)}%)
                            </text>
                          </g>
                        );
                      })}
                    </svg>
                  )}
                </div>
              ) : (
                <div className="text-center p-8 space-y-3">
                  <UploadCloud className="w-10 h-10 text-slate-600 mx-auto" />
                  <p className="text-xs text-slate-400">No sketch selected for component detection</p>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => fileInputRef.current?.click()}
                    className="border-slate-700 text-xs"
                  >
                    Upload Sketch Image
                  </Button>
                </div>
              )}
            </div>

            {/* Error Message */}
            {error && (
              <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center space-x-2">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{error}</span>
              </div>
            )}
          </div>

          {/* Right Sidebar: Controls, Telemetry & Results */}
          <div className="space-y-5 flex flex-col justify-between">
            <div className="space-y-4">
              {/* Image Input Selection */}
              <div className="space-y-2">
                <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block">
                  1. Source Image
                </span>
                <input
                  type="file"
                  ref={fileInputRef}
                  onChange={handleFileChange}
                  accept="image/png,image/jpeg,image/webp"
                  className="hidden"
                />
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => fileInputRef.current?.click()}
                  className="w-full text-xs font-semibold justify-center border border-slate-800"
                >
                  <UploadCloud className="w-3.5 h-3.5 mr-1.5 text-cyan-400" />
                  {selectedFile ? selectedFile.name : 'Upload New Sketch File'}
                </Button>
              </div>

              {/* Confidence Slider */}
              <div className="space-y-2">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-bold text-slate-400 uppercase tracking-wider">
                    2. Confidence Threshold
                  </span>
                  <span className="font-mono font-bold text-cyan-400">
                    {Math.round(confidenceThreshold * 100)}%
                  </span>
                </div>
                <Slider
                  value={confidenceThreshold}
                  min={0.05}
                  max={0.95}
                  step={0.05}
                  onValueChange={(val) => setConfidenceThreshold(val)}
                  className="py-1"
                />
              </div>

              {/* Detection Trigger Button */}
              <Button
                variant="gold"
                size="sm"
                onClick={handleRunDetection}
                disabled={isDetecting || !previewUrl}
                className="w-full font-bold text-xs bg-gradient-to-r from-cyan-500 via-sky-400 to-cyan-500 text-slate-950 hover:brightness-110 shadow-md"
              >
                {isDetecting ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 mr-1.5 animate-spin" />
                    Running YOLO Inference...
                  </>
                ) : (
                  <>
                    <Cpu className="w-3.5 h-3.5 mr-1.5" />
                    Detect Components (YOLO11)
                  </>
                )}
              </Button>

              {/* Results & Summary */}
              {detectionResult ? (
                <div className="space-y-3 pt-2">
                  <div className="flex items-center justify-between text-xs pb-2 border-b border-slate-800">
                    <span className="font-bold text-white uppercase tracking-wider">
                      Detected Classes ({detectionResult.total_detections})
                    </span>
                    <Badge variant="outline" className="text-[10px] text-cyan-400 font-mono">
                      {detectionResult.inference_time_ms} ms
                    </Badge>
                  </div>

                  {/* Class Badge Grid */}
                  <div className="flex flex-wrap gap-1.5">
                    {Object.entries(classCounts).map(([cls, count]) => {
                      const color = getDefaultColor(cls);
                      return (
                        <div
                          key={cls}
                          className={`px-2.5 py-1 rounded-lg border text-xs font-semibold flex items-center gap-1.5 ${color.badge}`}
                        >
                          <span>{cls}</span>
                          <span className="text-[10px] px-1.5 py-0.2 rounded bg-black/40 font-mono">
                            {count}
                          </span>
                        </div>
                      );
                    })}
                  </div>

                  {/* Granular Detections List */}
                  <div className="space-y-1.5 max-h-[160px] overflow-y-auto pr-1 pt-1">
                    {detectionResult.detections.map((det, idx) => {
                      const color = getDefaultColor(det.class_name);
                      const isSelected = selectedComponent === det;
                      return (
                        <div
                          key={idx}
                          onClick={() => setSelectedComponent(isSelected ? null : det)}
                          className={`p-2 rounded-lg border transition-all cursor-pointer flex items-center justify-between text-xs ${
                            isSelected
                              ? 'bg-cyan-500/10 border-cyan-500/60'
                              : 'bg-slate-950/40 border-slate-800/80 hover:border-slate-700'
                          }`}
                        >
                          <span className={`font-semibold capitalize ${color.text}`}>
                            {det.class_name} #{idx + 1}
                          </span>
                          <span className="font-mono text-[10px] text-slate-400">
                            {Math.round(det.confidence * 100)}% conf
                          </span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              ) : (
                <div className="p-4 rounded-xl bg-slate-950/40 border border-slate-800 text-xs text-slate-400 space-y-1">
                  <div className="font-semibold text-slate-300 flex items-center gap-1">
                    <Info className="w-3.5 h-3.5 text-cyan-400" />
                    Model Taxonomy
                  </div>
                  <p className="text-[11px] leading-relaxed">
                    Identifies stones, hook clasps, connectors, ring shanks, beads, and pendants for automated BOM & cost predictions.
                  </p>
                </div>
              )}
            </div>

            {/* Bottom Hardware Stamp */}
            <div className="text-[10px] text-slate-500 font-mono border-t border-slate-800/80 pt-3 flex items-center justify-between">
              <span>Device: {detectionResult?.device_used || 'Local PyTorch / CUDA'}</span>
              <span>Model: YOLO11-seg</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
