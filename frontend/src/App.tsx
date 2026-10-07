import React, { useEffect, useState, useCallback, Suspense } from 'react';
import { Gem, Loader2 } from 'lucide-react';
import { healthService } from './services/api/healthService';
import { HealthResponse } from './types/api';
import { AuthProvider, useAuth } from './hooks/useAuth';
import { TopNavigation } from './components/navigation/TopNavigation';
import { SidebarNavigation } from './components/navigation/SidebarNavigation';
import { LandingPage } from './pages/LandingPage';
import { Design } from './types/design';

// Code-split application pages on-demand for lightning-fast initial load
const LoginPage = React.lazy(() => import('./pages/LoginPage').then(m => ({ default: m.LoginPage || m.default })));
const RegisterPage = React.lazy(() => import('./pages/RegisterPage').then(m => ({ default: m.RegisterPage || m.default })));
const DashboardPage = React.lazy(() => import('./pages/DashboardPage').then(m => ({ default: m.DashboardPage || m.default })));
const DesignsPage = React.lazy(() => import('./pages/DesignsPage').then(m => ({ default: m.DesignsPage || m.default })));
const DesignDetailPage = React.lazy(() => import('./pages/DesignDetailPage').then(m => ({ default: m.DesignDetailPage || m.default })));
const DesignWorkspacePage = React.lazy(() => import('./pages/DesignWorkspacePage').then(m => ({ default: m.DesignWorkspacePage || m.default })));
const StudioPage = React.lazy(() => import('./pages/StudioPage').then(m => ({ default: m.StudioPage || m.default })));
const ProductionPage = React.lazy(() => import('./pages/ProductionPage').then(m => ({ default: m.ProductionPage })));

export type ViewMode = 'landing' | 'login' | 'register' | 'dashboard' | 'designs' | 'design-detail' | 'studio' | 'canvas' | 'production';

export const parseRouteFromLocation = (): { view: ViewMode; designId: string | null } => {
  if (typeof window === 'undefined') return { view: 'landing', designId: null };
  const pathname = window.location.pathname.toLowerCase().replace(/\/$/, '') || '/';
  const params = new URLSearchParams(window.location.search);
  const idFromParam = params.get('id') || params.get('designId');

  if (pathname === '/login') return { view: 'login', designId: null };
  if (pathname === '/register') return { view: 'register', designId: null };
  if (pathname === '/dashboard') return { view: 'dashboard', designId: null };
  if (pathname === '/designs') {
    if (idFromParam) return { view: 'design-detail', designId: idFromParam };
    return { view: 'designs', designId: null };
  }
  if (pathname.startsWith('/designs/')) {
    const id = pathname.substring('/designs/'.length);
    if (id) return { view: 'design-detail', designId: id };
    return { view: 'designs', designId: null };
  }
  if (pathname === '/studio') return { view: 'studio', designId: null };
  if (pathname === '/canvas') {
    return { view: 'canvas', designId: idFromParam };
  }
  if (pathname.startsWith('/canvas/')) {
    const id = pathname.substring('/canvas/'.length);
    return { view: 'canvas', designId: id || null };
  }
  if (pathname === '/production' || pathname === '/shop-floor' || pathname === '/analytics' || pathname === '/yield-analytics') {
    return { view: 'production', designId: idFromParam };
  }

  return { view: 'landing', designId: null };
};

export const getPathForView = (view: ViewMode, designId?: string | null): string => {
  switch (view) {
    case 'login': return '/login';
    case 'register': return '/register';
    case 'dashboard': return '/dashboard';
    case 'designs': return '/designs';
    case 'design-detail': return designId ? `/designs?id=${designId}` : '/designs';
    case 'studio': return '/studio';
    case 'canvas': return designId ? `/canvas?id=${designId}` : '/canvas';
    case 'production': {
      if (typeof window !== 'undefined' && window.location.pathname.startsWith('/production') && window.location.search) {
        return `/production${window.location.search}`;
      }
      return '/production';
    }
    case 'landing':
    default:
      return '/';
  }
};

const MainLayout: React.FC = () => {
  const { isAuthenticated, isLoading, logout, user } = useAuth();

  const initialRoute = parseRouteFromLocation();
  const [currentView, setCurrentView] = useState<ViewMode>(initialRoute.view);
  const [selectedDesignId, setSelectedDesignId] = useState<string | null>(initialRoute.designId);
  const [currentPath, setCurrentPath] = useState<string>(() =>
    typeof window !== 'undefined' ? window.location.pathname + window.location.search : '/'
  );
  const [backendHealth, setBackendHealth] = useState<HealthResponse | null>(null);
  const [loadingHealth, setLoadingHealth] = useState<boolean>(true);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState<boolean>(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('jewelmind_sidebar_collapsed') === 'true';
    }
    return false;
  });

  const toggleSidebar = () => {
    setIsSidebarCollapsed((prev) => {
      const next = !prev;
      if (typeof window !== 'undefined') {
        localStorage.setItem('jewelmind_sidebar_collapsed', String(next));
      }
      return next;
    });
  };

  // Centralized navigation helper that synchronizes internal state and HTML5 History
  const navigateTo = useCallback((view: ViewMode, customPath?: string, options?: { replace?: boolean; designId?: string | null }) => {
    setCurrentView(view);
    if (options?.designId !== undefined) {
      setSelectedDesignId(options.designId);
    }
    const targetPath = customPath || getPathForView(view, options?.designId !== undefined ? options.designId : selectedDesignId);
    setCurrentPath(targetPath);
    if (typeof window !== 'undefined') {
      const currentFull = window.location.pathname + window.location.search;
      if (options?.replace) {
        window.history.replaceState(null, '', targetPath);
      } else if (currentFull !== targetPath) {
        window.history.pushState(null, '', targetPath);
      }
      window.dispatchEvent(new Event('app-location-change'));
    }
  }, [selectedDesignId]);

  // Handle browser Back / Forward navigation (popstate)
  useEffect(() => {
    const handlePopState = () => {
      const { view, designId } = parseRouteFromLocation();
      setCurrentView(view);
      setSelectedDesignId(designId);
      if (typeof window !== 'undefined') {
        setCurrentPath(window.location.pathname + window.location.search);
      }
    };

    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);

  const checkHealth = async () => {
    setLoadingHealth(true);
    try {
      const data = await healthService.getHealth();
      setBackendHealth(data);
    } catch {
      setBackendHealth(null);
    } finally {
      setLoadingHealth(false);
    }
  };

  useEffect(() => {
    checkHealth();
  }, []);

  // Enforce route protection for private application views ONLY AFTER auth token initialization completes
  useEffect(() => {
    if (isLoading) return; // Prevent premature redirect while verifying stored token!

    const protectedViews: ViewMode[] = ['dashboard', 'designs', 'design-detail', 'studio', 'canvas', 'production'];
    if (!isAuthenticated && protectedViews.includes(currentView)) {
      // Save intended destination so after login user lands back on it
      const currentFull = typeof window !== 'undefined' ? window.location.pathname + window.location.search : '/';
      if (typeof window !== 'undefined') {
        sessionStorage.setItem('jewelmind_intended_path', currentFull);
      }
      navigateTo('login', '/login', { replace: true });
    } else if (isAuthenticated && (currentView === 'login' || currentView === 'register')) {
      const intended = typeof window !== 'undefined' ? sessionStorage.getItem('jewelmind_intended_path') : null;
      if (intended) {
        sessionStorage.removeItem('jewelmind_intended_path');
        const parsed = parseRouteFromLocation();
        navigateTo(parsed.view, intended, { replace: true });
      } else {
        navigateTo('dashboard', '/dashboard', { replace: true });
      }
    }
  }, [isAuthenticated, isLoading, currentView, navigateTo]);

  // Redirect after user logs in or registers
  const handleAuthSuccess = () => {
    const intended = typeof window !== 'undefined' ? sessionStorage.getItem('jewelmind_intended_path') : null;
    if (intended) {
      sessionStorage.removeItem('jewelmind_intended_path');
      const parsed = parseRouteFromLocation();
      navigateTo(parsed.view, intended, { replace: true });
      return;
    }

    const { view } = parseRouteFromLocation();
    if (view !== 'login' && view !== 'register' && view !== 'landing') {
      const path = window.location.pathname + window.location.search;
      navigateTo(view, path, { replace: true });
    } else {
      navigateTo('dashboard', '/dashboard', { replace: true });
    }
  };

  const handleSelectDesign = (design: Design | { id: string }) => {
    navigateTo('design-detail', `/designs?id=${design.id}`, { designId: design.id });
  };

  const handleOpenCanvas = (designId?: string) => {
    if (designId) {
      navigateTo('canvas', `/canvas?id=${designId}`, { designId });
    } else {
      navigateTo('canvas', '/canvas', { designId: null });
    }
  };

  const handleBackToDesigns = () => {
    navigateTo('designs', '/designs', { designId: null });
  };

  const handleBackFromCanvas = () => {
    if (selectedDesignId) {
      navigateTo('design-detail', `/designs?id=${selectedDesignId}`, { designId: selectedDesignId });
    } else {
      navigateTo('designs', '/designs', { designId: null });
    }
  };

  // While auth session is restoring from localStorage token, display seamless loading screen without redirect flashes
  if (isLoading) {
    return (
      <div className="min-h-screen bg-[#050506] text-slate-100 flex flex-col items-center justify-center font-sans">
        <div className="flex flex-col items-center space-y-4">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-amber-400/20 via-amber-300/10 to-transparent border border-amber-400/30 flex items-center justify-center shadow-lg shadow-amber-500/10 animate-pulse">
            <Gem className="w-6 h-6 text-amber-300" />
          </div>
          <div className="text-center space-y-1">
            <h2 className="font-serif text-lg font-semibold tracking-wide text-white">JewelMind Atelier</h2>
            <p className="text-xs text-slate-400 font-light tracking-wider flex items-center justify-center gap-2">
              <Loader2 className="w-3.5 h-3.5 animate-spin text-amber-300" />
              Restoring atelier session...
            </p>
          </div>
        </div>
      </div>
    );
  }

  const isAuthView = isAuthenticated && currentView !== 'landing' && currentView !== 'login' && currentView !== 'register';

  return (
    <div className="min-h-screen bg-[#050806] text-[#F4EFE5] flex flex-row font-sans selection:bg-[#D8AD55]/20 selection:text-[#F1D28A]">
      {/* Left Sidebar for Authenticated Application Views */}
      {isAuthView && (
        <SidebarNavigation
          currentView={currentView}
          currentPath={currentPath}
          user={user}
          backendHealth={backendHealth}
          loadingHealth={loadingHealth}
          isCollapsed={isSidebarCollapsed}
          onToggleCollapse={toggleSidebar}
          onNavigate={(view, path) => navigateTo(view, path)}
          onLogout={() => {
            logout();
            navigateTo('landing', '/', { replace: true });
          }}
        />
      )}

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top Atelier Navigation Shell */}
        <TopNavigation
          currentView={currentView}
          currentPath={currentPath}
          isAuthenticated={isAuthenticated}
          user={user}
          backendHealth={backendHealth}
          loadingHealth={loadingHealth}
          onNavigate={(view, path) => navigateTo(view, path)}
          onLogout={() => {
            logout();
            navigateTo('landing', '/', { replace: true });
          }}
        />

        {/* Main View Router & Container */}
        <main
          className={`flex-1 w-full ${
            currentView === 'canvas'
              ? 'p-0'
              : 'max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-10'
          }`}
        >
          <Suspense
            fallback={
              <div className="flex-1 min-h-[50vh] flex flex-col items-center justify-center space-y-3">
                <div className="w-10 h-10 rounded-xl bg-[#0B1210] border border-[#1C2621] flex items-center justify-center animate-pulse shadow-lg shadow-black/40">
                  <Gem className="w-5 h-5 text-[#D8AD55]" />
                </div>
                <div className="flex items-center gap-2 text-xs font-mono text-[#A9ADA7]">
                  <Loader2 className="w-3.5 h-3.5 animate-spin text-[#D8AD55]" />
                  <span>Loading view...</span>
                </div>
              </div>
            }
          >
            {currentView === 'login' && (
              <LoginPage
                onNavigateToRegister={() => navigateTo('register', '/register')}
                onSuccess={handleAuthSuccess}
              />
            )}

            {currentView === 'register' && (
              <RegisterPage
                onNavigateToLogin={() => navigateTo('login', '/login')}
                onSuccess={handleAuthSuccess}
              />
            )}

            {currentView === 'dashboard' && (
              <DashboardPage 
                onLogout={() => {
                  logout();
                  navigateTo('landing', '/', { replace: true });
                }} 
                onNavigateToDesigns={() => navigateTo('designs', '/designs')}
                onSelectDesign={handleSelectDesign}
                onNavigateToStudio={() => navigateTo('studio', '/studio')}
                onNavigateToProduction={() => navigateTo('production', '/production')}
                onOpenCanvas={handleOpenCanvas}
              />
            )}

            {currentView === 'designs' && (
              <DesignsPage onSelectDesign={handleSelectDesign} onOpenCanvas={handleOpenCanvas} />
            )}

            {currentView === 'design-detail' && selectedDesignId && (
              <DesignDetailPage
                designId={selectedDesignId}
                onBack={handleBackToDesigns}
                onOpenCanvas={handleOpenCanvas}
              />
            )}

            {currentView === 'canvas' && (
              <DesignWorkspacePage
                designId={selectedDesignId || undefined}
                onBack={handleBackFromCanvas}
              />
            )}

            {currentView === 'studio' && (
              <StudioPage
                onNavigateDesigns={() => navigateTo('designs', '/designs')}
                onOpenCanvas={handleOpenCanvas}
                onNavigateProduction={(designId, renderId) => {
                  const query = designId
                    ? `?tab=orders&designId=${designId}${renderId ? `&renderId=${renderId}` : ''}`
                    : '?tab=orders';
                  navigateTo('production', `/production${query}`);
                }}
              />
            )}

            {currentView === 'production' && (
              <ProductionPage
                onNavigateToStudio={() => navigateTo('studio', '/studio')}
                onSelectDesign={handleSelectDesign}
              />
            )}

            {currentView === 'landing' && (
              <LandingPage
                isAuthenticated={isAuthenticated}
                onEnterAtelier={() => navigateTo(isAuthenticated ? 'dashboard' : 'register', isAuthenticated ? '/dashboard' : '/register')}
                onExploreAtelier={() => {
                  if (isAuthenticated) {
                    navigateTo('studio', '/studio');
                  } else {
                    navigateTo('login', '/login');
                  }
                }}
                onSignIn={() => navigateTo('login', '/login')}
              />
            )}
          </Suspense>
        </main>

        {/* Footer */}
        {currentView !== 'canvas' && (
          <footer className="border-t border-[#1C2621] py-8 bg-[#050806] mt-auto">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-[#6F756F]">
              <div className="flex items-center space-x-2">
                <span className="font-serif text-[#F4EFE5] font-medium">JewelMind</span>
                <span>— AI Jewellery Design &amp; Manufacturing System</span>
              </div>
              <div className="flex items-center space-x-4 sm:space-x-6 text-[11px] font-mono text-[#A9ADA7]">
                <span>ControlNet Diffusion</span>
                <span>•</span>
                <span>YOLO Segmentation</span>
                <span>•</span>
                <span>OR-Tools CP-SAT</span>
              </div>
            </div>
          </footer>
        )}
      </div>
    </div>
  );
};

export const App: React.FC = () => {
  return (
    <AuthProvider>
      <MainLayout />
    </AuthProvider>
  );
};

export default App;
