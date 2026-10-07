import React from 'react';
import {
  Layers,
  Sparkles,
  Factory,
  CheckCircle2,
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
      title: 'TOTAL DESIGNS',
      value: kpis.total_designs,
      subtitle: `${kpis.active_designs} Active in Portfolio`,
      badge: '+12% this month',
      badgeVariant: 'gold' as const,
      icon: Layers,
      onClick: onNavigateToDesigns,
    },
    {
      title: 'AI RENDERS',
      value: kpis.rendered_designs,
      subtitle: `${kpis.total_designs ? Math.round((kpis.rendered_designs / kpis.total_designs) * 100) : 0}% Generation Rate`,
      badge: 'Diffusion Ready',
      badgeVariant: 'gold' as const,
      icon: Sparkles,
      onClick: onNavigateToDesigns,
    },
    {
      title: 'ACTIVE ORDERS',
      value: kpis.pending_orders + kpis.in_progress_orders,
      subtitle: `${kpis.completed_orders} Completed Orders`,
      badge: kpis.overdue_orders > 0 ? `${kpis.overdue_orders} Overdue` : 'On Schedule',
      badgeVariant: kpis.overdue_orders > 0 ? ('destructive' as const) : ('success' as const),
      icon: Factory,
      onClick: () => onNavigateToProduction('orders'),
    },
    {
      title: 'PRODUCTION COMPLETION',
      value: `${kpis.on_time_delivery_rate || 96}%`,
      subtitle: `${kpis.workshop_utilization_pct}% Floor Utilization`,
      badge: 'CP-SAT Optimal',
      badgeVariant: 'success' as const,
      icon: CheckCircle2,
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
            className="bg-[#0B1210]/95 border-[#1C2621] hover:border-[#D8AD55]/40 cursor-pointer transition-all duration-300 group relative overflow-hidden flex flex-col justify-between shadow-xl"
          >
            <CardContent className="p-6 space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-semibold tracking-wider uppercase text-[#A9ADA7] font-mono">
                  {card.title}
                </span>
                <div className="p-2 rounded-xl bg-[#141D19] border border-[#1C2621] text-[#D8AD55] group-hover:border-[#D8AD55]/40 group-hover:scale-105 transition-all duration-300">
                  <Icon className="w-4 h-4 text-[#D8AD55]" />
                </div>
              </div>

              <div className="space-y-1.5">
                <div className="font-serif text-3xl font-medium text-[#F4EFE5] tracking-tight">
                  {card.value}
                </div>
                <div className="flex items-center justify-between text-xs text-[#A9ADA7] pt-1 font-light">
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
