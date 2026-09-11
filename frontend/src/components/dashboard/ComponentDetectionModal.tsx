import React, { useState, useRef } from 'react';
import {
  X,
  Cpu,
  Loader2,
  AlertCircle,
  UploadCloud,
  Info,
  Scan,
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
  stone: { stroke: '#F1DE9D', fill: 'rgba(241, 222, 157, 0.25)', badge: 'bg-amber-400/15 text-amber-200 border-amber-400/30', text: 'text-amber-200' },
  gemstone: { stroke: '#F1DE9D', fill: 'rgba(241, 222, 157, 0.25)', badge: 'bg-amber-400/15 text-amber-200 border-amber-400/30', text: 'text-amber-200' },
  clasp: { stroke: '#E2E8F0', fill: 'rgba(226, 232, 240, 0.25)', badge: 'bg-white/10 text-slate-200 border-white/20', text: 'text-slate-200' },
  hook: { stroke: '#E2E8F0', fill: 'rgba(226, 232, 240, 0.25)', badge: 'bg-white/10 text-slate-200 border-white/20', text: 'text-slate-200' },
  connector: { stroke: '#D4AF37', fill: 'rgba(212, 175, 55, 0.25)', badge: 'bg-amber-500/15 text-amber-300 border-amber-500/30', text: 'text-amber-300' },
  ring_shank: { stroke: '#E8C868', fill: 'rgba(232, 200, 104, 0.25)', badge: 'bg-yellow-400/15 text-yellow-200 border-yellow-400/30', text: 'text-yellow-200' },
  metal_body: { stroke: '#E8C868', fill: 'rgba(232, 200, 104, 0.25)', badge: 'bg-yellow-400/15 text-yellow-200 border-yellow-400/30', text: 'text-yellow-200' },
  bead: { stroke: '#CBD5E1', fill: 'rgba(203, 213, 225, 0.25)', badge: 'bg-slate-400/15 text-slate-200 border-slate-400/30', text: 'text-slate-200' },
  pendant: { stroke: '#F9F1D8', fill: 'rgba(249, 241, 216, 0.25)', badge: 'bg-amber-200/15 text-amber-100 border-amber-200/30', text: 'text-amber-100' },
};

const getDefaultColor = (className: string) => {
  const normalized = className.toLowerCase().replace(/[\s-]+/g, '_');
  return (
    CLASS_COLORS[normalized] || {
      stroke: '#D4AF37',
      fill: 'rgba(212, 175, 55, 0.2)',
      badge: 'bg-amber-400/10 text-amber-200 border-amber-400/20',
      text: 'text-amber-200',
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

  const classCounts = detectionResult?.detections.reduce((acc, curr) => {
    acc[curr.class_name] = (acc[curr.class_name] || 0) + 1;
    return acc;
  }, {} as Record<string, number>) || {};

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/85 backdrop-blur-md p-4 animate-in fade-in">
      <div className="bg-[#0E111A] border border-white/10 rounded-2xl w-full max-w-5xl max-h-[92vh] flex flex-col shadow-2xl overflow-hidden">
        {/* Modal Header */}
        <div className="flex items-center justify-between px-7 py-5 border-b border-white/[0.07] bg-[#0A0C12]/70">
          <div className="flex items-center space-x-3">
            <div className="p-2.5 rounded-xl bg-amber-400/10 text-amber-300 border border-amber-400/20">
              <Scan className="w-4 h-4" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h2 className="font-serif text-base font-medium text-white tracking-wide">
                  YOLO Jewellery Component Scanner
                </h2>
                <Badge variant="gold" className="text-[9px]">
                  CV Instance Segmentation
                </Badge>
              </div>
              <p className="text-[11px] text-slate-400 font-light">
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
        <div className="flex-1 overflow-y-auto p-7 grid grid-cols-1 lg:grid-cols-3 gap-7">
          {/* Left/Middle: Image Canvas with Detection Overlays */}
          <div className="lg:col-span-2 space-y-4 flex flex-col">
            <div className="flex items-center justify-between text-xs">
              <span className="font-medium text-slate-300">
                Blueprint Inspector {designTitle ? `• ${designTitle}` : ''}
              </span>
              <div className="flex items-center space-x-3">
                <label className="flex items-center space-x-1.5 cursor-pointer text-slate-400 hover:text-white text-[11px]">
                  <input
                    type="checkbox"
                    checked={showMasks}
                    onChange={(e) => setShowMasks(e.target.checked)}
                    className="rounded bg-[#080A10] border-white/20 text-amber-400 focus:ring-0"
                  />
                  <span>Masks</span>
                </label>
                <label className="flex items-center space-x-1.5 cursor-pointer text-slate-400 hover:text-white text-[11px]">
                  <input
                    type="checkbox"
                    checked={showBoxes}
                    onChange={(e) => setShowBoxes(e.target.checked)}
                    className="rounded bg-[#080A10] border-white/20 text-amber-400 focus:ring-0"
                  />
                  <span>Bounding Boxes</span>
                </label>
              </div>
            </div>

            {/* Visual Canvas Container */}
            <div className="relative flex-1 min-h-[380px] max-h-[480px] bg-[#080A10] rounded-2xl border border-white/[0.07] p-4 flex items-center justify-center overflow-hidden group">
              {previewUrl ? (
                <div className="relative max-h-full max-w-full flex items-center justify-center">
                  <img
                    src={previewUrl}
                    alt="Inspection blueprint"
                    className="max-h-[420px] object-contain rounded-lg filter invert opacity-85"
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
                  <p className="text-xs text-slate-400 font-light">No blueprint selected for component scanning</p>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => fileInputRef.current?.click()}
                    className="border-white/10 text-xs"
                  >
                    Upload Sketch Blueprint
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
                <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-widest block">
                  1. Blueprint Source
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
                  className="w-full text-xs font-medium justify-center bg-[#121622] hover:bg-[#181E2E] border-white/5"
                >
                  <UploadCloud className="w-3.5 h-3.5 mr-1.5 text-amber-300" />
                  {selectedFile ? selectedFile.name : 'Upload New Blueprint'}
                </Button>
              </div>

              {/* Confidence Slider */}
              <div className="space-y-2">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-widest">
                    2. Confidence Threshold
                  </span>
                  <span className="font-mono font-semibold text-amber-300">
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
                className="w-full font-semibold text-xs shadow-md shadow-amber-500/10"
              >
                {isDetecting ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 mr-1.5 animate-spin" />
                    Scanning Blueprint...
                  </>
                ) : (
                  <>
                    <Cpu className="w-3.5 h-3.5 mr-1.5" />
                    Detect Components (YOLO V2)
                  </>
                )}
              </Button>

              {/* Results & Summary */}
              {detectionResult ? (
                <div className="space-y-3 pt-2">
                  <div className="flex items-center justify-between text-xs pb-2 border-b border-white/5">
                    <span className="text-[11px] font-semibold text-white uppercase tracking-wider">
                      Detected ({detectionResult.total_detections})
                    </span>
                    <Badge variant="outline" className="text-[10px] text-amber-300 font-mono">
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
                          className={`px-2.5 py-1 rounded-lg border text-xs font-medium flex items-center gap-1.5 ${color.badge}`}
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
                          className={`p-2.5 rounded-xl border transition-all duration-150 cursor-pointer flex items-center justify-between text-xs ${
                            isSelected
                              ? 'bg-amber-400/15 border-amber-400/50'
                              : 'bg-[#080A10] border-white/5 hover:border-white/15'
                          }`}
                        >
                          <span className={`font-medium capitalize ${color.text}`}>
                            {det.class_name} #{idx + 1}
                          </span>
                          <span className="font-mono text-[10px] text-slate-400 font-light">
                            {Math.round(det.confidence * 100)}%
                          </span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              ) : (
                <div className="p-4 rounded-xl bg-[#080A10] border border-white/5 text-xs text-slate-400 space-y-1 font-light">
                  <div className="font-medium text-slate-300 flex items-center gap-1.5">
                    <Info className="w-3.5 h-3.5 text-amber-300" />
                    Atelier Vision Taxonomy
                  </div>
                  <p className="text-[11px] leading-relaxed">
                    Identifies stones, hook clasps, connectors, ring shanks, beads, and mounts for automated bill-of-materials and cost estimation.
                  </p>
                </div>
              )}
            </div>

            {/* Bottom Hardware Stamp */}
            <div className="text-[10px] text-slate-500 font-mono border-t border-white/5 pt-3 flex items-center justify-between">
              <span>Device: {detectionResult?.device_used || 'Local PyTorch / CUDA'}</span>
              <span>Model: YOLO V2 Production</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
