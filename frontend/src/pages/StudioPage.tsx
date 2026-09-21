import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { Loader2, AlertCircle } from 'lucide-react';
import { StudioSidebar } from '../components/studio/StudioSidebar';
import { StudioMediaGrid } from '../components/studio/StudioMediaGrid';
import { StudioMediaDetails } from '../components/studio/StudioMediaDetails';
import { StudioMediaItem } from '../components/studio/StudioMediaCard';
import { StudioComparisonModal } from '../components/studio/StudioComparisonModal';
import { designService } from '../services/api/designService';
import { Design, DesignRender } from '../types/design';
import { useAuth } from '../hooks/useAuth';

interface StudioPageProps {
  onNavigateDesigns: () => void;
  onOpenCanvas: (designId: string) => void;
  onNavigateProduction?: (designId: string, renderId?: string) => void;
}

const generateSku = (design: Design): string => {
  const catCode = design.category.substring(0, 2).toUpperCase();
  const hexPart = design.id.replace(/-/g, '').substring(0, 6).toUpperCase();
  return `SKU #JM-${catCode}-${hexPart}`;
};

export const StudioPage: React.FC<StudioPageProps> = ({
  onNavigateDesigns,
  onOpenCanvas,
  onNavigateProduction,
}) => {
  const { user } = useAuth();
  const [designs, setDesigns] = useState<Design[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Sidebar navigation & Filters
  const [activeSection, setActiveSection] = useState<string>('studio');
  const [selectedCollection, setSelectedCollection] = useState<string | null>(null);

  // Grid search & category filter
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [selectedCategory, setSelectedCategory] = useState<string>('All');

  // Selected media for right inspector
  const [selectedMedia, setSelectedMedia] = useState<StudioMediaItem | null>(null);

  // Comparison modal state
  const [comparisonModalData, setComparisonModalData] = useState<{
    isOpen: boolean;
    design: Design | null;
    renders: DesignRender[];
    renderAId?: string;
    renderBId?: string;
  }>({
    isOpen: false,
    design: null,
    renders: [],
  });

  const fetchStudioDesigns = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await designService.getDesigns({ page_size: 100 });
      setDesigns(res.items);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to load studio media.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStudioDesigns();
  }, [fetchStudioDesigns]);

  // Map designs & render iterations into Studio media items
  const allMediaItems: StudioMediaItem[] = useMemo(() => {
    const items: StudioMediaItem[] = [];

    designs.forEach((d) => {
      const rendersList = d.renders || [];
      const totalRenders = rendersList.length;

      // If design has renders, add each render iteration
      if (totalRenders > 0) {
        rendersList.forEach((r) => {
          items.push({
            id: `render-${r.id}`,
            designId: d.id,
            title: totalRenders > 1 ? `${d.name} (V${r.version_number})` : d.name,
            sku: generateSku(d),
            mediaType: 'Photorealistic Render',
            thumbnailUrl: r.thumbnail_url || r.image_url,
            category: d.category,
            status: d.status,
            createdAt: r.created_at,
            creatorName: user?.full_name || 'Artisan',
            fileSize: '2.4 MB',
            design: d,
            versionNumber: r.version_number,
            renderId: r.id,
            renderMode: r.render_mode,
            isApprovedForProduction: r.is_approved_for_production,
            totalVersionsCount: totalRenders,
          });
        });
      } else if (d.rendered_image_url) {
        // Fallback for single render without renders relation
        items.push({
          id: `render-${d.id}`,
          designId: d.id,
          title: d.name,
          sku: generateSku(d),
          mediaType: 'Photorealistic Render',
          thumbnailUrl: d.rendered_image_url,
          category: d.category,
          status: d.status,
          createdAt: d.updated_at || d.created_at,
          creatorName: user?.full_name || 'Artisan',
          fileSize: '2.4 MB',
          design: d,
          versionNumber: 1,
          totalVersionsCount: 1,
        });
      }

      // Add sketch blueprint item if sketch exists
      if (d.sketch_image_url) {
        items.push({
          id: `sketch-${d.id}`,
          designId: d.id,
          title: totalRenders > 0 ? `${d.name} (Blueprint)` : d.name,
          sku: generateSku(d),
          mediaType: 'PNG Sketch',
          thumbnailUrl: d.sketch_image_url,
          category: d.category,
          status: d.status,
          createdAt: d.created_at,
          creatorName: user?.full_name || 'Artisan',
          fileSize: '1.2 MB',
          design: d,
          totalVersionsCount: totalRenders,
        });
      }
    });

    return items;
  }, [designs, user]);

  // Real dynamic counts for guidance & version filters
  const collectionCounts = useMemo(() => {
    const total = allMediaItems.length;
    const approved = allMediaItems.filter((m) => m.isApprovedForProduction).length;
    const text = allMediaItems.filter((m) => m.renderMode === 'text').length;
    const doodle = allMediaItems.filter((m) => m.renderMode === 'doodle').length;
    const image = allMediaItems.filter((m) => m.renderMode === 'image').length;
    const sketches = allMediaItems.filter((m) => m.mediaType === 'PNG Sketch').length;

    return {
      total,
      approved,
      text,
      doodle,
      image,
      sketches,
    };
  }, [allMediaItems]);

  // Filtered media items
  const filteredItems = useMemo(() => {
    return allMediaItems.filter((item, index) => {
      // Guidance & version filter
      if (selectedCollection === 'approved' && !item.isApprovedForProduction) return false;
      if (selectedCollection === 'text' && item.renderMode !== 'text') return false;
      if (selectedCollection === 'doodle' && item.renderMode !== 'doodle') return false;
      if (selectedCollection === 'image' && item.renderMode !== 'image') return false;
      if (selectedCollection === 'sketches' && item.mediaType !== 'PNG Sketch') return false;

      // Section filter
      if (activeSection === 'trash') {
        if (item.status !== 'archived') return false;
      } else if (activeSection === 'recent') {
        if (index > 8) return false;
      }

      // Category filter
      if (selectedCategory !== 'All' && item.category !== selectedCategory) {
        return false;
      }

      // Search keyword filter
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase().trim();
        const matchTitle = item.title.toLowerCase().includes(q);
        const matchSku = item.sku.toLowerCase().includes(q);
        const matchCategory = item.category.toLowerCase().includes(q);
        const matchMode = item.renderMode ? item.renderMode.toLowerCase().includes(q) : false;
        if (!matchTitle && !matchSku && !matchCategory && !matchMode) return false;
      }

      return true;
    });
  }, [allMediaItems, selectedCollection, activeSection, selectedCategory, searchQuery]);

  // Delete sketch asset
  const handleDeleteMedia = async (item: StudioMediaItem) => {
    await designService.deleteSketch(item.designId);
    setDesigns((prev) =>
      prev.map((d) => (d.id === item.designId ? { ...d, sketch_image_url: null } : d))
    );
    setSelectedMedia(null);
  };

  // Phase H: Approve render iteration
  const handleApproveRender = async (designId: string, renderId: string) => {
    await designService.approveRender(designId, renderId);
    setDesigns((prev) =>
      prev.map((d) => {
        if (d.id !== designId) return d;
        const updatedRenders = d.renders?.map((r) => ({
          ...r,
          is_approved_for_production: r.id === renderId,
        }));
        const approved = updatedRenders?.find((r) => r.id === renderId);
        return {
          ...d,
          rendered_image_url: approved ? approved.image_url : d.rendered_image_url,
          renders: updatedRenders,
        };
      })
    );
  };

  // Phase H: Delete render iteration
  const handleDeleteRender = async (designId: string, renderId: string) => {
    await designService.deleteRender(designId, renderId);
    setDesigns((prev) =>
      prev.map((d) => {
        if (d.id !== designId) return d;
        const remainingRenders = d.renders?.filter((r) => r.id !== renderId) || [];
        const latest = remainingRenders[remainingRenders.length - 1];
        return {
          ...d,
          rendered_image_url: latest ? latest.image_url : null,
          renders: remainingRenders,
        };
      })
    );
    setSelectedMedia(null);
  };

  // Open comparison modal
  const handleCompareVersions = (
    design: Design,
    renders: DesignRender[],
    renderAId?: string,
    renderBId?: string
  ) => {
    setComparisonModalData({
      isOpen: true,
      design,
      renders,
      renderAId,
      renderBId,
    });
  };

  // Production handoff
  const handleSendToProduction = (designId: string, renderId?: string) => {
    if (onNavigateProduction) {
      onNavigateProduction(designId, renderId);
    }
  };

  return (
    <div className="fixed inset-0 top-[72px] z-30 bg-[#08090D] flex overflow-hidden">
      {/* Left Sidebar */}
      <StudioSidebar
        activeSection={activeSection}
        onSelectSection={setActiveSection}
        selectedCollection={selectedCollection}
        onSelectCollection={setSelectedCollection}
        collectionCounts={collectionCounts}
        onNavigateDesigns={onNavigateDesigns}
      />

      {/* Main Studio Grid Content */}
      <main className="flex-1 flex flex-col h-full overflow-hidden">
        {loading ? (
          <div className="flex flex-col items-center justify-center h-full space-y-3 text-slate-400">
            <Loader2 className="w-8 h-8 animate-spin text-amber-300" />
            <span className="text-xs font-light">Loading Atelier Lookbook...</span>
          </div>
        ) : error ? (
          <div className="p-6 max-w-lg mx-auto my-12 bg-rose-500/10 border border-rose-500/30 rounded-2xl text-rose-300 text-xs flex items-center space-x-2.5">
            <AlertCircle className="w-5 h-5 shrink-0" />
            <span>{error}</span>
          </div>
        ) : (
          <StudioMediaGrid
            items={filteredItems}
            selectedItem={selectedMedia}
            onSelectItem={setSelectedMedia}
            searchQuery={searchQuery}
            onSearchChange={setSearchQuery}
            selectedCategory={selectedCategory}
            onSelectCategory={setSelectedCategory}
          />
        )}
      </main>

      {/* Right Side Media Details Inspector */}
      {selectedMedia && (
        <StudioMediaDetails
          item={selectedMedia}
          onClose={() => setSelectedMedia(null)}
          onOpenCanvas={onOpenCanvas}
          onDeleteMedia={handleDeleteMedia}
          onApproveRender={handleApproveRender}
          onDeleteRender={handleDeleteRender}
          onCompareVersions={handleCompareVersions}
          onSendToProduction={handleSendToProduction}
        />
      )}

      {/* Comparison Modal */}
      {comparisonModalData.isOpen && comparisonModalData.design && (
        <StudioComparisonModal
          isOpen={comparisonModalData.isOpen}
          onClose={() => setComparisonModalData((prev) => ({ ...prev, isOpen: false }))}
          design={comparisonModalData.design}
          renders={comparisonModalData.renders}
          initialRenderIdA={comparisonModalData.renderAId}
          initialRenderIdB={comparisonModalData.renderBId}
          onApproveRender={async (renderId) => {
            if (comparisonModalData.design) {
              await handleApproveRender(comparisonModalData.design.id, renderId);
            }
          }}
        />
      )}
    </div>
  );
};

export default StudioPage;
