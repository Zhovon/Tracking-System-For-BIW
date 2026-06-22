"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import { supabase } from "@/lib/supabase";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { AlertCircle, Loader2, ArrowLeft, CheckCircle2 } from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";

export default function LoginPage() {
  const [view, setView] = useState<"login" | "forgot_password">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [resetSent, setResetSent] = useState(false);
  const router = useRouter();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    const { data, error: authError } = await supabase.auth.signInWithPassword({
      email,
      password,
    });

    if (authError) {
      setError(authError.message);
      setLoading(false);
      return;
    }

    if (data.session) {
      localStorage.removeItem("mock_user");
      router.push("/dashboard");
    }
  };

  const handleForgotPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    // Redirect back to our reset-password page after clicking the email link
    const { error: resetError } = await supabase.auth.resetPasswordForEmail(email, {
      redirectTo: `${window.location.origin}/reset-password`,
    });

    setLoading(false);

    if (resetError) {
      setError(resetError.message);
    } else {
      setResetSent(true);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-indigo-50 p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8 flex flex-col items-center">
          <Image src="/logo.jpeg" alt="BIW OS Logo" width={64} height={64} className="rounded-xl mb-4 shadow-sm object-cover" />
          <h1 className="text-3xl font-bold tracking-tight text-indigo-900 mb-2">BIW OS</h1>
          <p className="text-slate-600">
            {view === "login" ? "Sign in to manage your system" : "Reset your password"}
          </p>
        </div>

        <Card className="bg-white border-slate-200 shadow-xl overflow-hidden relative">
          {view === "login" ? (
            <div className="animate-in fade-in slide-in-from-bottom-4 duration-300">
              <CardHeader>
                <CardTitle className="text-xl text-slate-900">Welcome back</CardTitle>
                <CardDescription className="text-slate-500">Enter your credentials to access the system.</CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleLogin} className="space-y-4">
                  {error && (
                    <Alert variant="destructive" className="bg-red-500/10 border-red-500/20 text-red-400">
                      <AlertCircle className="h-4 w-4" />
                      <AlertDescription>{error}</AlertDescription>
                    </Alert>
                  )}
                  
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-slate-700">Email address</label>
                    <Input
                      type="email"
                      required
                      placeholder="name@biw.com"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      className="bg-slate-50 border-slate-200 text-slate-900"
                      autoComplete="username"
                    />
                  </div>

                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <label className="text-sm font-medium text-slate-700">Password</label>
                      <button 
                        type="button" 
                        onClick={() => { setView("forgot_password"); setError(null); setResetSent(false); }}
                        className="text-xs text-indigo-600 hover:text-indigo-800 font-medium"
                      >
                        Forgot password?
                      </button>
                    </div>
                    <Input
                      type="password"
                      required
                      placeholder="••••••••"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      className="bg-slate-50 border-slate-200 text-slate-900"
                      autoComplete="current-password"
                    />
                  </div>

                  <Button
                    type="submit"
                    className="w-full bg-indigo-500 hover:bg-indigo-600 text-white mt-2"
                    disabled={loading}
                  >
                    {loading ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Signing in...
                      </>
                    ) : (
                      "Sign in"
                    )}
                  </Button>
                </form>
              </CardContent>
            </div>
          ) : (
            <div className="animate-in fade-in slide-in-from-right-4 duration-300">
              <CardHeader>
                <Button 
                  variant="ghost" 
                  size="sm" 
                  className="-ml-2 mb-2 w-fit text-slate-500 hover:text-slate-900"
                  onClick={() => { setView("login"); setError(null); }}
                >
                  <ArrowLeft className="w-4 h-4 mr-2" />
                  Back to login
                </Button>
                <CardTitle className="text-xl text-slate-900">Forgot Password</CardTitle>
                <CardDescription className="text-slate-500">
                  Enter your email address and we&apos;ll send you a link to reset your password.
                </CardDescription>
              </CardHeader>
              <CardContent>
                {resetSent ? (
                  <Alert className="bg-emerald-50 text-emerald-700 border-emerald-200 mb-4">
                    <CheckCircle2 className="h-4 w-4" />
                    <AlertDescription>
                      If an account exists with that email, a password reset link has been sent. Please check your inbox.
                    </AlertDescription>
                  </Alert>
                ) : (
                  <form onSubmit={handleForgotPassword} className="space-y-4">
                    {error && (
                      <Alert variant="destructive" className="bg-red-500/10 border-red-500/20 text-red-400">
                        <AlertCircle className="h-4 w-4" />
                        <AlertDescription>{error}</AlertDescription>
                      </Alert>
                    )}
                    
                    <div className="space-y-2">
                      <label className="text-sm font-medium text-slate-700">Email address</label>
                      <Input
                        type="email"
                        required
                        placeholder="name@biw.com"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        className="bg-slate-50 border-slate-200 text-slate-900"
                      />
                    </div>

                    <Button
                      type="submit"
                      className="w-full bg-indigo-500 hover:bg-indigo-600 text-white mt-2"
                      disabled={loading || !email}
                    >
                      {loading ? (
                        <>
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                          Sending link...
                        </>
                      ) : (
                        "Send reset link"
                      )}
                    </Button>
                  </form>
                )}
              </CardContent>
            </div>
          )}
        </Card>
        <p className="text-center text-sm text-slate-500 mt-8">
          Don&apos;t have an account? Contact your BIW owner to request access.
        </p>
      </div>
    </div>
  );
}
