import React, { useState, useEffect } from 'react';
import { X, Loader2, Sparkles, AlertCircle } from 'lucide-react';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Textarea } from '../ui/textarea';
import { 
  Design, 
  DesignCategory, 
  DesignStatus, 
  DESIGN_CATEGORIES, 
  DESIGN_STATUSES,
  DesignCreateInput,
  DesignUpdateInput 
} from '../../types/design';

interface DesignModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: DesignCreateInput | DesignUpdateInput) => Promise<void>;
  initialDesign?: Design | null;
}

export const DesignModal: React.FC<DesignModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  initialDesign,
}) => {
  const isEditing = Boolean(initialDesign);

  const [name, setName] = useState('');
  const [category, setCategory] = useState<DesignCategory>('Ring');
  const [status, setStatus] = useState<DesignStatus>('draft');
  const [description, setDescription] = useState('');
  const [sketchImageUrl, setSketchImageUrl] = useState('');
  const [aiPrompt, setAiPrompt] = useState('');

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (initialDesign) {
      setName(initialDesign.name || '');
      setCategory(initialDesign.category || 'Ring');
      setStatus(initialDesign.status || 'draft');
      setDescription(initialDesign.description || '');
      setSketchImageUrl(initialDesign.sketch_image_url || '');
      setAiPrompt(initialDesign.ai_prompt || '');
    } else {
      setName('');
      setCategory('Ring');
      setStatus('draft');
      setDescription('');
      setSketchImageUrl('');
      setAiPrompt('');
    }
    setError(null);
  }, [initialDesign, isOpen]);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      setError('Please provide a name for this jewellery design.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      await onSubmit({
        name: name.trim(),
        category,
        status,
        description: description.trim() || null,
        sketch_image_url: sketchImageUrl.trim() || null,
        ai_prompt: aiPrompt.trim() || null,
      });
      onClose();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to save jewellery design.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-in fade-in duration-200">
      <div 
        className="relative w-full max-w-xl bg-[#0b0e17] border border-slate-800 rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div className="flex items-center justify-between p-5 sm:p-6 border-b border-slate-800 bg-[#0d121f]/50">
          <div className="flex items-center space-x-2.5">
            <div className="p-2 rounded-xl bg-amber-500/10 text-amber-400 border border-amber-500/20">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white tracking-tight">
                {isEditing ? 'Edit Jewellery Design' : 'Create New Jewellery Design'}
              </h2>
              <p className="text-xs text-slate-400">
                {isEditing ? 'Update specifications and status' : 'Define jewellery metadata and initial requirements'}
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
            aria-label="Close dialog"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Form */}
        <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto p-5 sm:p-6 space-y-4">
          {error && (
            <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/30 flex items-start space-x-2.5 text-rose-300 text-xs">
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          {/* Design Name */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-300 flex items-center justify-between">
              <span>Design Name <span className="text-amber-400">*</span></span>
              <span className="text-[10px] text-slate-500 font-normal">e.g. Victorian Diamond Solitaire</span>
            </label>
            <Input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Royal Emerald Pendant"
              required
              autoFocus
            />
          </div>

          {/* Category and Status Dual Columns */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-300">
                Category <span className="text-amber-400">*</span>
              </label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value as DesignCategory)}
                className="w-full h-10 rounded-md border border-slate-700 bg-slate-900/80 px-3 text-sm text-slate-100 focus:outline-none focus:ring-1 focus:ring-amber-400 focus:border-amber-400 transition cursor-pointer"
              >
                {DESIGN_CATEGORIES.map((cat) => (
                  <option key={cat} value={cat} className="bg-slate-900 text-slate-100">
                    {cat}
                  </option>
                ))}
              </select>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-300">
                Status <span className="text-amber-400">*</span>
              </label>
              <select
                value={status}
                onChange={(e) => setStatus(e.target.value as DesignStatus)}
                className="w-full h-10 rounded-md border border-slate-700 bg-slate-900/80 px-3 text-sm text-slate-100 focus:outline-none focus:ring-1 focus:ring-amber-400 focus:border-amber-400 transition cursor-pointer"
              >
                {DESIGN_STATUSES.map((st) => (
                  <option key={st.value} value={st.value} className="bg-slate-900 text-slate-100">
                    {st.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Description */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-300">
              Description & Crafting Notes
            </label>
            <Textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Specify metal purity (e.g. 18K Yellow Gold), gemstone prong style, shank dimensions, etc."
              rows={3}
            />
          </div>

          {/* Sketch Image URL Reference */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-300 flex items-center justify-between">
              <span>Sketch Image Reference (Optional)</span>
              <span className="text-[10px] text-slate-500 font-normal">HTTP URL or storage reference</span>
            </label>
            <Input
              value={sketchImageUrl}
              onChange={(e) => setSketchImageUrl(e.target.value)}
              placeholder="https://example.com/sketches/ring-01.png"
            />
          </div>

          {/* AI Prompt Input */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-300 flex items-center justify-between">
              <span>Generative AI Prompt (Optional)</span>
              <span className="text-[10px] text-amber-400/80 font-normal">For Phase 7 AI diffusion</span>
            </label>
            <Textarea
              value={aiPrompt}
              onChange={(e) => setAiPrompt(e.target.value)}
              placeholder="e.g. Photorealistic 18k yellow gold emerald ring, studio lighting, macro jewelry photography..."
              rows={2}
            />
          </div>

          {/* Footer Actions */}
          <div className="pt-4 border-t border-slate-800/80 flex items-center justify-end space-x-3">
            <Button
              type="button"
              variant="outline"
              onClick={onClose}
              disabled={loading}
              className="border-slate-700"
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="gold"
              disabled={loading}
              className="font-bold min-w-[120px]"
            >
              {loading ? (
                <div className="flex items-center space-x-2">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Saving...</span>
                </div>
              ) : isEditing ? (
                'Update Design'
              ) : (
                'Create Design'
              )}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};
