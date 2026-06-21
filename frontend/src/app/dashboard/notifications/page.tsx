"use client";

import { useInfiniteQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchNotifications, markNotificationRead } from "@/lib/api";
import { Loader2, Bell, CheckCircle2, ChevronDown } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useEffect, Fragment } from "react";
import { supabase } from "@/lib/supabase";

export default function NotificationsPage() {
  const queryClient = useQueryClient();

  const {
    data,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    status,
  } = useInfiniteQuery({
    queryKey: ["notifications_page"],
    queryFn: async ({ pageParam = 0 }) => {
      return fetchNotifications(pageParam, 20);
    },
    initialPageParam: 0,
    getNextPageParam: (lastPage, allPages) => {
      if (lastPage.length < 20) {
        return undefined; // No more pages
      }
      return allPages.length * 20; // next skip value
    },
  });

  const markReadMutation = useMutation({
    mutationFn: (id: string) => markNotificationRead(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications_page"] });
      queryClient.invalidateQueries({ queryKey: ["notifications"] }); // Update layout bell too
    },
  });

  // Keep page updated in real-time
  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      if (!session) return;
      const channel = supabase.channel('notifications_page_changes')
        .on(
          'postgres_changes',
          { event: '*', schema: 'public', table: 'notifications', filter: `user_id=eq.${session.user.id}` },
          () => {
            queryClient.invalidateQueries({ queryKey: ["notifications_page"] });
          }
        )
        .subscribe();
      return () => {
        supabase.removeChannel(channel);
      };
    });
  }, [queryClient]);

  if (status === "pending") {
    return (
      <div className="flex-1 flex items-center justify-center bg-slate-50">
        <Loader2 className="w-8 h-8 animate-spin text-indigo-500" />
      </div>
    );
  }

  if (status === "error") {
    return (
      <div className="flex-1 flex flex-col items-center justify-center text-red-500 bg-slate-50">
        <p>Error loading notifications</p>
      </div>
    );
  }

  const allNotifications = data?.pages.flatMap(page => page) || [];

  return (
    <div className="flex-1 flex justify-center bg-slate-50 overflow-y-auto w-full">
      <div className="w-full max-w-2xl bg-white shadow-sm min-h-full border-x border-slate-200">
        <div className="p-4 md:p-6 border-b border-slate-200 bg-white sticky top-0 z-10">
          <h2 className="text-xl font-bold flex items-center gap-2 text-slate-800">
            <Bell className="w-6 h-6 text-indigo-500" />
            Notifications
          </h2>
        </div>

        <div className="divide-y divide-slate-100">
          {allNotifications.length === 0 ? (
            <div className="p-12 text-center text-slate-500 flex flex-col items-center">
              <Bell className="w-12 h-12 text-slate-200 mb-4" />
              <p>You have no notifications yet.</p>
            </div>
          ) : (
            allNotifications.map((notif: any) => (
              <div 
                key={notif.id} 
                className={`p-4 md:p-5 flex gap-4 transition-colors ${
                  notif.is_read ? 'opacity-60 bg-white' : 'bg-indigo-50/50'
                }`}
              >
                <div className="flex-1">
                  <p className={`text-[15px] ${notif.is_read ? 'text-slate-600' : 'text-slate-900 font-medium'}`}>
                    {notif.message}
                  </p>
                  <p className="text-xs text-slate-400 mt-2 font-medium">
                    {new Date(notif.created_at).toLocaleString()}
                  </p>
                </div>
                {!notif.is_read && (
                  <button 
                    onClick={() => markReadMutation.mutate(notif.id)}
                    className="text-emerald-500 hover:text-emerald-600 transition-colors self-center p-2 rounded-full hover:bg-emerald-50 active:scale-95"
                    title="Mark as read"
                  >
                    <CheckCircle2 className="w-6 h-6" />
                  </button>
                )}
              </div>
            ))
          )}
        </div>

        {hasNextPage && (
          <div className="p-6 flex justify-center border-t border-slate-100">
            <Button
              variant="outline"
              size="lg"
              onClick={() => fetchNextPage()}
              disabled={isFetchingNextPage}
              className="w-full md:w-auto min-w-[200px]"
            >
              {isFetchingNextPage ? (
                <Loader2 className="w-4 h-4 animate-spin mr-2" />
              ) : (
                <ChevronDown className="w-4 h-4 mr-2" />
              )}
              {isFetchingNextPage ? "Loading more..." : "Load More"}
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
