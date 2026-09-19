import React, { useState, useEffect, useCallback } from 'react';
import { 
  Plus, 
  Layers, 
  Sparkles, 
  AlertCircle, 
  FolderPlus,
  RefreshCw,
  Search
} from 'lucide-react';

import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { DesignCard } from '../components/designs/DesignCard';
import { DesignModal } from '../components/designs/DesignModal';
import { DesignDeleteModal } from '../components/designs/DesignDeleteModal';
import { DesignFilters } from '../components/designs/DesignFilters';
import { designService } from '../services/api/designService';
import { 
  Design, 
  DesignCategory, 
  DesignStatus, 
  DesignCreateInput, 
  DesignUpdateInput 
} from '../types/design';

interface DesignsPageProps {
  onSelectDesign: (design: Design) => void;
  onOpenCanvas?: (designId: string) => void;
}

export const DesignsPage: React.FC<DesignsPageProps> = ({ onSelectDesign, onOpenCanvas }) => {
  const [designs, setDesigns] = useState<Design[]>([]);
  const [totalCount, setTotalCount] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Filter states
  const [search, setSearch] = useState<string>('');
  const [category, setCategory] = useState<DesignCategory | ''>('');
  const [status, setStatus] = useState<DesignStatus | ''>('');
  const [page, setPage] = useState<number>(1);
  const [pageSize] = useState<number>(24);

  // Modal states
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
  const [editingDesign, setEditingDesign] = useState<Design | null>(null);
  const [deletingDesign, setDeletingDesign] = useState<Design | null>(null);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState<boolean>(false);

  // Success toast feedback
  const [feedbackMessage, setFeedbackMessage] = useState<string | null>(null);

  const fetchDesigns = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await designService.getDesigns({
        category: category || undefined,
        status: status || undefined,
        search: search || undefined,
        page,
        page_size: pageSize,
      });
      setDesigns(response.items);
      setTotalCount(response.total);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to fetch jewellery catalogue.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, [category, status, search, page, pageSize]);

  useEffect(() => {
    fetchDesigns();
  }, [fetchDesigns]);

  useEffect(() => {
    if (feedbackMessage) {
      const timer = setTimeout(() => setFeedbackMessage(null), 4000);
      return () => clearTimeout(timer);
    }
  }, [feedbackMessage]);

  const handleOpenCreateModal = () => {
    setEditingDesign(null);
    setIsModalOpen(true);
  };

  const handleOpenEditModal = (design: Design) => {
    setEditingDesign(design);
    setIsModalOpen(true);
  };

  const handleOpenDeleteModal = (design: Design) => {
    setDeletingDesign(design);
    setIsDeleteModalOpen(true);
  };

  const handleSaveDesign = async (data: DesignCreateInput | DesignUpdateInput, openInCanvas?: boolean) => {
    if (editingDesign) {
      await designService.updateDesign(editingDesign.id, data);
      setFeedbackMessage(`Updated design "${data.name || editingDesign.name}" successfully.`);
      await fetchDesigns();
    } else {
      const created = await designService.createDesign(data as DesignCreateInput);
      setFeedbackMessage(`Created new jewellery design "${data.name}" successfully.`);
      if (openInCanvas && onOpenCanvas) {
        onOpenCanvas(created.id);
        return;
      }
      await fetchDesigns();
    }
  };

  const handleConfirmDelete = async () => {
    if (deletingDesign) {
      await designService.deleteDesign(deletingDesign.id);
      setFeedbackMessage(`Deleted design "${deletingDesign.name}".`);
      await fetchDesigns();
    }
  };

  const handleResetFilters = () => {
    setSearch('');
    setCategory('');
    setStatus('');
    setPage(1);
  };

  return (
    <div className="space-y-8 max-w-7xl mx-auto py-2 sm:py-4">
      {/* Workspace Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-6 p-7 sm:p-9 rounded-2xl bg-[#0E111A]/90 border border-white/[0.07] shadow-2xl relative overflow-hidden">
        <div className="flex items-center space-x-4">
          <div className="w-13 h-13 rounded-2xl bg-gradient-to-tr from-amber-400/20 via-yellow-400/10 to-transparent border border-amber-400/30 flex items-center justify-center shadow-lg shadow-amber-500/5 shrink-0">
            <Layers className="w-6 h-6 text-amber-300" />
          </div>
          <div>
            <div className="flex items-center space-x-2.5">
              <h1 className="font-serif text-2xl sm:text-3xl font-normal text-white tracking-tight">
                Design Catalogue
              </h1>
              <Badge variant="gold" className="text-[10px]">
                {totalCount} {totalCount === 1 ? 'Design' : 'Designs'}
              </Badge>
            </div>
            <p className="text-xs sm:text-sm text-slate-400 font-light mt-1 max-w-xl">
              Editorial portfolio of fine jewellery blueprints, generative diffusion targets, and bespoke collections.
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          <Button
            variant="outline"
            size="sm"
            onClick={fetchDesigns}
            disabled={loading}
            className="h-9 px-3 border-white/10 text-slate-300 hover:border-white/20"
            title="Refresh Designs"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          </Button>

          <Button
            variant="gold"
            size="default"
            onClick={handleOpenCreateModal}
            className="h-9 px-5 font-semibold text-xs shadow-md shadow-amber-500/10"
          >
            <Plus className="w-4 h-4 mr-1.5" />
            New Design
          </Button>
        </div>
      </div>

      {/* Feedback Banner */}
      {feedbackMessage && (
        <div className="p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-between text-emerald-300 text-xs animate-in fade-in">
          <div className="flex items-center space-x-2">
            <Sparkles className="w-4 h-4 text-emerald-400" />
            <span>{feedbackMessage}</span>
          </div>
        </div>
      )}

      {/* Error Banner */}
      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 flex items-start space-x-3 text-rose-300 text-xs">
          <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <div className="font-semibold">Unable to load catalogue</div>
            <div>{error}</div>
            <Button
              variant="outline"
              size="sm"
              onClick={fetchDesigns}
              className="mt-2 text-xs border-rose-500/40 hover:bg-rose-500/20"
            >
              Retry
            </Button>
          </div>
        </div>
      )}

      {/* Filter Toolbar */}
      <DesignFilters
        search={search}
        onSearchChange={setSearch}
        selectedCategory={category}
        onCategoryChange={setCategory}
        selectedStatus={status}
        onStatusChange={setStatus}
        onReset={handleResetFilters}
      />

      {/* Designs Grid or States */}
      {loading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {Array.from({ length: 8 }).map((_, idx) => (
            <div
              key={idx}
              className="h-88 rounded-2xl bg-[#0E111A]/60 border border-white/5 animate-pulse flex flex-col justify-between p-5"
            >
              <div className="space-y-3">
                <div className="h-44 bg-white/[0.03] rounded-xl" />
                <div className="h-4 bg-white/[0.04] rounded w-3/4" />
                <div className="h-3 bg-white/[0.02] rounded w-1/2" />
              </div>
              <div className="h-8 bg-white/[0.03] rounded-lg w-full" />
            </div>
          ))}
        </div>
      ) : designs.length > 0 ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {designs.map((design) => (
            <DesignCard
              key={design.id}
              design={design}
              onView={onSelectDesign}
              onEdit={handleOpenEditModal}
              onDelete={handleOpenDeleteModal}
            />
          ))}
        </div>
      ) : (
        /* Empty State */
        <div className="text-center py-20 px-6 bg-[#0E111A]/50 rounded-2xl border border-white/[0.07] space-y-5">
          <div className="mx-auto w-16 h-16 rounded-2xl bg-[#080A10] border border-white/10 flex items-center justify-center text-slate-500">
            {search || category || status ? (
              <Search className="w-8 h-8 text-slate-400" />
            ) : (
              <FolderPlus className="w-8 h-8 text-amber-300" />
            )}
          </div>

          <div className="space-y-1.5 max-w-md mx-auto">
            <h3 className="font-serif text-lg font-medium text-white">
              {search || category || status
                ? 'No designs match your filters'
                : 'No jewellery designs yet'}
            </h3>
            <p className="text-xs text-slate-400 font-light leading-relaxed">
              {search || category || status
                ? 'Try adjusting your search terms, changing the category tab, or resetting filters.'
                : 'Begin assembling your portfolio by creating your first ring, necklace, earring, or pendant design.'}
            </p>
          </div>

          <div>
            {search || category || status ? (
              <Button
                variant="outline"
                size="sm"
                onClick={handleResetFilters}
                className="border-white/10 text-xs"
              >
                Reset All Filters
              </Button>
            ) : (
              <Button
                variant="gold"
                size="default"
                onClick={handleOpenCreateModal}
                className="font-semibold text-xs"
              >
                <Plus className="w-4 h-4 mr-1.5" />
                Create First Design
              </Button>
            )}
          </div>
        </div>
      )}

      {/* Create / Edit Modal Dialog */}
      <DesignModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSubmit={handleSaveDesign}
        initialDesign={editingDesign}
      />

      {/* Delete Confirmation Modal */}
      <DesignDeleteModal
        isOpen={isDeleteModalOpen}
        onClose={() => setIsDeleteModalOpen(false)}
        onConfirm={handleConfirmDelete}
        design={deletingDesign}
      />
    </div>
  );
};

export default DesignsPage;
