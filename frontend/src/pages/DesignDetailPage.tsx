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
import { Separator } from '../components/ui/separator';
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
          Rendering (In Progress)
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
      <div className="flex flex-col items-center justify-center py-24 space-y-4 text-slate-400">
        <Loader2 className="w-8 h-8 animate-spin text-amber-400" />
        <span className="text-xs">Loading jewellery design details...</span>
      </div>
    );
  }

  if (error || !design) {
    return (
      <div className="max-w-2xl mx-auto py-12 space-y-6">
        <Button variant="outline" size="sm" onClick={onBack} className="border-slate-700">
          <ArrowLeft className="w-4 h-4 mr-2" /> Back to Designs
        </Button>
        <div className="p-6 rounded-2xl bg-rose-500/10 border border-rose-500/30 text-rose-300 space-y-3">
          <div className="flex items-center space-x-2 font-bold">
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
    <div className="space-y-8 max-w-6xl mx-auto py-6">
      {/* Top Breadcrumb & Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <Button
          variant="outline"
          size="sm"
          onClick={onBack}
          className="border-slate-700 text-slate-300 hover:text-white w-fit"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Workspace
        </Button>

        <div className="flex items-center space-x-3">
          <Button
            variant="secondary"
            size="sm"
            onClick={() => setIsEditModalOpen(true)}
            className="text-xs font-semibold"
          >
            <Edit3 className="w-3.5 h-3.5 mr-1.5" />
            Edit Metadata
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={() => setIsDeleteModalOpen(true)}
            className="text-xs border-slate-700 hover:border-rose-500 hover:text-rose-400 hover:bg-rose-500/10"
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
      <div className="bg-gradient-to-br from-slate-900/90 to-[#0d121f] p-6 sm:p-8 rounded-2xl border border-slate-800 shadow-xl space-y-4">
        <div className="flex flex-wrap items-center gap-2.5">
          <span className="px-3 py-1 rounded-md bg-amber-400/15 border border-amber-400/30 text-xs font-bold text-amber-300">
            {design.category}
          </span>
          {getStatusBadge(design.status)}
        </div>

        <div>
          <h1 className="text-2xl sm:text-4xl font-extrabold text-white tracking-tight">
            {design.name}
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-2 leading-relaxed max-w-3xl">
            {design.description || 'No extended description provided.'}
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-4 sm:gap-6 pt-4 text-xs text-slate-400 border-t border-slate-800/80">
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

      {/* Visual Pipeline Previews (Sketch & Future AI Render) */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Sketch Blueprint Section */}
        <Card className="bg-[#0b0f19] border-slate-800 flex flex-col justify-between overflow-hidden">
          <CardHeader className="pb-3 flex flex-row items-center justify-between">
            <div className="space-y-1">
              <div className="flex items-center space-x-2 text-amber-400">
                <Layers className="w-5 h-5" />
                <CardTitle className="text-base">Sketch Blueprint</CardTitle>
              </div>
              <CardDescription className="text-xs">
                {design.sketch_image_url 
                  ? 'Active sketch asset stored in Supabase Storage bucket jewelmind-assets'
                  : 'Upload your hand-drawn sketch or line drawing'}
              </CardDescription>
            </div>

            <div className="flex items-center space-x-2">
              {onOpenCanvas && (
                <Button
                  variant="gold"
                  size="sm"
                  onClick={() => onOpenCanvas(design.id)}
                  className="h-8 text-xs font-bold shadow"
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
                    className="h-8 text-xs border-slate-700 hover:text-amber-300"
                  >
                    <RefreshCw className="w-3.5 h-3.5 mr-1" /> Replace
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setIsSketchDeleteModalOpen(true)}
                    className="h-8 text-xs border-slate-700 text-slate-400 hover:text-rose-400 hover:border-rose-500/50"
                    aria-label="Delete Sketch"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </Button>
                </>
              )}
            </div>
          </CardHeader>
          <Separator />
          <CardContent className="p-6 flex-1 flex flex-col items-center justify-center min-h-[300px]">
            {showReplaceUpload ? (
              <div className="w-full space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-amber-300">Replace Sketch</span>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setShowReplaceUpload(false)}
                    className="h-7 text-xs text-slate-400 hover:text-white"
                  >
                    Cancel Replacement
                  </Button>
                </div>
                <SketchUploadDropzone onUpload={handleUploadSketch} isReplacing={true} />
              </div>
            ) : design.sketch_image_url ? (
              <div className="w-full flex flex-col items-center space-y-3">
                <div className="relative w-full max-h-72 bg-slate-950/80 rounded-xl border border-slate-800/80 p-4 flex items-center justify-center overflow-hidden group">
                  <img
                    src={design.sketch_image_url}
                    alt={`${design.name} sketch`}
                    className="max-h-64 object-contain rounded-lg filter invert opacity-95 transition group-hover:scale-[1.02] duration-200"
                  />
                </div>
                <div className="text-[11px] font-mono text-slate-500 truncate max-w-md">
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
        <Card className="bg-[#0b0f19] border-slate-800 flex flex-col justify-between overflow-hidden">
          <CardHeader className="pb-3 flex flex-row items-center justify-between">
            <div className="space-y-1">
              <div className="flex items-center space-x-2 text-amber-400">
                <Sparkles className="w-5 h-5" />
                <CardTitle className="text-base">Photorealistic Render</CardTitle>
              </div>
              <CardDescription className="text-xs">
                Generative ControlNet + Diffusion preview
              </CardDescription>
            </div>

            {design.sketch_image_url && (
              <Button
                variant="gold"
                size="sm"
                onClick={() => setIsAiRenderOpen(true)}
                className="h-8 text-xs font-bold shadow bg-gradient-to-r from-amber-500 via-amber-400 to-amber-500 text-slate-950 hover:brightness-110"
              >
                <Sparkles className="w-3.5 h-3.5 mr-1.5" />
                AI Render
              </Button>
            )}
          </CardHeader>
          <Separator />
          <CardContent className="p-6 flex-1 flex flex-col items-center justify-center min-h-[300px]">
            {design.rendered_image_url ? (
              <img
                src={design.rendered_image_url}
                alt={`${design.name} AI Render`}
                className="w-full max-h-72 object-cover rounded-xl"
              />
            ) : (
              <div className="text-center p-6 space-y-3">
                <div className="p-3.5 rounded-2xl bg-amber-500/10 text-amber-400 border border-amber-500/20 w-fit mx-auto">
                  <Sparkles className="w-7 h-7" />
                </div>
                <div className="text-xs font-semibold text-white">Generative Diffusion Active</div>
                <div className="p-3.5 rounded-xl bg-slate-950/80 border border-slate-800/80 text-[11px] text-amber-300/90 leading-relaxed max-w-sm">
                  Photorealistic AI rendering with ControlNet conditioning is active. Generate metallic and gemstone previews from this sketch.
                </div>
                {design.sketch_image_url && (
                  <Button
                    variant="gold"
                    size="sm"
                    onClick={() => setIsAiRenderOpen(true)}
                    className="font-bold text-xs shadow-md bg-gradient-to-r from-amber-500 via-amber-400 to-amber-500 text-slate-950 hover:brightness-110"
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
      <Card className="bg-[#0b0f19] border-slate-800">
        <CardHeader className="pb-3">
          <div className="flex items-center space-x-2 text-amber-400">
            <FileText className="w-5 h-5" />
            <CardTitle className="text-base">Generative Diffusion Prompt</CardTitle>
          </div>
          <CardDescription className="text-xs">
            Conditioning prompt parameters for generative inference
          </CardDescription>
        </CardHeader>
        <Separator />
        <CardContent className="pt-4 text-xs font-mono text-slate-300">
          {design.ai_prompt ? (
            <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 leading-relaxed">
              {design.ai_prompt}
            </div>
          ) : (
            <div className="text-slate-500 italic">
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
