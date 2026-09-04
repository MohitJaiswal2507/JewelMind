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
      title: 'Total Portfolio Designs',
      value: kpis.total_designs,
      subtitle: `${kpis.rendered_designs} Photorealistic Renders`,
      badge: `${kpis.active_designs} Active`,
      badgeVariant: 'gold' as const,
      icon: Layers,
      color: 'from-amber-500/20 via-amber-500/10 to-transparent',
      textColor: 'text-amber-400',
      onClick: onNavigateToDesigns,
    },
    {
      title: 'Active Production Orders',
      value: kpis.pending_orders + kpis.in_progress_orders,
      subtitle: `${kpis.completed_orders} Completed Batches`,
      badge: kpis.overdue_orders > 0 ? `${kpis.overdue_orders} Overdue` : 'On Schedule',
      badgeVariant: kpis.overdue_orders > 0 ? ('destructive' as const) : ('success' as const),
      icon: Factory,
      color: 'from-sky-500/20 via-sky-500/10 to-transparent',
      textColor: 'text-sky-400',
      onClick: () => onNavigateToProduction('orders'),
    },
    {
      title: 'Artisan Workshop Capacity',
      value: `${kpis.total_worker_capacity_hours} hrs`,
      subtitle: `${kpis.available_workers} / ${kpis.total_workers} Artisans Active`,
      badge: `${kpis.available_machines} Machines Ready`,
      badgeVariant: 'success' as const,
      icon: Users,
      color: 'from-emerald-500/20 via-emerald-500/10 to-transparent',
      textColor: 'text-emerald-400',
      onClick: () => onNavigateToProduction('workers'),
    },
    {
      title: 'CP-SAT Schedule Utilization',
      value: `${kpis.workshop_utilization_pct}%`,
      subtitle: `Delivery Rate: ${kpis.on_time_delivery_rate}%`,
      badge: 'OR-Tools Optimal',
      badgeVariant: 'gold' as const,
      icon: Percent,
      color: 'from-purple-500/20 via-purple-500/10 to-transparent',
      textColor: 'text-purple-400',
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
            className="bg-[#0b0f19] border-slate-800/90 hover:border-amber-500/40 cursor-pointer transition-all duration-200 group relative overflow-hidden flex flex-col justify-between shadow-lg"
          >
            {/* Top gradient highlight */}
            <div
              className={`absolute top-0 left-0 right-0 h-1 bg-gradient-to-r ${card.color}`}
            />
            <CardContent className="p-5 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-slate-400">{card.title}</span>
                <div
                  className={`p-2 rounded-xl bg-slate-900 border border-slate-800 ${card.textColor} group-hover:scale-110 transition-transform`}
                >
                  <Icon className="w-4 h-4" />
                </div>
              </div>

              <div className="space-y-1">
                <div className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
                  {card.value}
                </div>
                <div className="flex items-center justify-between text-xs text-slate-400 pt-1">
                  <span className="truncate max-w-[140px] sm:max-w-none">{card.subtitle}</span>
                  <Badge variant={card.badgeVariant} className="text-[10px] py-0 px-2">
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
