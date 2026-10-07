import React, { useState } from 'react';
import {
  Users,
  Cpu,
  Plus,
  Edit2,
  Trash2,
} from 'lucide-react';
import { Button } from '../../ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../../ui/card';
import { Worker, Machine, WORKER_SKILLS, MACHINE_TYPES } from '../../../types/production';

interface WorkshopResourcesViewProps {
  workers: Worker[];
  machines: Machine[];
  onAddWorker: () => void;
  onEditWorker: (worker: Worker) => void;
  onToggleWorkerAvailability: (worker: Worker) => void;
  onDeleteWorker: (worker: Worker) => void;
  onAddMachine: () => void;
  onEditMachine: (machine: Machine) => void;
  onToggleMachineAvailability: (machine: Machine) => void;
  onDeleteMachine: (machine: Machine) => void;
}

export const WorkshopResourcesView: React.FC<WorkshopResourcesViewProps> = ({
  workers,
  machines,
  onAddWorker,
  onEditWorker,
  onToggleWorkerAvailability,
  onDeleteWorker,
  onAddMachine,
  onEditMachine,
  onToggleMachineAvailability,
  onDeleteMachine,
}) => {
  const [activeTab, setActiveTab] = useState<'workers' | 'machines'>('workers');

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Tab Switcher & Action */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-[#1E2333]">
        <div className="flex space-x-2">
          <Button
            variant={activeTab === 'workers' ? 'gold' : 'outline'}
            size="sm"
            onClick={() => setActiveTab('workers')}
            className="text-xs h-8"
          >
            <Users className="w-3.5 h-3.5 mr-1.5" />
            <span>Karigars ({workers.length})</span>
          </Button>

          <Button
            variant={activeTab === 'machines' ? 'gold' : 'outline'}
            size="sm"
            onClick={() => setActiveTab('machines')}
            className="text-xs h-8"
          >
            <Cpu className="w-3.5 h-3.5 mr-1.5" />
            <span>Machinery & Tools ({machines.length})</span>
          </Button>
        </div>

        <div>
          {activeTab === 'workers' ? (
            <Button variant="gold" size="sm" onClick={onAddWorker} className="text-xs h-8">
              <Plus className="w-3.5 h-3.5 mr-1.5" />
              <span>Register Karigar</span>
            </Button>
          ) : (
            <Button variant="gold" size="sm" onClick={onAddMachine} className="text-xs h-8">
              <Plus className="w-3.5 h-3.5 mr-1.5" />
              <span>Register Equipment</span>
            </Button>
          )}
        </div>
      </div>

      {/* Karigars (Artisans) Tab */}
      {activeTab === 'workers' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {workers.map((worker) => {
            const skillConfig = WORKER_SKILLS.find((s) => s.value === worker.skill);
            return (
              <Card key={worker.id} className="bg-[#0E111A]/95 border-white/[0.08] hover:border-amber-400/30 transition-all">
                <CardHeader className="p-4 pb-2 flex flex-row items-center justify-between space-y-0">
                  <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 rounded-xl bg-blue-500/10 border border-blue-500/20 text-blue-300 flex items-center justify-center font-serif font-bold text-sm">
                      {worker.name[0]}
                    </div>
                    <div>
                      <CardTitle className="text-sm font-medium text-white">{worker.name}</CardTitle>
                      <span className="text-[11px] text-slate-400 font-light">
                        {skillConfig?.label || worker.skill}
                      </span>
                    </div>
                  </div>

                  <button
                    type="button"
                    onClick={() => onToggleWorkerAvailability(worker)}
                    className={`px-2 py-0.5 rounded text-[10px] font-medium border transition-colors ${
                      worker.is_available
                        ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30'
                        : 'bg-slate-500/10 text-slate-400 border-slate-700'
                    }`}
                  >
                    {worker.is_available ? 'Available' : 'Off-Bench'}
                  </button>
                </CardHeader>

                <CardContent className="p-4 pt-2 space-y-3">
                  <div className="flex items-center justify-between text-xs text-slate-400 font-light pt-2 border-t border-white/[0.04]">
                    <span>Bench Capacity:</span>
                    <span className="text-white font-mono font-medium">{worker.capacity_hours_per_day}h / day</span>
                  </div>

                  <div className="flex items-center justify-end space-x-2 pt-1">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => onEditWorker(worker)}
                      className="h-7 px-2 text-slate-400 hover:text-white"
                    >
                      <Edit2 className="w-3.5 h-3.5" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => onDeleteWorker(worker)}
                      className="h-7 px-2 text-rose-400 hover:text-rose-300 hover:bg-rose-500/10"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      {/* Machinery Tab */}
      {activeTab === 'machines' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {machines.map((machine) => {
            const machineConfig = MACHINE_TYPES.find((m) => m.value === machine.machine_type);
            return (
              <Card key={machine.id} className="bg-[#0E111A]/95 border-white/[0.08] hover:border-amber-400/30 transition-all">
                <CardHeader className="p-4 pb-2 flex flex-row items-center justify-between space-y-0">
                  <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 rounded-xl bg-purple-500/10 border border-purple-500/20 text-purple-300 flex items-center justify-center font-bold text-sm">
                      <Cpu className="w-4 h-4" />
                    </div>
                    <div>
                      <CardTitle className="text-sm font-medium text-white">{machine.name}</CardTitle>
                      <span className="text-[11px] text-slate-400 font-light">
                        {machineConfig?.label || machine.machine_type}
                      </span>
                    </div>
                  </div>

                  <button
                    type="button"
                    onClick={() => onToggleMachineAvailability(machine)}
                    className={`px-2 py-0.5 rounded text-[10px] font-medium border transition-colors ${
                      machine.is_available
                        ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30'
                        : 'bg-slate-500/10 text-slate-400 border-slate-700'
                    }`}
                  >
                    {machine.is_available ? 'Operational' : 'Maintenance'}
                  </button>
                </CardHeader>

                <CardContent className="p-4 pt-2 space-y-3">
                  <div className="flex items-center justify-between text-xs text-slate-400 font-light pt-2 border-t border-white/[0.04]">
                    <span>Machine Duty Cycle:</span>
                    <span className="text-white font-mono font-medium">{machine.capacity_hours_per_day}h / day</span>
                  </div>

                  <div className="flex items-center justify-end space-x-2 pt-1">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => onEditMachine(machine)}
                      className="h-7 px-2 text-slate-400 hover:text-white"
                    >
                      <Edit2 className="w-3.5 h-3.5" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => onDeleteMachine(machine)}
                      className="h-7 px-2 text-rose-400 hover:text-rose-300 hover:bg-rose-500/10"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
};
