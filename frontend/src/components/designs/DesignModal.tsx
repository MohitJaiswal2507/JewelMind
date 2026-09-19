import React, { useState, useEffect } from 'react';
import { X, Loader2, Sparkles, AlertCircle, Brush } from 'lucide-react';
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
  onSubmit: (data: DesignCreateInput | DesignUpdateInput, openInCanvas?: boolean) => Promise<void>;
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

  const handleSave = async (openInCanvas: boolean = false) => {
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
      }, openInCanvas);
      onClose();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to save jewellery design.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/85 backdrop-blur-md animate-in fade-in duration-200">
      <div 
        className="relative w-full max-w-xl bg-[#0E111A] border border-white/10 rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div className="flex items-center justify-between p-6 sm:p-7 border-b border-white/[0.07] bg-[#0A0C12]/70">
          <div className="flex items-center space-x-3">
            <div className="p-2.5 rounded-xl bg-amber-400/10 text-amber-300 border border-amber-400/20">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <h2 className="font-serif text-lg font-medium text-white tracking-tight">
                {isEditing ? 'Edit Jewellery Design' : 'Create New Jewellery Design'}
              </h2>
              <p className="text-xs text-slate-400 font-light">
                {isEditing ? 'Update specifications and crafting notes' : 'Define jewellery metadata and initial requirements'}
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-white/5 transition"
            aria-label="Close dialog"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Form */}
        <form onSubmit={(e) => { e.preventDefault(); handleSave(!isEditing); }} className="flex-1 overflow-y-auto p-6 sm:p-7 space-y-4">
          {error && (
            <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/30 flex items-start space-x-2.5 text-rose-300 text-xs">
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          {/* Design Name */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-300 flex items-center justify-between">
              <span>Design Name <span className="text-amber-300">*</span></span>
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
                Category <span className="text-amber-300">*</span>
              </label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value as DesignCategory)}
                className="w-full h-10 rounded-xl border border-white/10 bg-[#080A10] px-3 text-xs text-slate-100 focus:outline-none focus:ring-1 focus:ring-amber-400/50 transition cursor-pointer shadow-inner"
              >
                {DESIGN_CATEGORIES.map((cat) => (
                  <option key={cat} value={cat} className="bg-[#0E111A] text-slate-100">
                    {cat}
                  </option>
                ))}
              </select>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-300">
                Status <span className="text-amber-300">*</span>
              </label>
              <select
                value={status}
                onChange={(e) => setStatus(e.target.value as DesignStatus)}
                className="w-full h-10 rounded-xl border border-white/10 bg-[#080A10] px-3 text-xs text-slate-100 focus:outline-none focus:ring-1 focus:ring-amber-400/50 transition cursor-pointer shadow-inner"
              >
                {DESIGN_STATUSES.map((st) => (
                  <option key={st.value} value={st.value} className="bg-[#0E111A] text-slate-100">
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
              <span className="text-[10px] text-amber-300/80 font-normal">For ControlNet AI diffusion</span>
            </label>
            <Textarea
              value={aiPrompt}
              onChange={(e) => setAiPrompt(e.target.value)}
              placeholder="e.g. Photorealistic 18k yellow gold emerald ring, studio lighting, macro jewelry photography..."
              rows={2}
            />
          </div>

          {/* Footer Actions */}
          <div className="pt-4 border-t border-white/5 flex flex-wrap items-center justify-end gap-2.5">
            <Button
              type="button"
              variant="ghost"
              onClick={onClose}
              disabled={loading}
              className="text-xs text-slate-400 hover:text-white"
            >
              Cancel
            </Button>
            
            {isEditing ? (
              <Button
                type="submit"
                variant="gold"
                disabled={loading}
                className="font-semibold text-xs min-w-[120px]"
              >
                {loading ? (
                  <div className="flex items-center space-x-2">
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Updating...</span>
                  </div>
                ) : (
                  'Update Design'
                )}
              </Button>
            ) : (
              <>
                <Button
                  type="button"
                  variant="outline"
                  disabled={loading}
                  onClick={() => handleSave(false)}
                  className="text-xs border-white/10 hover:bg-white/5 text-slate-300"
                >
                  Save & Close
                </Button>
                <Button
                  type="button"
                  variant="gold"
                  disabled={loading}
                  onClick={() => handleSave(true)}
                  className="text-xs font-semibold shadow flex items-center"
                >
                  {loading ? (
                    <div className="flex items-center space-x-2">
                      <Loader2 className="w-4 h-4 animate-spin" />
                      <span>Creating...</span>
                    </div>
                  ) : (
                    <>
                      <Brush className="w-3.5 h-3.5 mr-1.5" />
                      Open in Canva
                    </>
                  )}
                </Button>
              </>
            )}
          </div>
        </form>
      </div>
    </div>
  );
};
