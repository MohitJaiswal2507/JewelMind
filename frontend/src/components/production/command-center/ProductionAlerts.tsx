import React from 'react';
import {
  AlertTriangle,
  Clock,
  ShieldCheck,
  Repeat,
  Scale,
  ArrowRight,
} from 'lucide-react';


export interface ProductionAlertItem {
  id: string;
  orderId: string;
  orderNumber: string;
  designName: string;
  type: 'delayed' | 'qc_pending' | 'rework' | 'wastage';
  title: string;
  description: string;
  severity: 'high' | 'medium' | 'info';
}

interface ProductionAlertsProps {
  alerts: ProductionAlertItem[];
  onSelectOrder: (orderId: string) => void;
}

export const ProductionAlerts: React.FC<ProductionAlertsProps> = ({
  alerts,
  onSelectOrder,
}) => {
  if (!alerts || alerts.length === 0) {
    return null;
  }

  return (
    <div className="space-y-2.5">
      <div className="flex items-center justify-between">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-amber-300/90 flex items-center gap-2">
          <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
          <span>Attention Required in Workshop ({alerts.length})</span>
        </h3>
        <span className="text-[11px] text-slate-500 font-light">Real-time atelier alerts</span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
        {alerts.slice(0, 4).map((alert) => {
          let Icon = AlertTriangle;
          let borderClass = 'border-amber-500/30 hover:border-amber-400/60 bg-amber-500/5';
          let iconColor = 'text-amber-400';

          if (alert.type === 'delayed') {
            Icon = Clock;
            borderClass = 'border-rose-500/30 hover:border-rose-400/60 bg-rose-500/5';
            iconColor = 'text-rose-400';
          } else if (alert.type === 'qc_pending') {
            Icon = ShieldCheck;
            borderClass = 'border-cyan-500/30 hover:border-cyan-400/60 bg-cyan-500/5';
            iconColor = 'text-cyan-400';
          } else if (alert.type === 'rework') {
            Icon = Repeat;
            borderClass = 'border-purple-500/30 hover:border-purple-400/60 bg-purple-500/5';
            iconColor = 'text-purple-400';
          } else if (alert.type === 'wastage') {
            Icon = Scale;
            borderClass = 'border-orange-500/30 hover:border-orange-400/60 bg-orange-500/5';
            iconColor = 'text-orange-400';
          }

          return (
            <button
              key={alert.id}
              type="button"
              onClick={() => onSelectOrder(alert.orderId)}
              className={`p-3 rounded-xl border text-left transition-all duration-200 group flex items-start justify-between gap-3 ${borderClass}`}
            >
              <div className="space-y-1 min-w-0 flex-1">
                <div className="flex items-center gap-1.5 flex-wrap">
                  <Icon className={`w-3.5 h-3.5 shrink-0 ${iconColor}`} />
                  <span className="text-[11px] font-mono text-white font-medium truncate">
                    {alert.orderNumber}
                  </span>
                  <span className="text-[10px] text-slate-400 truncate">
                    • {alert.designName}
                  </span>
                </div>
                <div className="text-xs text-slate-200 font-medium truncate">
                  {alert.title}
                </div>
                <div className="text-[11px] text-slate-400 leading-snug line-clamp-1">
                  {alert.description}
                </div>
              </div>

              <div className="p-1 rounded-lg bg-white/[0.04] text-slate-400 group-hover:text-amber-300 group-hover:bg-amber-400/10 transition-colors shrink-0 mt-0.5">
                <ArrowRight className="w-3.5 h-3.5" />
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
};
