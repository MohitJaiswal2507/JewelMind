import React, { useEffect, useState } from 'react';
import { 
  Sparkles, 
  Layers, 
  Cpu, 
  Clock, 
  Activity, 
  ShieldCheck, 
  CheckCircle2, 
  ArrowRight,
  Database,
  Sliders,
  FolderGit2
} from 'lucide-react';

interface HealthStatus {
  status: string;
  service: string;
  version: string;
  environment: string;
}

export const App: React.FC = () => {
  const [backendHealth, setBackendHealth] = useState<HealthStatus | null>(null);
  const [loadingHealth, setLoadingHealth] = useState<boolean>(true);
  const [errorHealth, setErrorHealth] = useState<string | null>(null);

  useEffect(() => {
    fetch('http://localhost:8000/health')
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then((data: HealthStatus) => {
        setBackendHealth(data);
        setLoadingHealth(false);
      })
      .catch((err) => {
        setErrorHealth(err.message);
        setLoadingHealth(false);
      });
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
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-amber-500 via-amber-400 to-yellow-200 p-[1px] shadow-lg shadow-amber-500/10">
              <div className="w-full h-full bg-[#0b0e17] rounded-[11px] flex items-center justify-center">
                <Sparkles className="w-5 h-5 text-amber-400" />
              </div>
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-bold text-lg tracking-tight bg-gradient-to-r from-amber-200 via-amber-400 to-yellow-300 bg-clip-text text-transparent">
                  JewelMind
                </span>
                <span className="text-[10px] uppercase font-bold tracking-widest px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20">
                  Phase 0
                </span>
              </div>
              <p className="text-xs text-slate-400 hidden sm:block">AI Jewellery Design → Production Platform</p>
            </div>
          </div>

          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-slate-900/90 border border-slate-800 text-xs">
              <span className="relative flex h-2 w-2">
                <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${backendHealth ? 'bg-emerald-400' : 'bg-amber-400'}`}></span>
                <span className={`relative inline-flex rounded-full h-2 w-2 ${backendHealth ? 'bg-emerald-500' : 'bg-amber-500'}`}></span>
              </span>
              <span className="text-slate-300">
                {loadingHealth
                  ? 'Checking Backend...'
                  : backendHealth
                  ? `FastAPI: ${backendHealth.status.toUpperCase()}`
                  : errorHealth
                  ? `Backend: Disconnected (${errorHealth})`
                  : 'Backend: Standby'}
              </span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 max-w-7xl mx-auto px-6 py-12 w-full space-y-16">
        {/* Hero Section */}
        <section className="text-center space-y-6 max-w-3xl mx-auto pt-6">
          <div className="inline-flex items-center space-x-2 px-4 py-1.5 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs font-medium">
            <ShieldCheck className="w-4 h-4 text-amber-400" />
            <span>Repository Foundation & Architecture Locked</span>
          </div>

          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-white leading-tight">
            Connecting Jewellery Sketching to{' '}
            <span className="bg-gradient-to-r from-amber-300 via-amber-400 to-yellow-200 bg-clip-text text-transparent">
              Precision Production
            </span>
          </h1>

          <p className="text-base sm:text-lg text-slate-400 leading-relaxed">
            JewelMind is an AI-assisted decision-support platform integrating generative diffusion, 
            YOLO component detection, predictive manufacturing regression, and constraint-based workshop optimization.
          </p>

          <div className="flex flex-wrap justify-center gap-3 pt-2">
            <span className="px-3.5 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs text-slate-300">
              ⚡ ₹0 Infrastructure Budget
            </span>
            <span className="px-3.5 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs text-slate-300">
              🎮 Local RTX 4060 GPU Accelerated
            </span>
            <span className="px-3.5 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs text-slate-300">
              ☁️ Cloudflare + Supabase Free Ecosystem
            </span>
          </div>
        </section>

        {/* Phase 0 Status Banner */}
        <section className="bg-gradient-to-br from-slate-900/90 to-[#0d121f] border border-slate-800/90 rounded-2xl p-6 sm:p-8 shadow-xl">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
            <div className="space-y-2">
              <div className="flex items-center space-x-2">
                <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                <h2 className="text-xl font-bold text-white">Phase 0: Project Foundation Active</h2>
              </div>
              <p className="text-sm text-slate-400 max-w-2xl">
                The repository structure, frontend client, FastAPI health service, AI directory contracts, 
                and comprehensive architecture documentation are established.
              </p>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
              <div className="p-3 bg-slate-950/60 rounded-xl border border-slate-800/70">
                <div className="text-xs text-slate-400">Frontend</div>
                <div className="text-sm font-semibold text-emerald-400 mt-1">Ready (Vite)</div>
              </div>
              <div className="p-3 bg-slate-950/60 rounded-xl border border-slate-800/70">
                <div className="text-xs text-slate-400">Backend</div>
                <div className="text-sm font-semibold text-emerald-400 mt-1">FastAPI /health</div>
              </div>
              <div className="p-3 bg-slate-950/60 rounded-xl border border-slate-800/70">
                <div className="text-xs text-slate-400">AI Worker</div>
                <div className="text-sm font-semibold text-amber-300 mt-1">Decoupled</div>
              </div>
              <div className="p-3 bg-slate-950/60 rounded-xl border border-slate-800/70">
                <div className="text-xs text-slate-400">Next Step</div>
                <div className="text-sm font-semibold text-slate-200 mt-1">Phase 1</div>
              </div>
            </div>
          </div>
        </section>

        {/* Workflow Pipeline */}
        <section className="space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold text-white tracking-tight">End-to-End AI/ML Pipeline</h2>
              <p className="text-sm text-slate-400">The 5-stage intelligent manufacturing workflow planned for JewelMind</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4">
            {workflowSteps.map((item, idx) => {
              const Icon = item.icon;
              return (
                <div 
                  key={idx}
                  className="bg-[#0b0f19] border border-slate-800 hover:border-amber-500/40 rounded-xl p-5 transition duration-200 flex flex-col justify-between space-y-4 group"
                >
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-mono text-amber-400 font-semibold">{item.step}</span>
                      <div className="p-2 rounded-lg bg-slate-900 group-hover:bg-amber-500/10 text-slate-400 group-hover:text-amber-400 transition">
                        <Icon className="w-4 h-4" />
                      </div>
                    </div>
                    <h3 className="font-semibold text-slate-100 text-sm">{item.title}</h3>
                    <p className="text-xs text-slate-400 leading-relaxed">{item.desc}</p>
                  </div>
                  <div className="text-[11px] font-medium text-slate-500 flex items-center space-x-1 group-hover:text-amber-400/80 transition">
                    <span>Target Stage</span>
                    <ArrowRight className="w-3 h-3 ml-0.5" />
                  </div>
                </div>
              );
            })}
          </div>
        </section>

        {/* System Architecture Specifications */}
        <section className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="bg-[#0b0f19] border border-slate-800 rounded-xl p-6 space-y-4">
            <div className="flex items-center space-x-3 text-amber-400">
              <Activity className="w-5 h-5" />
              <h3 className="font-bold text-white text-base">Decoupled AI Workers</h3>
            </div>
            <p className="text-xs text-slate-400 leading-relaxed">
              FastAPI manages design records and queues tasks. Heavy deep learning inference executes asynchronously on local RTX 4060 or cloud GPU nodes without blocking web requests.
            </p>
            <div className="pt-2 text-xs font-mono text-slate-500 border-t border-slate-800/80">
              Location: <code>ai/workers/</code>
            </div>
          </div>

          <div className="bg-[#0b0f19] border border-slate-800 rounded-xl p-6 space-y-4">
            <div className="flex items-center space-x-3 text-amber-400">
              <Database className="w-5 h-5" />
              <h3 className="font-bold text-white text-base">Relational & Asset Tier</h3>
            </div>
            <p className="text-xs text-slate-400 leading-relaxed">
              PostgreSQL stores relational business entities (users, designs, components, schedules). Supabase Storage securely hosts sketches, high-res renders, and segmentation masks.
            </p>
            <div className="pt-2 text-xs font-mono text-slate-500 border-t border-slate-800/80">
              Location: <code>backend/app/models/</code>
            </div>
          </div>

          <div className="bg-[#0b0f19] border border-slate-800 rounded-xl p-6 space-y-4">
            <div className="flex items-center space-x-3 text-amber-400">
              <FolderGit2 className="w-5 h-5" />
              <h3 className="font-bold text-white text-base">Strict Phase Execution</h3>
            </div>
            <p className="text-xs text-slate-400 leading-relaxed">
              17 discrete phases from Foundation (Phase 0) to Capstone Presentation (Phase 16). Each phase is independently implemented, tested, verified, and documented.
            </p>
            <div className="pt-2 text-xs font-mono text-slate-500 border-t border-slate-800/80">
              Location: <code>docs/phases/</code>
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-900 py-8 bg-[#04060a]">
        <div className="max-w-7xl mx-auto px-6 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-slate-500">
          <p>© 2026 JewelMind — AI Jewellery Design, Analysis & Production Planning Platform</p>
          <div className="flex items-center space-x-6">
            <span>₹0 Budget Architecture</span>
            <span>•</span>
            <span>RTX 4060 Accelerated</span>
            <span>•</span>
            <span>FastAPI + React</span>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default App;
