import React, { useState, useEffect } from 'react';
import { 
  ArrowLeft, 
  Sparkles, 
  Layers, 
  Edit3, 
  Trash2, 
  Calendar, 
  Clock, 
  Key, 
  Loader2, 
  AlertCircle,
  FileText,
  CheckCircle2,
  RefreshCw,
  Brush
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { DesignModal } from '../components/designs/DesignModal';
import { DesignDeleteModal } from '../components/designs/DesignDeleteModal';
import { SketchUploadDropzone } from '../components/designs/SketchUploadDropzone';
import { SketchDeleteModal } from '../components/designs/SketchDeleteModal';
import { AiRenderModal } from '../components/studio/AiRenderModal';
import { designService } from '../services/api/designService';
import { 
  Design, 
  DesignStatus, 
  DesignUpdateInput 
} from '../types/design';

interface DesignDetailPageProps {
  designId: string;
  onBack: () => void;
  onOpenCanvas?: (designId: string) => void;
}

const getStatusBadge = (status: DesignStatus) => {
  switch (status) {
    case 'ready':
      return <Badge variant="success">Ready for Review</Badge>;
    case 'rendering':
      return (
        <Badge variant="gold" className="animate-pulse">
          <Sparkles className="w-3 h-3 mr-1" />
          Rendering
        </Badge>
      );
    case 'rendered':
      return (
        <Badge variant="gold">
          <Sparkles className="w-3 h-3 mr-1" />
          Rendered Visuals Ready
        </Badge>
      );
    case 'archived':
      return <Badge variant="secondary">Archived</Badge>;
    case 'draft':
    default:
      return <Badge variant="outline">Draft</Badge>;
  }
};

export const DesignDetailPage: React.FC<DesignDetailPageProps> = ({
  designId,
  onBack,
  onOpenCanvas,
}) => {
  const [design, setDesign] = useState<Design | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Modals
  const [isEditModalOpen, setIsEditModalOpen] = useState<boolean>(false);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState<boolean>(false);
  const [isSketchDeleteModalOpen, setIsSketchDeleteModalOpen] = useState<boolean>(false);
  const [isAiRenderOpen, setIsAiRenderOpen] = useState<boolean>(false);

  // Sketch replacement mode
  const [showReplaceUpload, setShowReplaceUpload] = useState<boolean>(false);

  // Feedback Toast
  const [feedback, setFeedback] = useState<string | null>(null);

  const fetchDesign = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await designService.getDesign(designId);
      setDesign(data);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to load design details.';
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
      const timer = setTimeout(() => setFeedback(null), 4000);
      return () => clearTimeout(timer);
    }
  }, [feedback]);

  const handleUpdate = async (data: DesignUpdateInput) => {
    if (!design) return;
    const updated = await designService.updateDesign(design.id, data);
    setDesign(updated);
    setFeedback('Design metadata updated successfully.');
  };

  const handleDelete = async () => {
    if (!design) return;
    await designService.deleteDesign(design.id);
    onBack();
  };

  const handleUploadSketch = async (file: File) => {
    if (!design) return;
    const updated = await designService.uploadSketch(design.id, file);
    setDesign(updated);
    setShowReplaceUpload(false);
    setFeedback('Sketch uploaded and synced with Supabase Storage.');
  };

  const handleDeleteSketch = async () => {
    if (!design) return;
    const updated = await designService.deleteSketch(design.id);
    setDesign(updated);
    setShowReplaceUpload(false);
    setFeedback('Sketch removed from Supabase Storage.');
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-28 space-y-4 text-slate-400">
        <Loader2 className="w-8 h-8 animate-spin text-amber-300" />
        <span className="text-xs font-light">Loading jewellery design details...</span>
      </div>
    );
  }

  if (error || !design) {
    return (
      <div className="max-w-2xl mx-auto py-12 space-y-6">
        <Button variant="outline" size="sm" onClick={onBack} className="border-white/10">
          <ArrowLeft className="w-4 h-4 mr-2" /> Back to Catalogue
        </Button>
        <div className="p-6 rounded-2xl bg-rose-500/10 border border-rose-500/30 text-rose-300 space-y-3">
          <div className="flex items-center space-x-2 font-medium">
            <AlertCircle className="w-5 h-5" />
            <span>Design Error</span>
          </div>
          <p className="text-xs">{error || 'Design not found or you do not have permission to view it.'}</p>
        </div>
      </div>
    );
  }

  const formattedCreatedDate = new Date(design.created_at).toLocaleString();
  const formattedUpdatedDate = new Date(design.updated_at).toLocaleString();

  return (
    <div className="space-y-8 max-w-6xl mx-auto py-2 sm:py-4">
      {/* Top Breadcrumb & Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <Button
          variant="outline"
          size="sm"
          onClick={onBack}
          className="border-white/10 text-slate-300 hover:text-white w-fit text-xs"
        >
          <ArrowLeft className="w-3.5 h-3.5 mr-1.5" />
          Back to Catalogue
        </Button>

        <div className="flex items-center space-x-2.5">
          <Button
            variant="secondary"
            size="sm"
            onClick={() => setIsEditModalOpen(true)}
            className="text-xs font-semibold bg-[#121622] hover:bg-[#181E2E] border-white/5"
          >
            <Edit3 className="w-3.5 h-3.5 mr-1.5" />
            Edit Metadata
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={() => setIsDeleteModalOpen(true)}
            className="text-xs border-white/10 hover:border-rose-500/40 hover:text-rose-300"
          >
            <Trash2 className="w-3.5 h-3.5 mr-1.5" />
            Delete Design
          </Button>
        </div>
      </div>

      {/* Toast Feedback */}
      {feedback && (
        <div className="p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center space-x-2 text-emerald-300 text-xs animate-in fade-in">
          <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>{feedback}</span>
        </div>
      )}

      {/* Main Title Banner */}
      <div className="bg-[#0E111A]/90 p-7 sm:p-9 rounded-2xl border border-white/[0.07] shadow-2xl space-y-4 relative overflow-hidden">
        <div className="flex flex-wrap items-center gap-2.5">
          <Badge variant="gold" className="text-[10px]">
            {design.category}
          </Badge>
          {getStatusBadge(design.status)}
        </div>

        <div>
          <h1 className="font-serif text-3xl sm:text-4xl text-white font-normal tracking-tight">
            {design.name}
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 font-light mt-2 leading-relaxed max-w-3xl">
            {design.description || 'No extended crafting notes provided.'}
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-4 sm:gap-6 pt-4 text-[11px] text-slate-400 font-light border-t border-white/5">
          <div className="flex items-center gap-1.5 font-mono">
            <Key className="w-3.5 h-3.5 text-slate-500" />
            <span className="text-slate-500">ID:</span>
            <span className="text-slate-300 truncate max-w-[140px] sm:max-w-none">{design.id}</span>
          </div>
          <div className="flex items-center gap-1.5">
            <Calendar className="w-3.5 h-3.5 text-slate-500" />
            <span className="text-slate-500">Created:</span>
            <span className="text-slate-300">{formattedCreatedDate}</span>
          </div>
          <div className="flex items-center gap-1.5">
            <Clock className="w-3.5 h-3.5 text-slate-500" />
            <span className="text-slate-500">Updated:</span>
            <span className="text-slate-300">{formattedUpdatedDate}</span>
          </div>
        </div>
      </div>

      {/* Visual Dual Canvas Previews (Sketch & Future AI Render) */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Sketch Blueprint Section */}
        <Card className="bg-[#0E111A]/90 border-white/[0.07] flex flex-col justify-between overflow-hidden shadow-2xl">
          <CardHeader className="p-6 pb-3 border-b border-white/[0.06] bg-[#0A0C12]/50 flex flex-row items-center justify-between">
            <div className="space-y-1">
              <div className="flex items-center space-x-2 text-amber-300">
                <Layers className="w-5 h-5" />
                <CardTitle className="text-base font-serif font-medium">Sketch Blueprint</CardTitle>
              </div>
              <CardDescription className="text-xs text-slate-400 font-light">
                {design.sketch_image_url 
                  ? 'Blueprint asset synced with cloud storage'
                  : 'Upload your hand-drawn sketch or CAD drawing'}
              </CardDescription>
            </div>

            <div className="flex items-center space-x-2">
              {onOpenCanvas && (
                <Button
                  variant="gold"
                  size="sm"
                  onClick={() => onOpenCanvas(design.id)}
                  className="h-8 text-xs font-semibold shadow"
                >
                  <Brush className="w-3.5 h-3.5 mr-1.5" />
                  Open Canvas
                </Button>
              )}
              {design.sketch_image_url && !showReplaceUpload && (
                <>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setShowReplaceUpload(true)}
                    className="h-8 text-xs border-white/10 hover:text-amber-300"
                  >
                    <RefreshCw className="w-3.5 h-3.5 mr-1" /> Replace
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setIsSketchDeleteModalOpen(true)}
                    className="h-8 text-xs border-white/10 text-slate-400 hover:text-rose-300 hover:border-rose-500/40"
                    aria-label="Delete Sketch"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </Button>
                </>
              )}
            </div>
          </CardHeader>
          <CardContent className="p-6 flex-1 flex flex-col items-center justify-center min-h-[320px]">
            {showReplaceUpload ? (
              <div className="w-full space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-medium text-amber-300">Replace Blueprint</span>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setShowReplaceUpload(false)}
                    className="h-7 text-xs text-slate-400 hover:text-white"
                  >
                    Cancel
                  </Button>
                </div>
                <SketchUploadDropzone onUpload={handleUploadSketch} isReplacing={true} />
              </div>
            ) : design.sketch_image_url ? (
              <div className="w-full flex flex-col items-center space-y-3">
                <div className="relative w-full max-h-80 bg-[#080A10] rounded-xl border border-white/5 p-4 flex items-center justify-center overflow-hidden group">
                  <img
                    src={design.sketch_image_url}
                    alt={`${design.name} sketch`}
                    className="max-h-72 object-contain rounded-lg filter invert opacity-90 transition-transform duration-300 group-hover:scale-[1.02]"
                  />
                </div>
                <div className="text-[10px] font-mono text-slate-500 truncate max-w-md">
                  Source: {design.sketch_image_url}
                </div>
              </div>
            ) : (
              <div className="w-full">
                <SketchUploadDropzone onUpload={handleUploadSketch} isReplacing={false} />
              </div>
            )}
          </CardContent>
        </Card>

        {/* AI Photorealistic Render Section */}
        <Card className="bg-[#0E111A]/90 border-white/[0.07] flex flex-col justify-between overflow-hidden shadow-2xl">
          <CardHeader className="p-6 pb-3 border-b border-white/[0.06] bg-[#0A0C12]/50 flex flex-row items-center justify-between">
            <div className="space-y-1">
              <div className="flex items-center space-x-2 text-amber-300">
                <Sparkles className="w-5 h-5" />
                <CardTitle className="text-base font-serif font-medium">Diffusion Prototype</CardTitle>
              </div>
              <CardDescription className="text-xs text-slate-400 font-light">
                Generative ControlNet structural synthesis
              </CardDescription>
            </div>

            {design.sketch_image_url && (
              <Button
                variant="gold"
                size="sm"
                onClick={() => setIsAiRenderOpen(true)}
                className="h-8 text-xs font-semibold shadow"
              >
                <Sparkles className="w-3.5 h-3.5 mr-1.5" />
                AI Render
              </Button>
            )}
          </CardHeader>
          <CardContent className="p-6 flex-1 flex flex-col items-center justify-center min-h-[320px]">
            {design.rendered_image_url ? (
              <div className="relative w-full max-h-80 bg-[#080A10] rounded-xl border border-white/5 p-2 flex items-center justify-center overflow-hidden">
                <img
                  src={design.rendered_image_url}
                  alt={`${design.name} AI Render`}
                  className="w-full max-h-72 object-contain rounded-lg shadow-xl"
                />
              </div>
            ) : (
              <div className="text-center p-6 space-y-3.5">
                <div className="p-3.5 rounded-2xl bg-amber-400/10 text-amber-300 border border-amber-400/20 w-fit mx-auto">
                  <Sparkles className="w-7 h-7" />
                </div>
                <div className="text-sm font-serif font-medium text-white">Generative Diffusion Active</div>
                <div className="p-4 rounded-xl bg-[#080A10] border border-white/5 text-[11px] text-amber-200/90 leading-relaxed max-w-sm font-light">
                  Photorealistic rendering conditioned on your blueprint geometry is active. Synthesize 18K gold and gemstone previews with one click.
                </div>
                {design.sketch_image_url && (
                  <Button
                    variant="gold"
                    size="sm"
                    onClick={() => setIsAiRenderOpen(true)}
                    className="font-semibold text-xs shadow-md"
                  >
                    <Sparkles className="w-3.5 h-3.5 mr-1.5" />
                    Render Now
                  </Button>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* AI Prompt Specification */}
      <Card className="bg-[#0E111A]/90 border-white/[0.07] shadow-2xl">
        <CardHeader className="p-6 pb-3 border-b border-white/[0.06] bg-[#0A0C12]/50">
          <div className="flex items-center space-x-2 text-amber-300">
            <FileText className="w-5 h-5" />
            <CardTitle className="text-base font-serif font-medium">Generative Diffusion Prompt</CardTitle>
          </div>
          <CardDescription className="text-xs text-slate-400 font-light">
            Conditioning prompt parameters for generative inference
          </CardDescription>
        </CardHeader>
        <CardContent className="p-6 text-xs font-mono text-slate-300">
          {design.ai_prompt ? (
            <div className="p-4 rounded-xl bg-[#080A10] border border-white/5 leading-relaxed font-sans text-xs text-slate-200">
              {design.ai_prompt}
            </div>
          ) : (
            <div className="text-slate-500 italic font-sans text-xs">
              No prompt configured. Click "Edit Metadata" to add descriptive prompts for metallic finish and gemstone specifications.
            </div>
          )}
        </CardContent>
      </Card>

      {/* Edit Design Modal */}
      <DesignModal
        isOpen={isEditModalOpen}
        onClose={() => setIsEditModalOpen(false)}
        onSubmit={handleUpdate}
        initialDesign={design}
      />

      {/* Delete Design Modal */}
      <DesignDeleteModal
        isOpen={isDeleteModalOpen}
        onClose={() => setIsDeleteModalOpen(false)}
        onConfirm={handleDelete}
        design={design}
      />

      {/* Delete Sketch Modal */}
      <SketchDeleteModal
        isOpen={isSketchDeleteModalOpen}
        onClose={() => setIsSketchDeleteModalOpen(false)}
        onConfirm={handleDeleteSketch}
        designName={design.name}
      />

      {/* AI Render Modal */}
      {design.sketch_image_url && (
        <AiRenderModal
          isOpen={isAiRenderOpen}
          onClose={() => {
            setIsAiRenderOpen(false);
            fetchDesign();
          }}
          sketchUrl={design.sketch_image_url}
          designTitle={design.name}
          category={design.category}
          sourceBlueprintCategory={design.category}
          designId={design.id}
          onSuccess={() => {
            fetchDesign();
          }}
        />
      )}
    </div>
  );
};

export default DesignDetailPage;
