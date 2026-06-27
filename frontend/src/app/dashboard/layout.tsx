"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchRooms, fetchCurrentUser, fetchNotifications, markNotificationRead } from "@/lib/api";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { supabase } from "@/lib/supabase";
import { LayoutDashboard, Users, User, Loader2, Bell, CheckCircle2, UserPlus, LogOut, Menu, X } from "lucide-react";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { ChangePasswordDialog } from "@/components/ChangePasswordDialog";
import { Skeleton } from "@/components/ui/skeleton";

export const getSlug = (name: string) => name.toLowerCase().replace(/[^a-z0-9]+/g, '-');

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  
  // Protect route
  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      if (!session) {
        router.push("/login");
      }
    });
    
    const { data: { subscription } } = supabase.auth.onAuthStateChange((event, session) => {
      if (event === 'SIGNED_OUT' || !session) {
        router.push("/login");
      }
    });
    
    return () => subscription.unsubscribe();
  }, [router]);

  const { data: currentUser, isLoading: loadingUser } = useQuery({
    queryKey: ["currentUser"],
    queryFn: fetchCurrentUser,
    retry: false,
  });

  const { data: rooms, isLoading, error } = useQuery({
    queryKey: ["rooms"],
    queryFn: fetchRooms,
    enabled: !!currentUser,
  });

  const queryClient = useQueryClient();
  const { data: notifications } = useQuery({
    queryKey: ["notifications"],
    queryFn: () => fetchNotifications(0, 20),
    refetchInterval: 10000,
    enabled: !!currentUser,
  });

  const unreadCount = notifications?.filter((n: any) => !n.is_read).length || 0;

  const markReadMutation = useMutation({
    mutationFn: (id: string) => markNotificationRead(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["notifications"] }),
  });

  const [showNotifications, setShowNotifications] = useState(false);
  const [mobileRoomsOpen, setMobileRoomsOpen] = useState(false);
  const [mobileProfileOpen, setMobileProfileOpen] = useState(false);
  
  // Audio for notifications
  const [audio] = useState(() => typeof Audio !== "undefined" ? new Audio("/ding.mp3") : null);

  useEffect(() => {
    if ("Notification" in window && Notification.permission === "default") {
      Notification.requestPermission();
    }
  }, []);

  // Supabase Realtime for Notifications
  useEffect(() => {
    if (!currentUser) return;
    
    const channel = supabase.channel('notifications_changes')
      .on(
        'postgres_changes',
        { event: 'INSERT', schema: 'public', table: 'notifications', filter: `user_id=eq.${currentUser.id}` },
        (payload: any) => {
          queryClient.invalidateQueries({ queryKey: ["notifications"] });
          
          // Play sound
          if (audio) {
            audio.currentTime = 0;
            audio.play().catch(e => console.log("Audio play blocked", e));
          }

          // Show native notification
          if ("Notification" in window && Notification.permission === "granted") {
            new Notification("New Notification", {
              body: payload.new.message,
              icon: "/logo.jpeg"
            });
          }
        }
      )
      .on(
        'postgres_changes',
        { event: 'UPDATE', schema: 'public', table: 'notifications', filter: `user_id=eq.${currentUser.id}` },
        () => {
          queryClient.invalidateQueries({ queryKey: ["notifications"] });
        }
      )
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, [currentUser, queryClient]);

  const handleLogout = async () => {
    await supabase.auth.signOut();
    router.push("/login");
  };

  if (loadingUser) {
    return <div className="min-h-screen flex items-center justify-center bg-slate-50"><Loader2 className="h-8 w-8 animate-spin text-slate-400" /></div>;
  }

  const NotificationBell = () => (
    <div className="relative">
      <button 
        className="p-2 rounded-full hover:bg-slate-100 transition-colors relative"
        onClick={() => setShowNotifications(!showNotifications)}
      >
        <Bell className="w-5 h-5 text-slate-600" />
        {unreadCount > 0 && (
          <span className="absolute top-1 right-1 w-2.5 h-2.5 bg-red-500 rounded-full border-2 border-white" />
        )}
      </button>
      
      {/* Desktop Notification Popup (Hidden on Mobile) */}
      {showNotifications && (
        <div className="hidden md:block absolute top-full left-0 mt-2 w-80 bg-white rounded-xl shadow-xl border border-slate-200 z-50 overflow-hidden">
          <div className="p-3 border-b border-slate-200 bg-slate-50 font-semibold text-sm">
            Notifications
          </div>
          <div className="max-h-80 overflow-y-auto">
            {notifications?.length === 0 ? (
              <div className="p-4 text-center text-sm text-zinc-500">No notifications</div>
            ) : (
              <div className="divide-y divide-slate-100">
                {notifications?.map((notif: any) => (
                  <div key={notif.id} className={`p-3 text-sm flex gap-3 ${notif.is_read ? 'opacity-60' : 'bg-indigo-50/50'}`}>
                    <div className="flex-1">
                      <p className="text-slate-800">{notif.message}</p>
                      <p className="text-xs text-slate-400 mt-1">{new Date(notif.created_at).toLocaleString()}</p>
                    </div>
                    {!notif.is_read && (
                      <button 
                        onClick={() => markReadMutation.mutate(notif.id)}
                        className="text-emerald-500 hover:text-emerald-600 transition-colors self-start mt-1"
                        title="Mark as read"
                      >
                        <CheckCircle2 className="w-4 h-4" />
                      </button>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
          <Link
            href="/dashboard/notifications"
            onClick={() => setShowNotifications(false)}
            className="block p-3 border-t border-slate-200 bg-slate-50 text-center text-sm font-semibold text-indigo-600 hover:bg-slate-100 transition-colors"
          >
            See all in Notifications
          </Link>
        </div>
      )}
    </div>
  );

  return (
    <div className="flex h-[100dvh] overflow-hidden bg-slate-50 text-slate-900 relative">
      
      {/* Desktop Sidebar (Hidden on Mobile) */}
      <aside className="hidden md:flex inset-y-0 left-0 z-50 w-64 bg-white border-r border-slate-200 flex-col flex-shrink-0">
        <div className="h-16 flex items-center justify-between px-6 border-b border-slate-200 relative">
          <h1 className="text-lg font-bold flex items-center gap-2">
            <img src="/logo.jpeg" alt="BIW OS Logo" className="w-6 h-6 rounded object-cover" />
            BIW OS
          </h1>
          <NotificationBell />
        </div>

        <div className="flex-1 overflow-y-auto py-4">
          <nav className="space-y-1 px-3">
            <h2 className="px-3 text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-2 mt-2">
              Your Rooms
            </h2>
            
            {isLoading && (
              <div className="space-y-2 px-3 py-1">
                {[...Array(5)].map((_, i) => (
                  <div key={i} className="flex items-center gap-3 py-1.5 animate-pulse">
                    <Skeleton className="w-4 h-4 rounded-full bg-slate-200" />
                    <Skeleton className="h-4 flex-1 bg-slate-200" />
                  </div>
                ))}
              </div>
            )}
            
            {error && (
              <div className="px-3 text-sm text-red-500">Failed to load rooms</div>
            )}

            {rooms?.map((room: any) => (
              <Link
                key={room.id}
                href={`/dashboard?room=${getSlug(room.name)}`}
                className="flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-md hover:bg-slate-100 transition-colors"
              >
                {room.type === "branch" ? (
                  <Users className="w-4 h-4 text-blue-500" />
                ) : room.type === "founder" ? (
                  <User className="w-4 h-4 text-purple-500" />
                ) : (
                  <Users className="w-4 h-4 text-green-500" />
                )}
                {room.name}
              </Link>
            ))}

            {currentUser?.role === "owner" && (
              <>
                <div className="my-4 border-t border-slate-200"></div>
                <h2 className="px-3 text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">
                  Administration
                </h2>
                <Link
                  href="/dashboard/staff"
                  className="flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-md hover:bg-slate-100 transition-colors text-indigo-600"
                >
                  <UserPlus className="w-4 h-4" />
                  Staff Management
                </Link>
              </>
            )}
          </nav>
        </div>

        <div className="p-4 border-t border-slate-200 bg-slate-50 flex items-center justify-between">
          <div className="flex flex-col">
            <span className="text-sm font-medium text-slate-800">{currentUser?.name}</span>
            <span className="text-xs text-slate-500 capitalize">{currentUser?.role.replace('_', ' ')}</span>
          </div>
          <div className="flex gap-1">
            <ChangePasswordDialog>
              <Button variant="ghost" size="icon" className="text-slate-500 hover:text-slate-900 hover:bg-slate-200" title="Change Password">
                <LogOut className="h-4 w-4 hidden" /> {/* Dummy to keep sizing */}
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="lucide lucide-key-round"><path d="M2 18v3c0 .6.4 1 1 1h4v-3h3v-3h2l1.4-1.4a6.5 6.5 0 1 0-4-4Z"/><circle cx="16.5" cy="7.5" r=".5"/></svg>
              </Button>
            </ChangePasswordDialog>
            <Button variant="ghost" size="icon" onClick={handleLogout} className="text-slate-500 hover:text-red-600 hover:bg-red-50" title="Log Out">
              <LogOut className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col min-w-0 overflow-hidden pb-[60px] md:pb-0">
        <div className="flex-1 overflow-hidden flex flex-col">
          {children}
        </div>
      </main>

      {/* Mobile Bottom Navigation Bar (Hidden on Desktop) */}
      <div className="md:hidden fixed bottom-0 left-0 right-0 h-[60px] bg-white/85 backdrop-blur-xl border-t border-slate-200/50 flex items-center justify-around z-50 px-2 pb-safe shadow-[0_-4px_25px_rgba(0,0,0,0.06)]">
        <button 
          onClick={() => {
            const params = new URLSearchParams(window.location.search);
            params.delete('ticket_id');
            router.push(`/dashboard?${params.toString()}`);
          }} 
          className="flex flex-col items-center justify-center w-16 h-full text-slate-500 hover:text-indigo-600 transition-colors active:scale-95"
        >
          <LayoutDashboard className="w-5 h-5 mb-1" />
          <span className="text-[10px] font-medium">Tickets</span>
        </button>
        
        <button onClick={() => { setMobileRoomsOpen(!mobileRoomsOpen); setMobileProfileOpen(false); setShowNotifications(false); }} className="flex flex-col items-center justify-center w-16 h-full text-slate-500 hover:text-indigo-600 transition-colors active:scale-95">
          <Users className="w-5 h-5 mb-1" />
          <span className="text-[10px] font-medium">Rooms</span>
        </button>

        <Link 
          href="/dashboard/notifications" 
          onClick={() => { setMobileProfileOpen(false); setMobileRoomsOpen(false); setShowNotifications(false); }}
          className="flex flex-col items-center justify-center w-16 h-full text-slate-500 hover:text-indigo-600 transition-colors active:scale-95 relative"
        >
          <Bell className="w-5 h-5 mb-1" />
          <span className="text-[10px] font-medium">Alerts</span>
          {unreadCount > 0 && (
            <span className="absolute top-2 right-4 w-2.5 h-2.5 bg-red-500 rounded-full border-2 border-white" />
          )}
        </Link>

        <button onClick={() => { setMobileProfileOpen(!mobileProfileOpen); setMobileRoomsOpen(false); setShowNotifications(false); }} className="flex flex-col items-center justify-center w-16 h-full text-slate-500 hover:text-indigo-600 transition-colors active:scale-95">
          <User className="w-5 h-5 mb-1" />
          <span className="text-[10px] font-medium">Profile</span>
        </button>
      </div>

      {/* Mobile Rooms Drawer */}
      {mobileRoomsOpen && (
        <div className="md:hidden fixed bottom-[60px] left-0 right-0 bg-white border-t border-slate-200 rounded-t-3xl shadow-[0_-15px_40px_rgba(0,0,0,0.12)] z-40 max-h-[60vh] overflow-hidden flex flex-col animate-in slide-in-from-bottom duration-300 ease-out">
          <div className="p-4 border-b border-slate-100 flex justify-between items-center bg-slate-50/50">
            <h3 className="font-semibold text-sm">Your Rooms</h3>
            <button onClick={() => setMobileRoomsOpen(false)}><X className="w-4 h-4 text-slate-400" /></button>
          </div>
          <div className="overflow-y-auto p-2">
            {rooms?.map((room: any) => (
              <Link
                key={room.id}
                href={`/dashboard?room=${getSlug(room.name)}`}
                onClick={() => setMobileRoomsOpen(false)}
                className="flex items-center gap-3 p-3 rounded-xl hover:bg-slate-50 transition-colors active:bg-slate-100"
              >
                {room.type === "branch" ? (
                  <div className="p-2 bg-blue-50 rounded-lg"><Users className="w-4 h-4 text-blue-500" /></div>
                ) : room.type === "founder" ? (
                  <div className="p-2 bg-purple-50 rounded-lg"><User className="w-4 h-4 text-purple-500" /></div>
                ) : (
                  <div className="p-2 bg-green-50 rounded-lg"><Users className="w-4 h-4 text-green-500" /></div>
                )}
                {room.name}
              </Link>
            ))}
            {currentUser?.role === "owner" && (
              <>
                <div className="mx-4 my-2 border-t border-slate-100"></div>
                <Link
                  href="/dashboard/staff"
                  onClick={() => setMobileRoomsOpen(false)}
                  className="flex items-center gap-3 px-4 py-3 text-sm font-medium rounded-xl hover:bg-slate-50 transition-colors text-indigo-600"
                >
                  <div className="p-2 bg-indigo-50 rounded-lg"><UserPlus className="w-4 h-4" /></div>
                  Staff Management
                </Link>
              </>
            )}
          </div>
        </div>
      )}

      {/* Mobile Profile Drawer */}
      {mobileProfileOpen && (
        <div className="md:hidden fixed bottom-[60px] left-0 right-0 bg-white border-t border-slate-200 rounded-t-2xl shadow-[0_-10px_40px_rgba(0,0,0,0.1)] z-40 overflow-hidden flex flex-col">
          <div className="p-4 border-b border-slate-100 flex justify-between items-center bg-slate-50">
            <h3 className="font-semibold text-sm">Profile Account</h3>
            <button onClick={() => setMobileProfileOpen(false)}><X className="w-4 h-4 text-slate-400" /></button>
          </div>
          <div className="p-6 flex flex-col items-center">
            <div className="w-16 h-16 bg-indigo-100 text-indigo-600 rounded-full flex items-center justify-center text-xl font-bold mb-3">
              {currentUser?.name?.charAt(0)}
            </div>
            <h2 className="text-lg font-bold text-slate-800">{currentUser?.name}</h2>
            <p className="text-sm text-slate-500 capitalize mb-6">{currentUser?.role.replace('_', ' ')}</p>
            
            <div className="w-full space-y-2">
              <ChangePasswordDialog />
              <Button onClick={handleLogout} className="w-full bg-slate-900 text-white rounded-xl h-12 hover:bg-slate-800 transition-colors">
                <LogOut className="w-4 h-4 mr-2" /> Log Out
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Mobile Notifications Drawer */}
      {showNotifications && (
        <div className="md:hidden fixed bottom-[60px] left-0 right-0 bg-white border-t border-slate-200 rounded-t-2xl shadow-[0_-10px_40px_rgba(0,0,0,0.1)] z-40 max-h-[60vh] overflow-hidden flex flex-col">
          <div className="p-4 border-b border-slate-100 flex justify-between items-center bg-slate-50">
            <h3 className="font-semibold text-sm">Notifications</h3>
            <button onClick={() => setShowNotifications(false)}><X className="w-4 h-4 text-slate-400" /></button>
          </div>
          <div className="overflow-y-auto p-2">
            {notifications?.length === 0 ? (
              <div className="p-8 text-center text-sm text-zinc-500">No notifications</div>
            ) : (
              <div className="flex flex-col gap-2">
                {notifications?.map((notif: any) => (
                  <div key={notif.id} className={`p-4 rounded-xl text-sm flex gap-3 ${notif.is_read ? 'opacity-60 bg-slate-50' : 'bg-indigo-50 border border-indigo-100'}`}>
                    <div className="flex-1">
                      <p className="text-slate-800">{notif.message}</p>
                      <p className="text-xs text-slate-400 mt-2">{new Date(notif.created_at).toLocaleString()}</p>
                    </div>
                    {!notif.is_read && (
                      <button 
                        onClick={() => markReadMutation.mutate(notif.id)}
                        className="text-emerald-500 hover:text-emerald-600 transition-colors self-start mt-1 bg-white rounded-full p-1 shadow-sm"
                        title="Mark as read"
                      >
                        <CheckCircle2 className="w-5 h-5" />
                      </button>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
