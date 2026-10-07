import React, { useState, useEffect } from 'react';
import {
  Sparkles,
  ArrowRight,
  Factory,
  CheckCircle2,
  Compass,
  Scale,
  Gem,
  Play,
  Pause,
  ChevronLeft,
  ChevronRight,
  Check,
  PenTool,
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { CardBezel } from '../components/ui/card';

interface LandingPageProps {
  isAuthenticated: boolean;
  onEnterAtelier: () => void;
  onExploreAtelier: () => void;
  onSignIn: () => void;
}

export const LandingPage: React.FC<LandingPageProps> = ({
  isAuthenticated,
  onEnterAtelier,
  onExploreAtelier,
  onSignIn,
}) => {
  const [activeStep, setActiveStep] = useState<number>(1);
  const [isPlaying, setIsPlaying] = useState<boolean>(true);
  const [isHovered, setIsHovered] = useState<boolean>(false);

  // Pure 4-second auto-transition: 1 -> 2 -> 3 -> 4 -> 5 -> 1
  useEffect(() => {
    if (!isPlaying || isHovered) return;

    const timer = setInterval(() => {
      setActiveStep((curr) => (curr >= 5 ? 1 : curr + 1));
    }, 4000);

    return () => clearInterval(timer);
  }, [isPlaying, isHovered]);

  // Preload workflow step images into browser cache for zero-lag switching
  useEffect(() => {
    workflowSteps.forEach((s) => {
      const img = new Image();
      img.src = s.image;
    });
  }, []);

  const handleSelectStep = (stepNumber: number) => {
    setActiveStep(stepNumber);
  };

  const handlePrevStep = () => {
    setActiveStep((curr) => (curr <= 1 ? 5 : curr - 1));
  };

  const handleNextStep = () => {
    setActiveStep((curr) => (curr >= 5 ? 1 : curr + 1));
  };

  const workflowSteps = [
    {
      step: '01',
      title: 'Sketch',
      tagline: 'Initial Drawing & CAD',
      desc: 'Draw with real-time radial symmetry or upload paper sketches. Guides align stone seats and shank profiles instantly.',
      image: '/assets/datasets/sketch_ring.png',
      badge: 'Concept Input',
    },
    {
      step: '02',
      title: 'Analyse',
      tagline: 'Gemological Vision',
      desc: 'Neural vision parses prongs, stone counts, mount depths, and checks casting manufacturability before render.',
      image: '/assets/photos/pexels-hatice-genc-3580692-32797480.jpg',
      badge: 'YOLO Vision',
    },
    {
      step: '03',
      title: 'Generate',
      tagline: 'Photorealistic Render',
      desc: 'Generate studio-grade customer renders in solid 18K gold and platinum with lifelike reflections and diamond fire.',
      image: '/assets/photos/pexels-coppertist-wu-313365563-15967464.jpg',
      badge: 'AI Rendering',
    },
    {
      step: '04',
      title: 'Approve',
      tagline: 'Client Sign-off & Specs',
      desc: 'Clients sign off on realistic visuals. JewelMind locks the bill of materials, bullion weights, and stone inventories.',
      image: '/assets/photos/pexels-kushith-m-442883749-20493839.jpg',
      badge: 'Design Approved',
    },
    {
      step: '05',
      title: 'Manufacture',
      tagline: 'Artisan Bench & Shop Floor',
      desc: 'Automatic dispatch to karigar workbenches with step-by-step casting, setting, polishing, and multi-point QC checklists.',
      image: '/assets/photos/pexels-cottonbro-10293692.jpg',
      badge: 'Shop Floor OS',
    },
  ];

  return (
    <div className="w-full space-y-28 sm:space-y-36 pb-24 selection:bg-[#D8AD55]/20 selection:text-[#F1D28A]">
      {/* ===================================================================== */}
      {/* HERO SECTION: The Luxury Jewellery Tech Atelier */}
      {/* ===================================================================== */}
      <section className="relative pt-6 sm:pt-12 max-w-7xl mx-auto px-4">
        {/* Subtle Ambient Radial Glow */}
        <div className="absolute top-10 left-1/3 -translate-x-1/2 w-[650px] h-[380px] bg-gradient-to-b from-[#D8AD55]/8 via-[#18A879]/5 to-transparent blur-3xl pointer-events-none -z-10" />

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-8 items-center">
          {/* Left Column: Editorial Headline & Actions */}
          <div className="lg:col-span-7 space-y-8 text-left">
            {/* Small Premium Metadata */}
            <div className="inline-flex items-center space-x-3 px-3.5 py-1.5 rounded-full bg-[#0B1210] border border-[#1C2621] text-xs font-mono text-[#D8AD55] tracking-widest uppercase shadow-sm">
              <span className="w-2 h-2 rounded-full bg-[#18A879] animate-pulse" />
              <span>AI-POWERED JEWELLERY WORKSPACE</span>
              <span className="text-[#6F756F]">|</span>
              <span className="text-[#A9ADA7]">SKETCH → AI → PRODUCTION</span>
            </div>

            {/* Headline */}
            <div className="space-y-4">
              <h1 className="font-serif text-5xl sm:text-6xl lg:text-7xl font-normal tracking-tight text-[#F4EFE5] leading-[1.08]">
                FROM SKETCH <br />
                <span className="atelier-gold-text italic font-serif">
                  TO MASTERPIECE.
                </span>
              </h1>
              <p className="text-base sm:text-lg text-[#A9ADA7] leading-relaxed max-w-xl font-light">
                JewelMind transforms hand-drawn concepts into photorealistic customer renders,
                exact gold and gem bills of material, and intelligent karigar bench schedules
                before a single gram of gold is melted.
              </p>
            </div>

            {/* CTAs */}
            <div className="flex flex-wrap items-center gap-4 pt-2">
              <Button
                variant="gold"
                size="touch"
                onClick={onEnterAtelier}
                className="font-bold px-8 shadow-xl shadow-[#D8AD55]/15 text-[#050806] group"
                iconTrailing={<ArrowRight className="w-4 h-4 text-[#050806]" />}
              >
                {isAuthenticated ? 'Launch Platform' : 'Start Designing'}
              </Button>
              <Button
                variant="outline"
                size="touch"
                onClick={isAuthenticated ? onExploreAtelier : onSignIn}
                className="px-7 border-[#1C2621] text-[#F4EFE5] hover:border-[#D8AD55]/40 hover:text-white"
              >
                Explore the Studio
              </Button>
            </div>

            {/* Trust Indicators */}
            <div className="flex flex-wrap items-center gap-6 sm:gap-8 pt-4 text-xs text-[#A9ADA7] font-mono">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-[#18A879]" />
                <span>BIS Hallmarking Standards</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-[#18A879]" />
                <span>18K / 22K Gold &amp; Platinum</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-[#18A879]" />
                <span>Live Bullion Costing</span>
              </div>
            </div>
          </div>

          {/* Right Column: Large Premium Jewellery Visual */}
          <div className="lg:col-span-5">
            <CardBezel variant="gold" className="w-full">
              <div className="relative rounded-[calc(1.5rem-6px)] overflow-hidden bg-[#080D0B] border border-[#1C2621] group">
                <div className="relative h-[440px] sm:h-[520px] w-full overflow-hidden bg-gradient-to-b from-[#0B1210] to-[#050806] flex items-center justify-center p-4">
                  <img
                    src="/assets/photos/pexels-lappen-fashion-2754326-4295007.jpg"
                    alt="High Jewellery Necklace Masterpiece on Dark Background"
                    className="w-full h-full object-cover object-center drop-shadow-[0_20px_40px_rgba(0,0,0,0.9)] transition-transform duration-700 group-hover:scale-105"
                  />

                  {/* Vignette Overlay */}
                  <div className="absolute inset-0 bg-gradient-to-t from-[#050806] via-transparent to-black/30 pointer-events-none" />

                  {/* Floating Top Badge */}
                  <div className="absolute top-4 left-4 flex items-center gap-2 px-3 py-1.5 rounded-xl bg-[#050806]/85 backdrop-blur-md border border-[#1C2621] text-xs shadow-lg z-10">
                    <span className="w-2 h-2 rounded-full bg-[#18A879] animate-ping" />
                    <span className="font-serif font-semibold text-[#F1D28A]">JewelMind</span>
                    <span className="text-[#6F756F]">|</span>
                    <span className="text-[#A9ADA7] text-[11px] font-mono">Design Studio</span>
                  </div>

                  {/* Floating Bottom Metadata Frame */}
                  <div className="absolute bottom-4 left-4 right-4 p-4 rounded-xl bg-[#0B1210]/95 backdrop-blur-xl border border-[#1C2621] flex items-center justify-between shadow-2xl z-10">
                    <div className="space-y-0.5">
                      <div className="flex items-center gap-2">
                        <Badge variant="gold">Signature Series</Badge>
                        <span className="text-[11px] text-[#A9ADA7] font-mono">Ref: JM-NECK-4295</span>
                      </div>
                      <h3 className="font-serif text-base font-semibold text-[#F4EFE5]">
                        Sovereign Coin Necklace Set
                      </h3>
                      <p className="text-[11px] text-[#A9ADA7]">
                        Solid 22K yellow gold • Hand-linked medallions
                      </p>
                    </div>
                    <Button
                      variant="gold"
                      size="sm"
                      onClick={onEnterAtelier}
                      className="text-xs font-bold text-[#050806]"
                    >
                      Open
                      <ArrowRight className="w-3 h-3 ml-1 text-[#050806]" />
                    </Button>
                  </div>
                </div>
              </div>
            </CardBezel>
          </div>
        </div>
      </section>

      {/* ===================================================================== */}
      {/* 5-STEP VISUAL CONTINUUM: 01 Sketch -> 02 Analyse -> 03 Generate -> 04 Approve -> 05 Manufacture */}
      {/* ===================================================================== */}
      <section
        className="max-w-7xl mx-auto px-4 space-y-8 select-none"
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
      >
        {/* Section Header */}
        <div className="text-center space-y-3 max-w-2xl mx-auto">
          <Badge variant="gold" className="px-3 py-1">Crafting Workflow</Badge>
          <h2 className="font-serif text-3xl sm:text-5xl text-[#F4EFE5] font-normal">
            The 5-Step Crafting Continuum
          </h2>
          <p className="text-sm text-[#A9ADA7] font-light leading-relaxed">
            From the designer's first pencil stroke to the final polish on the workshop bench.
          </p>
        </div>

        {/* Animation & Autoplay Controls Bar */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-3 px-2 py-1">
          <div className="flex items-center gap-2.5">
            <span className="px-2.5 py-1 rounded-lg bg-[#0B1210] border border-[#1C2621] text-xs font-mono font-medium text-[#D8AD55]">
              Stage 0{activeStep} of 05
            </span>
          </div>

          {/* Stepper Navigation Buttons */}
          <div className="flex items-center gap-1.5">
            <button
              onClick={handlePrevStep}
              className="p-1.5 rounded-lg bg-[#0B1210] hover:bg-[#141D19] border border-[#1C2621] text-[#A9ADA7] hover:text-white transition-colors cursor-pointer"
              title="Previous Step"
              aria-label="Previous step"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <button
              onClick={() => setIsPlaying(!isPlaying)}
              className="px-2.5 py-1 rounded-lg bg-[#0B1210] hover:bg-[#141D19] border border-[#1C2621] text-[#A9ADA7] hover:text-[#D8AD55] text-xs flex items-center gap-1.5 transition-colors cursor-pointer font-mono"
              title={isPlaying ? 'Pause Auto-advance' : 'Resume Auto-advance'}
            >
              {isPlaying ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
              <span>{isPlaying ? 'Pause' : 'Play'}</span>
            </button>
            <button
              onClick={handleNextStep}
              className="p-1.5 rounded-lg bg-[#0B1210] hover:bg-[#141D19] border border-[#1C2621] text-[#A9ADA7] hover:text-white transition-colors cursor-pointer"
              title="Next Step"
              aria-label="Next step"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Horizontal 5-Step Selector Bar with Live Progression */}
        <div className="relative p-2 rounded-2xl bg-[#0B1210] border border-[#1C2621] shadow-2xl">
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-2.5 relative z-10">
            {workflowSteps.map((s, idx) => {
              const stepNum = idx + 1;
              const isActive = activeStep === stepNum;
              const isPast = stepNum < activeStep;
              return (
                <button
                  key={s.step}
                  onClick={() => handleSelectStep(stepNum)}
                  className={`group relative p-3.5 rounded-xl text-left transition-all duration-300 cursor-pointer overflow-hidden ${
                    isActive
                      ? 'bg-[#141D19] border border-[#D8AD55]/60 shadow-[0_0_25px_rgba(216,173,85,0.15)] ring-1 ring-[#D8AD55]/30'
                      : isPast
                      ? 'bg-white/[0.02] border border-white/[0.06] hover:bg-white/[0.04]'
                      : 'hover:bg-white/[0.03] border border-transparent'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <span
                      className={`font-mono text-xs font-bold flex items-center gap-1.5 ${
                        isActive ? 'text-[#D8AD55]' : isPast ? 'text-[#D8AD55]/70' : 'text-[#6F756F]'
                      }`}
                    >
                      {s.step}
                      {isPast && <Check className="w-3 h-3 text-[#D8AD55]/80" />}
                    </span>
                    {isActive && (
                      <span className="relative flex h-2 w-2">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#18A879] opacity-75" />
                        <span className="relative inline-flex rounded-full h-2 w-2 bg-[#18A879]" />
                      </span>
                    )}
                  </div>
                  <h4 className={`font-serif text-sm font-medium transition-colors ${isActive ? 'text-[#F4EFE5]' : 'text-[#A9ADA7] group-hover:text-white'}`}>
                    {s.title}
                  </h4>
                  <p className="text-[11px] text-[#6F756F] truncate mt-0.5 font-light">
                    {s.tagline}
                  </p>

                  {/* Animated Gold Progress Bar at the bottom of the active button */}
                  {isActive && (
                    <div className="absolute bottom-0 left-0 right-0 h-[2.5px] bg-white/[0.08] overflow-hidden">
                      <div
                        key={`bar-${activeStep}-${isPlaying}-${isHovered}`}
                        className="h-full bg-gradient-to-r from-[#D8AD55] via-[#F1D28A] to-[#D8AD55] shadow-[0_0_10px_#D8AD55]"
                        style={{
                          animation: isPlaying && !isHovered ? 'stepProgress 4000ms linear forwards' : 'none',
                          width: isPlaying && !isHovered ? undefined : '100%',
                        }}
                      />
                    </div>
                  )}
                </button>
              );
            })}
          </div>
        </div>

        {/* Selected Step Spotlight Feature Card */}
        {(() => {
          const cur = workflowSteps[activeStep - 1] || workflowSteps[0];
          return (
            <div
              key={activeStep}
              className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center bg-[#080D0B] p-6 sm:p-10 rounded-3xl border border-[#1C2621] shadow-2xl transition-all duration-700 animate-in fade-in duration-500"
            >
              <div className="lg:col-span-6 space-y-6">
                <div className="flex items-center gap-3">
                  <span className="font-mono text-xl text-[#D8AD55] font-bold tracking-widest">{cur.step}</span>
                  <div className="h-[1px] w-12 bg-gradient-to-r from-[#D8AD55] to-transparent" />
                  <Badge variant="gold" className="text-xs">{cur.badge}</Badge>
                </div>

                <div className="space-y-2">
                  <h3 className="font-serif text-3xl sm:text-4xl text-[#F4EFE5] font-normal leading-tight">
                    {cur.step} — {cur.title}: <span className="text-[#D8AD55] font-serif">{cur.tagline}</span>
                  </h3>
                </div>

                <p className="text-sm sm:text-base text-[#A9ADA7] leading-relaxed font-light">
                  {cur.desc}
                </p>

                <div className="pt-2 flex flex-wrap items-center gap-4">
                  <Button
                    variant="gold"
                    size="default"
                    onClick={onEnterAtelier}
                    className="font-bold text-xs text-[#050806] flex items-center gap-2 shadow-lg shadow-[#D8AD55]/10 hover:shadow-[#D8AD55]/25"
                  >
                    <span>Open Step in Studio</span>
                    <ArrowRight className="w-3.5 h-3.5 text-[#050806]" />
                  </Button>
                  <Button
                    variant="outline"
                    size="default"
                    onClick={onEnterAtelier}
                    className="text-xs border-[#1C2621] hover:border-[#D8AD55]/40 text-[#A9ADA7] hover:text-white"
                  >
                    <PenTool className="w-3.5 h-3.5 mr-1.5 text-[#D8AD55]" />
                    Design in Canvas
                  </Button>
                </div>
              </div>

              <div className="lg:col-span-6 flex justify-center">
                <CardBezel variant="gold" className="w-full max-w-md shadow-2xl">
                  <div className="relative aspect-[4/3] w-full rounded-[calc(1.5rem-6px)] overflow-hidden bg-[#050806] border border-[#1C2621] group">
                    <img
                      src={cur.image}
                      alt={cur.title}
                      loading="eager"
                      decoding="async"
                      className="w-full h-full object-cover object-center transition-transform duration-700 group-hover:scale-105"
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/10 to-transparent pointer-events-none" />
                    <div className="absolute bottom-3 left-3 px-3 py-1.5 rounded-lg bg-black/80 backdrop-blur-md border border-white/10 text-xs font-mono text-[#D8AD55] flex items-center gap-2">
                      <span className="w-1.5 h-1.5 rounded-full bg-[#18A879]" />
                      <span>Stage {cur.step} Prototype</span>
                    </div>
                  </div>
                </CardBezel>
              </div>
            </div>
          );
        })()}
      </section>

      {/* ===================================================================== */}
      {/* PRODUCT CAPABILITIES: 4 Premium Atelier Cards */}
      {/* ===================================================================== */}
      <section className="max-w-7xl mx-auto px-4 space-y-12">
        <div className="text-center space-y-3 max-w-xl mx-auto">
          <Badge variant="gold">Platform Capabilities</Badge>
          <h2 className="font-serif text-3xl sm:text-4xl text-[#F4EFE5] font-normal">
            Four pillars of jewellery intelligence.
          </h2>
          <p className="text-xs sm:text-sm text-[#A9ADA7] font-light">
            Engineered exclusively for luxury ateliers, fine custom houses, and high-volume workshops.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {/* Card 1: AI Design Intelligence */}
          <CardBezel>
            <div className="p-6 space-y-4 flex flex-col justify-between h-full bg-[#0B1210]">
              <div className="space-y-4">
                <div className="w-11 h-11 rounded-xl bg-[#141D19] border border-[#1C2621] text-[#D8AD55] flex items-center justify-center">
                  <Compass className="w-5 h-5 text-[#D8AD55]" />
                </div>
                <div className="space-y-1.5">
                  <h3 className="font-serif text-lg font-medium text-[#F4EFE5]">AI Design Intelligence</h3>
                  <p className="text-xs text-[#A9ADA7] font-light leading-relaxed">
                    Symmetry CAD canvas with millimeter stone seats, prong spacing, and shank contouring.
                  </p>
                </div>
              </div>
              <div className="pt-4 border-t border-[#1C2621] text-[11px] font-mono text-[#18A879] flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>YOLO Component Scanner</span>
              </div>
            </div>
          </CardBezel>

          {/* Card 2: Generative Rendering */}
          <CardBezel>
            <div className="p-6 space-y-4 flex flex-col justify-between h-full bg-[#0B1210]">
              <div className="space-y-4">
                <div className="w-11 h-11 rounded-xl bg-[#141D19] border border-[#1C2621] text-[#D8AD55] flex items-center justify-center">
                  <Sparkles className="w-5 h-5 text-[#D8AD55]" />
                </div>
                <div className="space-y-1.5">
                  <h3 className="font-serif text-lg font-medium text-[#F4EFE5]">Generative Rendering</h3>
                  <p className="text-xs text-[#A9ADA7] font-light leading-relaxed">
                    Photorealistic studio renders in yellow gold, rose gold, white gold, and platinum with client sign-off.
                  </p>
                </div>
              </div>
              <div className="pt-4 border-t border-[#1C2621] text-[11px] font-mono text-[#D8AD55] flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>Gemini Atelier Copilot</span>
              </div>
            </div>
          </CardBezel>

          {/* Card 3: Production Intelligence */}
          <CardBezel>
            <div className="p-6 space-y-4 flex flex-col justify-between h-full bg-[#0B1210]">
              <div className="space-y-4">
                <div className="w-11 h-11 rounded-xl bg-[#141D19] border border-[#1C2621] text-[#D8AD55] flex items-center justify-center">
                  <Scale className="w-5 h-5 text-[#D8AD55]" />
                </div>
                <div className="space-y-1.5">
                  <h3 className="font-serif text-lg font-medium text-[#F4EFE5]">Production Intelligence</h3>
                  <p className="text-xs text-[#A9ADA7] font-light leading-relaxed">
                    Automated bills of material, precious metal loss tracking, and live bullion rate costing.
                  </p>
                </div>
              </div>
              <div className="pt-4 border-t border-[#1C2621] text-[11px] font-mono text-[#18A879] flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>CP-SAT Schedule Engine</span>
              </div>
            </div>
          </CardBezel>

          {/* Card 4: Shop Floor Execution */}
          <CardBezel>
            <div className="p-6 space-y-4 flex flex-col justify-between h-full bg-[#0B1210]">
              <div className="space-y-4">
                <div className="w-11 h-11 rounded-xl bg-[#141D19] border border-[#1C2621] text-[#D8AD55] flex items-center justify-center">
                  <Factory className="w-5 h-5 text-[#D8AD55]" />
                </div>
                <div className="space-y-1.5">
                  <h3 className="font-serif text-lg font-medium text-[#F4EFE5]">Shop Floor Execution</h3>
                  <p className="text-xs text-[#A9ADA7] font-light leading-relaxed">
                    Touch-friendly workstation interface for karigars, tracking elapsed time, casting, and QC gates.
                  </p>
                </div>
              </div>
              <div className="pt-4 border-t border-[#1C2621] text-[11px] font-mono text-[#D8AD55] flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>Live Floor Telemetry</span>
              </div>
            </div>
          </CardBezel>
        </div>
      </section>

      {/* ===================================================================== */}
      {/* FINAL CALL TO ACTION: Large Centered Section */}
      {/* ===================================================================== */}
      <section className="max-w-4xl mx-auto px-4 text-center">
        <CardBezel variant="gold">
          <div className="p-10 sm:p-16 space-y-6 bg-[#080D0B] rounded-[calc(1.5rem-6px)]">
            <div className="w-14 h-14 rounded-2xl bg-[#141D19] border border-[#D8AD55]/30 text-[#D8AD55] flex items-center justify-center mx-auto shadow-lg shadow-[#D8AD55]/10">
              <Gem className="w-7 h-7 text-[#D8AD55]" />
            </div>

            <div className="space-y-3 max-w-xl mx-auto">
              <h2 className="font-serif text-3xl sm:text-5xl text-[#F4EFE5] font-normal leading-tight">
                YOUR NEXT PIECE <br />
                <span className="atelier-gold-text italic">STARTS HERE.</span>
              </h2>
              <p className="text-xs sm:text-sm text-[#A9ADA7] font-light leading-relaxed">
                Experience the luxury jewellery atelier operating system. Turn ideas into approved pieces and scheduled orders in minutes.
              </p>
            </div>

            <div className="pt-2">
              <Button
                variant="gold"
                size="touch"
                onClick={onEnterAtelier}
                className="px-10 text-[#050806] font-bold text-sm shadow-xl shadow-[#D8AD55]/20 group"
                iconTrailing={<ArrowRight className="w-4 h-4 text-[#050806]" />}
              >
                Enter JewelMind
              </Button>
            </div>
          </div>
        </CardBezel>
      </section>
    </div>
  );
};

export default LandingPage;
