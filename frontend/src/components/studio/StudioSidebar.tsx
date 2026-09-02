import {
  Palette,
  FolderKanban,
  Clock,
  Trash2,
  Settings,
  Layers,
  FolderOpen
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

const COLLECTIONS = [
  { id: 'summer-25', name: "Summer '25 Collection", tag: 'Summer 25' },
  { id: 'spring-25', name: "Spring '25 Bridal", tag: 'Spring 25' },
  { id: 'winter-24', name: "Winter '24 High Jewellery", tag: 'Winter 24' },
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
    <aside className="w-full lg:w-60 bg-[#070a12] border-r border-slate-800/90 flex flex-col justify-between select-none p-4 space-y-6 text-slate-300">
      <div className="space-y-6">
        {/* User Workspace Info */}
        <div className="flex items-center space-x-3 p-2 rounded-xl bg-slate-900/60 border border-slate-800">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-amber-500 to-amber-300 flex items-center justify-center font-bold text-slate-950 text-xs shadow">
            {user?.full_name?.charAt(0) || 'A'}
          </div>
          <div className="min-w-0 flex-1">
            <div className="text-xs font-bold text-white truncate">{user?.full_name || 'Artisan'}</div>
            <div className="text-[10px] text-amber-400/90 font-mono truncate">{user?.role || 'Master Jeweller'}</div>
          </div>
        </div>

        {/* Primary Navigation */}
        <div className="space-y-1">
          <div className="text-[10px] font-bold text-slate-500 uppercase tracking-wider px-2 pb-1">
            Workspace
          </div>

          <button
            onClick={onNavigateDesigns}
            className="w-full flex items-center space-x-2.5 px-3 py-2 rounded-xl text-xs font-medium text-slate-400 hover:text-white hover:bg-slate-900/60 transition"
          >
            <FolderKanban className="w-4 h-4 text-slate-400" />
            <span>Design Portfolio</span>
          </button>

          <button
            onClick={() => {
              onSelectSection('studio');
              onSelectCollection(null);
            }}
            className={`w-full flex items-center justify-between px-3 py-2 rounded-xl text-xs font-semibold transition ${
              activeSection === 'studio' && !selectedCollection
                ? 'bg-amber-400/15 text-amber-300 border border-amber-400/30'
                : 'text-slate-400 hover:text-white hover:bg-slate-900/60'
            }`}
          >
            <div className="flex items-center space-x-2.5">
              <Palette className="w-4 h-4 text-amber-400" />
              <span>Studio Files</span>
            </div>
            <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-slate-800 text-slate-400 font-mono">
              {collectionCounts.total || 0}
            </span>
          </button>

          <button
            onClick={() => onSelectSection('recent')}
            className={`w-full flex items-center space-x-2.5 px-3 py-2 rounded-xl text-xs font-medium transition ${
              activeSection === 'recent'
                ? 'bg-amber-400/15 text-amber-300 border border-amber-400/30'
                : 'text-slate-400 hover:text-white hover:bg-slate-900/60'
            }`}
          >
            <Clock className="w-4 h-4 text-slate-400" />
            <span>Recent Media</span>
          </button>

          <button
            onClick={() => onSelectSection('trash')}
            className={`w-full flex items-center space-x-2.5 px-3 py-2 rounded-xl text-xs font-medium transition ${
              activeSection === 'trash'
                ? 'bg-amber-400/15 text-amber-300 border border-amber-400/30'
                : 'text-slate-400 hover:text-white hover:bg-slate-900/60'
            }`}
          >
            <Trash2 className="w-4 h-4 text-slate-400" />
            <span>Trash</span>
          </button>
        </div>

        {/* Collections */}
        <div className="space-y-1.5 pt-2 border-t border-slate-800/80">
          <div className="flex items-center justify-between px-2 pb-1 text-[10px] font-bold text-slate-500 uppercase tracking-wider">
            <span>Seasonal Collections</span>
            <FolderOpen className="w-3 h-3" />
          </div>

          {COLLECTIONS.map((col) => {
            const count = collectionCounts[col.id] || 0;
            const isSelected = selectedCollection === col.id;
            return (
              <button
                key={col.id}
                onClick={() => {
                  onSelectSection('collections');
                  onSelectCollection(col.id);
                }}
                className={`w-full flex items-center justify-between px-3 py-2 rounded-xl text-xs font-medium transition ${
                  isSelected
                    ? 'bg-amber-400/15 text-amber-300 border border-amber-400/30'
                    : 'text-slate-400 hover:text-white hover:bg-slate-900/60'
                }`}
              >
                <div className="flex items-center space-x-2.5 truncate">
                  <Layers className="w-3.5 h-3.5 text-amber-400 shrink-0" />
                  <span className="truncate">{col.name}</span>
                </div>
                <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-slate-800 text-slate-400 font-mono shrink-0">
                  {count}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Bottom Settings Link */}
      <div className="pt-4 border-t border-slate-800/80">
        <button
          onClick={() => onSelectSection('settings')}
          className={`w-full flex items-center space-x-2.5 px-3 py-2 rounded-xl text-xs font-medium transition ${
            activeSection === 'settings'
              ? 'bg-amber-400/15 text-amber-300 border border-amber-400/30'
              : 'text-slate-400 hover:text-white hover:bg-slate-900/60'
          }`}
        >
          <Settings className="w-4 h-4 text-slate-400" />
          <span>Studio Settings</span>
        </button>
      </div>
    </aside>
  );
};
