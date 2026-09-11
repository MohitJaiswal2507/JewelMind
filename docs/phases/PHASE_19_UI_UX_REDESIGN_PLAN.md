# PHASE 19 — JEWELMIND PREMIUM UI/UX REDESIGN PLAN

**Project:** JewelMind  
**Branch:** `phase-19-ui-ux-redesign`  
**Execution Mode:** Architectural & UX Design Plan (Audit First)  
**Visual Inspiration:** https://blng.ai/ (Calm luxury, editorial aesthetics, sophisticated minimalism, generous whitespace, large imagery, studio feel)  

---

## 1. Existing Frontend Routes & Views

The JewelMind single-page application manages stateful routing across 9 primary views defined in [`frontend/src/App.tsx`](file:///c:/Users/usern/Desktop/JewelMind/frontend/src/App.tsx):

| View Route Key | Title / Purpose | Access Mode | Current Component |
| :--- | :--- | :--- | :--- |
| `landing` | Public Welcome & Feature Showcase | Public | Inline Hero & Workflow section in `App.tsx` |
| `login` | Atelier Authentication | Public | [`LoginPage.tsx`](file:///c:/Users/usern/Desktop/JewelMind/frontend/src/pages/LoginPage.tsx) |
| `register` | Atelier Account Creation | Public | [`RegisterPage.tsx`](file:///c:/Users/usern/Desktop/JewelMind/frontend/src/pages/RegisterPage.tsx) |
| `dashboard` | Creative Studio Hub & Portfolio Overview | Protected | [`DashboardPage.tsx`](file:///c:/Users/usern/Desktop/JewelMind/frontend/src/pages/DashboardPage.tsx) |
| `designs` | Visual Design Catalogue & Library | Protected | [`DesignsPage.tsx`](file:///c:/Users/usern/Desktop/JewelMind/frontend/src/pages/DesignsPage.tsx) |
| `design-detail` | Design Inspector, Sketch & AI Render Launch | Protected | [`DesignDetailPage.tsx`](file:///c:/Users/usern/Desktop/JewelMind/frontend/src/pages/DesignDetailPage.tsx) |
| `canvas` | Blueprint Drawing Studio & Canvas Workspace | Protected | [`DesignWorkspacePage.tsx`](file:///c:/Users/usern/Desktop/JewelMind/frontend/src/pages/DesignWorkspacePage.tsx) |
| `studio` | Visual Media Lookbook & Render Showcase | Protected | [`StudioPage.tsx`](file:///c:/Users/usern/Desktop/JewelMind/frontend/src/pages/StudioPage.tsx) |
| `production` | Workshop Orders & CP-SAT Optimization | Protected | [`ProductionPage.tsx`](file:///c:/Users/usern/Desktop/JewelMind/frontend/src/pages/ProductionPage.tsx) |

---

## 2. Existing Frontend Architecture

- **Core Engine:** React 19.2 + TypeScript + Vite 8.2.
- **Styling Framework:** TailwindCSS v4 (`@tailwindcss/vite` 4.3.3) with `@layer base` root variables.
- **UI Primitives:** Radix UI (`@radix-ui/react-slot`, `@radix-ui/react-separator`) + `class-variance-authority` + `lucide-react`.
- **API Communication Layer:** Centralized `ApiClient` in `frontend/src/services/api/client.ts` with automatic Bearer token injection, CORS compatibility, and structured error boundaries.
- **State Management:** `AuthContext` for global session, localized React hooks for page state, and instant Supabase signed URL asset resolution.

---

## 3. Current Visual & UX Deficiencies

1. **Generic Dark "Developer SaaS" Aesthetic:** The UI currently relies on heavy `#07090e` / `#0b0f19` dark blues and neon emerald/amber badges, resembling a cloud monitoring dashboard rather than a high-end luxury jewellery atelier.
2. **Lack of Editorial Typography:** Relying solely on standard system sans-serif fonts strips the interface of elegance and luxury prestige.
3. **Cluttered Dashboard Information Density:** The dashboard currently displays dense KPI number cards and technical status pills upfront, pushing creative jewellery imagery below the fold.
4. **Thumbnail-Constrained Visuals:** Jewellery is inherently visual and tactile; current 120px-200px thumbnail grids fail to convey photorealistic luster and fine craftsmanship.
5. **Noisy Multi-Button Header Navigation:** The top navigation bar is packed with health status pills and dense buttons, creating visual distraction.
6. **Disjointed AI Generation States:** When ControlNet diffusion runs, users see a simple spinner without engaging progressive feedback describing jewellery material synthesis.
7. **Monolithic Production Tables:** The Production page is heavily data-dense and needs an editorial split between Artisan Workshop Capacity, Active Projects, and CP-SAT Schedule Intelligence.

---

## 4. BLNG-Inspired Design Principles for JewelMind

- **Calm Luxury & Editorial Restraint:** Clean, uncrowded layouts where every element has purpose and room to breathe.
- **Image-First Experience:** Large, high-resolution jewellery visuals take centre stage with subtle border treatments and refined hover elevation.
- **Sophisticated Neutral Palette:** Warm obsidian, charcoal, champagne gold accents, and pearl tones rather than loud neon gradients.
- **Editorial Hierarchy:** Striking display headings paired with refined, letter-spaced metadata captions (`tracking-widest text-[11px] uppercase font-medium`).
- **Tactile Studio Feel:** Interacting with the canvas and studio should feel like working on an architect's jewellery desk.
- **Fluid & Intentional Micro-Interactions:** Gentle transitions (300ms ease-out), soft backdrop blur (`backdrop-blur-xl`), and crisp focus rings.

---

## 5. Original JewelMind Visual Identity

- **Brand Essence:** *"Where High Craftsmanship Meets Generative AI."*
- **Aesthetic Tone:** Quiet Luxury Atelier, Contemporary High Jewellery Studio, Intelligent Precision Engineering.
- **Brand Emblem:** Faceted Hexagonal Diamond Silhouette with luminous champagne highlights.
- **Voice & Tone:** Confident, refined, creative, and operationally rigorous.

---

## 6. Curated Color Palette (The Atelier Palette)

```
Surface / Background Hierarchy:
  - Canvas Deep:       #0A0C10  (Immersive dark atelier backdrop)
  - Surface Card:      #11141D  (Elevated card and module surface)
  - Surface Elevated:  #181D2A  (Interactive hover surface and floating toolbars)
  - Border Subdued:    rgba(255, 255, 255, 0.07)
  - Border Refined:    rgba(212, 175, 55, 0.20)  (Champagne gold border accent)

Text & Content:
  - Text Primary:      #F8FAFC  (Pearlescent pure white)
  - Text Secondary:    #94A3B8  (Warm platinum gray)
  - Text Muted:        #64748B  (Soft muted charcoal)

Jewellery Metallic Accents (Used Sparingly as Accents):
  - Champagne Gold:    #D4AF37  (Primary luxury accent)
  - Pale Luster:       #EED885  (Subtle gradient highlight)
  - Warm Bronze:       #A37836  (Warm shadow tone)
  - Platinum Silver:   #E2E8F0  (Metal contrast accent)
```

---

## 7. Refined Typography Hierarchy

- **Primary Display & Headings:** `Playfair Display` or `Cinzel` / `Plus Jakarta Sans` luxury display weight for hero titles, section headlines, and design names.
- **UI & Navigation:** `Plus Jakarta Sans` / `Inter` with tailored tracking:
  - **Display (Hero):** 44px – 56px, `font-serif tracking-tight font-medium`
  - **H1 (Page Title):** 28px – 36px, `font-serif font-semibold tracking-tight`
  - **H2 (Section):** 20px – 24px, `font-sans font-medium text-slate-100`
  - **H3 (Card Header):** 16px – 18px, `font-sans font-semibold text-slate-200`
  - **Body Text:** 14px – 15px, `font-sans font-normal leading-relaxed text-slate-300`
  - **Eyebrow / Metadata Label:** 11px, `font-sans font-semibold tracking-widest uppercase text-amber-300/80`
  - **Data / Stats:** 22px – 28px, `font-mono font-medium tracking-tight text-slate-100`

---

## 8. Spacing & Layout Architecture

- **Page Container:** `max-w-7xl mx-auto px-6 sm:px-8 lg:px-12 py-8 lg:py-12` with generous vertical rhythm (`space-y-12`).
- **Card Padding:** `p-6 sm:p-8` with `rounded-2xl` smooth curves and 1px border highlights (`border border-white/5 shadow-2xl`).
- **Whitespace:** Dedicated breathing room between creative actions and data summaries.

---

## 9. UI Component Overhaul (Shadcn + Tailwind Design System)

- **Buttons ([`components/ui/button.tsx`](file:///c:/Users/usern/Desktop/JewelMind/frontend/src/components/ui/button.tsx)):**
  - `gold`: Sleek champagne metallic gradient with soft golden glow on hover (`hover:shadow-amber-500/20`).
  - `atelier`: Subtle dark glass with 1px border (`bg-white/5 border-white/10 hover:bg-white/10 text-slate-200`).
  - `ghost` / `outline`: Minimalist refined border with luxury text contrast.
- **Cards ([`components/ui/card.tsx`](file:///c:/Users/usern/Desktop/JewelMind/frontend/src/components/ui/card.tsx)):**
  - Deep obsidian background (`bg-[#11141d]/90 backdrop-blur-xl border-white/5 shadow-2xl rounded-2xl`).
- **Badges ([`components/ui/badge.tsx`](file:///c:/Users/usern/Desktop/JewelMind/frontend/src/components/ui/badge.tsx)):**
  - Muted metallic tags with lowercase/uppercase tracking (`bg-amber-500/10 text-amber-300 border-amber-500/20`).
- **Inputs & Selects ([`components/ui/input.tsx`](file:///c:/Users/usern/Desktop/JewelMind/frontend/src/components/ui/input.tsx)):**
  - Smooth dark fields with gold focus ring (`focus:border-amber-400/50 focus:ring-amber-400/20`).

---

## 10. Page-by-Page Redesign Strategy

### A. Application Shell & Navigation
- **Top Bar / Sidebar:** Minimalist glassmorphic header with logo emblem, clean navigation links (`Overview`, `Designs`, `Studio`, `Production`), user avatar dropdown, and quiet system indicator.

### B. Dashboard Page ([`pages/DashboardPage.tsx`](file:///c:/Users/usern/Desktop/JewelMind/frontend/src/pages/DashboardPage.tsx))
- **Hero Atelier Greeting:** *"Welcome to the Atelier, [Name]"* with inspirational subtitle *"Craft your next collection with precision generative intelligence."*
- **Creative Launchpad (4 Large Visual Action Cards):**
  1. **New Blueprint Sketch:** Direct link to interactive drawing desk.
  2. **AI Generative Rendering:** Instant sketch-to-photorealistic render workflow.
  3. **YOLO Component Detection:** Deep structural jewellery vision analysis.
  4. **Production Schedule:** OR-Tools CP-SAT workshop optimization.
- **Hero Recent Creations Carousel:** Large card previews of recent designs and high-resolution renders.
- **Curated Atelier Insights:** Minimalist KPI strip (Active Collections, Rendered Pieces, Workshop Orders, Efficiency Score).

### C. Design Library / Catalogue ([`pages/DesignsPage.tsx`](file:///c:/Users/usern/Desktop/JewelMind/frontend/src/pages/DesignsPage.tsx))
- **Editorial Gallery View:** Large 3-column / 4-column responsive cards with full-bleed sketch and render previews.
- **Pill Filter Bar:** Clean category filter (`All`, `Ring`, `Earrings`, `Pendant`, `Necklace`, `Bracelet`, `Bangle`, `Brooch`, `Other`).
- **Fast Search & Sorting:** Live search with instant debounce and creation date sorting.

### D. Design Detail & Inspector ([`pages/DesignDetailPage.tsx`](file:///c:/Users/usern/Desktop/JewelMind/frontend/src/pages/DesignDetailPage.tsx))
- **Side-by-Side Dual Canvas:** Large high-contrast sketch preview alongside the photorealistic ControlNet AI render.
- **Interactive Action Toolbar:** Direct buttons to *"Edit Sketch in Studio"*, *"Render with New Material"*, *"Export Blueprint"*, and *"Create Production Order"*.
- **Jewellery Specs Panel:** Category badge, material details, gemstone configuration, and AI prompt history.

### E. Interactive Sketch Canvas ([`pages/DesignWorkspacePage.tsx`](file:///c:/Users/usern/Desktop/JewelMind/frontend/src/pages/DesignWorkspacePage.tsx))
- **Atelier Drawing Desk:** Maximize canvas workspace with floating glassmorphic toolbar (Pen, Brush, Line, Ellipse, Rectangle, Gemstone Stamp, Symmetry Axis, Grid).
- **Collapsible AI Assistant Drawer:** Side drawer for real-time prompt suggestions and prompt refinement.
- **Instant Save & Cloud Sync:** Feedback indicator syncing seamlessly with Supabase storage.

### F. AI Generative Rendering Modal ([`components/studio/AiRenderModal.tsx`](file:///c:/Users/usern/Desktop/JewelMind/frontend/src/components/studio/AiRenderModal.tsx))
- **Visual Material Selector:** High-quality visual swatches (18K Yellow Gold, Rose Gold, White Gold, 950 Platinum, Sterling Silver).
- **Gemstone Swatches:** Luminous presets (Brilliant Diamond, Royal Sapphire, Colombian Emerald, Burmese Ruby, Amethyst).
- **Progressive AI Generation Stages:** Engaging animated feedback:
  - Step 1: *Extracting LineArt blueprint geometry...*
  - Step 2: *Applying 1000-step ControlNet structural conditioning...*
  - Step 3: *Synthesizing precious metal luster & gemstone facets...*
  - Step 4: *Polishing photorealistic 512x512 render...*
- **Split Slider / Comparison Preview:** Instant before/after comparison between sketch and render.

### G. Studio Lookbook & Visual Gallery ([`pages/StudioPage.tsx`](file:///c:/Users/usern/Desktop/JewelMind/frontend/src/pages/StudioPage.tsx))
- **High-Fashion Lookbook:** Masonry/grid layout highlighting completed renders with metadata inspection, full-resolution zoom modal, and one-click download.

### H. Production & Optimization Hub ([`pages/ProductionPage.tsx`](file:///c:/Users/usern/Desktop/JewelMind/frontend/src/pages/ProductionPage.tsx))
- **Modern Workshop Control Center:**
  - Tab 1: **Production Orders** (Visual stage cards: CAD -> Casting -> Stone Setting -> Polishing -> Quality Check).
  - Tab 2: **Workshop Artisans** (Skill tags, active availability toggle, current assigned orders).
  - Tab 3: **Machinery & Equipment** (Status gauges, maintenance schedules).
  - Tab 4: **CP-SAT Solver Intelligence** (Interactive makespan timeline, bottleneck recommendations, instant one-click optimization).

---

## 11. Responsive Design Strategy

- **Mobile (< 640px):**
  - Collapsible mobile navigation menu with glass overlay.
  - Single-column cards with touch-friendly 44px tap targets.
  - Sketch canvas scaled with pinch-to-zoom and touch drawing.
- **Tablet (640px – 1024px):**
  - 2-column grid layout for designs and lookbook.
  - Floating canvas toolbars positioned horizontally.
- **Desktop (>= 1024px):**
  - Full multi-column editorial layouts with side-by-side inspectors.
  - Large display canvases utilizing maximum screen real estate.
- **Zero Horizontal Scroll:** All tables and layouts use `overflow-x-auto` or card transformation.

---

## 12. Accessibility & Performance Standards

- **Color Contrast:** All text meets WCAG AA standards (minimum 4.5:1 contrast ratio against dark backgrounds).
- **Keyboard Navigation:** Full focus management on modals, dropdowns, and canvas shortcuts.
- **Performance Budget:** Zero heavy 3D or physics libraries added; lightweight CSS animations and native canvas rendering.
- **Lazy Loading:** All image cards use lazy loading and skeleton loaders for instant page responsiveness.

---

## 13. Files to Modify

### 1. Design System & Global Styles
- [`frontend/src/index.css`](file:///c:/Users/usern/Desktop/JewelMind/frontend/src/index.css) — Custom Atelier color tokens, font imports, scrollbars, and keyframe animations.
- [`frontend/index.html`](file:///c:/Users/usern/Desktop/JewelMind/frontend/index.html) — Google Fonts import (Playfair Display / Plus Jakarta Sans) and page title branding.

### 2. UI Component Primitives
- [`frontend/src/components/ui/button.tsx`](file:///c:/Users/usern/Desktop/JewelMind/frontend/src/components/ui/button.tsx)
- [`frontend/src/components/ui/card.tsx`](file:///c:/Users/usern/Desktop/JewelMind/frontend/src/components/ui/card.tsx)
- [`frontend/src/components/ui/badge.tsx`](file:///c:/Users/usern/Desktop/JewelMind/frontend/src/components/ui/badge.tsx)
- [`frontend/src/components/ui/input.tsx`](file:///c:/Users/usern/Desktop/JewelMind/frontend/src/components/ui/input.tsx)
- [`frontend/src/components/ui/slider.tsx`](file:///c:/Users/usern/Desktop/JewelMind/frontend/src/components/ui/slider.tsx)

### 3. Application Shell & Pages
- [`frontend/src/App.tsx`](file:///c:/Users/usern/Desktop/JewelMind/frontend/src/App.tsx) — Header, navigation shell, landing hero, and view switcher.
- [`frontend/src/pages/DashboardPage.tsx`](file:///c:/Users/usern/Desktop/JewelMind/frontend/src/pages/DashboardPage.tsx) — Atelier hero, 4-action launchpad, recent creations.
- [`frontend/src/pages/DesignsPage.tsx`](file:///c:/Users/usern/Desktop/JewelMind/frontend/src/pages/DesignsPage.tsx) — Editorial design catalogue.
- [`frontend/src/pages/DesignDetailPage.tsx`](file:///c:/Users/usern/Desktop/JewelMind/frontend/src/pages/DesignDetailPage.tsx) — Dual-canvas inspector & render launcher.
- [`frontend/src/pages/DesignWorkspacePage.tsx`](file:///c:/Users/usern/Desktop/JewelMind/frontend/src/pages/DesignWorkspacePage.tsx) — Drawing desk workspace.
- [`frontend/src/pages/StudioPage.tsx`](file:///c:/Users/usern/Desktop/JewelMind/frontend/src/pages/StudioPage.tsx) — Media lookbook & zoom inspector.
- [`frontend/src/pages/ProductionPage.tsx`](file:///c:/Users/usern/Desktop/JewelMind/frontend/src/pages/ProductionPage.tsx) — Production operations & CP-SAT solver hub.
- [`frontend/src/pages/LoginPage.tsx`](file:///c:/Users/usern/Desktop/JewelMind/frontend/src/pages/LoginPage.tsx) & [`frontend/src/pages/RegisterPage.tsx`](file:///c:/Users/usern/Desktop/JewelMind/frontend/src/pages/RegisterPage.tsx) — Luxury atelier authentication cards.

### 4. Interactive Components
- [`frontend/src/components/studio/AiRenderModal.tsx`](file:///c:/Users/usern/Desktop/JewelMind/frontend/src/components/studio/AiRenderModal.tsx) — Material/gemstone swatches, progressive multi-stage rendering animation.
- [`frontend/src/components/canvas/CanvasToolbar.tsx`](file:///c:/Users/usern/Desktop/JewelMind/frontend/src/components/canvas/CanvasToolbar.tsx) — Floating glass drawing controls.
- [`frontend/src/components/dashboard/DashboardKpiCards.tsx`](file:///c:/Users/usern/Desktop/JewelMind/frontend/src/components/dashboard/DashboardKpiCards.tsx) & [`DashboardRecentRenders.tsx`](file:///c:/Users/usern/Desktop/JewelMind/frontend/src/components/dashboard/DashboardRecentRenders.tsx).

---

## 14. Files That Must Remain Untouched

- **AI Model Pipelines & Preprocessors:** `ai/rendering/`, `ai/vision/`, `ai/workers/`
- **Production Model Weights:** `outputs/rendering_v2_controlnet/`, `outputs/appearance_lora/`, `runs/segment/.../best.pt`, `models/diffusion/`
- **Backend API Routes & Core Logic:** `backend/app/api/`, `backend/app/services/`, `backend/app/models/`
- **Database Migrations & Supabase Schemas:** `backend/alembic/`, database tables.

---

## 15. Summary of Phase 19 Deliverables & Readiness

The redesign plan establishes a distinctive, high-end jewellery studio identity for JewelMind, upgrading aesthetics and visual storytelling while preserving 100% of underlying business logic and API integrations.

**Awaiting user approval before proceeding to implementation.**
