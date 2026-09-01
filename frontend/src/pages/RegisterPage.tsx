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
    <div className="flex items-center justify-center min-h-[calc(100vh-12rem)] px-4 py-6">
      <Card className="w-full max-w-md bg-[#0b0e17]/95 border-slate-800 shadow-2xl backdrop-blur-md">
        <CardHeader className="space-y-2 text-center pb-6">
          <div className="mx-auto w-12 h-12 rounded-xl bg-gradient-to-tr from-amber-500 via-amber-400 to-yellow-200 p-[1px] shadow-lg shadow-amber-500/20 mb-2">
            <div className="w-full h-full bg-[#0b0e17] rounded-[11px] flex items-center justify-center">
              <Sparkles className="w-6 h-6 text-amber-400" />
            </div>
          </div>
          <CardTitle className="text-2xl font-bold tracking-tight text-white">Create Your Account</CardTitle>
          <CardDescription className="text-xs text-slate-400">
            Join JewelMind to start designing and estimating jewellery with AI decision support
          </CardDescription>
        </CardHeader>

        <form onSubmit={handleSubmit}>
          <CardContent className="space-y-4">
            {error && (
              <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 flex items-start space-x-2 text-rose-300 text-xs">
                <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                <span>{error}</span>
              </div>
            )}

            <div className="space-y-1.5">
              <label className="text-xs font-medium text-slate-300 flex items-center space-x-1">
                <User className="w-3.5 h-3.5 text-slate-400" />
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
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-medium text-slate-300 flex items-center space-x-1">
                <Mail className="w-3.5 h-3.5 text-slate-400" />
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
              <label className="text-xs font-medium text-slate-300 flex items-center space-x-1">
                <Lock className="w-3.5 h-3.5 text-slate-400" />
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
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-medium text-slate-300 flex items-center space-x-1">
                <CheckCircle2 className="w-3.5 h-3.5 text-slate-400" />
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
              />
            </div>
          </CardContent>

          <CardFooter className="flex flex-col space-y-4 pt-2">
            <Button
              type="submit"
              variant="gold"
              className="w-full h-10 font-semibold"
              disabled={isSubmitting}
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Creating Account...
                </>
              ) : (
                <>
                  Register & Sign In
                  <ArrowRight className="w-4 h-4 ml-1.5" />
                </>
              )}
            </Button>

            <div className="text-center text-xs text-slate-400">
              Already have an account?{' '}
              <button
                type="button"
                onClick={onNavigateToLogin}
                className="text-amber-400 hover:text-amber-300 font-semibold underline-offset-4 hover:underline ml-1"
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
