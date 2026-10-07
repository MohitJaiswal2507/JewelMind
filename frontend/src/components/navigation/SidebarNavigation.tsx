import React from 'react';
import {
  Gem,
  LayoutDashboard,
  Layers,
  Palette,
  Factory,
  Hammer,
  TrendingUp,
  LogOut,
  User as UserIcon,
  PenTool,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import { ViewMode } from '../../App';
import { User } from '../../types/auth';
import { HealthResponse } from '../../types/api';

interface SidebarNavigationProps {
  currentView: ViewMode;
  currentPath?: string;
  user: User | null;
  backendHealth: HealthResponse | null;
  loadingHealth: boolean;
  onNavigate: (view: ViewMode, path?: string) => void;
  onLogout: () => void;
  isCollapsed?: boolean;
  onToggleCollapse?: () => void;
}

export const SidebarNavigation: React.FC<SidebarNavigationProps> = ({
  currentView,
  currentPath,
  user,
  backendHealth,
  loadingHealth,
  onNavigate,
  onLogout,
  isCollapsed = false,
  onToggleCollapse,
}) => {
  const isViewActive = (view: ViewMode, path?: string) => {
    const effective = currentPath || (typeof window !== 'undefined' ? window.location.pathname + window.location.search : '');
    if (view === 'designs' && currentView === 'design-detail') return true;
    if (view === 'canvas') return currentView === 'canvas' || effective.startsWith('/canvas');
    if (view === 'studio' && currentView === 'studio') return true;
    if (path && path.includes('shop-floor')) {
      return currentView === 'production' && effective.includes('shop-floor');
    }
    if (path && path.includes('analytics')) {
      return currentView === 'production' && (effective.includes('analytics') || effective.includes('yield'));
    }
    if (view === 'production' && currentView === 'production') {
      if (effective.includes('shop-floor') || effective.includes('analytics') || effective.includes('yield')) {
        return false;
      }
      return true;
    }
    return currentView === view;
  };

  const navItems: { view: ViewMode; path: string; label: string; icon: React.ElementType }[] = [
    { view: 'dashboard', path: '/dashboard', label: 'Overview', icon: LayoutDashboard },
    { view: 'designs', path: '/designs', label: 'Designs', icon: Layers },
    { view: 'canvas', path: '/canvas', label: 'Canvas', icon: PenTool },
    { view: 'studio', path: '/studio', label: 'Studio', icon: Palette },
    { view: 'production', path: '/production', label: 'Production', icon: Factory },
    { view: 'production', path: '/production?view=shop-floor', label: 'Shop Floor', icon: Hammer },
    { view: 'production', path: '/production?tab=analytics', label: 'Analytics', icon: TrendingUp },
  ];

  return (
    <aside
      className={`hidden lg:flex ${
        isCollapsed ? 'w-20 p-3' : 'w-64 p-5'
      } bg-[#080D0B] border-r border-[#1C2621] flex-col justify-between select-none h-screen sticky top-0 shrink-0 z-40 transition-all duration-300 ease-in-out`}
    >
      <div className="space-y-6">
        {/* Top Header: Logo & Collapse Button */}
        {isCollapsed ? (
          <div className="flex flex-col items-center py-1">
            <button
              onClick={onToggleCollapse}
              className="w-10 h-10 rounded-xl bg-[#141D19] border border-[#D8AD55]/40 flex items-center justify-center shadow-lg hover:border-[#D8AD55] transition-all cursor-pointer group relative"
              title="Expand Sidebar"
            >
              <Gem className="w-4 h-4 text-[#D8AD55] group-hover:scale-110 transition-transform" />
              <span className="absolute -bottom-1 -right-1 w-3.5 h-3.5 rounded-full bg-[#080D0B] border border-[#D8AD55]/40 flex items-center justify-center text-[8px] text-[#D8AD55] group-hover:bg-[#141D19]">
                <ChevronRight className="w-2.5 h-2.5" />
              </span>
            </button>
          </div>
        ) : (
          <div className="flex items-center justify-between px-1 py-1">
            <div
              onClick={() => onNavigate('dashboard', '/dashboard')}
              className="flex items-center space-x-3 cursor-pointer group"
            >
              <div className="w-9 h-9 rounded-xl bg-[#141D19] border border-[#D8AD55]/40 flex items-center justify-center shadow-lg group-hover:border-[#D8AD55] transition-all">
                <Gem className="w-4 h-4 text-[#D8AD55] group-hover:scale-110 transition-transform" />
              </div>
              <div>
                <span className="font-serif font-bold text-lg text-[#F4EFE5] group-hover:text-[#F1D28A] transition-colors">
                  JewelMind
                </span>
              </div>
            </div>

            {/* Collapse Button */}
            {onToggleCollapse && (
              <button
                onClick={onToggleCollapse}
                className="p-1.5 rounded-lg text-[#A9ADA7] hover:text-[#D8AD55] hover:bg-white/[0.05] transition-colors cursor-pointer"
                title="Collapse Sidebar"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
            )}
          </div>
        )}

        {/* Divider */}
        <div className="h-[1px] bg-[#1C2621]" />

        {/* Navigation Items */}
        <nav className="space-y-1.5">
          {!isCollapsed && (
            <div className="text-[10px] font-mono uppercase tracking-widest text-[#6F756F] px-3 pb-1">
              Workspace
            </div>
          )}

          {navItems.map((item) => {
            const Icon = item.icon;
            const active = isViewActive(item.view, item.path);

            if (isCollapsed) {
              return (
                <button
                  key={item.label}
                  onClick={() => onNavigate(item.view, item.path)}
                  title={item.label}
                  className={`w-full h-11 rounded-xl flex items-center justify-center transition-all duration-200 cursor-pointer relative group ${
                    active
                      ? 'bg-[#141D19] text-[#F1D28A] border border-[#D8AD55]/40 shadow-sm'
                      : 'text-[#A9ADA7] hover:text-[#F4EFE5] hover:bg-white/[0.04]'
                  }`}
                >
                  <Icon className={`w-4 h-4 ${active ? 'text-[#D8AD55]' : 'text-[#6F756F] group-hover:text-[#F4EFE5]'}`} />
                  {active && (
                    <span className="absolute right-1 w-1 h-3 rounded-full bg-[#D8AD55] shadow-[0_0_6px_#D8AD55]" />
                  )}
                </button>
              );
            }

            return (
              <button
                key={item.label}
                onClick={() => onNavigate(item.view, item.path)}
                className={`w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-xs font-medium transition-all duration-200 cursor-pointer ${
                  active
                    ? 'bg-[#141D19] text-[#F1D28A] border border-[#D8AD55]/30 shadow-sm font-semibold'
                    : 'text-[#A9ADA7] hover:text-[#F4EFE5] hover:bg-white/[0.03]'
                }`}
              >
                <div className="flex items-center space-x-3">
                  <Icon className={`w-4 h-4 ${active ? 'text-[#D8AD55]' : 'text-[#6F756F]'}`} />
                  <span>{item.label}</span>
                </div>
                {active && (
                  <span className="w-1.5 h-1.5 rounded-full bg-[#D8AD55] shadow-[0_0_8px_#D8AD55]" />
                )}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Bottom Area: Telemetry & User */}
      <div className={`pt-4 border-t border-[#1C2621] ${isCollapsed ? 'space-y-3 flex flex-col items-center' : 'space-y-4'}`}>
        {isCollapsed ? (
          <>
            {/* Collapsed Neural Core Indicator */}
            <div
              className="w-10 h-10 rounded-xl bg-[#0B1210] border border-[#1C2621] flex items-center justify-center cursor-default"
              title={backendHealth ? 'Neural Core Active' : 'Core Offline'}
            >
              <span className="relative flex h-2.5 w-2.5">
                <span
                  className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${
                    backendHealth ? 'bg-[#18A879]' : 'bg-rose-400'
                  }`}
                />
                <span
                  className={`relative inline-flex rounded-full h-2.5 w-2.5 ${
                    backendHealth ? 'bg-[#18A879]' : 'bg-rose-500'
                  }`}
                />
              </span>
            </div>

            {/* Collapsed User Avatar & Logout */}
            <button
              onClick={onLogout}
              className="w-10 h-10 rounded-xl bg-[#141D19] border border-[#D8AD55]/30 text-[#D8AD55] hover:border-rose-400 hover:text-rose-400 flex items-center justify-center text-xs font-bold transition cursor-pointer"
              title={`Signed in as ${user?.full_name || user?.email || 'User'} (Click to Sign Out)`}
            >
              {user?.full_name ? user.full_name[0].toUpperCase() : <UserIcon className="w-4 h-4" />}
            </button>
          </>
        ) : (
          <>
            {/* Neural Core Status Indicator */}
            <div className="flex items-center space-x-2.5 px-3 py-2 rounded-xl bg-[#0B1210] border border-[#1C2621] text-[11px] font-mono">
              <span className="relative flex h-2 w-2">
                <span
                  className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${
                    backendHealth ? 'bg-[#18A879]' : 'bg-rose-400'
                  }`}
                />
                <span
                  className={`relative inline-flex rounded-full h-2 w-2 ${
                    backendHealth ? 'bg-[#18A879]' : 'bg-rose-500'
                  }`}
                />
              </span>
              <span className="text-[#A9ADA7] truncate">
                {loadingHealth
                  ? 'Connecting...'
                  : backendHealth
                  ? 'Neural Core Active'
                  : 'Core Offline'}
              </span>
            </div>

            {/* User Monogram & Logout */}
            <div className="flex items-center justify-between p-2 rounded-xl bg-[#0B1210] border border-[#1C2621]">
              <div className="flex items-center space-x-2.5 min-w-0">
                <div className="w-7 h-7 rounded-lg bg-[#141D19] border border-[#D8AD55]/30 text-[#D8AD55] flex items-center justify-center text-xs font-bold shrink-0">
                  {user?.full_name ? user.full_name[0].toUpperCase() : <UserIcon className="w-3.5 h-3.5" />}
                </div>
                <div className="min-w-0">
                  <p className="text-xs font-medium text-[#F4EFE5] truncate">
                    {user?.full_name || user?.email || 'Artisan'}
                  </p>
                  <p className="text-[10px] text-[#6F756F] font-mono uppercase tracking-wider">
                    {user?.role || 'Artisan'}
                  </p>
                </div>
              </div>

              <button
                onClick={onLogout}
                className="p-1.5 rounded-lg text-[#6F756F] hover:text-rose-400 hover:bg-rose-500/10 transition-colors cursor-pointer"
                title="Sign Out"
              >
                <LogOut className="w-3.5 h-3.5" />
              </button>
            </div>
          </>
        )}
      </div>
    </aside>
  );
};

export default SidebarNavigation;
