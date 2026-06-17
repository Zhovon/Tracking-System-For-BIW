"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchRooms, fetchAllUsers, fetchNotifications, markNotificationRead } from "@/lib/api";
import Link from "next/link";
import { LayoutDashboard, Users, User, Loader2, Bell, CheckCircle2 } from "lucide-react";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useEffect, useState } from "react";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { data: rooms, isLoading, error } = useQuery({
    queryKey: ["rooms"],
    queryFn: fetchRooms,
  });

  const { data: allUsers } = useQuery({
    queryKey: ["allUsers"],
    queryFn: fetchAllUsers,
  });

  const queryClient = useQueryClient();
  const { data: notifications } = useQuery({
    queryKey: ["notifications"],
    queryFn: fetchNotifications,
    refetchInterval: 10000, // Poll every 10s for new notifications
  });

  const unreadCount = notifications?.filter((n: any) => !n.is_read).length || 0;

  const markReadMutation = useMutation({
    mutationFn: (id: string) => markNotificationRead(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["notifications"] }),
  });

  const [currentUser, setCurrentUser] = useState("alice@example.com");
  const [showNotifications, setShowNotifications] = useState(false);

  useEffect(() => {
    if (typeof window !== "undefined") {
      const stored = localStorage.getItem("mock_user");
      if (stored) setCurrentUser(stored);
    }
  }, []);

  const handleUserChange = (email: string) => {
    if (typeof window !== "undefined") {
      localStorage.setItem("mock_user", email);
      window.location.reload(); // Refresh to re-fetch rooms and tickets for new user
    }
  };

  return (
    <div className="flex h-screen overflow-hidden bg-zinc-50 dark:bg-zinc-950 text-zinc-900 dark:text-zinc-50">
      {/* Sidebar */}
      <aside className="w-64 flex-shrink-0 border-r border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 flex flex-col">
        <div className="h-16 flex items-center justify-between px-6 border-b border-zinc-200 dark:border-zinc-800 relative">
          <h1 className="text-lg font-bold flex items-center gap-2">
            <LayoutDashboard className="w-5 h-5" />
            Ticketing System
          </h1>
          
          {/* Notification Bell */}
          <div className="relative">
            <button 
              className="p-2 rounded-full hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors relative"
              onClick={() => setShowNotifications(!showNotifications)}
            >
              <Bell className="w-5 h-5 text-zinc-600 dark:text-zinc-400" />
              {unreadCount > 0 && (
                <span className="absolute top-1 right-1 w-2.5 h-2.5 bg-red-500 rounded-full border-2 border-white dark:border-zinc-900" />
              )}
            </button>
            
            {showNotifications && (
              <div className="absolute top-full left-0 mt-2 w-80 bg-white dark:bg-zinc-900 rounded-xl shadow-xl border border-zinc-200 dark:border-zinc-800 z-50 overflow-hidden">
                <div className="p-3 border-b border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-950 font-semibold text-sm">
                  Notifications
                </div>
                <div className="max-h-96 overflow-y-auto">
                  {notifications?.length === 0 ? (
                    <div className="p-4 text-center text-sm text-zinc-500">No notifications</div>
                  ) : (
                    <div className="divide-y divide-zinc-100 dark:divide-zinc-800">
                      {notifications?.map((notif: any) => (
                        <div key={notif.id} className={`p-3 text-sm flex gap-3 ${notif.is_read ? 'opacity-60' : 'bg-blue-50/50 dark:bg-zinc-800/50'}`}>
                          <div className="flex-1">
                            <p className="text-zinc-800 dark:text-zinc-200">{notif.message}</p>
                            <p className="text-xs text-zinc-400 mt-1">{new Date(notif.created_at).toLocaleString()}</p>
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
              </div>
            )}
          </div>
        </div>

        <div className="flex-1 overflow-y-auto py-4">
          <nav className="space-y-1 px-3">
            <h2 className="px-3 text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-2 mt-4">
              Your Rooms
            </h2>
            
            {isLoading && (
              <div className="flex justify-center p-4">
                <Loader2 className="w-5 h-5 animate-spin text-zinc-400" />
              </div>
            )}
            
            {error && (
              <div className="px-3 text-sm text-red-500">Failed to load rooms</div>
            )}

            {rooms?.map((room: any) => (
              <Link
                key={room.id}
                href={`/dashboard?room_id=${room.id}`}
                className="flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-md hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors"
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
          </nav>
        </div>

        <div className="p-4 border-t border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-900/50">
          <h2 className="text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-2">Switch User (Test)</h2>
          <Select value={currentUser} onValueChange={handleUserChange}>
            <SelectTrigger className="w-full h-8 text-xs bg-white dark:bg-zinc-950">
              <SelectValue placeholder="Select user" />
            </SelectTrigger>
            <SelectContent>
              {allUsers?.map((u: any) => (
                <SelectItem key={u.id} value={u.email} className="text-xs">
                  {u.name} ({u.role})
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {children}
      </main>
    </div>
  );
}
