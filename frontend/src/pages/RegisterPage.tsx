import React, { useState } from 'react';
import { Sparkles, Lock, Mail, User, AlertCircle, ArrowRight, Loader2, CheckCircle2 } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { useAuth } from '../hooks/useAuth';

interface RegisterPageProps {
  onNavigateToLogin: () => void;
  onSuccess: () => void;
}

export const RegisterPage: React.FC<RegisterPageProps> = ({ onNavigateToLogin, onSuccess }) => {
  const { register } = useAuth();
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!fullName.trim()) {
      setError('Please enter your full name.');
      return;
    }
    if (!email.trim()) {
      setError('Please enter a valid email address.');
      return;
    }
    if (password.length < 8) {
      setError('Password must be at least 8 characters long.');
      return;
    }
    if (password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    setIsSubmitting(true);
    try {
      await register({
        full_name: fullName.trim(),
        email: email.trim(),
        password,
      });
      onSuccess();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Registration failed. Please try again.';
      setError(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="flex items-center justify-center min-h-[calc(100vh-14rem)] px-4 py-8">
      <Card className="w-full max-w-md bg-[#0E111A]/95 border-[#1E2333] shadow-2xl backdrop-blur-md rounded-2xl relative overflow-hidden">
        <div className="absolute top-0 inset-x-0 h-px bg-gradient-to-r from-transparent via-[#D4AF37]/40 to-transparent" />

        <CardHeader className="space-y-3 text-center pb-6 pt-8">
          <div className="mx-auto w-12 h-12 rounded-xl bg-gradient-to-br from-[#D4AF37]/20 via-[#161B26] to-[#08090D] border border-[#D4AF37]/30 flex items-center justify-center shadow-lg shadow-[#D4AF37]/5 mb-1">
            <Sparkles className="w-5 h-5 text-[#E6CA65]" />
          </div>
          <CardTitle className="text-2xl font-serif font-light tracking-wide text-[#F3F4F6]">
            Create Atelier Account
          </CardTitle>
          <CardDescription className="text-xs text-slate-400 max-w-xs mx-auto leading-relaxed">
            Join JewelMind to orchestrate bespoke jewellery designs, ControlNet renders, and workshop scheduling
          </CardDescription>
        </CardHeader>

        <form onSubmit={handleSubmit}>
          <CardContent className="space-y-4 px-6 sm:px-8">
            {error && (
              <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 flex items-start space-x-2.5 text-rose-300 text-xs">
                <AlertCircle className="w-4 h-4 shrink-0 mt-0.5 text-rose-400" />
                <span className="leading-relaxed">{error}</span>
              </div>
            )}

            <div className="space-y-1.5">
              <label className="text-xs font-medium text-slate-300 flex items-center space-x-1.5">
                <User className="w-3.5 h-3.5 text-[#D4AF37]/70" />
                <span>Full Name</span>
              </label>
              <Input
                type="text"
                placeholder="Elena Rostova"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                disabled={isSubmitting}
                autoComplete="name"
                required
                className="bg-[#121622] border-[#22283A] text-slate-100 placeholder:text-slate-600 focus:border-[#D4AF37]/60 focus:ring-1 focus:ring-[#D4AF37]/40 rounded-xl"
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-medium text-slate-300 flex items-center space-x-1.5">
                <Mail className="w-3.5 h-3.5 text-[#D4AF37]/70" />
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
                className="bg-[#121622] border-[#22283A] text-slate-100 placeholder:text-slate-600 focus:border-[#D4AF37]/60 focus:ring-1 focus:ring-[#D4AF37]/40 rounded-xl"
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-medium text-slate-300 flex items-center space-x-1.5">
                <Lock className="w-3.5 h-3.5 text-[#D4AF37]/70" />
                <span>Password (min. 8 characters)</span>
              </label>
              <Input
                type="password"
                placeholder="••••••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                disabled={isSubmitting}
                autoComplete="new-password"
                required
                className="bg-[#121622] border-[#22283A] text-slate-100 placeholder:text-slate-600 focus:border-[#D4AF37]/60 focus:ring-1 focus:ring-[#D4AF37]/40 rounded-xl"
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-medium text-slate-300 flex items-center space-x-1.5">
                <CheckCircle2 className="w-3.5 h-3.5 text-[#D4AF37]/70" />
                <span>Confirm Password</span>
              </label>
              <Input
                type="password"
                placeholder="••••••••••••"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                disabled={isSubmitting}
                autoComplete="new-password"
                required
                className="bg-[#121622] border-[#22283A] text-slate-100 placeholder:text-slate-600 focus:border-[#D4AF37]/60 focus:ring-1 focus:ring-[#D4AF37]/40 rounded-xl"
              />
            </div>
          </CardContent>

          <CardFooter className="flex flex-col space-y-4 pt-4 pb-8 px-6 sm:px-8">
            <Button
              type="submit"
              variant="gold"
              className="w-full h-11 text-sm font-medium tracking-wide rounded-xl shadow-lg shadow-[#D4AF37]/10"
              disabled={isSubmitting}
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Creating Account...
                </>
              ) : (
                <>
                  Register & Enter Atelier
                  <ArrowRight className="w-4 h-4 ml-1.5 opacity-80" />
                </>
              )}
            </Button>

            <div className="text-center text-xs text-slate-400 pt-1">
              Already have an atelier account?{' '}
              <button
                type="button"
                onClick={onNavigateToLogin}
                className="text-[#E6CA65] hover:text-[#F3DB7C] font-medium underline-offset-4 hover:underline ml-1 transition-colors"
              >
                Sign In
              </button>
            </div>
          </CardFooter>
        </form>
      </Card>
    </div>
  );
};

export default RegisterPage;
