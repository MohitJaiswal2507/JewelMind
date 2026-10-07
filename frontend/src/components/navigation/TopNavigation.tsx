import React, { useState } from 'react';
import {
  Gem,
  LayoutDashboard,
  Layers,
  Palette,
  Factory,
  Hammer,
  TrendingUp,
  LogOut,
  LogIn,
  UserPlus,
  Menu,
  X,
  User as UserIcon,
  PenTool,
} from 'lucide-react';
import { Button } from '../ui/button';
import { ViewMode } from '../../App';
import { HealthResponse } from '../../types/api';
import { User } from '../../types/auth';

interface TopNavigationProps {
  currentView: ViewMode;
  currentPath?: string;
  isAuthenticated: boolean;
  user: User | null;
  backendHealth: HealthResponse | null;
  loadingHealth: boolean;
  onNavigate: (view: ViewMode, path?: string) => void;
  onLogout: () => void;
}

export const TopNavigation: React.FC<TopNavigationProps> = ({
  currentView,
  currentPath,
  isAuthenticated,
  user,
  backendHealth,
  loadingHealth,
  onNavigate,
  onLogout,
}) => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navItems: { view: ViewMode; path: string; label: string; icon: React.ElementType }[] = [
    { view: 'dashboard', path: '/dashboard', label: 'Overview', icon: LayoutDashboard },
    { view: 'designs', path: '/designs', label: 'Designs', icon: Layers },
    { view: 'canvas', path: '/canvas', label: 'Canvas', icon: PenTool },
    { view: 'studio', path: '/studio', label: 'Studio', icon: Palette },
    { view: 'production', path: '/production', label: 'Production', icon: Factory },
    { view: 'production', path: '/production?view=shop-floor', label: 'Shop Floor', icon: Hammer },
    { view: 'production', path: '/production?tab=analytics', label: 'Analytics', icon: TrendingUp },
  ];

  const handleNavClick = (view: ViewMode, path: string) => {
    onNavigate(view, path);
    setMobileMenuOpen(false);
  };

  const isViewActive = (item: { view: ViewMode; path: string }) => {
    const effective = currentPath || (typeof window !== 'undefined' ? window.location.pathname + window.location.search : '');
    if (item.view === 'designs' && currentView === 'design-detail') return true;
    if (item.view === 'canvas') return currentView === 'canvas' || effective.startsWith('/canvas');
    if (item.view === 'studio' && currentView === 'studio') return true;
    if (item.path.includes('shop-floor')) {
      return currentView === 'production' && effective.includes('shop-floor');
    }
    if (item.path.includes('analytics')) {
      return currentView === 'production' && (effective.includes('analytics') || effective.includes('yield'));
    }
    if (item.path === '/production' && currentView === 'production') {
      if (effective.includes('shop-floor') || effective.includes('analytics') || effective.includes('yield')) {
        return false;
      }
      return true;
    }
    return currentView === item.view;
  };

  const isAuthView = isAuthenticated && currentView !== 'landing' && currentView !== 'login' && currentView !== 'register';

  return (
    <header className="border-b border-[#1C2621] bg-[#050806]/95 backdrop-blur-2xl sticky top-0 z-30 transition-all duration-300">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Left: Brand Monogram on public views, or mobile menu button on authenticated views */}
        <div className="flex items-center space-x-3.5">
          {!isAuthView ? (
            <div
              className="flex items-center space-x-3 cursor-pointer group select-none"
              onClick={() => onNavigate('landing', '/')}
            >
              <div className="w-8 h-8 rounded-xl bg-[#141D19] border border-[#D8AD55]/40 flex items-center justify-center shadow-lg group-hover:border-[#D8AD55] transition-all">
                <Gem className="w-4 h-4 text-[#D8AD55] group-hover:scale-110 transition-transform" />
              </div>
              <div>
                <span className="font-serif font-bold text-base tracking-wide text-[#F4EFE5] group-hover:text-[#F1D28A] transition-colors">
                  JewelMind
                </span>
              </div>
            </div>
          ) : (
            /* On mobile authenticated, provide drawer button without desktop logo/breadcrumbs */
            <div className="lg:hidden flex items-center">
              <button
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                className="p-1.5 rounded-lg text-[#A9ADA7] hover:text-[#F4EFE5] hover:bg-white/5 cursor-pointer"
                title="Toggle menu"
              >
                {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
              </button>
            </div>
          )}
        </div>



        {/* Right Section: Telemetry & Actions */}
        <div className="flex items-center space-x-3">
          {/* Neural Core Pill */}
          <div className="hidden sm:flex items-center space-x-2 px-3 py-1 rounded-full bg-[#0B1210] border border-[#1C2621] text-[11px] font-mono">
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
            <span className="text-[#A9ADA7]">
              {loadingHealth
                ? 'Connecting...'
                : backendHealth
                ? 'Neural Core Active'
                : 'Core Offline'}
            </span>
          </div>

          {/* User Auth Actions */}
          {isAuthenticated ? (
            <div className="flex items-center space-x-2">
              {user && (
                <div className="hidden sm:flex items-center space-x-2 px-3 py-1 rounded-xl bg-[#0B1210] border border-[#1C2621]">
                  <div className="w-5 h-5 rounded-full bg-[#141D19] text-[#D8AD55] border border-[#D8AD55]/30 flex items-center justify-center text-[10px] font-bold">
                    {user.full_name ? user.full_name[0].toUpperCase() : <UserIcon className="w-3 h-3" />}
                  </div>
                  <span className="text-xs text-[#F4EFE5] font-medium max-w-[120px] truncate">
                    {user.full_name || user.email}
                  </span>
                </div>
              )}

              <Button
                variant="outline"
                size="sm"
                onClick={onLogout}
                className="hidden sm:flex h-8 px-3 text-xs text-[#A9ADA7] hover:text-rose-300 hover:border-rose-500/30 border-[#1C2621]"
              >
                <LogOut className="w-3.5 h-3.5 mr-1.5" />
                <span>Sign Out</span>
              </Button>
            </div>
          ) : (
            <div className="flex items-center space-x-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => onNavigate('login', '/login')}
                className="h-8 px-3 text-xs font-medium text-[#A9ADA7] hover:text-white"
              >
                <LogIn className="w-3.5 h-3.5 mr-1.5" />
                Sign In
              </Button>
              <Button
                variant="gold"
                size="sm"
                onClick={() => onNavigate('register', '/register')}
                className="h-8 px-3.5 text-xs font-bold text-[#050806]"
              >
                <UserPlus className="w-3.5 h-3.5 mr-1.5 text-[#050806]" />
                Get Started
              </Button>
            </div>
          )}

          {/* Mobile Menu Toggle */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="lg:hidden p-2 rounded-xl bg-[#0B1210] border border-[#1C2621] text-[#A9ADA7] hover:text-[#F4EFE5] cursor-pointer"
            aria-label="Toggle navigation drawer"
          >
            {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {/* Mobile Drawer */}
      {mobileMenuOpen && (
        <div className="lg:hidden border-b border-[#1C2621] bg-[#080D0B] px-4 py-5 space-y-4">
          {isAuthenticated ? (
            <div className="space-y-1">
              {navItems.map((item) => {
                const Icon = item.icon;
                const active = isViewActive(item);
                return (
                  <button
                    key={item.label}
                    onClick={() => handleNavClick(item.view, item.path)}
                    className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-medium cursor-pointer ${
                      active
                        ? 'bg-[#141D19] text-[#F1D28A] border border-[#D8AD55]/30'
                        : 'text-[#A9ADA7] hover:text-white hover:bg-white/[0.04]'
                    }`}
                  >
                    <div className="flex items-center space-x-3">
                      <Icon className={`w-4 h-4 ${active ? 'text-[#D8AD55]' : 'text-[#6F756F]'}`} />
                      <span>{item.label}</span>
                    </div>
                    {active && <span className="w-1.5 h-1.5 rounded-full bg-[#D8AD55]" />}
                  </button>
                );
              })}

              <div className="pt-3 border-t border-[#1C2621]">
                <button
                  onClick={() => {
                    setMobileMenuOpen(false);
                    onLogout();
                  }}
                  className="w-full flex items-center space-x-3 px-3.5 py-2 rounded-xl text-xs text-rose-300 hover:bg-rose-500/10 cursor-pointer"
                >
                  <LogOut className="w-4 h-4" />
                  <span>Sign Out</span>
                </button>
              </div>
            </div>
          ) : (
            <div className="space-y-2 pt-2">
              <Button
                variant="gold"
                size="sm"
                onClick={() => {
                  setMobileMenuOpen(false);
                  onNavigate('register', '/register');
                }}
                className="w-full text-xs font-bold text-[#050806]"
              >
                Create Account
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  setMobileMenuOpen(false);
                  onNavigate('login', '/login');
                }}
                className="w-full text-xs text-[#F4EFE5] border-[#1C2621]"
              >
                Sign In
              </Button>
            </div>
          )}
        </div>
      )}
    </header>
  );
};

export default TopNavigation;
