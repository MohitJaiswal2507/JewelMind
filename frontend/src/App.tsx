import React, { useEffect, useState } from 'react';
import { 
  Sparkles, 
  Layers, 
  Cpu, 
  Clock, 
  ArrowRight,
  Sliders,
  LogIn,
  UserPlus,
  LayoutDashboard,
  LogOut,
  Palette,
  Brush,
  Factory,
  Gem
} from 'lucide-react';
import { Button } from './components/ui/button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from './components/ui/card';
import { healthService } from './services/api/healthService';
import { HealthResponse } from './types/api';
import { AuthProvider, useAuth } from './hooks/useAuth';
import { LoginPage } from './pages/LoginPage';
import { RegisterPage } from './pages/RegisterPage';
import { DashboardPage } from './pages/DashboardPage';
import { DesignsPage } from './pages/DesignsPage';
import { DesignDetailPage } from './pages/DesignDetailPage';
import { DesignWorkspacePage } from './pages/DesignWorkspacePage';
import { StudioPage } from './pages/StudioPage';
import { ProductionPage } from './pages/ProductionPage';
import { Design } from './types/design';

type ViewMode = 'landing' | 'login' | 'register' | 'dashboard' | 'designs' | 'design-detail' | 'studio' | 'canvas' | 'production';

const MainLayout: React.FC = () => {
  const { isAuthenticated, logout } = useAuth();

  const [currentView, setCurrentView] = useState<ViewMode>('landing');
  const [selectedDesignId, setSelectedDesignId] = useState<string | null>(null);
  const [backendHealth, setBackendHealth] = useState<HealthResponse | null>(null);
  const [loadingHealth, setLoadingHealth] = useState<boolean>(true);

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

  // Redirect to dashboard if user logs in
  const handleAuthSuccess = () => {
    setCurrentView('dashboard');
  };

  // Enforce route protection for private application views
  useEffect(() => {
    const protectedViews: ViewMode[] = ['dashboard', 'designs', 'design-detail', 'studio', 'canvas', 'production'];
    if (!isAuthenticated && protectedViews.includes(currentView)) {
      setCurrentView('login');
    }
  }, [isAuthenticated, currentView]);

  const handleSelectDesign = (design: Design | { id: string }) => {
    setSelectedDesignId(design.id);
    setCurrentView('design-detail');
  };

  const handleOpenCanvas = (designId?: string) => {
    if (designId) {
      setSelectedDesignId(designId);
      setCurrentView('canvas');
    } else {
      setCurrentView('designs');
    }
  };

  const handleBackToDesigns = () => {
    setSelectedDesignId(null);
    setCurrentView('designs');
  };

  const handleBackFromCanvas = () => {
    if (selectedDesignId) {
      setCurrentView('design-detail');
    } else {
      setCurrentView('designs');
    }
  };

  const workflowSteps = [
    {
      step: '01',
      title: 'Blueprint Sketching',
      desc: 'Precision HTML5 canvas with symmetry guides, geometry tools, and instant lineart extraction.',
      icon: Brush,
    },
    {
      step: '02',
      title: 'Diffusion Rendering',
      desc: 'ControlNet-conditioned structural diffusion rendering 18K gold, platinum, diamonds, and gemstones.',
      icon: Sparkles,
    },
    {
      step: '03',
      title: 'Computer Vision Analysis',
      desc: 'YOLO segmentation identifying prongs, bezels, gemstones, mounts, and structural connectors.',
      icon: Cpu,
    },
    {
      step: '04',
      title: 'Cost & Labor Estimation',
      desc: 'Predictive intelligence calculating precious metal gram weights, stone carats, and bench hours.',
      icon: Sliders,
    },
    {
      step: '05',
      title: 'Atelier Optimization',
      desc: 'Google OR-Tools CP-SAT scheduler balancing artisan bench capacity and casting machine runs.',
      icon: Clock,
    },
  ];

  return (
    <div className="min-h-screen bg-[#08090D] text-slate-100 flex flex-col font-sans selection:bg-amber-400/20 selection:text-amber-200">
      {/* Top Atelier Navigation */}
      <header className="border-b border-white/[0.07] bg-[#0A0C12]/90 backdrop-blur-xl sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-18 flex items-center justify-between">
          {/* Logo and Brand */}
          <div 
            className="flex items-center space-x-3.5 cursor-pointer group select-none"
            onClick={() => setCurrentView(isAuthenticated ? 'dashboard' : 'landing')}
          >
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-amber-400/20 via-amber-300/10 to-transparent border border-amber-400/30 flex items-center justify-center shadow-lg shadow-amber-500/5 group-hover:border-amber-400/60 transition-all duration-300">
              <Gem className="w-4 h-4 text-amber-300 group-hover:scale-110 transition-transform duration-300" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-serif font-semibold text-lg tracking-wide text-white group-hover:text-amber-200 transition-colors">
                  JewelMind
                </span>
                <span className="text-[10px] uppercase font-semibold tracking-widest text-amber-300/70 border border-amber-400/20 px-1.5 py-0.5 rounded">
                  Atelier
                </span>
              </div>
              <p className="text-[11px] text-slate-400 hidden sm:block tracking-wider font-light">AI Jewellery Studio & Production</p>
            </div>
          </div>

          {/* Navigation Items */}
          <div className="flex items-center space-x-2 sm:space-x-3">
            {/* System Status Pill */}
            <div className="hidden lg:flex items-center space-x-2 px-3 py-1 rounded-full bg-white/[0.03] border border-white/[0.06] text-[11px]">
              <span className="relative flex h-2 w-2">
                <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${backendHealth ? 'bg-emerald-400' : 'bg-rose-400'}`}></span>
                <span className={`relative inline-flex rounded-full h-2 w-2 ${backendHealth ? 'bg-emerald-500' : 'bg-rose-500'}`}></span>
              </span>
              <span className="text-slate-400">
                {loadingHealth
                  ? 'Connecting...'
                  : backendHealth
                  ? 'Neural Core Active'
                  : 'Core Offline'}
              </span>
            </div>

            {/* Authenticated Navigation */}
            {isAuthenticated ? (
              <div className="flex items-center space-x-1.5 sm:space-x-2">
                <Button
                  variant={currentView === 'dashboard' ? 'gold' : 'ghost'}
                  size="sm"
                  onClick={() => setCurrentView('dashboard')}
                  className="h-8.5 px-3 text-xs"
                >
                  <LayoutDashboard className="w-3.5 h-3.5 mr-1.5" />
                  <span className="hidden sm:inline">Overview</span>
                  <span className="sm:hidden">Home</span>
                </Button>

                <Button
                  variant={currentView === 'designs' || currentView === 'design-detail' ? 'gold' : 'ghost'}
                  size="sm"
                  onClick={() => setCurrentView('designs')}
                  className="h-8.5 px-3 text-xs"
                >
                  <Layers className="w-3.5 h-3.5 mr-1.5" />
                  Designs
                </Button>

                <Button
                  variant={currentView === 'studio' ? 'gold' : 'ghost'}
                  size="sm"
                  onClick={() => setCurrentView('studio')}
                  className="h-8.5 px-3 text-xs"
                >
                  <Palette className="w-3.5 h-3.5 mr-1.5" />
                  Studio
                </Button>

                <Button
                  variant={currentView === 'production' ? 'gold' : 'ghost'}
                  size="sm"
                  onClick={() => setCurrentView('production')}
                  className="h-8.5 px-3 text-xs"
                >
                  <Factory className="w-3.5 h-3.5 mr-1.5" />
                  Production
                </Button>

                <div className="h-4 w-[1px] bg-white/10 mx-1 hidden sm:block" />

                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    logout();
                    setCurrentView('landing');
                  }}
                  className="h-8.5 px-3 text-xs text-slate-300 hover:text-rose-300 hover:border-rose-500/30"
                >
                  <LogOut className="w-3.5 h-3.5 mr-1.5" />
                  <span className="hidden md:inline">Sign Out</span>
                </Button>
              </div>
            ) : (
              <div className="flex items-center space-x-2">
                <Button
                  variant={currentView === 'login' ? 'atelier' : 'ghost'}
                  size="sm"
                  onClick={() => setCurrentView('login')}
                  className="h-8.5 px-4 text-xs font-medium"
                >
                  <LogIn className="w-3.5 h-3.5 mr-1.5" />
                  Sign In
                </Button>
                <Button
                  variant={currentView === 'register' ? 'gold' : 'gold'}
                  size="sm"
                  onClick={() => setCurrentView('register')}
                  className="h-8.5 px-4 text-xs font-semibold"
                >
                  <UserPlus className="w-3.5 h-3.5 mr-1.5" />
                  Enter Atelier
                </Button>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Main View Router */}
      <main className="flex-1 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-10 w-full">
        {currentView === 'login' && (
          <LoginPage
            onNavigateToRegister={() => setCurrentView('register')}
            onSuccess={handleAuthSuccess}
          />
        )}

        {currentView === 'register' && (
          <RegisterPage
            onNavigateToLogin={() => setCurrentView('login')}
            onSuccess={handleAuthSuccess}
          />
        )}

        {currentView === 'dashboard' && (
          <DashboardPage 
            onLogout={() => setCurrentView('landing')} 
            onNavigateToDesigns={() => setCurrentView('designs')}
            onSelectDesign={handleSelectDesign}
            onNavigateToStudio={() => setCurrentView('studio')}
            onNavigateToProduction={() => setCurrentView('production')}
            onOpenCanvas={handleOpenCanvas}
          />
        )}

        {currentView === 'designs' && (
          <DesignsPage onSelectDesign={handleSelectDesign} />
        )}

        {currentView === 'design-detail' && selectedDesignId && (
          <DesignDetailPage
            designId={selectedDesignId}
            onBack={handleBackToDesigns}
            onOpenCanvas={handleOpenCanvas}
          />
        )}

        {currentView === 'canvas' && selectedDesignId && (
          <DesignWorkspacePage
            designId={selectedDesignId}
            onBack={handleBackFromCanvas}
          />
        )}

        {currentView === 'studio' && (
          <StudioPage
            onNavigateDesigns={() => setCurrentView('designs')}
            onOpenCanvas={handleOpenCanvas}
          />
        )}

        {currentView === 'production' && (
          <ProductionPage
            onNavigateToStudio={() => setCurrentView('studio')}
            onSelectDesign={handleSelectDesign}
          />
        )}

        {currentView === 'landing' && (
          <div className="space-y-16 sm:space-y-24 py-6">
            {/* Hero Section */}
            <section className="text-center space-y-8 max-w-3xl mx-auto">
              <div className="inline-flex items-center space-x-2 px-3.5 py-1.5 rounded-full bg-amber-400/10 border border-amber-400/20 text-amber-200 text-xs tracking-wider">
                <Sparkles className="w-3.5 h-3.5 text-amber-300" />
                <span>The Intelligent Fine Jewellery Atelier</span>
              </div>

              <h1 className="font-serif text-4xl sm:text-6xl lg:text-7xl font-normal tracking-tight text-white leading-[1.15]">
                From Initial Sketch to <br className="hidden sm:inline" />
                <span className="atelier-gold-text italic font-normal">
                  Masterpiece Production
                </span>
              </h1>

              <p className="text-sm sm:text-base text-slate-400/90 leading-relaxed max-w-xl mx-auto font-light">
                JewelMind bridges freehand jewellery sketching with precision ControlNet diffusion, 
                YOLO computer vision segmentation, and CP-SAT workshop optimization.
              </p>

              <div className="flex flex-wrap justify-center gap-3.5 pt-3">
                {isAuthenticated ? (
                  <div className="flex items-center gap-3">
                    <Button
                      variant="gold"
                      size="lg"
                      onClick={() => setCurrentView('dashboard')}
                      className="font-bold tracking-wide"
                    >
                      Enter Atelier Studio
                      <ArrowRight className="w-4 h-4 ml-2" />
                    </Button>
                    <Button
                      variant="outline"
                      size="lg"
                      onClick={() => setCurrentView('studio')}
                    >
                      View Studio Gallery
                    </Button>
                  </div>
                ) : (
                  <>
                    <Button
                      variant="gold"
                      size="lg"
                      onClick={() => setCurrentView('register')}
                      className="font-bold tracking-wide"
                    >
                      Begin Creating
                      <ArrowRight className="w-4 h-4 ml-2" />
                    </Button>
                    <Button
                      variant="outline"
                      size="lg"
                      onClick={() => setCurrentView('login')}
                    >
                      Sign In to Studio
                    </Button>
                  </>
                )}
              </div>
            </section>

            {/* Atelier Intelligence Matrix */}
            <section className="space-y-8">
              <div className="text-center space-y-2 max-w-lg mx-auto">
                <p className="text-[11px] font-semibold uppercase tracking-widest text-amber-300/80">Workflow Continuum</p>
                <h2 className="font-serif text-2xl sm:text-3xl text-white font-medium">The 5-Stage Jewellery Atelier</h2>
                <p className="text-xs sm:text-sm text-slate-400 font-light">End-to-end synergy from drawing canvas to artisan workbench</p>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
                {workflowSteps.map((item, idx) => {
                  const Icon = item.icon;
                  return (
                    <Card 
                      key={idx}
                      className="bg-[#0E111A]/90 border-white/[0.07] hover:border-amber-400/30 transition-all duration-300 group flex flex-col justify-between"
                    >
                      <CardHeader className="p-6 space-y-3">
                        <div className="flex items-center justify-between">
                          <span className="text-[11px] font-mono text-amber-300 font-semibold tracking-wider">{item.step}</span>
                          <div className="p-2 rounded-xl bg-white/[0.04] text-slate-400 group-hover:text-amber-300 group-hover:bg-amber-400/10 transition-all duration-300">
                            <Icon className="w-4 h-4" />
                          </div>
                        </div>
                        <CardTitle className="text-sm font-serif font-medium">{item.title}</CardTitle>
                        <CardDescription className="text-xs leading-relaxed text-slate-400 font-light">{item.desc}</CardDescription>
                      </CardHeader>
                      <CardContent className="p-6 pt-0">
                        <div className="text-[10px] font-semibold uppercase tracking-widest text-slate-500 flex items-center space-x-1 group-hover:text-amber-300 transition-colors">
                          <span>Stage Active</span>
                          <ArrowRight className="w-3 h-3 ml-0.5" />
                        </div>
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            </section>

            {/* Core Atelier Capabilities */}
            <section className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <Card className="bg-[#0E111A]/90 border-white/[0.07]">
                <CardHeader className="p-6 space-y-3">
                  <div className="flex items-center space-x-3 text-amber-300">
                    <Brush className="w-5 h-5" />
                    <CardTitle className="text-base font-serif font-medium">Interactive Drawing Desk</CardTitle>
                  </div>
                  <CardDescription className="text-xs leading-relaxed text-slate-400 font-light">
                    Real-time precision canvas with symmetry mirroring, stroke smoothing, custom jewelers grid, and direct LineArt serialization.
                  </CardDescription>
                </CardHeader>
              </Card>

              <Card className="bg-[#0E111A]/90 border-white/[0.07]">
                <CardHeader className="p-6 space-y-3">
                  <div className="flex items-center space-x-3 text-amber-300">
                    <Sparkles className="w-5 h-5" />
                    <CardTitle className="text-base font-serif font-medium">Diffusion Rendering Suite</CardTitle>
                  </div>
                  <CardDescription className="text-xs leading-relaxed text-slate-400 font-light">
                    Custom ControlNet conditioning pipeline tuned on 1000-step jewelers geometry with real-time material facet synthesis.
                  </CardDescription>
                </CardHeader>
              </Card>

              <Card className="bg-[#0E111A]/90 border-white/[0.07]">
                <CardHeader className="p-6 space-y-3">
                  <div className="flex items-center space-x-3 text-amber-300">
                    <Factory className="w-5 h-5" />
                    <CardTitle className="text-base font-serif font-medium">Operations & Scheduling</CardTitle>
                  </div>
                  <CardDescription className="text-xs leading-relaxed text-slate-400 font-light">
                    Constraint programming optimization for jewelers bench allocations, casting mold batches, and stone-setting bottlenecks.
                  </CardDescription>
                </CardHeader>
              </Card>
            </section>
          </div>
        )}
      </main>

      {/* Atelier Footer */}
      <footer className="border-t border-white/[0.06] py-8 bg-[#06070A] mt-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-slate-500">
          <div className="flex items-center space-x-2">
            <span className="font-serif text-slate-400">JewelMind</span>
            <span>— The AI Jewellery Atelier & Production Studio</span>
          </div>
          <div className="flex items-center space-x-4 sm:space-x-6 text-[11px] font-light">
            <span>ControlNet Diffusion</span>
            <span>•</span>
            <span>YOLO Segmentation</span>
            <span>•</span>
            <span>OR-Tools CP-SAT</span>
          </div>
        </div>
      </footer>
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
