import React, { useState } from 'react';
import { Lock, Mail, AlertCircle, ArrowRight, Loader2, Gem } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { useAuth } from '../hooks/useAuth';

interface LoginPageProps {
  onNavigateToRegister: () => void;
  onSuccess: () => void;
}

export const LoginPage: React.FC<LoginPageProps> = ({ onNavigateToRegister, onSuccess }) => {
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!email.trim() || !password) {
      setError('Please enter both your email address and password.');
      return;
    }

    setIsSubmitting(true);
    try {
      await login({ email: email.trim(), password });
      onSuccess();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Invalid credentials. Please try again.';
      setError(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-[calc(100vh-12rem)] flex items-center justify-center px-4 py-8">
      <div className="w-full max-w-4xl grid grid-cols-1 lg:grid-cols-12 rounded-3xl overflow-hidden bg-[#0B1210] border border-[#1C2621] shadow-2xl">
        {/* Left Column: Luxury Atelier Visual */}
        <div className="hidden lg:flex lg:col-span-5 relative bg-[#050806] flex-col justify-between p-8 overflow-hidden border-r border-[#1C2621]">
          {/* Background Photo with Dark Luxury Vignette */}
          <div className="absolute inset-0">
            <img
              src="/assets/photos/pexels-hatice-genc-3580692-32797480.jpg"
              alt="Luxury Jewellery Collection"
              className="w-full h-full object-cover object-center opacity-40 scale-105"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-[#050806] via-[#050806]/70 to-[#050806]/50" />
          </div>

          {/* Top Brand Monogram */}
          <div className="relative z-10 flex items-center space-x-3">
            <div className="w-9 h-9 rounded-xl bg-[#141D19] border border-[#D8AD55]/40 flex items-center justify-center shadow-lg">
              <Gem className="w-4 h-4 text-[#D8AD55]" />
            </div>
            <div>
              <span className="font-serif font-bold text-lg text-[#F4EFE5] tracking-wide">JewelMind</span>
              <p className="text-[10px] text-[#A9ADA7] uppercase font-mono tracking-widest">Fine Jewellery Studio</p>
            </div>
          </div>

          {/* Editorial Quote */}
          <div className="relative z-10 space-y-3">
            <div className="w-8 h-[2px] bg-[#D8AD55]" />
            <blockquote className="font-serif text-lg text-[#F4EFE5] font-light italic leading-relaxed">
              "Every fine jewel begins with an intention. Precision turns it into eternity."
            </blockquote>
            <p className="text-xs text-[#A9ADA7] font-mono uppercase tracking-widest">
              High Jewellery Intelligence
            </p>
          </div>
        </div>

        {/* Right Column: Clean Luxury Login Form */}
        <div className="lg:col-span-7 p-8 sm:p-12 flex flex-col justify-center bg-[#0B1210]">
          <div className="space-y-6 max-w-md mx-auto w-full">
            <div className="space-y-2">
              <h2 className="text-3xl font-serif font-normal tracking-wide text-[#F4EFE5]">
                Welcome back.
              </h2>
              <p className="text-xs sm:text-sm text-[#A9ADA7] font-light">
                Sign in to your JewelMind workspace.
              </p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-5">
              {error && (
                <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/30 flex items-start space-x-2.5 text-rose-300 text-xs">
                  <AlertCircle className="w-4 h-4 shrink-0 mt-0.5 text-rose-400" />
                  <span className="leading-relaxed">{error}</span>
                </div>
              )}

              <div className="space-y-1.5">
                <label className="text-xs font-medium text-[#A9ADA7] flex items-center space-x-1.5">
                  <Mail className="w-3.5 h-3.5 text-[#D8AD55]" />
                  <span>Email Address</span>
                </label>
                <Input
                  type="email"
                  placeholder="artisan@jewelmind.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  disabled={isSubmitting}
                  autoComplete="email"
                  required
                />
              </div>

              <div className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <label className="text-xs font-medium text-[#A9ADA7] flex items-center space-x-1.5">
                    <Lock className="w-3.5 h-3.5 text-[#D8AD55]" />
                    <span>Password</span>
                  </label>
                  <span className="text-[11px] text-[#6F756F] hover:text-[#D8AD55] cursor-pointer">
                    Forgot password?
                  </span>
                </div>
                <Input
                  type="password"
                  placeholder="••••••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  disabled={isSubmitting}
                  autoComplete="current-password"
                  required
                />
              </div>

              <div className="pt-2 space-y-4">
                <Button
                  type="submit"
                  variant="gold"
                  size="touch"
                  className="w-full text-[#050806] font-bold text-xs shadow-lg shadow-[#D8AD55]/15"
                  disabled={isSubmitting}
                >
                  {isSubmitting ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin text-[#050806]" />
                      Signing In...
                    </>
                  ) : (
                    <>
                      Sign In
                      <ArrowRight className="w-4 h-4 ml-1.5 text-[#050806]" />
                    </>
                  )}
                </Button>

                <div className="text-center text-xs text-[#A9ADA7] pt-2">
                  Don't have an account?{' '}
                  <button
                    type="button"
                    onClick={onNavigateToRegister}
                    className="text-[#D8AD55] hover:text-[#F1D28A] font-semibold underline-offset-4 hover:underline ml-1 transition-colors cursor-pointer"
                  >
                    Create Account
                  </button>
                </div>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
