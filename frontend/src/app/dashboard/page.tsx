"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchTickets, fetchTicketDetails, postMessage, updateTicket, fetchAllUsers, fetchAllRooms, approveTicket } from "@/lib/api";
import { useSearchParams, useRouter } from "next/navigation";
import { Suspense, useState, useEffect } from "react";
import { Loader2, Ticket, MessageSquare, Send, CheckCircle2, AlertCircle } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { CreateTicketDialog } from "@/components/CreateTicketDialog";

function DashboardContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  
  const roomId = searchParams.get("room_id");
  const ticketId = searchParams.get("ticket_id");
  const [sortBy, setSortBy] = useState<"newest" | "oldest">("newest");
  const [comment, setComment] = useState("");
  const queryClient = useQueryClient();

  const { data: fetchedTickets, isLoading, error } = useQuery({
    queryKey: ["tickets", roomId],
    queryFn: () => fetchTickets(roomId || undefined),
    enabled: true,
  });

  const tickets = fetchedTickets ? [...fetchedTickets].sort((a, b) => {
    if (sortBy === "newest") {
      return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
    }
    return new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
  }) : [];

  const { data: selectedTicket, isLoading: isTicketLoading } = useQuery({
    queryKey: ["ticket", ticketId],
    queryFn: () => fetchTicketDetails(ticketId as string),
    enabled: !!ticketId,
  });

  const postMessageMutation = useMutation({
    mutationFn: (content: string) => postMessage(ticketId as string, content),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["ticket", ticketId] });
      setComment("");
    }
  });

  const updateTicketMutation = useMutation({
    mutationFn: (updates: any) => updateTicket(ticketId as string, updates),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["ticket", ticketId] });
      queryClient.invalidateQueries({ queryKey: ["tickets"] });
    }
  });

  const { data: allUsers } = useQuery({
    queryKey: ["allUsers"],
    queryFn: fetchAllUsers,
  });

  const [currentUserEmail, setCurrentUserEmail] = useState("alice@example.com");
  useEffect(() => {
    if (typeof window !== "undefined") {
      setCurrentUserEmail(localStorage.getItem("mock_user") || "alice@example.com");
    }
  }, []);
  
  const currentUserRole = allUsers?.find((u: any) => u.email === currentUserEmail)?.role || "";

  const approveTicketMutation = useMutation({
    mutationFn: () => approveTicket(ticketId as string),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["ticket", ticketId] });
      queryClient.invalidateQueries({ queryKey: ["tickets"] });
    }
  });

  const { data: allRooms } = useQuery({
    queryKey: ["allRooms"],
    queryFn: fetchAllRooms,
  });

  const getStatusColor = (status: string) => {
    switch (status) {
      case "open": return "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200";
      case "in_progress": return "bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200";
      case "approved": return "bg-emerald-100 text-emerald-800 dark:bg-emerald-900 dark:text-emerald-200";
      case "resolved": return "bg-zinc-100 text-zinc-800 dark:bg-zinc-800 dark:text-zinc-200";
      default: return "bg-zinc-100 text-zinc-800";
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case "high": return "text-red-600 dark:text-red-400";
      case "medium": return "text-amber-600 dark:text-amber-400";
      case "low": return "text-green-600 dark:text-green-400";
      default: return "text-zinc-600";
    }
  };

  return (
    <div className="flex flex-1 h-full overflow-hidden bg-white dark:bg-zinc-950">
      {/* Middle Column (Feed) */}
      <div className={`flex flex-col border-r border-zinc-200 dark:border-zinc-800 ${ticketId ? 'w-1/3 min-w-[320px] max-w-sm hidden md:flex' : 'w-full'}`}>
        <div className="p-4 border-b border-zinc-200 dark:border-zinc-800 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <h2 className="text-lg font-semibold flex items-center gap-2">
              <Ticket className="w-5 h-5 text-zinc-500" />
              Tickets
            </h2>
            {roomId && (
              <Badge variant="outline" className="text-xs font-normal text-zinc-500">
                Filtered
              </Badge>
            )}
          </div>
          {["owner", "manager", "hr", "it_team"].includes(currentUserRole) && (
            <CreateTicketDialog roomId={roomId} />
          )}
        </div>
        
        <div className="flex-1 overflow-y-auto">
          {isLoading ? (
            <div className="p-8 flex justify-center text-zinc-400">
              <Loader2 className="w-6 h-6 animate-spin" />
            </div>
          ) : error ? (
            <div className="p-8 text-center text-red-500 text-sm">
              Failed to load tickets.
            </div>
          ) : tickets?.length === 0 ? (
            <div className="p-8 text-center text-zinc-500 text-sm">
              No tickets found in this room.
            </div>
          ) : (
            <div className="divide-y divide-zinc-200 dark:divide-zinc-800">
              {tickets?.map((ticket: any) => (
                <div
                  key={ticket.id}
                  onClick={() => router.push(`?${new URLSearchParams({
                    ...(roomId && { room_id: roomId }),
                    ticket_id: ticket.id
                  }).toString()}`)}
                  className={`p-4 cursor-pointer hover:bg-zinc-50 dark:hover:bg-zinc-900 transition-colors ${
                    ticket.id === ticketId ? "bg-blue-50/50 dark:bg-zinc-800/50" : ""
                  }`}
                >
                  <div className="flex justify-between items-start mb-2">
                    <span className="text-xs font-medium uppercase tracking-wider flex items-center gap-1">
                      <span className={`w-2 h-2 rounded-full ${getPriorityColor(ticket.priority).replace('text-', 'bg-').replace('dark:text-', 'dark:bg-')}`} />
                      {ticket.priority}
                    </span>
                    <div className="flex gap-1">
                      {ticket.approval_status === "pending" && (
                        <Badge variant="outline" className="text-[10px] uppercase font-bold text-amber-500 border-amber-200">
                          Pending
                        </Badge>
                      )}
                      <Badge variant="secondary" className={`text-[10px] uppercase font-bold border-none ${getStatusColor(ticket.status)}`}>
                        {ticket.status.replace("_", " ")}
                      </Badge>
                    </div>
                  </div>
                  <h3 className="font-semibold text-zinc-900 dark:text-zinc-100 text-sm mb-1 leading-tight line-clamp-2">
                    {ticket.title}
                  </h3>
                  <div className="flex items-center gap-2 mt-3 text-xs text-zinc-500">
                    <span className="truncate flex-1">
                      {ticket.creator.name}
                    </span>
                    <span className="flex-shrink-0">
                      {new Date(ticket.created_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Right Panel (Detail View) */}
      {ticketId ? (
        <div className="flex-1 flex flex-col bg-zinc-50 dark:bg-zinc-900 overflow-hidden">
          {selectedTicket ? (
            <>
              <div className="p-6 bg-white dark:bg-zinc-950 border-b border-zinc-200 dark:border-zinc-800 flex-shrink-0">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-2">
                    {selectedTicket.approval_status === "pending" && (
                      <Badge variant="outline" className="text-amber-500 border-amber-200 uppercase text-xs tracking-wider">
                        Pending Approval
                      </Badge>
                    )}
                    <Badge variant="secondary" className={`${getStatusColor(selectedTicket.status)} uppercase text-xs tracking-wider border-none`}>
                      {selectedTicket.status.replace("_", " ")}
                    </Badge>
                    <span className={`text-sm font-medium uppercase flex items-center gap-1 ${getPriorityColor(selectedTicket.priority)}`}>
                      Priority: {selectedTicket.priority}
                    </span>
                  </div>
                  <div className="flex gap-2">
                    {selectedTicket.approval_status === "pending" && currentUserRole === "owner" && (
                      <Button 
                        variant="default" 
                        size="sm" 
                        className="bg-amber-500 hover:bg-amber-600 text-white"
                        onClick={() => approveTicketMutation.mutate()}
                        disabled={approveTicketMutation.isPending}
                      >
                        <CheckCircle2 className="w-4 h-4 mr-2" />
                        Approve
                      </Button>
                    )}
                    {selectedTicket.status !== "resolved" && (
                      <Button 
                        variant="outline" 
                        size="sm" 
                        className="text-emerald-600 border-emerald-200 hover:bg-emerald-50 dark:hover:bg-emerald-900/20"
                        onClick={() => updateTicketMutation.mutate({ status: "resolved" })}
                        disabled={updateTicketMutation.isPending}
                      >
                        <CheckCircle2 className="w-4 h-4 mr-2" />
                        Mark Resolved
                      </Button>
                    )}
                  </div>
                </div>
                <h1 className="text-2xl font-bold text-zinc-900 dark:text-zinc-50 mb-2">
                  {selectedTicket.title}
                </h1>
                
                <div className="flex gap-4 mt-4 mb-2">
                  <div className="flex-1">
                    <p className="text-xs font-semibold text-zinc-500 uppercase mb-1">Assignee</p>
                    <Select 
                      value={selectedTicket.assignee?.id || "unassigned"} 
                      onValueChange={(val) => updateTicketMutation.mutate({ assigned_to_id: val })}
                      disabled={updateTicketMutation.isPending || selectedTicket.status === "resolved"}
                    >
                      <SelectTrigger className="h-8 text-xs w-[180px]">
                        <SelectValue placeholder="Unassigned" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="unassigned" disabled>Unassigned</SelectItem>
                        {allUsers?.map((u: any) => (
                          <SelectItem key={u.id} value={u.id} className="text-xs">
                            {u.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="flex-1">
                    <p className="text-xs font-semibold text-zinc-500 uppercase mb-1">Escalate to Room</p>
                    <Select 
                      value="placeholder"
                      onValueChange={(val) => updateTicketMutation.mutate({ add_room_id: val })}
                      disabled={updateTicketMutation.isPending || selectedTicket.status === "resolved"}
                    >
                      <SelectTrigger className="h-8 text-xs w-[180px]">
                        <SelectValue placeholder="Add Room..." />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="placeholder" disabled>Add Room...</SelectItem>
                        {allRooms?.filter((r: any) => !selectedTicket.rooms?.some((tr: any) => tr.id === r.id)).map((r: any) => (
                          <SelectItem key={r.id} value={r.id} className="text-xs">
                            {r.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="flex flex-wrap gap-1 mt-3 mb-4">
                  {selectedTicket.rooms?.map((room: any) => (
                    <Badge key={room.id} variant="secondary" className="bg-zinc-100 text-zinc-600 border border-zinc-200">
                      #{room.name}
                    </Badge>
                  ))}
                </div>

                <div className="bg-zinc-50 dark:bg-zinc-900 rounded-xl p-4 border border-zinc-100 dark:border-zinc-800">
                  <span>Opened by <strong className="text-zinc-700 dark:text-zinc-300">{selectedTicket.creator.name}</strong></span>
                  <span>•</span>
                  <span>{new Date(selectedTicket.created_at).toLocaleString()}</span>
                </div>
              </div>
              
              <div className="flex-1 overflow-y-auto p-6 bg-zinc-50 dark:bg-zinc-900">
                <div className="max-w-4xl mx-auto">
                  {/* Original Description */}
                  <div className="mb-8 bg-white dark:bg-zinc-950 rounded-xl p-5 shadow-sm border border-zinc-100 dark:border-zinc-800">
                    <h3 className="text-sm font-semibold text-zinc-900 dark:text-zinc-100 mb-3 border-b border-zinc-100 dark:border-zinc-800 pb-2">Description</h3>
                    <p className="text-zinc-700 dark:text-zinc-300 text-sm whitespace-pre-wrap leading-relaxed">
                      {selectedTicket.description}
                    </p>
                  </div>
                  
                  {/* Thread Area */}
                  <div className="flex items-center gap-2 text-sm font-medium text-zinc-500 mb-4 uppercase tracking-wider">
                    <MessageSquare className="w-4 h-4" />
                    Thread
                  </div>
                  
                  <div className="space-y-4 mb-8">
                    {selectedTicket.messages?.map((msg: any) => (
                      msg.type === "status_change" ? (
                        <div key={msg.id} className="flex justify-center my-4">
                          <span className="text-xs font-medium text-zinc-400 bg-zinc-100 dark:bg-zinc-800/50 px-3 py-1 rounded-full">
                            {msg.author.name} {msg.content.toLowerCase()}
                          </span>
                        </div>
                      ) : (
                        <div key={msg.id} className="bg-white dark:bg-zinc-950 rounded-xl p-4 shadow-sm border border-zinc-100 dark:border-zinc-800">
                          <div className="flex items-center justify-between mb-2">
                            <span className="font-semibold text-sm text-zinc-900 dark:text-zinc-100">{msg.author.name}</span>
                            <span className="text-xs text-zinc-400">{new Date(msg.created_at).toLocaleString()}</span>
                          </div>
                          <p className="text-sm text-zinc-700 dark:text-zinc-300 whitespace-pre-wrap">{msg.content}</p>
                        </div>
                      )
                    ))}
                    
                    {selectedTicket.messages?.length === 0 && (
                      <div className="text-center text-zinc-400 text-sm py-4">
                        No messages yet. Start the conversation!
                      </div>
                    )}
                  </div>
                  
                  {/* Reply Box */}
                  <div className="bg-white dark:bg-zinc-950 rounded-xl border border-zinc-200 dark:border-zinc-800 p-4 shadow-sm">
                    <Textarea 
                      placeholder="Type your message here..."
                      className="min-h-[100px] border-none focus-visible:ring-0 shadow-none resize-none p-0"
                      value={comment}
                      onChange={(e) => setComment(e.target.value)}
                    />
                    <div className="flex justify-end mt-2 pt-2 border-t border-zinc-100 dark:border-zinc-800">
                      <Button 
                        size="sm" 
                        disabled={!comment.trim() || postMessageMutation.isPending}
                        onClick={() => postMessageMutation.mutate(comment)}
                      >
                        {postMessageMutation.isPending ? "Sending..." : "Send Message"}
                        {!postMessageMutation.isPending && <Send className="w-4 h-4 ml-2" />}
                      </Button>
                    </div>
                  </div>
                </div>
              </div>
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center text-zinc-500">
              Loading ticket details...
            </div>
          )}
        </div>
      ) : (
        <div className="hidden md:flex flex-1 flex-col items-center justify-center bg-zinc-50/50 dark:bg-zinc-900/50 text-zinc-400">
          <Ticket className="w-16 h-16 mb-4 text-zinc-200 dark:text-zinc-800" />
          <p className="text-lg font-medium text-zinc-500">Select a ticket to view details</p>
          <p className="text-sm text-zinc-400 max-w-sm text-center mt-2">
            Click on any ticket in the feed on the left to see its full description and message thread.
          </p>
        </div>
      )}
    </div>
  );
}

export default function DashboardPage() {
  return (
    <Suspense fallback={<div className="p-8 flex justify-center text-zinc-400"><Loader2 className="w-6 h-6 animate-spin" /></div>}>
      <DashboardContent />
    </Suspense>
  );
}
