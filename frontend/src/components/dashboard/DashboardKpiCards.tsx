import React from 'react';
import {
  Layers,
  Factory,
  Users,
  Percent,
} from 'lucide-react';
import { Card, CardContent } from '../ui/card';
import { Badge } from '../ui/badge';
import { DashboardKpis } from '../../types/dashboard';

interface DashboardKpiCardsProps {
  kpis: DashboardKpis;
  onNavigateToDesigns: () => void;
  onNavigateToProduction: (tab?: string) => void;
}

export const DashboardKpiCards: React.FC<DashboardKpiCardsProps> = ({
  kpis,
  onNavigateToDesigns,
  onNavigateToProduction,
}) => {
  const cards = [
    {
      title: 'Portfolio Blueprints',
      value: kpis.total_designs,
      subtitle: `${kpis.rendered_designs} Synthesized Renders`,
      badge: `${kpis.active_designs} Active`,
      badgeVariant: 'gold' as const,
      icon: Layers,
      textColor: 'text-amber-300',
      onClick: onNavigateToDesigns,
    },
    {
      title: 'Workshop Batches',
      value: kpis.pending_orders + kpis.in_progress_orders,
      subtitle: `${kpis.completed_orders} Fulfilled Orders`,
      badge: kpis.overdue_orders > 0 ? `${kpis.overdue_orders} Overdue` : 'On Schedule',
      badgeVariant: kpis.overdue_orders > 0 ? ('destructive' as const) : ('success' as const),
      icon: Factory,
      textColor: 'text-slate-300',
      onClick: () => onNavigateToProduction('orders'),
    },
    {
      title: 'Artisan Bench Capacity',
      value: `${kpis.total_worker_capacity_hours}h`,
      subtitle: `${kpis.available_workers} / ${kpis.total_workers} Active Artisans`,
      badge: `${kpis.available_machines} Machines`,
      badgeVariant: 'atelier' as const,
      icon: Users,
      textColor: 'text-amber-200',
      onClick: () => onNavigateToProduction('workers'),
    },
    {
      title: 'CP-SAT Schedule Efficiency',
      value: `${kpis.workshop_utilization_pct}%`,
      subtitle: `Delivery Accuracy: ${kpis.on_time_delivery_rate}%`,
      badge: 'OR-Tools Optimal',
      badgeVariant: 'gold' as const,
      icon: Percent,
      textColor: 'text-amber-300',
      onClick: () => onNavigateToProduction('optimization'),
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map((card, idx) => {
        const Icon = card.icon;
        return (
          <Card
            key={idx}
            onClick={card.onClick}
            className="bg-[#0E111A]/90 border-white/[0.07] hover:border-amber-400/30 cursor-pointer transition-all duration-300 group relative overflow-hidden flex flex-col justify-between shadow-xl"
          >
            <CardContent className="p-6 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-semibold tracking-wider uppercase text-slate-400 font-sans">{card.title}</span>
                <div
                  className="p-2 rounded-xl bg-white/[0.04] border border-white/[0.06] text-amber-300 group-hover:scale-105 group-hover:bg-amber-400/10 transition-all duration-300"
                >
                  <Icon className="w-4 h-4" />
                </div>
              </div>

              <div className="space-y-1.5">
                <div className="font-serif text-3xl font-medium text-white tracking-tight">
                  {card.value}
                </div>
                <div className="flex items-center justify-between text-xs text-slate-400/90 pt-1 font-light">
                  <span className="truncate max-w-[140px] sm:max-w-none">{card.subtitle}</span>
                  <Badge variant={card.badgeVariant} className="text-[9px] py-0.5 px-2 font-medium">
                    {card.badge}
                  </Badge>
                </div>
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
};
