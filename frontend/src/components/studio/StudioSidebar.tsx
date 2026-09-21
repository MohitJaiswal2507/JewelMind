import React from 'react';
import {
  Palette,
  FolderKanban,
  Clock,
  Trash2,
  Settings,
  Layers,
  CheckCircle2,
  Sparkles,
  Brush,
  Image as ImageIcon,
  SlidersHorizontal,
} from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';

export interface StudioSidebarProps {
  activeSection: string;
  onSelectSection: (section: string) => void;
  selectedCollection: string | null;
  onSelectCollection: (col: string | null) => void;
  collectionCounts: Record<string, number>;
  onNavigateDesigns: () => void;
}

const GUIDANCE_FILTERS = [
  { id: 'approved', name: 'Approved Renders', icon: CheckCircle2, color: 'text-amber-400' },
  { id: 'text', name: 'Text Guided', icon: Sparkles, color: 'text-amber-300' },
  { id: 'doodle', name: 'Doodle Guided', icon: Brush, color: 'text-amber-300' },
  { id: 'image', name: 'Image Guided', icon: ImageIcon, color: 'text-amber-300' },
  { id: 'sketches', name: 'Sketches / Blueprints', icon: Layers, color: 'text-slate-400' },
];

export const StudioSidebar: React.FC<StudioSidebarProps> = ({
  activeSection,
  onSelectSection,
  selectedCollection,
  onSelectCollection,
  collectionCounts,
  onNavigateDesigns,
}) => {
  const { user } = useAuth();

  return (
    <aside className="w-full lg:w-64 bg-[#0A0C12] border-r border-white/[0.07] flex flex-col justify-between select-none p-5 space-y-6 text-slate-300">
      <div className="space-y-6">
        {/* User Workspace Info */}
        <div className="flex items-center space-x-3 p-3 rounded-xl bg-[#0E111A] border border-white/5">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-amber-400 to-yellow-200 flex items-center justify-center font-bold text-slate-950 text-xs shadow-sm">
            {user?.full_name?.charAt(0) || 'A'}
          </div>
          <div className="min-w-0 flex-1">
            <div className="text-xs font-semibold text-white truncate font-serif">{user?.full_name || 'Artisan Studio'}</div>
            <div className="text-[10px] text-amber-300/80 font-mono truncate">{user?.role || 'Principal Jeweller'}</div>
          </div>
        </div>

        {/* Primary Navigation */}
        <div className="space-y-1">
          <div className="text-[10px] font-semibold text-slate-500 uppercase tracking-widest px-2 pb-1">
            Atelier Files
          </div>

          <button
            onClick={onNavigateDesigns}
            className="w-full flex items-center space-x-2.5 px-3 py-2 rounded-xl text-xs font-medium text-slate-400 hover:text-white hover:bg-white/5 transition cursor-pointer"
          >
            <FolderKanban className="w-4 h-4 text-slate-400" />
            <span>Design Portfolio</span>
          </button>

          <button
            onClick={() => {
              onSelectSection('studio');
              onSelectCollection(null);
            }}
            className={`w-full flex items-center justify-between px-3 py-2 rounded-xl text-xs font-semibold transition cursor-pointer ${
              activeSection === 'studio' && !selectedCollection
                ? 'bg-amber-400/15 text-amber-200 border border-amber-400/30 shadow-sm'
                : 'text-slate-400 hover:text-white hover:bg-white/5'
            }`}
          >
            <div className="flex items-center space-x-2.5">
              <Palette className="w-4 h-4 text-amber-300" />
              <span>Studio Lookbook</span>
            </div>
            <span className="text-[10px] px-2 py-0.5 rounded-full bg-[#121622] text-slate-400 font-mono">
              {collectionCounts.total || 0}
            </span>
          </button>

          <button
            onClick={() => onSelectSection('recent')}
            className={`w-full flex items-center space-x-2.5 px-3 py-2 rounded-xl text-xs font-medium transition cursor-pointer ${
              activeSection === 'recent'
                ? 'bg-amber-400/15 text-amber-200 border border-amber-400/30'
                : 'text-slate-400 hover:text-white hover:bg-white/5'
            }`}
          >
            <Clock className="w-4 h-4 text-slate-400" />
            <span>Recent Media</span>
          </button>

          <button
            onClick={() => onSelectSection('trash')}
            className={`w-full flex items-center space-x-2.5 px-3 py-2 rounded-xl text-xs font-medium transition cursor-pointer ${
              activeSection === 'trash'
                ? 'bg-amber-400/15 text-amber-200 border border-amber-400/30'
                : 'text-slate-400 hover:text-white hover:bg-white/5'
            }`}
          >
            <Trash2 className="w-4 h-4 text-slate-400" />
            <span>Archived</span>
          </button>
        </div>

        {/* Phase H: Guidance & Version Filters */}
        <div className="space-y-1.5 pt-3 border-t border-white/5">
          <div className="flex items-center justify-between px-2 pb-1 text-[10px] font-semibold text-slate-500 uppercase tracking-widest">
            <span>Guidance & Curation</span>
            <SlidersHorizontal className="w-3 h-3 text-slate-500" />
          </div>

          {GUIDANCE_FILTERS.map((gf) => {
            const count = collectionCounts[gf.id] || 0;
            const isSelected = selectedCollection === gf.id;
            const Icon = gf.icon;
            return (
              <button
                key={gf.id}
                onClick={() => {
                  onSelectSection('collections');
                  onSelectCollection(gf.id);
                }}
                className={`w-full flex items-center justify-between px-3 py-2 rounded-xl text-xs font-medium transition cursor-pointer ${
                  isSelected
                    ? 'bg-amber-400/15 text-amber-200 border border-amber-400/30'
                    : 'text-slate-400 hover:text-white hover:bg-white/5'
                }`}
              >
                <div className="flex items-center space-x-2.5 truncate">
                  <Icon className={`w-3.5 h-3.5 shrink-0 ${gf.color}`} />
                  <span className="truncate font-light">{gf.name}</span>
                </div>
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-[#121622] text-slate-400 font-mono shrink-0">
                  {count}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Bottom Settings Link */}
      <div className="pt-4 border-t border-white/5">
        <button
          onClick={() => onSelectSection('settings')}
          className={`w-full flex items-center space-x-2.5 px-3 py-2 rounded-xl text-xs font-medium transition cursor-pointer ${
            activeSection === 'settings'
              ? 'bg-amber-400/15 text-amber-200 border border-amber-400/30'
              : 'text-slate-400 hover:text-white hover:bg-white/5'
          }`}
        >
          <Settings className="w-4 h-4 text-slate-400" />
          <span>Studio Preferences</span>
        </button>
      </div>
    </aside>
  );
};
