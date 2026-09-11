import React, { useState, useEffect, useMemo } from 'react';
import { Loader2, AlertCircle } from 'lucide-react';
import { StudioSidebar } from '../components/studio/StudioSidebar';
import { StudioMediaGrid } from '../components/studio/StudioMediaGrid';
import { StudioMediaDetails } from '../components/studio/StudioMediaDetails';
import { StudioMediaItem } from '../components/studio/StudioMediaCard';
import { designService } from '../services/api/designService';
import { Design } from '../types/design';
import { useAuth } from '../hooks/useAuth';

interface StudioPageProps {
  onNavigateDesigns: () => void;
  onOpenCanvas: (designId: string) => void;
}

const generateSku = (design: Design): string => {
  const catCode = design.category.substring(0, 2).toUpperCase();
  const hexPart = design.id.replace(/-/g, '').substring(0, 6).toUpperCase();
  return `SKU #JM-${catCode}-${hexPart}`;
};

export const StudioPage: React.FC<StudioPageProps> = ({
  onNavigateDesigns,
  onOpenCanvas,
}) => {
  const { user } = useAuth();
  const [designs, setDesigns] = useState<Design[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Sidebar navigation & Collections
  const [activeSection, setActiveSection] = useState<string>('studio');
  const [selectedCollection, setSelectedCollection] = useState<string | null>(null);

  // Grid search & category filter
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [selectedCategory, setSelectedCategory] = useState<string>('All');

  // Selected media for right inspector
  const [selectedMedia, setSelectedMedia] = useState<StudioMediaItem | null>(null);

  const fetchStudioDesigns = async () => {
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
  };

  useEffect(() => {
    fetchStudioDesigns();
  }, []);

  // Map designs into Studio media items
  const allMediaItems: StudioMediaItem[] = useMemo(() => {
    return designs.map((d, index) => {
      let mediaType: 'PNG Sketch' | 'Photorealistic Render' | 'Vector Blueprint' = 'PNG Sketch';
      let thumbnailUrl = d.sketch_image_url || '';
      if (d.rendered_image_url) {
        mediaType = 'Photorealistic Render';
        thumbnailUrl = d.rendered_image_url;
      }

      return {
        id: d.id,
        designId: d.id,
        title: d.name,
        sku: generateSku(d),
        mediaType,
        thumbnailUrl,
        category: d.category,
        status: d.status,
        createdAt: d.created_at,
        creatorName: user?.full_name || 'Artisan',
        fileSize: `${(1.2 + (index % 5) * 0.4).toFixed(1)} MB`,
        design: d,
      };
    });
  }, [designs, user]);

  // Dynamic counts for sidebar collections
  const collectionCounts = useMemo(() => {
    const total = allMediaItems.length;
    const summer = allMediaItems.filter((_, i) => i % 3 === 0).length;
    const spring = allMediaItems.filter((_, i) => i % 3 === 1).length;
    const winter = allMediaItems.filter((_, i) => i % 3 === 2).length;
    return {
      total,
      'summer-25': summer,
      'spring-25': spring,
      'winter-24': winter,
    };
  }, [allMediaItems]);

  // Filtered media items
  const filteredItems = useMemo(() => {
    return allMediaItems.filter((item, index) => {
      // Collection filter
      if (selectedCollection === 'summer-25' && index % 3 !== 0) return false;
      if (selectedCollection === 'spring-25' && index % 3 !== 1) return false;
      if (selectedCollection === 'winter-24' && index % 3 !== 2) return false;

      // Section filter
      if (activeSection === 'trash') {
        if (item.status !== 'archived') return false;
      } else if (activeSection === 'recent') {
        if (index > 4) return false;
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
        if (!matchTitle && !matchSku && !matchCategory) return false;
      }

      return true;
    });
  }, [allMediaItems, selectedCollection, activeSection, selectedCategory, searchQuery]);

  const handleDeleteMedia = async (item: StudioMediaItem) => {
    await designService.deleteSketch(item.designId);
    setDesigns((prev) =>
      prev.map((d) => (d.id === item.designId ? { ...d, sketch_image_url: null } : d))
    );
    setSelectedMedia(null);
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
        />
      )}
    </div>
  );
};

export default StudioPage;
