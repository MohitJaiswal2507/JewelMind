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
  RefreshCw,
  Server,
  Code2
} from 'lucide-react';
import { Button } from './components/ui/button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from './components/ui/card';
import { Badge } from './components/ui/badge';
import { Separator } from './components/ui/separator';
import { healthService } from './services/api/healthService';
import { HealthResponse } from './types/api';

export const App: React.FC = () => {
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
          <div className="flex items-center space-x-3">
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
                  Phase 1
                </Badge>
              </div>
              <p className="text-xs text-slate-400 hidden sm:block">AI Jewellery Design & Production Platform</p>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            <Badge 
              variant={backendHealth ? 'success' : errorHealth ? 'destructive' : 'secondary'}
              className="flex items-center space-x-1.5 py-1 px-3"
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

            <Button 
              variant="outline" 
              size="sm" 
              onClick={checkHealth}
              disabled={loadingHealth}
              className="h-8 px-2.5 text-xs text-slate-300 hover:text-white"
            >
              <RefreshCw className={`w-3.5 h-3.5 mr-1 ${loadingHealth ? 'animate-spin' : ''}`} />
              <span className="hidden sm:inline">Refresh</span>
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12 w-full space-y-12 sm:space-y-16">
        {/* Hero Section */}
        <section className="text-center space-y-6 max-w-3xl mx-auto pt-4">
          <div className="inline-flex items-center space-x-2 px-4 py-1.5 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs font-medium">
            <ShieldCheck className="w-4 h-4 text-amber-400" />
            <span>Architecture & Technical Foundation Locked</span>
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

          <div className="flex flex-wrap justify-center gap-2 sm:gap-3 pt-2">
            <Badge variant="secondary" className="px-3 py-1 text-xs">
              ⚡ ₹0 Budget Architecture
            </Badge>
            <Badge variant="secondary" className="px-3 py-1 text-xs">
              🎮 Local RTX 4060 GPU Accelerated
            </Badge>
            <Badge variant="secondary" className="px-3 py-1 text-xs">
              ☁️ Cloudflare + Supabase Free Ecosystem
            </Badge>
            <Badge variant="secondary" className="px-3 py-1 text-xs">
              🎨 Tailwind CSS + shadcn/ui
            </Badge>
          </div>
        </section>

        {/* Phase 1 Status & Diagnostics Card */}
        <section>
          <Card className="bg-gradient-to-br from-slate-900/90 to-[#0d121f] border-slate-800 shadow-xl">
            <CardHeader className="pb-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div className="space-y-1">
                  <div className="flex items-center space-x-2">
                    <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                    <CardTitle className="text-lg sm:text-xl">Phase 1: Technical Contracts Established</CardTitle>
                  </div>
                  <CardDescription className="text-xs sm:text-sm">
                    SQLAlchemy & Alembic configured, versioned API `/api/v1` active, centralized logging & error handling operational, and typed frontend client connected.
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
                  <div className="text-xs text-slate-400 font-medium">Frontend UI</div>
                  <div className="text-sm font-semibold text-emerald-400">shadcn/ui + Tailwind</div>
                </div>
                <div className="p-3.5 bg-slate-950/60 rounded-xl border border-slate-800/70 space-y-1">
                  <div className="text-xs text-slate-400 font-medium">API Version</div>
                  <div className="text-sm font-semibold text-emerald-400">
                    {backendHealth?.version ? `v${backendHealth.version} (/api/v1)` : 'FastAPI v1'}
                  </div>
                </div>
                <div className="p-3.5 bg-slate-950/60 rounded-xl border border-slate-800/70 space-y-1">
                  <div className="text-xs text-slate-400 font-medium">Database Layer</div>
                  <div className="text-sm font-semibold text-amber-300">SQLAlchemy + Alembic</div>
                </div>
                <div className="p-3.5 bg-slate-950/60 rounded-xl border border-slate-800/70 space-y-1">
                  <div className="text-xs text-slate-400 font-medium">Next Milestone</div>
                  <div className="text-sm font-semibold text-slate-200">Phase 2: Auth</div>
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
                <CardTitle className="text-base">FastAPI V1 & Correlation</CardTitle>
              </div>
              <CardDescription className="text-xs leading-relaxed">
                Centralized error handling, standardized JSON schema serialization, request timing, and <code>X-Request-ID</code> correlation headers across all endpoints.
              </CardDescription>
            </CardHeader>
            <CardContent className="p-6 pt-0 text-xs font-mono text-slate-500 border-t border-slate-800/80">
              Router: <code>backend/app/api/v1/</code>
            </CardContent>
          </Card>

          <Card className="bg-[#0b0f19] border-slate-800">
            <CardHeader className="p-6 space-y-3">
              <div className="flex items-center space-x-3 text-amber-400">
                <Database className="w-5 h-5" />
                <CardTitle className="text-base">ORM & Migrations</CardTitle>
              </div>
              <CardDescription className="text-xs leading-relaxed">
                SQLAlchemy DeclarativeBase with UUID and Timestamp mixins, environment-driven engine session factory, and Alembic version migration infrastructure.
              </CardDescription>
            </CardHeader>
            <CardContent className="p-6 pt-0 text-xs font-mono text-slate-500 border-t border-slate-800/80">
              Database: <code>backend/app/db/</code>
            </CardContent>
          </Card>

          <Card className="bg-[#0b0f19] border-slate-800">
            <CardHeader className="p-6 space-y-3">
              <div className="flex items-center space-x-3 text-amber-400">
                <Code2 className="w-5 h-5" />
                <CardTitle className="text-base">Typed Frontend Client</CardTitle>
              </div>
              <CardDescription className="text-xs leading-relaxed">
                Clean, typed API abstraction with error re-mapping, environment-based URL injection (<code>VITE_API_URL</code>), and shadcn/ui design primitives.
              </CardDescription>
            </CardHeader>
            <CardContent className="p-6 pt-0 text-xs font-mono text-slate-500 border-t border-slate-800/80">
              Client: <code>frontend/src/services/api/</code>
            </CardContent>
          </Card>
        </section>
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
            <span>Phase 1 Architecture</span>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default App;
