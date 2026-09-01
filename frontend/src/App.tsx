import React, { useEffect, useState } from 'react';
import { 
  Sparkles, 
  Layers, 
  Cpu, 
  Clock, 
  ShieldCheck, 
  CheckCircle2, 
  ArrowRight,
  Database,
  Sliders,
  Server,
  Code2,
  LogIn,
  UserPlus,
  LayoutDashboard,
  LogOut
} from 'lucide-react';
import { Button } from './components/ui/button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from './components/ui/card';
import { Badge } from './components/ui/badge';
import { Separator } from './components/ui/separator';
import { healthService } from './services/api/healthService';
import { HealthResponse } from './types/api';
import { AuthProvider, useAuth } from './hooks/useAuth';
import { LoginPage } from './pages/LoginPage';
import { RegisterPage } from './pages/RegisterPage';
import { DashboardPage } from './pages/DashboardPage';

type ViewMode = 'landing' | 'login' | 'register' | 'dashboard';

const MainLayout: React.FC = () => {
  const { user, isAuthenticated, logout } = useAuth();
  const [currentView, setCurrentView] = useState<ViewMode>('landing');
  const [backendHealth, setBackendHealth] = useState<HealthResponse | null>(null);
  const [loadingHealth, setLoadingHealth] = useState<boolean>(true);
  const [errorHealth, setErrorHealth] = useState<string | null>(null);
  const [lastChecked, setLastChecked] = useState<string>('');

  const checkHealth = async () => {
    setLoadingHealth(true);
    setErrorHealth(null);
    try {
      const data = await healthService.getHealth();
      setBackendHealth(data);
      setLastChecked(new Date().toLocaleTimeString());
    } catch (err: unknown) {
      const errorMsg = err instanceof Error ? err.message : 'Connection failed';
      setErrorHealth(errorMsg);
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

  const workflowSteps = [
    {
      step: '01',
      title: 'Sketch Ingestion',
      desc: 'Freehand jewellery line drawings and dimension inputs',
      icon: Layers,
    },
    {
      step: '02',
      title: 'Generative Render',
      desc: 'ControlNet + Diffusion photorealistic metallic/gem previews',
      icon: Sparkles,
    },
    {
      step: '03',
      title: 'CV Component Detection',
      desc: 'YOLO object detection for gemstones, clasps, and connectors',
      icon: Cpu,
    },
    {
      step: '04',
      title: 'Predictive Analytics',
      desc: 'XGBoost cost, labor hours, and metal wastage predictions',
      icon: Sliders,
    },
    {
      step: '05',
      title: 'Production Scheduling',
      desc: 'Google OR-Tools CP-SAT workshop artisan & machine optimization',
      icon: Clock,
    },
  ];

  return (
    <div className="min-h-screen bg-[#07090e] text-slate-100 flex flex-col font-sans selection:bg-amber-500/30 selection:text-amber-200">
      {/* Top Navigation */}
      <header className="border-b border-slate-800/80 bg-[#0b0e17]/80 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div 
            className="flex items-center space-x-3 cursor-pointer"
            onClick={() => setCurrentView(isAuthenticated ? 'dashboard' : 'landing')}
          >
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-amber-500 via-amber-400 to-yellow-200 p-[1px] shadow-lg shadow-amber-500/10 shrink-0">
              <div className="w-full h-full bg-[#0b0e17] rounded-[11px] flex items-center justify-center">
                <Sparkles className="w-5 h-5 text-amber-400" />
              </div>
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-bold text-lg tracking-tight bg-gradient-to-r from-amber-200 via-amber-400 to-yellow-300 bg-clip-text text-transparent">
                  JewelMind
                </span>
                <Badge variant="gold" className="text-[10px] uppercase font-bold tracking-wider">
                  Phase 2
                </Badge>
              </div>
              <p className="text-xs text-slate-400 hidden sm:block">AI Jewellery Design & Production Platform</p>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            {/* Backend Health Pill */}
            <Badge 
              variant={backendHealth ? 'success' : errorHealth ? 'destructive' : 'secondary'}
              className="hidden sm:flex items-center space-x-1.5 py-1 px-3"
            >
              <span className="relative flex h-2 w-2">
                <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${backendHealth ? 'bg-emerald-400' : 'bg-rose-400'}`}></span>
                <span className={`relative inline-flex rounded-full h-2 w-2 ${backendHealth ? 'bg-emerald-500' : 'bg-rose-500'}`}></span>
              </span>
              <span className="text-xs">
                {loadingHealth
                  ? 'Connecting...'
                  : backendHealth
                  ? `API /v1: ${backendHealth.status.toUpperCase()}`
                  : 'Backend: Offline'}
              </span>
            </Badge>

            {/* Auth Buttons */}
            {isAuthenticated ? (
              <div className="flex items-center space-x-2">
                <Button
                  variant={currentView === 'dashboard' ? 'gold' : 'secondary'}
                  size="sm"
                  onClick={() => setCurrentView('dashboard')}
                  className="h-8 text-xs font-semibold"
                >
                  <LayoutDashboard className="w-3.5 h-3.5 mr-1.5" />
                  Dashboard
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    logout();
                    setCurrentView('landing');
                  }}
                  className="h-8 text-xs text-slate-300 hover:text-rose-400 hover:border-rose-500"
                >
                  <LogOut className="w-3.5 h-3.5 mr-1.5" />
                  <span className="hidden sm:inline">Sign Out</span>
                </Button>
              </div>
            ) : (
              <div className="flex items-center space-x-2">
                <Button
                  variant={currentView === 'login' ? 'gold' : 'ghost'}
                  size="sm"
                  onClick={() => setCurrentView('login')}
                  className="h-8 text-xs"
                >
                  <LogIn className="w-3.5 h-3.5 mr-1.5" />
                  Sign In
                </Button>
                <Button
                  variant={currentView === 'register' ? 'gold' : 'secondary'}
                  size="sm"
                  onClick={() => setCurrentView('register')}
                  className="h-8 text-xs font-semibold"
                >
                  <UserPlus className="w-3.5 h-3.5 mr-1.5" />
                  Register
                </Button>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Main View Router */}
      <main className="flex-1 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12 w-full">
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
          <DashboardPage onLogout={() => setCurrentView('landing')} />
        )}

        {currentView === 'landing' && (
          <div className="space-y-12 sm:space-y-16">
            {/* Hero Section */}
            <section className="text-center space-y-6 max-w-3xl mx-auto pt-4">
              <div className="inline-flex items-center space-x-2 px-4 py-1.5 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs font-medium">
                <ShieldCheck className="w-4 h-4 text-amber-400" />
                <span>Phase 2: Authentication & User Management Active</span>
              </div>

              <h1 className="text-3xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-white leading-tight">
                Connecting Jewellery Sketching to{' '}
                <span className="bg-gradient-to-r from-amber-300 via-amber-400 to-yellow-200 bg-clip-text text-transparent">
                  Precision Production
                </span>
              </h1>

              <p className="text-sm sm:text-base lg:text-lg text-slate-400 leading-relaxed max-w-2xl mx-auto">
                JewelMind combines generative diffusion, computer vision component detection, 
                machine learning estimation, and constraint-based workshop optimization in a single platform.
              </p>

              <div className="flex flex-wrap justify-center gap-3 pt-2">
                {isAuthenticated ? (
                  <Button
                    variant="gold"
                    size="lg"
                    onClick={() => setCurrentView('dashboard')}
                    className="font-bold"
                  >
                    Open Workspace Dashboard
                    <ArrowRight className="w-4 h-4 ml-2" />
                  </Button>
                ) : (
                  <>
                    <Button
                      variant="gold"
                      size="lg"
                      onClick={() => setCurrentView('register')}
                      className="font-bold"
                    >
                      Get Started (Register)
                      <ArrowRight className="w-4 h-4 ml-2" />
                    </Button>
                    <Button
                      variant="outline"
                      size="lg"
                      onClick={() => setCurrentView('login')}
                      className="border-slate-700"
                    >
                      Sign In
                    </Button>
                  </>
                )}
              </div>
            </section>

            {/* Phase 2 Status Card */}
            <section>
              <Card className="bg-gradient-to-br from-slate-900/90 to-[#0d121f] border-slate-800 shadow-xl">
                <CardHeader className="pb-4">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                    <div className="space-y-1">
                      <div className="flex items-center space-x-2">
                        <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                        <CardTitle className="text-lg sm:text-xl">Phase 2: Authentication Layer Verified</CardTitle>
                      </div>
                      <CardDescription className="text-xs sm:text-sm">
                        User registration, bcrypt password hashing, JWT access token generation, protected <code>/me</code> endpoints, and React AuthContext are active.
                      </CardDescription>
                    </div>
                    {lastChecked && (
                      <span className="text-[11px] text-slate-500 font-mono">
                        Last synced: {lastChecked}
                      </span>
                    )}
                  </div>
                </CardHeader>
                <Separator />
                <CardContent className="pt-6">
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4 text-center">
                    <div className="p-3.5 bg-slate-950/60 rounded-xl border border-slate-800/70 space-y-1">
                      <div className="text-xs text-slate-400 font-medium">Security</div>
                      <div className="text-sm font-semibold text-emerald-400">bcrypt + JWT HS256</div>
                    </div>
                    <div className="p-3.5 bg-slate-950/60 rounded-xl border border-slate-800/70 space-y-1">
                      <div className="text-xs text-slate-400 font-medium">User Status</div>
                      <div className="text-sm font-semibold text-amber-300">
                        {isAuthenticated ? user?.email : 'Unauthenticated'}
                      </div>
                    </div>
                    <div className="p-3.5 bg-slate-950/60 rounded-xl border border-slate-800/70 space-y-1">
                      <div className="text-xs text-slate-400 font-medium">Database Entity</div>
                      <div className="text-sm font-semibold text-emerald-400">Users Table & Alembic</div>
                    </div>
                    <div className="p-3.5 bg-slate-950/60 rounded-xl border border-slate-800/70 space-y-1">
                      <div className="text-xs text-slate-400 font-medium">Next Milestone</div>
                      <div className="text-sm font-semibold text-slate-200">Phase 3: Designs</div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </section>

            {/* Workflow Pipeline */}
            <section className="space-y-6">
              <div>
                <h2 className="text-xl sm:text-2xl font-bold text-white tracking-tight">End-to-End AI/ML Pipeline</h2>
                <p className="text-xs sm:text-sm text-slate-400">The 5-stage intelligent jewellery manufacturing workflow</p>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
                {workflowSteps.map((item, idx) => {
                  const Icon = item.icon;
                  return (
                    <Card 
                      key={idx}
                      className="bg-[#0b0f19] border-slate-800 hover:border-amber-500/40 transition duration-200 group flex flex-col justify-between"
                    >
                      <CardHeader className="p-5 space-y-3">
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-mono text-amber-400 font-semibold">{item.step}</span>
                          <div className="p-2 rounded-lg bg-slate-900 group-hover:bg-amber-500/10 text-slate-400 group-hover:text-amber-400 transition">
                            <Icon className="w-4 h-4" />
                          </div>
                        </div>
                        <CardTitle className="text-sm">{item.title}</CardTitle>
                        <CardDescription className="text-xs leading-relaxed">{item.desc}</CardDescription>
                      </CardHeader>
                      <CardContent className="p-5 pt-0">
                        <div className="text-[11px] font-medium text-slate-500 flex items-center space-x-1 group-hover:text-amber-400/80 transition">
                          <span>Target Stage</span>
                          <ArrowRight className="w-3 h-3 ml-0.5" />
                        </div>
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            </section>

            {/* Technical Architecture Foundations */}
            <section className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <Card className="bg-[#0b0f19] border-slate-800">
                <CardHeader className="p-6 space-y-3">
                  <div className="flex items-center space-x-3 text-amber-400">
                    <Server className="w-5 h-5" />
                    <CardTitle className="text-base">Secure Auth Endpoints</CardTitle>
                  </div>
                  <CardDescription className="text-xs leading-relaxed">
                    <code>/register</code>, <code>/login</code>, protected <code>/me</code>, and <code>/logout</code> endpoints validating input, checking duplicate emails (409), and generating signed JWTs.
                  </CardDescription>
                </CardHeader>
                <CardContent className="p-6 pt-0 text-xs font-mono text-slate-500 border-t border-slate-800/80">
                  Router: <code>backend/app/api/v1/auth.py</code>
                </CardContent>
              </Card>

              <Card className="bg-[#0b0f19] border-slate-800">
                <CardHeader className="p-6 space-y-3">
                  <div className="flex items-center space-x-3 text-amber-400">
                    <Database className="w-5 h-5" />
                    <CardTitle className="text-base">Users Table & Alembic</CardTitle>
                  </div>
                  <CardDescription className="text-xs leading-relaxed">
                    SQLAlchemy <code>User</code> model with UUID primary key, indexed unique email, bcrypt hash storage, and active status tracking via migration <code>0001_create_users</code>.
                  </CardDescription>
                </CardHeader>
                <CardContent className="p-6 pt-0 text-xs font-mono text-slate-500 border-t border-slate-800/80">
                  Model: <code>backend/app/models/user.py</code>
                </CardContent>
              </Card>

              <Card className="bg-[#0b0f19] border-slate-800">
                <CardHeader className="p-6 space-y-3">
                  <div className="flex items-center space-x-3 text-amber-400">
                    <Code2 className="w-5 h-5" />
                    <CardTitle className="text-base">React Auth Context</CardTitle>
                  </div>
                  <CardDescription className="text-xs leading-relaxed">
                    Centralized authentication state provider with automatic bearer token attachment, error toasts, and protected workspace views.
                  </CardDescription>
                </CardHeader>
                <CardContent className="p-6 pt-0 text-xs font-mono text-slate-500 border-t border-slate-800/80">
                  Hook: <code>frontend/src/hooks/useAuth.ts</code>
                </CardContent>
              </Card>
            </section>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-900 py-8 bg-[#04060a] mt-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-slate-500">
          <p>© 2026 JewelMind — AI Jewellery Design, Analysis & Production Planning Platform</p>
          <div className="flex items-center space-x-4 sm:space-x-6">
            <span>₹0 Budget Architecture</span>
            <span>•</span>
            <span>RTX 4060 Accelerated</span>
            <span>•</span>
            <span>Phase 2 Authentication</span>
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
