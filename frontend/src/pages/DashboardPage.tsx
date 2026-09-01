import React, { useEffect, useState } from 'react';
import { 
  User as UserIcon, 
  ShieldCheck, 
  LogOut, 
  Key, 
  Mail, 
  Calendar, 
  Sparkles,
  Layers,
  Sliders,
  Clock,
  Loader2,
  AlertCircle
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Separator } from '../components/ui/separator';
import { useAuth } from '../hooks/useAuth';
import { authService } from '../services/api/authService';
import { User } from '../types/auth';

interface DashboardPageProps {
  onLogout: () => void;
}

export const DashboardPage: React.FC<DashboardPageProps> = ({ onLogout }) => {
  const { user, logout } = useAuth();
  const [profile, setProfile] = useState<User | null>(user);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchLatestProfile = async () => {
      setLoading(true);
      try {
        const data = await authService.getMe();
        setProfile(data);
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : 'Failed to load protected profile';
        setError(msg);
      } finally {
        setLoading(false);
      }
    };

    fetchLatestProfile();
  }, []);

  const handleLogout = async () => {
    await logout();
    onLogout();
  };

  return (
    <div className="space-y-8 max-w-6xl mx-auto py-6">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-gradient-to-br from-slate-900/90 to-[#0d121f] p-6 sm:p-8 rounded-2xl border border-slate-800 shadow-xl">
        <div className="flex items-center space-x-4">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-amber-500 via-amber-400 to-yellow-200 p-[1px] shadow-lg shadow-amber-500/20 shrink-0">
            <div className="w-full h-full bg-[#0b0e17] rounded-[15px] flex items-center justify-center">
              <UserIcon className="w-7 h-7 text-amber-400" />
            </div>
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
                Welcome back, {profile?.full_name || 'Artisan'}
              </h1>
              <Badge variant="gold" className="text-xs">
                {profile?.role.toUpperCase() || 'USER'}
              </Badge>
            </div>
            <p className="text-xs sm:text-sm text-slate-400 mt-1">
              Authenticated Session Active • Connected to JewelMind Backend
            </p>
          </div>
        </div>

        <Button
          variant="outline"
          size="sm"
          onClick={handleLogout}
          className="border-slate-700 hover:border-rose-500 hover:text-rose-400 hover:bg-rose-500/10 transition"
        >
          <LogOut className="w-4 h-4 mr-2" />
          Sign Out
        </Button>
      </div>

      {/* Profile & Security Information */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="bg-[#0b0f19] border-slate-800">
          <CardHeader className="pb-3">
            <div className="flex items-center space-x-2 text-amber-400">
              <ShieldCheck className="w-5 h-5" />
              <CardTitle className="text-base">Identity & Profile</CardTitle>
            </div>
            <CardDescription className="text-xs">Verified account credentials</CardDescription>
          </CardHeader>
          <Separator />
          <CardContent className="pt-4 space-y-3 text-xs">
            <div className="flex items-center justify-between">
              <span className="text-slate-400 flex items-center gap-1.5">
                <Mail className="w-3.5 h-3.5" /> Email
              </span>
              <span className="font-mono text-slate-200">{profile?.email}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-slate-400 flex items-center gap-1.5">
                <UserIcon className="w-3.5 h-3.5" /> Status
              </span>
              <Badge variant={profile?.is_active ? 'success' : 'destructive'} className="text-[10px]">
                {profile?.is_active ? 'Active' : 'Inactive'}
              </Badge>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-slate-400 flex items-center gap-1.5">
                <Calendar className="w-3.5 h-3.5" /> Registered
              </span>
              <span className="text-slate-300">
                {profile?.created_at ? new Date(profile.created_at).toLocaleDateString() : 'Today'}
              </span>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-[#0b0f19] border-slate-800 md:col-span-2">
          <CardHeader className="pb-3">
            <div className="flex items-center space-x-2 text-amber-400">
              <Key className="w-5 h-5" />
              <CardTitle className="text-base">Protected API Verification</CardTitle>
            </div>
            <CardDescription className="text-xs">
              Response from secure endpoint: <code>GET /api/v1/auth/me</code>
            </CardDescription>
          </CardHeader>
          <Separator />
          <CardContent className="pt-4">
            {loading ? (
              <div className="flex items-center space-x-2 text-slate-400 text-xs py-4">
                <Loader2 className="w-4 h-4 animate-spin text-amber-400" />
                <span>Loading latest profile data...</span>
              </div>
            ) : error ? (
              <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 flex items-center space-x-2 text-rose-300 text-xs">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{error}</span>
              </div>
            ) : (
              <div className="p-3.5 rounded-lg bg-slate-950/80 border border-slate-800/80 font-mono text-xs text-emerald-400 overflow-x-auto">
                <pre>{JSON.stringify(profile, null, 2)}</pre>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Upcoming Workflows (Phase 3+) */}
      <div className="space-y-4 pt-4">
        <div>
          <h2 className="text-lg font-bold text-white tracking-tight">Your Jewellery Workspace</h2>
          <p className="text-xs text-slate-400">Features unlocked as upcoming phases are deployed</p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card className="bg-[#0b0f19] border-slate-800 opacity-90">
            <CardHeader className="p-5 space-y-2">
              <div className="p-2 rounded-lg bg-amber-500/10 text-amber-400 w-fit">
                <Layers className="w-4 h-4" />
              </div>
              <CardTitle className="text-sm">Designs & Sketches</CardTitle>
              <CardDescription className="text-xs leading-relaxed">
                Phase 3: Manage your jewellery collections (Rings, Necklaces, Earrings, Pendants).
              </CardDescription>
            </CardHeader>
          </Card>

          <Card className="bg-[#0b0f19] border-slate-800 opacity-90">
            <CardHeader className="p-5 space-y-2">
              <div className="p-2 rounded-lg bg-amber-500/10 text-amber-400 w-fit">
                <Sparkles className="w-4 h-4" />
              </div>
              <CardTitle className="text-sm">AI Rendering</CardTitle>
              <CardDescription className="text-xs leading-relaxed">
                Phase 7: ControlNet photorealistic gold, silver & gemstone visual generation.
              </CardDescription>
            </CardHeader>
          </Card>

          <Card className="bg-[#0b0f19] border-slate-800 opacity-90">
            <CardHeader className="p-5 space-y-2">
              <div className="p-2 rounded-lg bg-amber-500/10 text-amber-400 w-fit">
                <Sliders className="w-4 h-4" />
              </div>
              <CardTitle className="text-sm">Cost & Time ML</CardTitle>
              <CardDescription className="text-xs leading-relaxed">
                Phase 9: XGBoost metal weight, crafting hours, and precious scrap estimation.
              </CardDescription>
            </CardHeader>
          </Card>

          <Card className="bg-[#0b0f19] border-slate-800 opacity-90">
            <CardHeader className="p-5 space-y-2">
              <div className="p-2 rounded-lg bg-amber-500/10 text-amber-400 w-fit">
                <Clock className="w-4 h-4" />
              </div>
              <CardTitle className="text-sm">OR-Tools Scheduling</CardTitle>
              <CardDescription className="text-xs leading-relaxed">
                Phase 12: Automated workshop schedule and artisan task optimization.
              </CardDescription>
            </CardHeader>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;
