/**
 * JewelMind — Indian Jewellery Material Valuation & Production Economics Types
 * Standard benchmark rate models for Indian bullion & atelier making charges.
 */

export interface MetalMarketRate {
  purity: string;
  metal: 'GOLD' | 'SILVER' | 'PLATINUM';
  ratePerGram: number; // in INR (₹)
  unit: string;
  source: string;
  effectiveDate: string;
}

export interface WorkshopRateConfig {
  gold24k: number;
  gold22k: number;
  gold18k: number;
  gold14k: number;
  silver925: number;
  platinum950: number;
  standardKarigarHourlyRate: number; // ₹ / hour for bench making charges
  machineOverheadHourlyRate: number; // ₹ / hour for furnace / lathe overhead
  standardRetailMarkupPercent: number; // default gross margin target
  currency: string;
  lastUpdated: string;
  source: string;
}

export const DEFAULT_INDIAN_WORKSHOP_RATES: WorkshopRateConfig = {
  gold24k: 7850,
  gold22k: 7200,
  gold18k: 5890,
  gold14k: 4580,
  silver925: 96,
  platinum950: 3250,
  standardKarigarHourlyRate: 450,
  machineOverheadHourlyRate: 150,
  standardRetailMarkupPercent: 22.5,
  currency: 'INR',
  lastUpdated: 'Today (Atelier Benchmark)',
  source: 'Atelier Standard Benchmarks (IBJA Derived)',
};

export interface MaterialCostItem {
  name: string;
  type: string;
  unit: string;
  plannedWeight: number;
  actualWeight: number;
  wastageWeight: number;
  ratePerUnit: number | null;
  totalCost: number | null;
  provenance: 'AI_ESTIMATE' | 'ARTISAN_VERIFIED' | 'BENCH_MEASURED' | 'SYSTEM_DERIVED';
}

export interface ProductionEconomicsSummary {
  materialCost: number;
  labourCost: number; // Making charges
  machineCost: number;
  totalManufacturingCost: number;
  estimatedSellingPrice: number;
  grossMarginAmount: number;
  grossMarginPercent: number;
  isComplete: boolean;
  rateSource: string;
}

/**
 * Derives metal rate per gram based on material name and configured rates.
 */
export function getIndianMetalRate(materialName: string, config: WorkshopRateConfig = DEFAULT_INDIAN_WORKSHOP_RATES): number | null {
  const norm = materialName.toLowerCase();
  if (norm.includes('24k') || norm.includes('999')) return config.gold24k;
  if (norm.includes('22k') || norm.includes('916')) return config.gold22k;
  if (norm.includes('18k') || norm.includes('750')) return config.gold18k;
  if (norm.includes('14k') || norm.includes('585')) return config.gold14k;
  if (norm.includes('gold')) return config.gold18k; // default to 18K fine jewelry standard
  if (norm.includes('silver') || norm.includes('925')) return config.silver925;
  if (norm.includes('platinum') || norm.includes('950')) return config.platinum950;
  return null;
}

/**
 * Formats Indian Currency (₹ Lakhs / Thousands) with symbol.
 */
export function formatINR(val: number | null | undefined): string {
  if (val === null || val === undefined || isNaN(val)) return '—';
  if (val >= 100000) {
    const inLakhs = val / 100000;
    return `₹${inLakhs.toFixed(2)}L`;
  }
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(val);
}
