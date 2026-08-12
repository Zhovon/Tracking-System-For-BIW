import { useState } from "react";
import { supabase } from "@/lib/supabase";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { AlertCircle, KeyRound, Loader2 } from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";

import { updateUser } from "@/lib/api";
import { useT } from "@/lib/i18n";

export function ChangePasswordDialog({ children }: { children?: React.ReactNode }) {
  const t = useT();
  const [open, setOpen] = useState(false);
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (password !== confirmPassword) {
      setError(t("cpd.mismatch"));
      return;
    }
    if (password.length < 6) {
      setError(t("cpd.tooShort"));
      return;
    }

    setLoading(true);
    setError(null);
    setSuccess(false);

    try {
      // 1. Update in Supabase client side auth
      const { error: updateError } = await supabase.auth.updateUser({ password });
      if (updateError) throw updateError;

      // 2. Fetch current user session to get user ID
      const { data: { session } } = await supabase.auth.getSession();
      const userId = session?.user?.id;
      if (!userId) {
        throw new Error(t("cpd.noSession"));
      }

      // 3. Call backend to update password & sync to Google Sheet
      await updateUser(userId, { password });

      setSuccess(true);
      setPassword("");
      setConfirmPassword("");
      setTimeout(() => {
        setOpen(false);
        setSuccess(false);
      }, 2000);
    } catch (err: any) {
      setError(err.message || t("cpd.genericError"));
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger 
        render={
          children ? (
            // If children is a valid React element, pass it directly to render.
            // Otherwise, wrap it in a span so it can receive DOM events/attributes.
            typeof children === "object" && children !== null && "type" in children ? (
              children as React.ReactElement
            ) : (
              <span className="cursor-pointer inline-flex">{children}</span>
            )
          ) : (
            <Button variant="outline" className="w-full justify-start text-slate-600 hover:text-slate-900">
              <KeyRound className="w-4 h-4 mr-2" />
              {t("cpd.trigger")}
            </Button>
          )
        } 
      />
      <DialogContent className="sm:max-w-[425px]">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>{t("cpd.title")}</DialogTitle>
            <DialogDescription>
              {t("cpd.desc")}
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            {error && (
              <Alert variant="destructive" className="bg-red-50 text-red-600 border-red-200">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}
            {success && (
              <Alert className="bg-green-50 text-green-600 border-green-200">
                <AlertDescription>{t("cpd.success")}</AlertDescription>
              </Alert>
            )}
            <div className="grid gap-2">
              <Label htmlFor="new-password">{t("cpd.newPassword")}</Label>
              <Input
                id="new-password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="confirm-password">{t("cpd.confirmPassword")}</Label>
              <Input
                id="confirm-password"
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
              />
            </div>
          </div>
          <DialogFooter>
            <Button type="button" variant="ghost" onClick={() => setOpen(false)}>
              {t("common.cancel")}
            </Button>
            <Button type="submit" disabled={loading} className="bg-indigo-600 hover:bg-indigo-700">
              {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              {t("cpd.saveChanges")}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
