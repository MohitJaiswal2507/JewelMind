import React, { useEffect, useState } from 'react';
import { Play, Pause, CheckCircle2, Clock } from 'lucide-react';
import { ExecutionStatus } from '../../../types/execution';

interface ExecutionTimerProps {
  status: ExecutionStatus;
  actualStartTime: string | null;
  pauseDurationHours?: number;
  lastPausedAt?: string | null;
  actualDurationHours?: number | null;
  plannedDurationHours?: number | null;
}

export const ExecutionTimer: React.FC<ExecutionTimerProps> = ({
  status,
  actualStartTime,
  pauseDurationHours = 0,
  lastPausedAt,
  actualDurationHours,
  plannedDurationHours,
}) => {
  const [elapsedSeconds, setElapsedSeconds] = useState<number>(0);

  useEffect(() => {
    if (!actualStartTime) {
      setElapsedSeconds(0);
      return;
    }

    const calculateElapsed = () => {
      const startMs = new Date(actualStartTime).getTime();
      const nowMs = Date.now();
      const pauseMs = (pauseDurationHours || 0) * 3600 * 1000;

      if (status === 'completed' && actualDurationHours != null) {
        return Math.floor(actualDurationHours * 3600);
      }

      if (status === 'paused' && lastPausedAt) {
        const pausedMs = new Date(lastPausedAt).getTime();
        const activeBeforeCurrentPause = Math.max(0, pausedMs - startMs - pauseMs);
        return Math.floor(activeBeforeCurrentPause / 1000);
      }

      if (status === 'in_progress') {
        const activeMs = Math.max(0, nowMs - startMs - pauseMs);
        return Math.floor(activeMs / 1000);
      }

      return 0;
    };

    setElapsedSeconds(calculateElapsed());

    if (status === 'in_progress') {
      const interval = setInterval(() => {
        setElapsedSeconds(calculateElapsed());
      }, 1000);
      return () => clearInterval(interval);
    }
  }, [status, actualStartTime, pauseDurationHours, lastPausedAt, actualDurationHours]);

  const formatTime = (totalSecs: number) => {
    const hours = Math.floor(totalSecs / 3600);
    const minutes = Math.floor((totalSecs % 3600) / 60);
    const seconds = totalSecs % 60;
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
  };

  const getStatusIcon = () => {
    switch (status) {
      case 'in_progress':
        return <Play className="w-4 h-4 text-emerald-400 animate-pulse fill-emerald-400" />;
      case 'paused':
        return <Pause className="w-4 h-4 text-amber-400 fill-amber-400" />;
      case 'completed':
        return <CheckCircle2 className="w-4 h-4 text-blue-400" />;
      default:
        return <Clock className="w-4 h-4 text-slate-500" />;
    }
  };

  return (
    <div className="flex items-center justify-between p-4 rounded-xl bg-black/40 border border-white/[0.08] shadow-inner">
      <div className="flex items-center space-x-3">
        <div className="w-9 h-9 rounded-lg bg-white/[0.05] border border-white/[0.08] flex items-center justify-center">
          {getStatusIcon()}
        </div>
        <div>
          <span className="text-[10px] uppercase font-bold tracking-widest text-slate-400">
            {status === 'in_progress' ? 'Active Timer' : status === 'paused' ? 'Operation Paused' : status === 'completed' ? 'Final Logged Time' : 'Standard Duration'}
          </span>
          <div className="font-mono text-2xl font-bold tracking-tight text-white flex items-baseline space-x-2">
            <span>{status === 'pending' || status === 'ready' ? (plannedDurationHours ? `${plannedDurationHours.toFixed(1)}h est` : '--:--:--') : formatTime(elapsedSeconds)}</span>
          </div>
        </div>
      </div>

      {plannedDurationHours != null && (
        <div className="text-right">
          <span className="text-[10px] text-slate-500 uppercase tracking-wider block">Target Norm</span>
          <span className="font-mono text-xs text-amber-200/90 font-medium">
            {plannedDurationHours.toFixed(2)}h
          </span>
        </div>
      )}
    </div>
  );
};
